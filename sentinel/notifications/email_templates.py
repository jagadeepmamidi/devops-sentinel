"""
Email Notification Templates - Professional Alert Emails
=========================================================

HTML email templates for various notifications
"""

from datetime import datetime
from typing import Dict, Optional


class EmailTemplates:
    """
    Professional email templates for DevOps Sentinel
    
    Templates:
    - Incident alerts
    - Daily digest
    - Weekly summary
    - SSL expiry warning
    - Postmortem ready
    - Welcome email
    """
    
    # Base template with styles
    BASE_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .header {{
                background: #000;
                color: #fff;
                padding: 24px 32px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 20px;
                font-weight: 600;
            }}
            .content {{
                padding: 32px;
            }}
            .alert-banner {{
                padding: 16px 20px;
                border-radius: 6px;
                margin-bottom: 24px;
            }}
            .alert-critical {{ background: #fef2f2; border-left: 4px solid #ef4444; }}
            .alert-warning {{ background: #fffbeb; border-left: 4px solid #f59e0b; }}
            .alert-info {{ background: #eff6ff; border-left: 4px solid #3b82f6; }}
            .alert-success {{ background: #f0fdf4; border-left: 4px solid #10b981; }}
            .metric-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 16px;
                margin: 24px 0;
            }}
            .metric {{
                background: #f9fafb;
                padding: 16px;
                border-radius: 6px;
                text-align: center;
            }}
            .metric-value {{
                font-size: 28px;
                font-weight: 700;
                color: #000;
            }}
            .metric-label {{
                font-size: 12px;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background: #000;
                color: #fff !important;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                margin: 16px 0;
            }}
            .button-secondary {{
                background: #fff;
                color: #000 !important;
                border: 2px solid #000;
            }}
            .timeline {{
                border-left: 2px solid #e5e7eb;
                padding-left: 20px;
                margin: 24px 0;
            }}
            .timeline-item {{
                position: relative;
                padding-bottom: 16px;
            }}
            .timeline-dot {{
                position: absolute;
                left: -26px;
                width: 10px;
                height: 10px;
                background: #000;
                border-radius: 50%;
            }}
            .timeline-time {{
                font-size: 12px;
                color: #6b7280;
            }}
            .footer {{
                background: #f9fafb;
                padding: 24px 32px;
                font-size: 12px;
                color: #6b7280;
                text-align: center;
            }}
            .footer a {{
                color: #6b7280;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #e5e7eb;
            }}
            th {{
                font-size: 12px;
                font-weight: 600;
                color: #6b7280;
                text-transform: uppercase;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {body}
        </div>
    </body>
    </html>
    """
    
    @staticmethod
    def incident_alert(
        service_name: str,
        severity: str,
        title: str,
        description: str,
        detected_at: str,
        incident_url: str,
        similar_incident: Optional[Dict] = None
    ) -> str:
        """Generate incident alert email"""
        severity_class = 'alert-critical' if severity in ['P0', 'P1'] else 'alert-warning'
        severity_label = {
            'P0': 'CRITICAL',
            'P1': 'HIGH',
            'P2': 'MEDIUM',
            'P3': 'LOW'
        }.get(severity, 'ALERT')
        
        similar_section = ""
        if similar_incident:
            similar_section = f"""
            <div class="alert-banner alert-info">
                <strong>Similar incident found</strong>
                <p style="margin: 8px 0 0 0;">
                    This looks like incident #{similar_incident.get('id', 'N/A')} from {similar_incident.get('occurred', 'previously')}.
                    <br>Resolution: {similar_incident.get('resolution', 'N/A')[:200]}
                </p>
            </div>
            """
        
        body = f"""
        <div class="header">
            <h1>DevOps Sentinel</h1>
        </div>
        <div class="content">
            <div class="alert-banner {severity_class}">
                <strong>{severity_label}: {service_name}</strong>
                <p style="margin: 8px 0 0 0;">{title}</p>
            </div>
            
            <p><strong>Description:</strong> {description}</p>
            <p><strong>Detected:</strong> {detected_at}</p>
            
            {similar_section}
            
            <a href="{incident_url}" class="button">View Incident</a>
            <a href="{incident_url}/acknowledge" class="button button-secondary" style="margin-left: 8px;">Acknowledge</a>
        </div>
        <div class="footer">
            <p>You're receiving this because you're on-call for {service_name}.</p>
            <p><a href="{{{{ unsubscribe_url }}}}">Manage notifications</a></p>
        </div>
        """
        
        return EmailTemplates.BASE_TEMPLATE.format(
            title=f"{severity_label}: {service_name}",
            body=body
        )
    
    @staticmethod
    def daily_digest(
        summary: Dict,
        top_incidents: list,
        services_status: Dict,
        dashboard_url: str
    ) -> str:
        """Generate daily digest email"""
        # Build incidents table
        incidents_rows = ""
        for inc in top_incidents[:5]:
            status_color = '#10b981' if inc['status'] == 'resolved' else '#f59e0b'
            incidents_rows += f"""
            <tr>
                <td>{inc['service']}</td>
                <td>{inc['title'][:50]}...</td>
                <td style="color: {status_color}; font-weight: 600;">{inc['status'].upper()}</td>
            </tr>
            """
        
        body = f"""
        <div class="header">
            <h1>Daily Digest - {datetime.utcnow().strftime('%B %d, %Y')}</h1>
        </div>
        <div class="content">
            <p>Here's your infrastructure summary for the past 24 hours.</p>
            
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value">{summary.get('total_incidents', 0)}</div>
                    <div class="metric-label">Incidents</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary.get('resolved', 0)}</div>
                    <div class="metric-label">Resolved</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary.get('mttr_minutes', 0)}m</div>
                    <div class="metric-label">Avg Resolution</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary.get('uptime_percent', 99.9):.1f}%</div>
                    <div class="metric-label">Uptime</div>
                </div>
            </div>
            
            <h3>Recent Incidents</h3>
            <table>
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Title</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {incidents_rows if incidents_rows else '<tr><td colspan="3" style="text-align: center; color: #6b7280;">No incidents today</td></tr>'}
                </tbody>
            </table>
            
            <a href="{dashboard_url}" class="button">View Dashboard</a>
        </div>
        <div class="footer">
            <p>DevOps Sentinel Daily Digest</p>
            <p><a href="{{{{ unsubscribe_url }}}}">Unsubscribe from digests</a></p>
        </div>
        """
        
        return EmailTemplates.BASE_TEMPLATE.format(
            title="Daily Digest - DevOps Sentinel",
            body=body
        )
    
    @staticmethod
    def ssl_expiry_warning(
        domain: str,
        days_remaining: int,
        expiry_date: str,
        service_url: str
    ) -> str:
        """Generate SSL expiry warning email"""
        urgency_class = 'alert-critical' if days_remaining <= 7 else 'alert-warning'
        
        body = f"""
        <div class="header">
            <h1>SSL Certificate Expiry Warning</h1>
        </div>
        <div class="content">
            <div class="alert-banner {urgency_class}">
                <strong>Certificate expires in {days_remaining} days</strong>
            </div>
            
            <p>The SSL certificate for <strong>{domain}</strong> will expire on <strong>{expiry_date}</strong>.</p>
            
            <p>Please renew the certificate before it expires to avoid service disruptions and security warnings for your users.</p>
            
            <h3>What to do</h3>
            <ul>
                <li>If using Let's Encrypt: Check your auto-renewal configuration</li>
                <li>If using a commercial CA: Start the renewal process now</li>
                <li>Verify your DNS records are correct</li>
            </ul>
            
            <a href="{service_url}" class="button">View Service</a>
        </div>
        <div class="footer">
            <p>SSL monitoring by DevOps Sentinel</p>
        </div>
        """
        
        return EmailTemplates.BASE_TEMPLATE.format(
            title=f"SSL Expiry: {domain}",
            body=body
        )
    
    @staticmethod
    def postmortem_ready(
        incident_title: str,
        service_name: str,
        postmortem_url: str,
        summary: str
    ) -> str:
        """Generate postmortem ready notification"""
        body = f"""
        <div class="header">
            <h1>Postmortem Generated</h1>
        </div>
        <div class="content">
            <div class="alert-banner alert-success">
                <strong>AI postmortem ready for review</strong>
            </div>
            
            <p>An AI-generated postmortem is ready for the following incident:</p>
            
            <p>
                <strong>Service:</strong> {service_name}<br>
                <strong>Incident:</strong> {incident_title}
            </p>
            
            <h3>Summary</h3>
            <p style="background: #f9fafb; padding: 16px; border-radius: 6px;">
                {summary[:500]}...
            </p>
            
            <p>Review and edit the postmortem before sharing with your team.</p>
            
            <a href="{postmortem_url}" class="button">Review Postmortem</a>
        </div>
        <div class="footer">
            <p>Generated by DevOps Sentinel AI</p>
        </div>
        """
        
        return EmailTemplates.BASE_TEMPLATE.format(
            title=f"Postmortem Ready: {incident_title}",
            body=body
        )
    
    @staticmethod
    def welcome_email(
        user_name: str,
        quick_start_url: str
    ) -> str:
        """Generate welcome email for new users"""
        body = f"""
        <div class="header">
            <h1>Welcome to DevOps Sentinel</h1>
        </div>
        <div class="content">
            <p>Hi {user_name},</p>
            
            <p>Welcome to DevOps Sentinel - the AI that remembers your incidents so you don't have to.</p>
            
            <h3>Get started in 3 steps:</h3>
            
            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <strong>1. Add your first service</strong>
                    <p>Enter a URL and we'll start monitoring immediately.</p>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <strong>2. Connect Slack</strong>
                    <p>Get instant alerts in your team's channels.</p>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <strong>3. Set up on-call</strong>
                    <p>Define who gets paged and when.</p>
                </div>
            </div>
            
            <a href="{quick_start_url}" class="button">Complete Setup</a>
            
            <p style="margin-top: 32px; color: #6b7280;">
                Need help? Reply to this email or check our <a href="https://docs.devops-sentinel.dev">documentation</a>.
            </p>
        </div>
        <div class="footer">
            <p>DevOps Sentinel - AI-Powered Incident Intelligence</p>
        </div>
        """
        
        return EmailTemplates.BASE_TEMPLATE.format(
            title="Welcome to DevOps Sentinel",
            body=body
        )
    
    @staticmethod
    def incident_resolved(
        service_name: str,
        incident_title: str,
        duration_minutes: int,
        resolution_notes: str,
        incident_url: str
    ) -> str:
        """Generate incident resolved notification"""
        hours = duration_minutes // 60
        mins = duration_minutes % 60
        duration_str = f"{hours}h {mins}m" if hours else f"{mins}m"
        
        body = f"""
        <div class="header">
            <h1>Incident Resolved</h1>
        </div>
        <div class="content">
            <div class="alert-banner alert-success">
                <strong>RESOLVED: {service_name}</strong>
                <p style="margin: 8px 0 0 0;">{incident_title}</p>
            </div>
            
            <div class="metric-grid">
                <div class="metric">
                    <div class="metric-value">{duration_str}</div>
                    <div class="metric-label">Time to Resolve</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #10b981;">✓</div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            
            <h3>Resolution Notes</h3>
            <p style="background: #f9fafb; padding: 16px; border-radius: 6px;">
                {resolution_notes or 'No notes provided'}
            </p>
            
            <a href="{incident_url}" class="button">View Details</a>
            <a href="{incident_url}/postmortem" class="button button-secondary" style="margin-left: 8px;">Generate Postmortem</a>
        </div>
        <div class="footer">
            <p>Incident tracking by DevOps Sentinel</p>
        </div>
        """
        
        return EmailTemplates.BASE_TEMPLATE.format(
            title=f"Resolved: {incident_title}",
            body=body
        )


# Example usage
if __name__ == "__main__":
    templates = EmailTemplates()
    
    # Generate incident alert
    html = templates.incident_alert(
        service_name="API Gateway",
        severity="P0",
        title="Connection timeout to database",
        description="Multiple connection timeouts detected to primary database cluster",
        detected_at="2026-01-27 10:30:00 UTC",
        incident_url="https://app.devops-sentinel.dev/incidents/123",
        similar_incident={
            'id': '45',
            'occurred': '3 weeks ago',
            'resolution': 'Restarted connection pool and increased max connections'
        }
    )
    
    print("Generated incident alert email")
    print(f"Length: {len(html)} characters")
