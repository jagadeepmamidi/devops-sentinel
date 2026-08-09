"""
Custom Health Check Tool - Execute Python/Bash Scripts
=====================================================

Enables custom health checks beyond basic HTTP:
- Python scripts
- Bash/Shell scripts  
- TCP port checks
- DNS resolution checks
"""

import asyncio
import subprocess
import socket
import dns.resolver
from typing import Dict, Optional, Tuple
from datetime import datetime
import tempfile
import os


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
        check_config: Dict
    ) -> Dict:
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
    
    async def execute_script_check(self, config: Dict) -> Dict:
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
        
        start_time = datetime.utcnow()
        
        try:
            # Write script to temp file
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py' if script_type == 'python' else '.sh',
                delete=False
            ) as f:
                f.write(script)
                script_path = f.name
            
            # Execute script
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
                return {
                    'is_healthy': False,
                    'error': f'Script execution timeout ({self.timeout}s)',
                    'response_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
                }
            
            # Clean up temp file
            os.unlink(script_path)
            
            exit_code = process.returncode
            output = stdout.decode('utf-8').strip()
            error_output = stderr.decode('utf-8').strip()
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Check success criteria
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
            
        except Exception as e:
            return {
                'is_healthy': False,
                'error': f'Script execution failed: {str(e)}',
                'response_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
            }
    
    async def execute_tcp_check(self, config: Dict) -> Dict:
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
        
        start_time = datetime.utcnow()
        
        try:
            # Attempt TCP connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
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
        except Exception as e:
            return {
                'is_healthy': False,
                'error': f'TCP connection failed: {str(e)}',
                'response_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
            }
    
    async def execute_dns_check(self, config: Dict) -> Dict:
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
        
        start_time = datetime.utcnow()
        
        try:
            # Resolve DNS
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout
            
            answers = await asyncio.to_thread(
                resolver.resolve,
                hostname,
                record_type
            )
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Extract IPs
            resolved_ips = [str(rdata) for rdata in answers]
            
            # Check if expected IP matches
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
                'response_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
            }
        except dns.resolver.Timeout:
            return {
                'is_healthy': False,
                'error': f'DNS resolution timeout for {hostname}',
                'response_time_ms': self.timeout * 1000
            }
        except Exception as e:
            return {
                'is_healthy': False,
                'error': f'DNS resolution failed: {str(e)}',
                'response_time_ms': (datetime.utcnow() - start_time).total_seconds() * 1000
            }


# Example usage
if __name__ == "__main__":
    async def test_custom_checks():
        tool = CustomHealthCheckTool(timeout_seconds=10)
        
        # Test Python script check
        print("Testing Python script check...")
        result = await tool.execute_script_check({
            'script': 'import sys\nprint("OK")\nsys.exit(0)',
            'script_type': 'python',
            'expected_output': 'OK'
        })
        print(f"Result: {result}\n")
        
        # Test TCP check
        print("Testing TCP check...")
        result = await tool.execute_tcp_check({
            'host': 'google.com',
            'port': 443
        })
        print(f"Result: {result}\n")
        
        # Test DNS check
        print("Testing DNS check...")
        result = await tool.execute_dns_check({
            'hostname': 'google.com'
        })
        print(f"Result: {result}")
    
    asyncio.run(test_custom_checks())
