"""
Email Notification System - SMTP-Based Alerting
================================================

Send email notifications for incidents, postmortems, and digests
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailNotificationSystem:
    """
    Email notification system for DevOps Sentinel
    
    Features:
    - Incident alerts (immediate)
    - Daily/weekly digest emails
    - Postmortem delivery
    - Custom templates per severity
    - HTML + plain text emails
    - Attachment support
    """
    
    def __init__(self, smtp_config: Dict):
        """
        Initialize email system
        
        Args:
            smtp_config: {
                'host': 'smtp.gmail.com',
                'port': 587,
                'username': 'alerts@company.com',
                'password': 'app_password',
                'from_email': 'DevOps Sentinel <alerts@company.com>',
                'use_tls': True
            }
        """
        self.host = smtp_config['host']
        self.port = smtp_config['port']
        self.username = smtp_config['username']
        self.password = smtp_config['password']
        self.from_email = smtp_config.get('from_email', smtp_config['username'])
        self.use_tls = smtp_config.get('use_tls', True)
    
    async def send_incident_alert(
        self,
        incident: Dict,
        recipients: List[str]
    ) -> Dict:
        """
        Send immediate incident alert
        
        Args:
            incident: Incident data
            recipients: List of email addresses
        
        Returns:
            Send status
        """
        severity = incident.get('severity', 'P2')
        service_name = incident.get('service_name', 'Unknown Service')
        
        subject = f"[{severity}] {service_name} - {incident.get('failure_type', 'Incident')}"
        
        # HTML email body
        html_body = self._render_incident_email(incident)
        
        # Plain text fallback
        text_body = self._render_incident_text(incident)
        
        return await self._send_email(
            recipients=recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    async def send_postmortem(
        self,
        incident: Dict,
        postmortem: str,
        recipients: List[str]
    ) -> Dict:
        """
        Send postmortem report
        
        Args:
            incident: Incident data
            postmortem: AI-generated postmortem
            recipients: Email addresses
        """
        service_name = incident.get('service_name', 'Unknown')
        incident_id = incident['id']
        
        subject = f"Postmortem: {service_name} Incident ({incident_id})"
        
        html_body = self._render_postmortem_email(incident, postmortem)
        text_body = f"Postmortem Report\n\n{postmortem}"
        
        return await self._send_email(
            recipients=recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    async def send_daily_digest(
        self,
        incidents: List[Dict],
        stats: Dict,
        recipients: List[str]
    ) -> Dict:
        """
        Send daily incident digest
        
        Args:
            incidents: List of incidents from last 24h
            stats: Summary statistics
            recipients: Email addresses
        """
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        subject = f"DevOps Sentinel Daily Digest - {date_str}"
        
        html_body = self._render_digest_email(incidents, stats, 'daily')
        text_body = self._render_digest_text(incidents, stats)
        
        return await self._send_email(
            recipients=recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    async def send_weekly_digest(
        self,
        incidents: List[Dict],
        stats: Dict,
        recipients: List[str]
    ) -> Dict:
        """Send weekly incident digest"""
        week_start = (datetime.utcnow() - timedelta(days=7)).strftime('%m/%d')
        week_end = datetime.utcnow().strftime('%m/%d')
        
        subject = f"DevOps Sentinel Weekly Digest - {week_start} to {week_end}"
        
        html_body = self._render_digest_email(incidents, stats, 'weekly')
        text_body = self._render_digest_text(incidents, stats)
        
        return await self._send_email(
            recipients=recipients,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    async def _send_email(
        self,
        recipients: List[str],
        subject: str,
        html_body: str,
        text_body: str
    ) -> Dict:
        """
        Send email via SMTP
        
        Returns:
            {'status': 'sent', 'recipients': [...]}
        """
        message = MIMEMultipart('alternative')
        message['From'] = self.from_email
        message['To'] = ', '.join(recipients)
        message['Subject'] = subject
        
        # Attach plain text and HTML parts
        text_part = MIMEText(text_body, 'plain')
        html_part = MIMEText(html_body, 'html')
        
        message.attach(text_part)
        message.attach(html_part)
        
        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                use_tls=self.use_tls
            )
            
            return {
                'status': 'sent',
                'recipients': recipients,
                'sent_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'recipients': recipients
            }
    
    def _render_incident_email(self, incident: Dict) -> str:
        """Generate HTML email for incident"""
        severity = incident.get('severity', 'P2')
        severity_colors = {
            'P0': '#DC2626',  # red
            'P1': '#F59E0B',  # yellow
            'P2': '#3B82F6',  # blue
            'P3': '#6B7280'   # gray
        }
        
        color = severity_colors.get(severity, '#6B7280')
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-top: none; }}
        .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
        .detail {{ margin: 10px 0; }}
        .label {{ font-weight: 600; color: #4b5563; }}
        .value {{ color: #111827; }}
        .button {{ display: inline-block; background: #000; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">[{severity}] Incident Alert</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{incident.get('service_name', 'Unknown Service')}</p>
        </div>
        
        <div class="content">
            <div class="detail">
                <span class="label">Incident ID:</span>
                <span class="value">{incident.get('id', 'Unknown')}</span>
            </div>
            
            <div class="detail">
                <span class="label">Failure Type:</span>
                <span class="value">{incident.get('failure_type', 'Unknown')}</span>
            </div>
            
            <div class="detail">
                <span class="label">Time:</span>
                <span class="value">{incident.get('created_at', 'Unknown')}</span>
            </div>
            
            <div class="detail">
                <span class="label">Service URL:</span>
                <span class="value">{incident.get('service_url', 'N/A')}</span>
            </div>
            
            <div class="detail">
                <span class="label">Error Message:</span>
                <span class="value">{incident.get('error_message', 'No details available')}</span>
            </div>
            
            <a href="https://devops-sentinel.dev/incidents/{incident.get('id')}" class="button">View Incident</a>
        </div>
        
        <div class="footer">
            <p>DevOps Sentinel - AI-Powered Monitoring</p>
            <p style="font-size: 12px;">You're receiving this because you're subscribed to incident alerts.</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _render_incident_text(self, incident: Dict) -> str:
        """Generate plain text email for incident"""
        return f"""
[{incident.get('severity', 'P2')}] INCIDENT ALERT

Service: {incident.get('service_name', 'Unknown')}
Incident ID: {incident.get('id')}
Failure Type: {incident.get('failure_type', 'Unknown')}
Time: {incident.get('created_at')}

Error Message:
{incident.get('error_message', 'No details available')}

View in Dashboard:
https://devops-sentinel.dev/incidents/{incident.get('id')}

---
DevOps Sentinel - AI-Powered Monitoring
        """
    
    def _render_postmortem_email(self, incident: Dict, postmortem: str) -> str:
        """Generate HTML email for postmortem"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.8; color: #333; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #000; color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .content {{ background: white; padding: 30px; border: 1px solid #e5e7eb; }}
        .postmortem {{ white-space: pre-wrap; font-size: 15px; line-height: 1.8; }}
        .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">Incident Postmortem</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">{incident.get('service_name')} - {incident.get('id')}</p>
        </div>
        
        <div class="content">
            <div class="postmortem">
{postmortem}
            </div>
        </div>
        
        <div class="footer">
            <p>DevOps Sentinel</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _render_digest_email(self, incidents: List[Dict], stats: Dict, period: str) -> str:
        """Generate HTML digest email"""
        incident_rows = '\n'.join([
            f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{inc.get('severity')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{inc.get('service_name')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{inc.get('failure_type')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{inc.get('status')}</td>
            </tr>
            """
            for inc in incidents[:10]  # Top 10
        ])
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #000; color: white; padding: 30px; text-align: center; }}
        .stats {{ display: flex; justify-content: space-around; padding: 20px; background: #f9fafb; }}
        .stat {{ text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #000; }}
        .stat-label {{ color: #6b7280; font-size: 14px; }}
        .content {{ padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #f3f4f6; padding: 12px; text-align: left; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">DevOps Sentinel {period.title()} Digest</h1>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{stats.get('total_incidents', 0)}</div>
                <div class="stat-label">Total Incidents</div>
            </div>
            <div class="stat">
                <div class="stat-value">{stats.get('p0_count', 0)}</div>
                <div class="stat-label">P0 Critical</div>
            </div>
            <div class="stat">
                <div class="stat-value">{stats.get('avg_resolution_time', 0)} min</div>
                <div class="stat-label">Avg Resolution Time</div>
            </div>
        </div>
        
        <div class="content">
            <h2>Recent Incidents</h2>
            <table>
                <thead>
                    <tr>
                        <th>Severity</th>
                        <th>Service</th>
                        <th>Type</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {incident_rows}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
        """
    
    def _render_digest_text(self, incidents: List[Dict], stats: Dict) -> str:
        """Generate plain text digest"""
        incident_list = '\n'.join([
            f"- [{inc.get('severity')}] {inc.get('service_name')}: {inc.get('failure_type')}"
            for inc in incidents[:10]
        ])
        
        return f"""
DEVOPS SENTINEL DIGEST

Summary:
- Total Incidents: {stats.get('total_incidents', 0)}
- P0 Critical: {stats.get('p0_count', 0)}
- Average Resolution: {stats.get('avg_resolution_time', 0)} minutes

Recent Incidents:
{incident_list}

---
DevOps Sentinel
        """


# Example usage
if __name__ == "__main__":
    async def test_email():
        config = {
            'host': 'smtp.gmail.com',
            'port': 587,
            'username': 'your-email@gmail.com',
            'password': 'your-app-password',
            'from_email': 'DevOps Sentinel <alerts@example.com>'
        }
        
        email_system = EmailNotificationSystem(config)
        
        incident = {
            'id': 'inc-123',
            'service_name': 'API Gateway',
            'severity': 'P1',
            'failure_type': 'High Response Time',
            'created_at': datetime.utcnow().isoformat(),
            'error_message': 'Average response time: 5000ms (baseline: 200ms)',
            'service_url': 'https://api.example.com'
        }
        
        result = await email_system.send_incident_alert(
            incident,
            recipients=['on-call@example.com']
        )
        
        print(f"Email sent: {result}")
    
    asyncio.run(test_email())
