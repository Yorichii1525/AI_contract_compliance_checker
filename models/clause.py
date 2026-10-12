"""Clause data model for contract analysis."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Clause:
    """Represents a single clause in a contract."""
    
    clause_id: str
    text: str
    start_position: int
    end_position: int
    section_number: Optional[str] = None
    heading: Optional[str] = None
    
    def __post_init__(self):
        """Validate clause data."""
        if not self.text or not self.text.strip():
            raise ValueError("Clause text cannot be empty")
        
        if self.start_position < 0:
            raise ValueError("Start position must be non-negative")
        
        if self.end_position <= self.start_position:
            raise ValueError("End position must be greater than start position")
    
    @property
    def length(self) -> int:
        """Get the length of the clause text."""
        return len(self.text)
    
    def __str__(self) -> str:
        """String representation of clause."""
        prefix = f"[{self.section_number}] " if self.section_number else ""
        heading = f"{self.heading}: " if self.heading else ""
        text_preview = self.text[:100] + "..." if len(self.text) > 100 else self.text
        return f"{prefix}{heading}{text_preview}"
