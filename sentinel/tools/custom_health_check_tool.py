"""Custom Health Check Tool - Execute Python/Bash Scripts"""

import asyncio
import os
import tempfile
from datetime import datetime, timezone

import dns.exception
import dns.resolver


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CustomHealthCheckTool:
    """
    Execute custom health check scripts and specialized checks

    Supported Check Types:
    - http: Standard HTTP/HTTPS (handled by existing tool)
    - script: Python or Bash script execution
    - tcp: TCP port connectivity
    - dns: DNS resolution test
    - ssl: SSL certificate validation (separate tool)
    """

    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize custom health check tool

        Args:
            timeout_seconds: Max execution time for scripts
        """
        self.timeout = timeout_seconds

    async def execute_check(
        self,
        check_type: str,
        check_config: dict
    ) -> dict:
        """
        Execute health check based on type

        Args:
            check_type: 'script', 'tcp', 'dns', 'http'
            check_config: Configuration dict

        Returns:
            Result dict with is_healthy, response_time, details
        """
        if check_type == 'script':
            return await self.execute_script_check(check_config)
        elif check_type == 'tcp':
            return await self.execute_tcp_check(check_config)
        elif check_type == 'dns':
            return await self.execute_dns_check(check_config)
        else:
            return {
                'is_healthy': False,
                'error': f'Unknown check type: {check_type}'
            }

    async def execute_script_check(self, config: dict) -> dict:
        """
        Execute Python or Bash script

        Config format:
        {
            'script': 'python script content or bash commands',
            'script_type': 'python' or 'bash',
            'expected_output': 'OK' (optional),
            'expected_exit_code': 0 (optional)
        }

        Returns:
            Health check result
        """
        script = config.get('script', '')
        script_type = config.get('script_type', 'bash')
        expected_output = config.get('expected_output')
        expected_exit_code = config.get('expected_exit_code', 0)

        if not script:
            return {
                'is_healthy': False,
                'error': 'No script provided'
            }

        if os.getenv('SENTINEL_ALLOW_SCRIPT_CHECKS', '').lower() != 'true':
            return {
                'is_healthy': False,
                'error': 'Script health checks are disabled; set SENTINEL_ALLOW_SCRIPT_CHECKS=true in a trusted environment'
            }

        if script_type not in {'python', 'bash'}:
            return {'is_healthy': False, 'error': 'script_type must be python or bash'}

        start_time = _now()
        script_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py' if script_type == 'python' else '.sh',
                delete=False
            ) as f:
                f.write(script)
                script_path = f.name

            if script_type == 'python':
                cmd = ['python', script_path]
            else:
                cmd = ['bash', script_path]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    'is_healthy': False,
                    'error': f'Script execution timeout ({self.timeout}s)',
                    'response_time_ms': (_now() - start_time).total_seconds() * 1000
                }

            exit_code = process.returncode
            output = stdout.decode('utf-8').strip()
            error_output = stderr.decode('utf-8').strip()

            response_time = (_now() - start_time).total_seconds() * 1000

            is_healthy = (exit_code == expected_exit_code)

            if expected_output and output != expected_output:
                is_healthy = False

            return {
                'is_healthy': is_healthy,
                'response_time_ms': response_time,
                'exit_code': exit_code,
                'output': output,
                'error': error_output if error_output else None,
                'details': f'Script executed with exit code {exit_code}'
            }

        except (OSError, UnicodeError, ValueError) as e:
            return {
                'is_healthy': False,
                'error': f'Script execution failed: {e!s}',
                'response_time_ms': (_now() - start_time).total_seconds() * 1000
            }
        finally:
            if script_path:
                try:
                    os.unlink(script_path)
                except FileNotFoundError:
                    pass

    async def execute_tcp_check(self, config: dict) -> dict:
        """
        Check TCP port connectivity

        Config format:
        {
            'host': 'localhost',
            'port': 5432
        }
        """
        host = config.get('host')
        port = config.get('port')

        if not host or not port:
            return {
                'is_healthy': False,
                'error': 'Missing host or port'
            }

        start_time = _now()

        try:
            _reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )

            writer.close()
            await writer.wait_closed()

            response_time = (_now() - start_time).total_seconds() * 1000

            return {
                'is_healthy': True,
                'response_time_ms': response_time,
                'details': f'TCP connection to {host}:{port} successful'
            }

        except asyncio.TimeoutError:
            return {
                'is_healthy': False,
                'error': f'TCP connection timeout to {host}:{port}',
                'response_time_ms': self.timeout * 1000
            }
        except OSError as e:
            return {
                'is_healthy': False,
                'error': f'TCP connection failed: {e!s}',
                'response_time_ms': (_now() - start_time).total_seconds() * 1000
            }

    async def execute_dns_check(self, config: dict) -> dict:
        """
        Check DNS resolution

        Config format:
        {
            'hostname': 'example.com',
            'expected_ip': '93.184.216.34' (optional),
            'record_type': 'A' (optional, default A)
        }
        """
        hostname = config.get('hostname')
        expected_ip = config.get('expected_ip')
        record_type = config.get('record_type', 'A')

        if not hostname:
            return {
                'is_healthy': False,
                'error': 'Missing hostname'
            }

        start_time = _now()

        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            answers = await asyncio.to_thread(
                resolver.resolve,
                hostname,
                record_type
            )

            response_time = (_now() - start_time).total_seconds() * 1000

            resolved_ips = [str(rdata) for rdata in answers]

            is_healthy = True
            if expected_ip and expected_ip not in resolved_ips:
                is_healthy = False

            return {
                'is_healthy': is_healthy,
                'response_time_ms': response_time,
                'resolved_ips': resolved_ips,
                'details': f'DNS resolved {hostname} to {", ".join(resolved_ips)}'
            }

        except dns.resolver.NXDOMAIN:
            return {
                'is_healthy': False,
                'error': f'DNS domain not found: {hostname}',
                'response_time_ms': (_now() - start_time).total_seconds() * 1000
            }
        except dns.resolver.Timeout:
            return {
                'is_healthy': False,
                'error': f'DNS resolution timeout for {hostname}',
                'response_time_ms': self.timeout * 1000
            }
        except dns.exception.DNSException as e:
            return {
                'is_healthy': False,
                'error': f'DNS resolution failed: {e!s}',
                'response_time_ms': (_now() - start_time).total_seconds() * 1000
            }
