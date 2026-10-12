"""
Slack Integration Service for Real-time Compliance Alerts
Sends notifications to Slack channels via webhooks
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class SlackNotificationService:
    """Service for sending compliance alerts to Slack channels."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notification service.
        
        Args:
            webhook_url: Slack webhook URL (or uses SLACK_WEBHOOK_URL env var)
        """
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        self.high_risk_threshold = int(os.getenv('SLACK_RISK_THRESHOLD', '80'))
        self.expiry_warning_days = int(os.getenv('SLACK_EXPIRY_WARNING_DAYS', '30'))
        self.channel = os.getenv('SLACK_CHANNEL', '#compliance-alerts')
        self.logger = logging.getLogger(__name__)
        
        if not self.webhook_url:
            self.logger.warning("Slack webhook URL not configured. Notifications disabled.")
    
    def is_enabled(self) -> bool:
        """Check if Slack notifications are enabled."""
        return self.webhook_url is not None
    
    def send_message(self, text: str, blocks: Optional[List[Dict]] = None) -> bool:
        """
        Send a message to Slack.
        
        Args:
            text: Plain text message (fallback)
            blocks: Rich message blocks for formatting
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            self.logger.warning("Slack not configured. Message not sent.")
            return False
        
        try:
            payload = {"text": text}
            if blocks:
                payload["blocks"] = blocks
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Slack notification sent successfully")
                return True
            else:
                self.logger.error(f"Slack notification failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")
            return False
    
    def notify_high_risk_contract(
        self,
        contract_name: str,
        risk_score: float,
        compliance_issues: List[Dict],
        contract_url: Optional[str] = None
    ) -> bool:
        """
        Send alert for high-risk contract detection.
        
        Args:
            contract_name: Name of the contract
            risk_score: Risk score (0-100)
            compliance_issues: List of compliance issues
            contract_url: Optional URL to view contract
            
        Returns:
            True if notification sent successfully
        """
        if risk_score < self.high_risk_threshold:
            return False  # Don't send notification for lower risk
        
        # Determine severity emoji
        emoji = "🔴" if risk_score >= 90 else "🟠"
        
        # Build message blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} High-Risk Contract Detected",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Contract:*\n{contract_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Risk Score:*\n{risk_score:.1f}/100"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Critical Issues Found:* {len([i for i in compliance_issues if i.get('severity') == 'high'])}"
                }
            }
        ]
        
        # Add top issues
        if compliance_issues:
            issues_text = "\n".join([
                f"• {issue.get('description', 'Unknown issue')}"
                for issue in compliance_issues[:3]
            ])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Issues:*\n{issues_text}"
                }
            })
        
        # Add action button if URL provided
        if contract_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Contract Details"
                        },
                        "url": contract_url,
                        "style": "danger"
                    }
                ]
            })
        
        text = f"⚠️ High-Risk Contract Alert: {contract_name} (Risk: {risk_score:.1f}/100)"
        return self.send_message(text, blocks)
    
    def notify_contract_expiring(
        self,
        contract_name: str,
        days_until_expiry: int,
        expiry_date: str,
        contract_url: Optional[str] = None
    ) -> bool:
        """
        Send alert for contracts nearing expiration.
        
        Args:
            contract_name: Name of the contract
            days_until_expiry: Days until expiration
            expiry_date: Expiration date string
            contract_url: Optional URL to view contract
            
        Returns:
            True if notification sent successfully
        """
        if days_until_expiry > self.expiry_warning_days:
            return False
        
        emoji = "⚠️" if days_until_expiry <= 7 else "📅"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Contract Expiration Warning",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Contract:*\n{contract_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Expires In:*\n{days_until_expiry} days"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Expiry Date:*\n{expiry_date}"
                    }
                ]
            }
        ]
        
        if contract_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Review Contract"
                        },
                        "url": contract_url
                    }
                ]
            })
        
        text = f"Contract expiring soon: {contract_name} (in {days_until_expiry} days)"
        return self.send_message(text, blocks)
    
    def notify_regulatory_update(
        self,
        regulation_title: str,
        jurisdiction: str,
        severity: str,
        affected_contracts: int,
        summary: str
    ) -> bool:
        """
        Send alert for new regulatory updates.
        
        Args:
            regulation_title: Title of the regulation
            jurisdiction: Jurisdiction (e.g., EU, US)
            severity: Severity level (critical, high, medium, low)
            affected_contracts: Number of affected contracts
            summary: Brief summary of the change
            
        Returns:
            True if notification sent successfully
        """
        emoji_map = {
            'critical': '🚨',
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        emoji = emoji_map.get(severity.lower(), '📋')
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} New Regulatory Update",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Regulation:*\n{regulation_title}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Jurisdiction:*\n{jurisdiction}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Affected Contracts:*\n{affected_contracts}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary}"
                }
            }
        ]
        
        text = f"New {severity} regulatory update: {regulation_title} (affects {affected_contracts} contracts)"
        return self.send_message(text, blocks)
    
    def notify_compliance_report_ready(
        self,
        report_type: str,
        contracts_analyzed: int,
        compliance_rate: float,
        report_url: Optional[str] = None
    ) -> bool:
        """
        Send notification when compliance report is ready.
        
        Args:
            report_type: Type of report
            contracts_analyzed: Number of contracts analyzed
            compliance_rate: Overall compliance rate (0-100)
            report_url: Optional URL to download report
            
        Returns:
            True if notification sent successfully
        """
        emoji = "✅" if compliance_rate >= 80 else "⚠️" if compliance_rate >= 60 else "🔴"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Compliance Report Ready",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Report Type:*\n{report_type}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Contracts Analyzed:*\n{contracts_analyzed}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Compliance Rate:*\n{compliance_rate:.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Generated:*\n{datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ]
        
        if report_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Download Report"
                        },
                        "url": report_url,
                        "style": "primary"
                    }
                ]
            })
        
        text = f"Compliance report ready: {report_type} - {compliance_rate:.1f}% compliant ({contracts_analyzed} contracts)"
        return self.send_message(text, blocks)


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize service
    slack = SlackNotificationService()
    
    if slack.is_enabled():
        # Test notification
        slack.notify_high_risk_contract(
            contract_name="Data Processing Agreement - Acme Corp",
            risk_score=92.5,
            compliance_issues=[
                {"severity": "high", "description": "Missing GDPR data processing clauses"},
                {"severity": "high", "description": "Inadequate security measures"},
                {"severity": "medium", "description": "Unclear termination terms"}
            ]
        )
