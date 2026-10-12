"""
Slack Notifier Service - Send real-time compliance alerts to Slack channels.
"""
import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Slack SDK, make it optional
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    logger.warning("slack_sdk not installed. Install with: pip install slack-sdk")
    SLACK_AVAILABLE = False
    WebClient = None
    SlackApiError = None


class SlackMessagePriority(Enum):
    """Priority levels for Slack messages."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SlackNotifier:
    """Send compliance alerts and notifications to Slack."""
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        webhook_url: Optional[str] = None,
        default_channel: str = "#compliance-alerts"
    ):
        """
        Initialize Slack notifier.
        
        Args:
            access_token: Slack bot token (defaults to SLACK_BOT_TOKEN or SLACK_ACCESS_TOKEN env var)
            webhook_url: Slack webhook URL (defaults to SLACK_WEBHOOK_URL env var) - preferred for Free plans
            default_channel: Default channel for notifications
        """
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        self.access_token = access_token or os.getenv('SLACK_BOT_TOKEN') or os.getenv('SLACK_ACCESS_TOKEN')
        self.default_channel = default_channel
        self.enabled = False
        self.use_webhook = bool(self.webhook_url)
        
        # Webhook mode (recommended for Free/Standard plans)
        if self.use_webhook:
            self.enabled = True
            logger.info("Slack notifier initialized with webhook URL")
            return
        
        # Bot token mode (for Enterprise or multi-channel)
        if not SLACK_AVAILABLE:
            logger.warning("Slack SDK not available. Notifications will be logged only.")
            return
        
        if not self.access_token:
            logger.warning("Neither SLACK_WEBHOOK_URL nor SLACK_BOT_TOKEN set. Slack notifications disabled.")
            return
        
        try:
            self.client = WebClient(token=self.access_token)
            # Test connection
            response = self.client.auth_test()
            self.bot_user_id = response["user_id"]
            self.team_name = response["team"]
            self.enabled = True
            logger.info(f"Slack notifier initialized for team: {self.team_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Slack client: {e}")
            self.enabled = False
    
    def _format_risk_emoji(self, risk_level: str) -> str:
        """Get emoji for risk level."""
        risk_emojis = {
            'high': '🔴',
            'critical': '❌',
            'medium': '🟡',
            'low': '🟢',
            'info': 'ℹ️'
        }
        return risk_emojis.get(risk_level.lower(), '📋')
    
    def _format_framework_emoji(self, framework: str) -> str:
        """Get emoji for compliance framework."""
        framework_emojis = {
            'GDPR': '🇪🇺',
            'HIPAA': '🏥',
            'SOX': '📊',
            'CCPA': '🇺🇸',
            'PCI-DSS': '💳'
        }
        return framework_emojis.get(framework.upper(), '⚖️')
    
    def _send_message(
        self,
        channel: str,
        blocks: List[Dict],
        text: str,
        thread_ts: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Send a message to Slack.
        
        Args:
            channel: Channel ID or name
            blocks: Message blocks (rich formatting)
            text: Fallback plain text
            thread_ts: Thread timestamp for replies
            
        Returns:
            Response dict or None if failed
        """
        if not self.enabled:
            logger.info(f"[SLACK DISABLED] Would send to {channel}: {text}")
            return None
        
        # Webhook mode - simpler, works on all Slack plans
        if self.use_webhook:
            try:
                payload = {
                    "text": text,
                    "blocks": blocks
                }
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook message sent successfully")
                    return {"ok": True}
                else:
                    logger.error(f"Webhook error: {response.status_code} - {response.text}")
                    return None
            except Exception as e:
                logger.error(f"Failed to send webhook message: {e}")
                return None
        
        # Bot token mode - requires Enterprise for chat:write.public
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=text,
                thread_ts=thread_ts
            )
            logger.info(f"Message sent to Slack channel: {channel}")
            return response.data
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return None
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return None
    
    def notify_high_risk_clause(
        self,
        contract_name: str,
        clause_id: str,
        clause_text: str,
        risk_level: str,
        framework: str,
        issues: List[str],
        channel: Optional[str] = None
    ) -> bool:
        """
        Send alert for high-risk clause detection.
        
        Args:
            contract_name: Name of the contract
            clause_id: Clause identifier
            clause_text: Text of the problematic clause
            risk_level: Risk level (high, medium, low)
            framework: Compliance framework (GDPR, HIPAA, etc.)
            issues: List of compliance issues
            channel: Override default channel
            
        Returns:
            True if notification sent successfully
        """
        channel = channel or self.default_channel
        risk_emoji = self._format_risk_emoji(risk_level)
        framework_emoji = self._format_framework_emoji(framework)
        
        # Truncate clause text if too long
        clause_preview = clause_text[:200] + "..." if len(clause_text) > 200 else clause_text
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{risk_emoji} High-Risk Clause Detected"
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
                        "text": f"*Framework:*\n{framework_emoji} {framework}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Clause ID:*\n{clause_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Risk Level:*\n{risk_emoji} {risk_level.upper()}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Clause Text:*\n```{clause_preview}```"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Issues Found:*\n" + "\n".join([f"• {issue}" for issue in issues[:5]])
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ Detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        text = f"High-Risk Clause Detected in {contract_name} ({framework})"
        
        response = self._send_message(channel, blocks, text)
        return response is not None
    
    def notify_batch_complete(
        self,
        total_files: int,
        successful: int,
        failed: int,
        total_time: float,
        avg_compliance_score: float,
        high_risk_count: int,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send notification when batch processing completes.
        
        Args:
            total_files: Total files processed
            successful: Successfully processed files
            failed: Failed files
            total_time: Total processing time
            avg_compliance_score: Average compliance score
            high_risk_count: Number of high-risk issues
            channel: Override default channel
            
        Returns:
            True if notification sent successfully
        """
        channel = channel or self.default_channel
        
        # Determine status emoji
        if failed == 0:
            status_emoji = "✅"
        elif failed < total_files / 2:
            status_emoji = "⚠️"
        else:
            status_emoji = "❌"
        
        # Score emoji
        if avg_compliance_score >= 80:
            score_emoji = "🟢"
        elif avg_compliance_score >= 60:
            score_emoji = "🟡"
        else:
            score_emoji = "🔴"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} Batch Processing Complete"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Files:*\n{total_files}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Successful:*\n✅ {successful}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Failed:*\n❌ {failed}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Processing Time:*\n⏱️ {total_time:.1f}s"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Avg Compliance Score:*\n{score_emoji} {avg_compliance_score:.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*High-Risk Issues:*\n🔴 {high_risk_count}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        text = f"Batch Processing Complete: {successful}/{total_files} files processed successfully"
        
        response = self._send_message(channel, blocks, text)
        return response is not None
    
    def notify_analysis_complete(
        self,
        contract_name: str,
        compliance_score: float,
        framework: str,
        missing_clauses_count: int,
        high_risk_issues: int,
        processing_time: float,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send notification when single contract analysis completes.
        
        Args:
            contract_name: Name of analyzed contract
            compliance_score: Overall compliance score
            framework: Compliance framework used
            missing_clauses_count: Number of missing clauses
            high_risk_issues: Number of high-risk issues
            processing_time: Time taken for analysis
            channel: Override default channel
            
        Returns:
            True if notification sent successfully
        """
        channel = channel or self.default_channel
        framework_emoji = self._format_framework_emoji(framework)
        
        # Score emoji
        if compliance_score >= 80:
            score_emoji = "🟢"
            score_status = "Good"
        elif compliance_score >= 60:
            score_emoji = "🟡"
            score_status = "Fair"
        else:
            score_emoji = "🔴"
            score_status = "Needs Attention"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Contract Analysis Complete"
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
                        "text": f"*Framework:*\n{framework_emoji} {framework}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Compliance Score:*\n{score_emoji} {compliance_score:.1f}% ({score_status})"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Processing Time:*\n⏱️ {processing_time:.2f}s"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Missing Clauses:*\n📋 {missing_clauses_count}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*High-Risk Issues:*\n🔴 {high_risk_issues}"
                    }
                ]
            }
        ]
        
        # Add warning if high-risk issues found
        if high_risk_issues > 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":warning: *Action Required:* {high_risk_issues} high-risk issue(s) require immediate attention."
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        text = f"Analysis Complete: {contract_name} - {compliance_score:.1f}% compliance"
        
        response = self._send_message(channel, blocks, text)
        return response is not None
    
    def notify_regulatory_update(
        self,
        framework: str,
        update_title: str,
        update_summary: str,
        source: str,
        link: Optional[str] = None,
        channel: Optional[str] = None
    ) -> bool:
        """
        Send notification about regulatory updates.
        
        Args:
            framework: Affected compliance framework
            update_title: Title of the update
            update_summary: Summary of changes
            source: Source of the update
            link: URL to full update
            channel: Override default channel
            
        Returns:
            True if notification sent successfully
        """
        channel = channel or self.default_channel
        framework_emoji = self._format_framework_emoji(framework)
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📰 Regulatory Update Alert"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Framework:*\n{framework_emoji} {framework}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:*\n{source}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{update_title}*\n\n{update_summary}"
                }
            }
        ]
        
        # Add link if provided
        if link:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{link}|Read full update >"
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        text = f"Regulatory Update: {framework} - {update_title}"
        
        response = self._send_message(channel, blocks, text)
        return response is not None
    
    def notify_missing_requirements(
        self,
        contract_name: str,
        framework: str,
        missing_requirements: List[Dict[str, Any]],
        channel: Optional[str] = None
    ) -> bool:
        """
        Send notification about missing compliance requirements.
        
        Args:
            contract_name: Name of the contract
            framework: Compliance framework
            missing_requirements: List of missing requirement dicts
            channel: Override default channel
            
        Returns:
            True if notification sent successfully
        """
        channel = channel or self.default_channel
        framework_emoji = self._format_framework_emoji(framework)
        
        # Group by risk level
        high_risk = [r for r in missing_requirements if r.get('risk_level', '').lower() == 'high']
        medium_risk = [r for r in missing_requirements if r.get('risk_level', '').lower() == 'medium']
        low_risk = [r for r in missing_requirements if r.get('risk_level', '').lower() == 'low']
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚠️ Missing Compliance Requirements"
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
                        "text": f"*Framework:*\n{framework_emoji} {framework}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*High Risk:*\n🔴 {len(high_risk)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Medium Risk:*\n🟡 {len(medium_risk)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Low Risk:*\n🟢 {len(low_risk)}"
                    }
                ]
            }
        ]
        
        # Show top 3 high-risk missing requirements
        if high_risk:
            requirement_text = "*Top High-Risk Missing Requirements:*\n"
            for i, req in enumerate(high_risk[:3], 1):
                req_name = req.get('requirement_name', 'Unknown')
                requirement_text += f"{i}. 🔴 {req_name}\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": requirement_text
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        text = f"Missing Requirements: {contract_name} - {len(missing_requirements)} issues found"
        
        response = self._send_message(channel, blocks, text)
        return response is not None
    
    def test_connection(self) -> bool:
        """
        Test Slack connection.
        
        Returns:
            True if connection successful
        """
        if not self.enabled:
            logger.warning("Slack notifier not enabled")
            return False
        
        try:
            response = self.client.auth_test()
            logger.info(f"Slack connection test successful: {response['team']}")
            return True
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False
