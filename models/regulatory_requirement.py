"""
Data models for regulatory requirements and compliance checking.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import numpy as np


class ComplianceStatus(Enum):
    """Enumeration of compliance status values."""
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    PARTIAL = "Partial"
    NOT_APPLICABLE = "Not Applicable"


class RiskLevel(Enum):
    """Enumeration of risk levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class RegulatoryRequirement:
    """
    Represents a single regulatory requirement from a compliance framework.
    """
    requirement_id: str
    framework: str  # GDPR, HIPAA, CCPA, SOX
    article_reference: str  # e.g., "GDPR Article 28", "HIPAA §164.308"
    clause_type: str  # Type of clause this requirement relates to
    description: str
    mandatory: bool
    keywords: List[str] = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None
    mandatory_elements: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.HIGH
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert requirement to dictionary (excluding embeddings)."""
        return {
            'requirement_id': self.requirement_id,
            'framework': self.framework,
            'article_reference': self.article_reference,
            'clause_type': self.clause_type,
            'description': self.description,
            'mandatory': self.mandatory,
            'keywords': self.keywords,
            'mandatory_elements': self.mandatory_elements,
            'risk_level': self.risk_level.value
        }


@dataclass
class ClauseComplianceResult:
    """
    Compliance assessment result for a single clause.
    """
    clause_id: str
    clause_text: str
    clause_type: str
    framework: str
    compliance_status: ComplianceStatus
    risk_level: RiskLevel
    matched_requirements: List[RegulatoryRequirement] = field(default_factory=list)
    confidence: float = 0.0
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'clause_id': self.clause_id,
            'clause_text': self.clause_text,
            'clause_type': self.clause_type,
            'framework': self.framework,
            'compliance_status': self.compliance_status.value,
            'risk_level': self.risk_level.value,
            'matched_requirements': [req.to_dict() for req in self.matched_requirements],
            'confidence': self.confidence,
            'issues': self.issues
        }


@dataclass
class ComplianceSummary:
    """
    Summary statistics for compliance analysis.
    """
    total_clauses: int
    compliant_clauses: int
    non_compliant_clauses: int
    partial_clauses: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            'total_clauses': self.total_clauses,
            'compliant_clauses': self.compliant_clauses,
            'non_compliant_clauses': self.non_compliant_clauses,
            'partial_clauses': self.partial_clauses,
            'high_risk_count': self.high_risk_count,
            'medium_risk_count': self.medium_risk_count,
            'low_risk_count': self.low_risk_count
        }


@dataclass
class ComplianceReport:
    """
    Complete compliance analysis report for a document.
    """
    document_id: str
    frameworks_checked: List[str]
    overall_score: float  # 0-100
    clause_results: List[ClauseComplianceResult] = field(default_factory=list)
    missing_requirements: List[RegulatoryRequirement] = field(default_factory=list)
    high_risk_items: List[ClauseComplianceResult] = field(default_factory=list)
    summary: Optional[ComplianceSummary] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            'document_id': self.document_id,
            'frameworks_checked': self.frameworks_checked,
            'overall_score': self.overall_score,
            'clause_results': [result.to_dict() for result in self.clause_results],
            'missing_requirements': [req.to_dict() for req in self.missing_requirements],
            'high_risk_items': [item.to_dict() for item in self.high_risk_items],
            'summary': self.summary.to_dict() if self.summary else None
        }
