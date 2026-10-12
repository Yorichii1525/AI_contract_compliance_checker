"""
Data models for NLP clause analysis.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Optional
import numpy as np


class ClauseType(Enum):
    """Enumeration of clause types for classification."""
    DATA_PROCESSING = "Data Processing"
    SUBPROCESSOR_AUTH = "Sub-processor Authorization"
    DATA_SUBJECT_RIGHTS = "Data Subject Rights"
    BREACH_NOTIFICATION = "Breach Notification"
    DATA_TRANSFER = "Data Transfer"
    SECURITY_SAFEGUARDS = "Security Safeguards"
    PERMITTED_USES = "Permitted Uses and Disclosures"
    OTHER = "Other"


@dataclass
class ClauseAnalysis:
    """Analysis results for a single clause."""
    clause_id: str
    clause_text: str
    clause_type: str
    confidence_score: float
    embeddings: Optional[np.ndarray] = None
    alternative_types: Optional[List[Tuple[str, float]]] = None  # Other possible types with scores
    
    def __post_init__(self):
        """Initialize alternative_types if not provided."""
        if self.alternative_types is None:
            self.alternative_types = []
