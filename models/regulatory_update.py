"""
Data models for real-time regulatory update tracking.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import json


class UpdateType(Enum):
    """Types of regulatory updates."""
    NEW_REGULATION = "New Regulation"
    AMENDMENT = "Amendment"
    CLARIFICATION = "Clarification"
    ENFORCEMENT = "Enforcement Action"
    GUIDANCE = "Guidance Document"
    CASE_LAW = "Case Law"
    PROPOSAL = "Proposed Rule"


class UpdateSeverity(Enum):
    """Severity levels for regulatory updates."""
    CRITICAL = "Critical"  # Immediate action required
    HIGH = "High"  # Action needed within weeks
    MEDIUM = "Medium"  # Review and plan
    LOW = "Low"  # Informational


class UpdateStatus(Enum):
    """Status of update processing."""
    DETECTED = "Detected"
    ANALYZED = "Analyzed"
    NOTIFIED = "Notified"
    REVIEWED = "Reviewed"
    IMPLEMENTED = "Implemented"
    ARCHIVED = "Archived"


@dataclass
class RegulatorySource:
    """Represents a source for regulatory information."""
    source_id: str
    name: str
    url: str
    framework: str  # GDPR, HIPAA, CCPA, SOX
    source_type: str  # Official, News, Blog, Legal Analysis
    check_frequency_hours: int = 24
    last_checked: Optional[datetime] = None
    is_active: bool = True
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source_id': self.source_id,
            'name': self.name,
            'url': self.url,
            'framework': self.framework,
            'source_type': self.source_type,
            'check_frequency_hours': self.check_frequency_hours,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'is_active': self.is_active,
            'keywords': self.keywords
        }


@dataclass
class RegulatoryUpdate:
    """Represents a detected regulatory update."""
    update_id: str
    framework: str  # GDPR, HIPAA, CCPA, SOX
    title: str
    summary: str
    full_text: str
    source: RegulatorySource
    update_type: UpdateType
    severity: UpdateSeverity
    status: UpdateStatus
    
    # Dates
    detected_date: datetime
    effective_date: Optional[datetime] = None
    compliance_deadline: Optional[datetime] = None
    
    # Analysis
    affected_clauses: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    impact_score: float = 0.0  # 0-1 scale
    
    # Metadata
    source_url: str = ""
    reference_number: str = ""
    keywords: List[str] = field(default_factory=list)
    related_updates: List[str] = field(default_factory=list)
    
    # Processing
    ai_analysis: Optional[str] = None
    human_notes: Optional[str] = None
    is_false_positive: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'update_id': self.update_id,
            'framework': self.framework,
            'title': self.title,
            'summary': self.summary,
            'full_text': self.full_text,
            'source': self.source.to_dict(),
            'update_type': self.update_type.value,
            'severity': self.severity.value,
            'status': self.status.value,
            'detected_date': self.detected_date.isoformat(),
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'compliance_deadline': self.compliance_deadline.isoformat() if self.compliance_deadline else None,
            'affected_clauses': self.affected_clauses,
            'required_actions': self.required_actions,
            'impact_score': self.impact_score,
            'source_url': self.source_url,
            'reference_number': self.reference_number,
            'keywords': self.keywords,
            'related_updates': self.related_updates,
            'ai_analysis': self.ai_analysis,
            'human_notes': self.human_notes,
            'is_false_positive': self.is_false_positive
        }
    
    def to_jsonl(self) -> str:
        """Convert to JSONL format."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegulatoryUpdate':
        """Create from dictionary."""
        source_data = data.get('source', {})
        source = RegulatorySource(
            source_id=source_data.get('source_id', ''),
            name=source_data.get('name', ''),
            url=source_data.get('url', ''),
            framework=source_data.get('framework', ''),
            source_type=source_data.get('source_type', ''),
            check_frequency_hours=source_data.get('check_frequency_hours', 24),
            last_checked=datetime.fromisoformat(source_data['last_checked']) if source_data.get('last_checked') else None,
            is_active=source_data.get('is_active', True),
            keywords=source_data.get('keywords', [])
        )
        
        return cls(
            update_id=data['update_id'],
            framework=data['framework'],
            title=data['title'],
            summary=data['summary'],
            full_text=data['full_text'],
            source=source,
            update_type=UpdateType(data['update_type']),
            severity=UpdateSeverity(data['severity']),
            status=UpdateStatus(data['status']),
            detected_date=datetime.fromisoformat(data['detected_date']),
            effective_date=datetime.fromisoformat(data['effective_date']) if data.get('effective_date') else None,
            compliance_deadline=datetime.fromisoformat(data['compliance_deadline']) if data.get('compliance_deadline') else None,
            affected_clauses=data.get('affected_clauses', []),
            required_actions=data.get('required_actions', []),
            impact_score=data.get('impact_score', 0.0),
            source_url=data.get('source_url', ''),
            reference_number=data.get('reference_number', ''),
            keywords=data.get('keywords', []),
            related_updates=data.get('related_updates', []),
            ai_analysis=data.get('ai_analysis'),
            human_notes=data.get('human_notes'),
            is_false_positive=data.get('is_false_positive', False)
        )


@dataclass
class UpdateAlert:
    """Alert configuration for regulatory updates."""
    alert_id: str
    framework: str
    keywords: List[str]
    min_severity: UpdateSeverity
    notification_channels: List[str]  # slack, email, etc.
    is_active: bool = True
    
    def matches_update(self, update: RegulatoryUpdate) -> bool:
        """Check if alert should trigger for an update."""
        if not self.is_active:
            return False
        
        if update.framework != self.framework:
            return False
        
        # Check severity
        severity_order = {
            UpdateSeverity.LOW: 0,
            UpdateSeverity.MEDIUM: 1,
            UpdateSeverity.HIGH: 2,
            UpdateSeverity.CRITICAL: 3
        }
        if severity_order[update.severity] < severity_order[self.min_severity]:
            return False
        
        # Check keywords
        if self.keywords:
            update_text = f"{update.title} {update.summary} {update.full_text}".lower()
            if not any(keyword.lower() in update_text for keyword in self.keywords):
                return False
        
        return True
