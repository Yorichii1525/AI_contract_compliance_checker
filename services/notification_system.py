"""Notification System - Real-time alerts for compliance issues."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationSeverity(Enum):
    """Notification severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    HIGH_RISK = "high_risk"


class NotificationType(Enum):
    """Types of notifications."""
    COMPLIANCE_ISSUE = "compliance_issue"
    MISSING_REQUIREMENT = "missing_requirement"
    HIGH_RISK_DETECTED = "high_risk_detected"
    ANALYSIS_COMPLETE = "analysis_complete"
    REGULATORY_UPDATE = "regulatory_update"
    SYSTEM_ALERT = "system_alert"


class NotificationSystem:
    """Centralized notification system for compliance alerts."""
    
    def __init__(self):
        """Initialize notification system."""
        self.logger = logging.getLogger(__name__)
        self.notifications = []
        self._init_services()
    
    def _init_services(self):
        """Initialize notification services."""
        from services.google_sheets_writer import GoogleSheetsWriter
        
        try:
            self.sheets_writer = GoogleSheetsWriter()
        except Exception as e:
            self.logger.warning(f"Google Sheets writer not available: {e}")
            self.sheets_writer = None
    
    def send_notification(
        self,
        notification_type: NotificationType,
        severity: NotificationSeverity,
        message: str,
        details: Dict[str, Any],
        targets: List[str] = None
    ) -> bool:
        """
        Send a notification through configured channels.
        
        Args:
            notification_type: Type of notification
            severity: Severity level
            message: Notification message
            details: Additional details
            targets: List of notification targets ('sheets', 'email', 'slack')
            
        Returns:
            True if notification sent successfully
        """
        if targets is None:
            targets = ['sheets']  # Default to Google Sheets
        
        notification = {
            'id': len(self.notifications) + 1,
            'timestamp': datetime.now(),
            'type': notification_type.value,
            'severity': severity.value,
            'message': message,
            'details': details,
            'sent': False
        }
        
        self.notifications.append(notification)
        
        # Send through configured channels
        success = True
        
        if 'sheets' in targets and self.sheets_writer:
            success &= self._send_to_sheets(notification)
        
        notification['sent'] = success
        
        self.logger.info(
            f"Notification sent: {notification_type.value} - {severity.value} - {message}"
        )
        
        return success
    
    def _send_to_sheets(self, notification: Dict[str, Any]) -> bool:
        """Send notification to Google Sheets."""
        try:
            # This would need a configured spreadsheet ID
            # For now, we just log it
            self.logger.info(f"Would send to sheets: {notification['message']}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send to sheets: {e}")
            return False
    
    def notify_high_risk_clause(
        self,
        clause_id: str,
        clause_text: str,
        risk_level: str,
        frameworks: List[str],
        issues: List[str],
        spreadsheet_id: Optional[str] = None
    ) -> bool:
        """
        Send notification for high-risk clause detection.
        
        Args:
            clause_id: Clause identifier
            clause_text: Text of the clause
            risk_level: Risk level
            frameworks: Affected frameworks
            issues: List of issues
            spreadsheet_id: Optional spreadsheet ID for Google Sheets notification
            
        Returns:
            True if notification sent
        """
        message = f"High-risk clause detected: {clause_id}"
        
        details = {
            'clause_id': clause_id,
            'clause_text': clause_text[:200] + '...' if len(clause_text) > 200 else clause_text,
            'risk_level': risk_level,
            'frameworks': frameworks,
            'issues': issues,
            'action_required': 'Review and update this clause immediately'
        }
        
        targets = ['sheets'] if spreadsheet_id else []
        
        return self.send_notification(
            NotificationType.HIGH_RISK_DETECTED,
            NotificationSeverity.CRITICAL,
            message,
            details,
            targets
        )
    
    def notify_missing_requirements(
        self,
        framework: str,
        missing_count: int,
        requirements: List[Dict[str, Any]],
        spreadsheet_id: Optional[str] = None
    ) -> bool:
        """
        Send notification for missing compliance requirements.
        
        Args:
            framework: Regulatory framework
            missing_count: Number of missing requirements
            requirements: List of missing requirements
            spreadsheet_id: Optional spreadsheet ID
            
        Returns:
            True if notification sent
        """
        message = f"{missing_count} missing requirements detected for {framework}"
        
        details = {
            'framework': framework,
            'missing_count': missing_count,
            'requirements': requirements[:5],  # Top 5
            'action_required': 'Add missing clauses to achieve compliance'
        }
        
        severity = NotificationSeverity.CRITICAL if missing_count > 5 else NotificationSeverity.WARNING
        targets = ['sheets'] if spreadsheet_id else []
        
        return self.send_notification(
            NotificationType.MISSING_REQUIREMENT,
            severity,
            message,
            details,
            targets
        )
    
    def notify_analysis_complete(
        self,
        overall_score: float,
        total_clauses: int,
        high_risk_count: int,
        frameworks: List[str],
        spreadsheet_id: Optional[str] = None
    ) -> bool:
        """
        Send notification when analysis is complete.
        
        Args:
            overall_score: Overall compliance score
            total_clauses: Total clauses analyzed
            high_risk_count: Number of high-risk items
            frameworks: Frameworks analyzed
            spreadsheet_id: Optional spreadsheet ID
            
        Returns:
            True if notification sent
        """
        status = "Compliant" if overall_score >= 75 else "Non-Compliant"
        message = f"Compliance analysis complete: {status} ({overall_score:.1f}%)"
        
        details = {
            'overall_score': overall_score,
            'total_clauses': total_clauses,
            'high_risk_count': high_risk_count,
            'frameworks': frameworks,
            'status': status
        }
        
        severity = (
            NotificationSeverity.CRITICAL if overall_score < 60
            else NotificationSeverity.WARNING if overall_score < 75
            else NotificationSeverity.INFO
        )
        
        targets = ['sheets'] if spreadsheet_id else []
        
        return self.send_notification(
            NotificationType.ANALYSIS_COMPLETE,
            severity,
            message,
            details,
            targets
        )
    
    def notify_regulatory_update(
        self,
        framework: str,
        update_title: str,
        update_summary: str,
        source: str,
        link: str,
        spreadsheet_id: Optional[str] = None
    ) -> bool:
        """
        Send notification for regulatory updates.
        
        Args:
            framework: Regulatory framework
            update_title: Title of the update
            update_summary: Summary of the update
            source: Source of the information
            link: Link to full information
            spreadsheet_id: Optional spreadsheet ID
            
        Returns:
            True if notification sent
        """
        message = f"New regulatory update: {framework} - {update_title}"
        
        details = {
            'framework': framework,
            'title': update_title,
            'summary': update_summary,
            'source': source,
            'link': link,
            'action_required': 'Review update and assess impact on current contracts'
        }
        
        targets = ['sheets'] if spreadsheet_id else []
        
        return self.send_notification(
            NotificationType.REGULATORY_UPDATE,
            NotificationSeverity.WARNING,
            message,
            details,
            targets
        )
    
    def get_notifications(
        self,
        severity: Optional[NotificationSeverity] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get notifications with optional filtering.
        
        Args:
            severity: Filter by severity
            notification_type: Filter by type
            limit: Maximum number to return
            
        Returns:
            List of notifications
        """
        filtered = self.notifications
        
        if severity:
            filtered = [n for n in filtered if n['severity'] == severity.value]
        
        if notification_type:
            filtered = [n for n in filtered if n['type'] == notification_type.value]
        
        # Return most recent first
        return sorted(filtered, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_critical_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get critical notifications."""
        return self.get_notifications(
            severity=NotificationSeverity.CRITICAL,
            limit=limit
        )
    
    def clear_notifications(self):
        """Clear all notifications."""
        self.notifications.clear()
        self.logger.info("All notifications cleared")
    
    def generate_notification_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of all notifications.
        
        Returns:
            Notification report
        """
        report = {
            'total_notifications': len(self.notifications),
            'by_severity': {},
            'by_type': {},
            'sent_count': sum(1 for n in self.notifications if n['sent']),
            'failed_count': sum(1 for n in self.notifications if not n['sent']),
            'recent_critical': self.get_critical_notifications(limit=10)
        }
        
        # Count by severity
        for severity in NotificationSeverity:
            count = sum(1 for n in self.notifications if n['severity'] == severity.value)
            report['by_severity'][severity.value] = count
        
        # Count by type
        for ntype in NotificationType:
            count = sum(1 for n in self.notifications if n['type'] == ntype.value)
            report['by_type'][ntype.value] = count
        
        return report
