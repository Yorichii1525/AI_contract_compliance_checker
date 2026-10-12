"""
Email Notification Service for Contract Compliance Alerts
Supports SendGrid, Mailgun, and SMTP
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending compliance alerts via email."""
    
    def __init__(self, service_type: Optional[str] = None):
        """
        Initialize email notification service.
        
        Args:
            service_type: 'sendgrid', 'mailgun', or 'smtp' (or uses EMAIL_SERVICE env var)
        """
        self.service_type = service_type or os.getenv('EMAIL_SERVICE', 'smtp')
        self.from_email = os.getenv('EMAIL_FROM', 'compliance-alerts@yourcompany.com')
        self.legal_team_email = os.getenv('LEGAL_TEAM_EMAIL', 'legal@yourcompany.com')
        self.logger = logging.getLogger(__name__)
        
        # Service-specific configuration
        if self.service_type == 'sendgrid':
            self.api_key = os.getenv('SENDGRID_API_KEY')
        elif self.service_type == 'mailgun':
            self.api_key = os.getenv('MAILGUN_API_KEY')
            self.domain = os.getenv('MAILGUN_DOMAIN')
        else:  # SMTP
            self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
            self.smtp_username = os.getenv('SMTP_USERNAME')
            self.smtp_password = os.getenv('SMTP_PASSWORD')
    
    def send_email_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            attachments: Optional list of file paths to attach
            
        Returns:
            True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for filepath in attachments:
                    if Path(filepath).exists():
                        with open(filepath, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={Path(filepath).name}'
                            )
                            msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def send_email_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Send email using SendGrid API."""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            from_email = Email(self.from_email)
            to_email = To(to_email)
            content = Content("text/html", html_content)
            mail = Mail(from_email, to_email, subject, content)
            
            response = sg.client.mail.send.post(request_body=mail.get())
            
            if response.status_code in [200, 201, 202]:
                self.logger.info(f"SendGrid email sent successfully to {to_email}")
                return True
            else:
                self.logger.error(f"SendGrid failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"SendGrid error: {e}")
            return False
    
    def send_email_mailgun(
        self,
        to_email: str,
        subject: str,
        html_content: str
    ) -> bool:
        """Send email using Mailgun API."""
        try:
            import requests
            
            response = requests.post(
                f"https://api.mailgun.net/v3/{self.domain}/messages",
                auth=("api", self.api_key),
                data={
                    "from": self.from_email,
                    "to": to_email,
                    "subject": subject,
                    "html": html_content
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Mailgun email sent successfully to {to_email}")
                return True
            else:
                self.logger.error(f"Mailgun failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Mailgun error: {e}")
            return False
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send email using configured service.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            attachments: Optional list of file paths to attach (SMTP only)
            
        Returns:
            True if sent successfully
        """
        if self.service_type == 'sendgrid':
            return self.send_email_sendgrid(to_email, subject, html_content)
        elif self.service_type == 'mailgun':
            return self.send_email_mailgun(to_email, subject, html_content)
        else:
            return self.send_email_smtp(to_email, subject, html_content, attachments)
    
    def send_high_risk_alert(
        self,
        contract_name: str,
        risk_score: float,
        compliance_issues: List[Dict],
        recommendations: List[str],
        to_email: Optional[str] = None
    ) -> bool:
        """
        Send high-risk contract alert email.
        
        Args:
            contract_name: Name of the contract
            risk_score: Risk score (0-100)
            compliance_issues: List of compliance issues
            recommendations: List of recommendations
            to_email: Recipient email (defaults to legal team)
            
        Returns:
            True if sent successfully
        """
        to_email = to_email or self.legal_team_email
        
        # Generate HTML content
        issues_html = "".join([
            f"<li><strong>{issue.get('clause', 'Unknown')}:</strong> {issue.get('description', '')}</li>"
            for issue in compliance_issues[:5]
        ])
        
        recommendations_html = "".join([
            f"<li>{rec}</li>"
            for rec in recommendations[:5]
        ])
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .risk-score {{ font-size: 24px; font-weight: bold; color: #dc3545; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px; }}
                ul {{ padding-left: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ High-Risk Contract Alert</h1>
            </div>
            <div class="content">
                <p><strong>Contract:</strong> {contract_name}</p>
                <p><strong>Risk Score:</strong> <span class="risk-score">{risk_score:.1f}/100</span></p>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="section">
                    <div class="section-title">Critical Compliance Issues:</div>
                    <ul>
                        {issues_html}
                    </ul>
                </div>
                
                <div class="section">
                    <div class="section-title">Recommended Actions:</div>
                    <ul>
                        {recommendations_html}
                    </ul>
                </div>
                
                <p><strong>Action Required:</strong> Please review this contract immediately and address the identified compliance issues.</p>
            </div>
            <div class="footer">
                <p>This is an automated notification from the AI-Powered Compliance Checker</p>
                <p>For questions, contact your compliance team</p>
            </div>
        </body>
        </html>
        """
        
        subject = f"⚠️ HIGH RISK: {contract_name} - Risk Score {risk_score:.1f}/100"
        return self.send_email(to_email, subject, html_content)
    
    def send_amendment_suggestions(
        self,
        contract_name: str,
        amendments: List[Dict[str, Any]],
        to_email: Optional[str] = None
    ) -> bool:
        """
        Send contract amendment suggestions email.
        
        Args:
            contract_name: Name of the contract
            amendments: List of amendment dictionaries with clause, issue, and suggestion
            to_email: Recipient email (defaults to legal team)
            
        Returns:
            True if sent successfully
        """
        to_email = to_email or self.legal_team_email
        
        # Generate amendments HTML
        amendments_html = ""
        for i, amendment in enumerate(amendments, 1):
            amendments_html += f"""
            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <h3>Amendment {i}: {amendment.get('clause_title', 'Clause')}</h3>
                <p><strong>Issue:</strong> {amendment.get('issue', '')}</p>
                <p><strong>Current Text:</strong></p>
                <div style="background-color: #f8d7da; padding: 10px; border-left: 4px solid #dc3545;">
                    {amendment.get('original_text', '')[:200]}...
                </div>
                <p><strong>Suggested Amendment:</strong></p>
                <div style="background-color: #d4edda; padding: 10px; border-left: 4px solid #28a745;">
                    {amendment.get('suggested_text', '')[:200]}...
                </div>
                <p><strong>Rationale:</strong> {amendment.get('rationale', '')}</p>
            </div>
            """
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📋 Contract Amendment Suggestions</h1>
            </div>
            <div class="content">
                <p><strong>Contract:</strong> {contract_name}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Total Amendments:</strong> {len(amendments)}</p>
                
                <p>The following amendments are suggested to improve compliance:</p>
                
                {amendments_html}
                
                <p style="margin-top: 30px; padding: 15px; background-color: #fff3cd; border-left: 4px solid #ffc107;">
                    <strong>⚠️ Important:</strong> These are AI-generated suggestions. Please review carefully with legal counsel before implementation.
                </p>
            </div>
            <div class="footer">
                <p>This is an automated notification from the AI-Powered Compliance Checker</p>
            </div>
        </body>
        </html>
        """
        
        subject = f"📋 Amendment Suggestions: {contract_name} ({len(amendments)} items)"
        return self.send_email(to_email, subject, html_content)
    
    def send_compliance_report(
        self,
        report_summary: Dict[str, Any],
        report_file_path: Optional[str] = None,
        to_email: Optional[str] = None
    ) -> bool:
        """
        Send compliance report email.
        
        Args:
            report_summary: Dictionary with report metrics
            report_file_path: Optional path to PDF report file
            to_email: Recipient email (defaults to legal team)
            
        Returns:
            True if sent successfully
        """
        to_email = to_email or self.legal_team_email
        
        total = report_summary.get('total_contracts', 0)
        compliant = report_summary.get('compliant_contracts', 0)
        non_compliant = report_summary.get('non_compliant_contracts', 0)
        compliance_rate = (compliant / total * 100) if total > 0 else 0
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .metrics {{ display: table; width: 100%; margin: 20px 0; }}
                .metric {{ display: table-cell; padding: 15px; text-align: center; background-color: #f8f9fa; border: 1px solid #dee2e6; }}
                .metric-value {{ font-size: 32px; font-weight: bold; color: #007bff; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Compliance Report Summary</h1>
            </div>
            <div class="content">
                <p><strong>Report Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{total}</div>
                        <div>Total Contracts</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" style="color: #28a745;">{compliant}</div>
                        <div>Compliant</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" style="color: #dc3545;">{non_compliant}</div>
                        <div>Non-Compliant</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{compliance_rate:.1f}%</div>
                        <div>Compliance Rate</div>
                    </div>
                </div>
                
                <p>Detailed compliance report is attached. Please review and take necessary actions for non-compliant contracts.</p>
            </div>
            <div class="footer">
                <p>This is an automated notification from the AI-Powered Compliance Checker</p>
            </div>
        </body>
        </html>
        """
        
        subject = f"📊 Compliance Report - {datetime.now().strftime('%Y-%m-%d')}"
        attachments = [report_file_path] if report_file_path and Path(report_file_path).exists() else None
        
        return self.send_email(to_email, subject, html_content, attachments)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize service
    email_service = EmailNotificationService()
    
    # Test high-risk alert
    email_service.send_high_risk_alert(
        contract_name="Data Processing Agreement - Acme Corp",
        risk_score=92.5,
        compliance_issues=[
            {"clause": "Article 28", "description": "Missing GDPR processor obligations"},
            {"clause": "Article 32", "description": "Inadequate security measures"}
        ],
        recommendations=[
            "Add explicit GDPR Article 28 compliance clauses",
            "Include detailed security measure requirements"
        ]
    )
