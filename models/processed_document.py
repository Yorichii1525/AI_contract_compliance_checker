"""Processed document data model."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.clause import Clause


@dataclass
class ProcessedDocument:
    """Represents a processed contract document."""
    
    document_id: str
    original_filename: str
    extracted_text: str
    clauses: List[Clause]
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    processing_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate processed document data."""
        if not self.document_id:
            raise ValueError("Document ID cannot be empty")
        
        if not self.original_filename:
            raise ValueError("Original filename cannot be empty")
        
        if not self.extracted_text or not self.extracted_text.strip():
            raise ValueError("Extracted text cannot be empty")
    
    @property
    def num_clauses(self) -> int:
        """Get the number of clauses in the document."""
        return len(self.clauses)
    
    @property
    def total_characters(self) -> int:
        """Get total character count."""
        return len(self.extracted_text)
    
    @property
    def total_words(self) -> int:
        """Get approximate word count."""
        return len(self.extracted_text.split())
    
    def get_clause_by_id(self, clause_id: str) -> Optional[Clause]:
        """
        Get a clause by its ID.
        
        Args:
            clause_id: The clause ID to search for
            
        Returns:
            Clause if found, None otherwise
        """
        for clause in self.clauses:
            if clause.clause_id == clause_id:
                return clause
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with document data
        """
        return {
            'document_id': self.document_id,
            'original_filename': self.original_filename,
            'extracted_text': self.extracted_text,
            'num_clauses': self.num_clauses,
            'total_characters': self.total_characters,
            'total_words': self.total_words,
            'metadata': self.metadata,
            'processing_time': self.processing_time,
            'processing_date': self.processing_date.isoformat(),
            'clauses': [
                {
                    'clause_id': c.clause_id,
                    'text': c.text,
                    'start_position': c.start_position,
                    'end_position': c.end_position,
                    'section_number': c.section_number,
                    'heading': c.heading
                }
                for c in self.clauses
            ]
        }
    
    def __str__(self) -> str:
        """String representation of processed document."""
        return (
            f"ProcessedDocument(id={self.document_id}, "
            f"filename={self.original_filename}, "
            f"clauses={self.num_clauses}, "
            f"words={self.total_words})"
        )
