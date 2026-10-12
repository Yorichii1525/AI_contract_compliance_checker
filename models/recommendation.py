"""
Data models for recommendations and actions.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any

from models.regulatory_requirement import RegulatoryRequirement


class ActionType(Enum):
    """Enumeration of recommendation action types."""
    ADD_CLAUSE = "Add Clause"
    MODIFY_CLAUSE = "Modify Clause"
    REMOVE_CLAUSE = "Remove Clause"
    CLARIFY_CLAUSE = "Clarify Clause"


@dataclass
class Recommendation:
    """
    Represents a recommendation for improving contract compliance.
    """
    recommendation_id: str
    requirement: RegulatoryRequirement
    priority: int  # 1 (highest) to 5 (lowest)
    action_type: ActionType
    description: str
    rationale: str
    regulatory_reference: str
    clause_id: Optional[str] = None  # None if recommending new clause
    suggested_text: Optional[str] = None
    confidence: float = 0.8
    estimated_risk_reduction: Optional[str] = None  # HIGH, MEDIUM, LOW
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary."""
        return {
            'recommendation_id': self.recommendation_id,
            'clause_id': self.clause_id,
            'requirement': self.requirement.to_dict(),
            'priority': self.priority,
            'action_type': self.action_type.value,
            'description': self.description,
            'suggested_text': self.suggested_text,
            'rationale': self.rationale,
            'regulatory_reference': self.regulatory_reference,
            'confidence': self.confidence,
            'estimated_risk_reduction': self.estimated_risk_reduction
        }
    
    def get_priority_label(self) -> str:
        """Get human-readable priority label."""
        priority_map = {
            1: "Critical",
            2: "High",
            3: "Medium",
            4: "Low",
            5: "Optional"
        }
        return priority_map.get(self.priority, "Unknown")
