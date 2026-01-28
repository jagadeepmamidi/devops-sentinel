"""
SSL Certificate Monitor - Track SSL Expiration
==============================================

Monitors SSL certificate expiration and alerts before expiry
"""

import ssl
import socket
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import asyncio


class SSLCertificateMonitor:
    """
    Monitor SSL certificate expiration dates
    
    Features:
    - Check certificate expiration
    - Alert at configurable thresholds (30 days, 7 days, 1 day)
    - Track certificate details (issuer, subject, validity)
    """
    
    def __init__(self):
        self.default_alert_days = [30, 7, 1]  # Alert at 30, 7, and 1 day before expiry
    
    async def check_certificate(
        self,
        hostname: str,
        port: int = 443,
        alert_days: Optional[list] = None
    ) -> Dict:
        """
        Check SSL certificate for a domain
        
        Args:
            hostname: Domain to check
            port: SSL port (default 443)
            alert_days: List of days before expiry to alert
        
        Returns:
            Certificate status dict
        """
        if alert_days is None:
            alert_days = self.default_alert_days
        
        try:
            # Get SSL certificate
            cert = await asyncio.to_thread(
                self._get_certificate,
                hostname,
                port
            )
            
            if not cert:
                return {
                    'is_healthy': False,
                    'error': 'Failed to retrieve certificate'
                }
            
            # Parse certificate
            not_after = cert.get('notAfter')
            not_before = cert.get('notBefore')
            subject = dict(x[0] for x in cert.get('subject', []))
            issuer = dict(x[0] for x in cert.get('issuer', []))
            
            # Parse expiration date
            expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            issue_date = datetime.strptime(not_before, '%b %d %H:%M:%S %Y %Z')
            now = datetime.utcnow()
            
            # Calculate days until expiry
            days_until_expiry = (expiry_date - now).days
            
            # Determine if we should alert
            should_alert = days_until_expiry in alert_days or days_until_expiry < 0
            
            # Determine health status
            is_healthy = days_until_expiry > min(alert_days)
            
            # Build alert message
            alert_message = None
            if days_until_expiry < 0:
                alert_message = f"SSL certificate EXPIRED {abs(days_until_expiry)} days ago!"
            elif should_alert:
                alert_message = f"SSL certificate expires in {days_until_expiry} days"
            
            return {
                'is_healthy': is_healthy,
                'days_until_expiry': days_until_expiry,
                'expiry_date': expiry_date.isoformat(),
                'issue_date': issue_date.isoformat(),
                'subject': subject.get('commonName', hostname),
                'issuer': issuer.get('organizationName', 'Unknown'),
                'should_alert': should_alert,
                'alert_message': alert_message,
                'certificate_valid': days_until_expiry > 0
            }
            
        except socket.gaierror:
            return {
                'is_healthy': False,
                'error': f'DNS resolution failed for {hostname}'
            }
        except socket.timeout:
            return {
                'is_healthy': False,
                'error': f'Connection timeout to {hostname}:{port}'
            }
        except Exception as e:
            return {
                'is_healthy': False,
                'error': f'Certificate check failed: {str(e)}'
            }
    
    def _get_certificate(self, hostname: str, port: int) -> Optional[Dict]:
        """
        Synchronously retrieve SSL certificate
        
        Args:
            hostname: Domain name
            port: SSL port
        
        Returns:
            Certificate dict or None
        """
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                return cert
    
    async def check_multiple_domains(
        self,
        domains: list,
        alert_days: Optional[list] = None
    ) -> Dict[str, Dict]:
        """
        Check multiple domains in parallel
        
        Args:
            domains: List of domain dicts [{'hostname': 'example.com', 'port': 443}]
            alert_days: Alert thresholds
        
        Returns:
            Dict mapping hostname to certificate status
        """
        tasks = []
        
        for domain in domains:
            hostname = domain.get('hostname')
            port = domain.get('port', 443)
            
            if hostname:
                tasks.append(self.check_certificate(hostname, port, alert_days))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to hostnames
        status_map = {}
        for i, domain in enumerate(domains):
            hostname = domain.get('hostname')
            if hostname:
                result = results[i]
                if isinstance(result, Exception):
                    status_map[hostname] = {
                        'is_healthy': False,
                        'error': str(result)
                    }
                else:
                    status_map[hostname] = result
        
        return status_map
    
    def get_alert_severity(self, days_until_expiry: int) -> str:
        """
        Determine alert severity based on days remaining
        
        Args:
            days_until_expiry: Days until certificate expires
        
        Returns:
            Severity level (P0-P3)
        """
        if days_until_expiry < 0:
            return 'P0'  # Expired!
        elif days_until_expiry <= 1:
            return 'P0'  # Expires within 1 day
        elif days_until_expiry <= 7:
            return 'P1'  # Expires within 7 days
        elif days_until_expiry <= 30:
            return 'P2'  # Expires within 30 days
        else:
            return 'P3'  # > 30 days


# Example usage
if __name__ == "__main__":
    async def test_ssl_monitor():
        monitor = SSLCertificateMonitor()
        
        # Test single domain
        print("Checking google.com SSL certificate...")
        result = await monitor.check_certificate('google.com')
        print(f"Result: {result}\n")
        
        # Test multiple domains
        print("Checking multiple domains...")
        domains = [
            {'hostname': 'google.com'},
            {'hostname': 'github.com'},
            {'hostname': 'example.com'}
        ]
        results = await monitor.check_multiple_domains(domains)
        
        for hostname, status in results.items():
            print(f"{hostname}: {status.get('days_until_expiry')} days until expiry")
    
    asyncio.run(test_ssl_monitor())
