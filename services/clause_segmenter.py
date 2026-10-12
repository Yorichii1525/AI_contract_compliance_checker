"""Clause segmentation engine for contract documents."""

import logging
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass

from models.clause import Clause

logger = logging.getLogger(__name__)


@dataclass
class SegmentationResult:
    """Result of clause segmentation."""
    clauses: List[Clause]
    method_used: str
    confidence: float


class ClauseSegmenter:
    """Segment contract text into individual clauses."""
    
    # Common section number patterns
    SECTION_PATTERNS = [
        r'^\s*(\d+\.)+\s+',  # 1.1, 1.1.1, etc.
        r'^\s*\(([a-z]|[ivx]+)\)\s+',  # (a), (i), (iv), etc.
        r'^\s*([A-Z]\.)\s+',  # A., B., C., etc.
        r'^\s*Article\s+(\d+)',  # Article 1, Article 2, etc.
        r'^\s*Section\s+(\d+)',  # Section 1, Section 2, etc.
        r'^\s*§\s*(\d+)',  # § 1, § 2, etc.
    ]
    
    # Heading patterns (all caps or title case followed by colon or newline)
    HEADING_PATTERNS = [
        r'^([A-Z][A-Z\s]+):\s*',  # ALL CAPS HEADING:
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):?\s*$',  # Title Case Heading
    ]
    
    def __init__(self, min_clause_length: int = 50, max_clause_length: int = 5000):
        """
        Initialize clause segmenter.
        
        Args:
            min_clause_length: Minimum characters for a valid clause
            max_clause_length: Maximum characters for a single clause
        """
        self.logger = logging.getLogger(__name__)
        self.min_clause_length = min_clause_length
        self.max_clause_length = max_clause_length
    
    def segment(self, text: str) -> List[Clause]:
        """
        Segment text into clauses using best available method.
        
        Args:
            text: Contract text to segment
            
        Returns:
            List of Clause objects
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided for segmentation")
            return []
        
        # Try structure-based segmentation first
        result = self.segment_by_structure(text)
        
        if result.confidence > 0.7 and len(result.clauses) >= 3:
            self.logger.info(
                f"Structure-based segmentation: {len(result.clauses)} clauses, "
                f"{result.confidence:.2%} confidence"
            )
            return result.clauses
        
        # Fallback to semantic segmentation
        result = self.segment_by_semantics(text)
        self.logger.info(
            f"Semantic segmentation: {len(result.clauses)} clauses, "
            f"{result.confidence:.2%} confidence"
        )
        return result.clauses
    
    def segment_by_structure(self, text: str) -> SegmentationResult:
        """
        Segment text using document structure (headings, numbering).
        
        Args:
            text: Contract text to segment
            
        Returns:
            SegmentationResult with clauses and confidence
        """
        lines = text.split('\n')
        clauses = []
        current_clause_lines = []
        current_section = None
        current_heading = None
        current_start = 0
        char_position = 0
        
        section_count = 0
        heading_count = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            if not line_stripped:
                char_position += len(line) + 1
                continue
            
            # Check for section number
            section_match = self._match_section_number(line_stripped)
            
            # Check for heading
            heading_match = self._match_heading(line_stripped)
            
            # If we found a new section or heading, save previous clause
            if section_match or heading_match:
                if current_clause_lines:
                    clause_text = '\n'.join(current_clause_lines).strip()
                    
                    if len(clause_text) >= self.min_clause_length:
                        clause = Clause(
                            clause_id=f"clause_{len(clauses) + 1}",
                            text=clause_text,
                            start_position=current_start,
                            end_position=char_position,
                            section_number=current_section,
                            heading=current_heading
                        )
                        clauses.append(clause)
                
                # Start new clause
                current_clause_lines = [line_stripped]
                current_start = char_position
                
                if section_match:
                    current_section = section_match
                    section_count += 1
                
                if heading_match:
                    current_heading = heading_match
                    heading_count += 1
            else:
                current_clause_lines.append(line_stripped)
            
            char_position += len(line) + 1
        
        # Add final clause
        if current_clause_lines:
            clause_text = '\n'.join(current_clause_lines).strip()
            if len(clause_text) >= self.min_clause_length:
                clause = Clause(
                    clause_id=f"clause_{len(clauses) + 1}",
                    text=clause_text,
                    start_position=current_start,
                    end_position=char_position,
                    section_number=current_section,
                    heading=current_heading
                )
                clauses.append(clause)
        
        # Calculate confidence based on structure found
        total_markers = section_count + heading_count
        confidence = min(1.0, total_markers / max(len(clauses), 1) * 0.8)
        
        return SegmentationResult(
            clauses=clauses,
            method_used="structure",
            confidence=confidence
        )
    
    def segment_by_semantics(self, text: str) -> SegmentationResult:
        """
        Segment text using semantic boundaries (paragraphs, sentences).
        
        Args:
            text: Contract text to segment
            
        Returns:
            SegmentationResult with clauses and confidence
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        clauses = []
        char_position = 0
        current_clause_text = []
        current_start = 0
        
        for para in paragraphs:
            para = para.strip()
            
            if not para:
                char_position += 2  # Account for double newline
                continue
            
            # Add paragraph to current clause
            current_clause_text.append(para)
            combined_text = '\n\n'.join(current_clause_text)
            
            # Check if we should split here
            should_split = (
                len(combined_text) >= self.min_clause_length * 2 or
                len(combined_text) >= self.max_clause_length or
                self._is_semantic_boundary(para)
            )
            
            if should_split and len(combined_text) >= self.min_clause_length:
                clause = Clause(
                    clause_id=f"clause_{len(clauses) + 1}",
                    text=combined_text.strip(),
                    start_position=current_start,
                    end_position=char_position + len(para)
                )
                clauses.append(clause)
                
                # Reset for next clause
                current_clause_text = []
                current_start = char_position + len(para) + 2
            
            char_position += len(para) + 2
        
        # Add final clause
        if current_clause_text:
            combined_text = '\n\n'.join(current_clause_text).strip()
            if len(combined_text) >= self.min_clause_length:
                clause = Clause(
                    clause_id=f"clause_{len(clauses) + 1}",
                    text=combined_text,
                    start_position=current_start,
                    end_position=char_position
                )
                clauses.append(clause)
        
        # If we got very few clauses, try sentence-based splitting
        if len(clauses) < 3:
            clauses = self._segment_by_sentences(text)
        
        confidence = 0.6  # Semantic segmentation is less confident
        
        return SegmentationResult(
            clauses=clauses,
            method_used="semantic",
            confidence=confidence
        )
    
    def _segment_by_sentences(self, text: str) -> List[Clause]:
        """
        Fallback: segment by sentences when other methods fail.
        
        Args:
            text: Contract text
            
        Returns:
            List of clauses
        """
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        clauses = []
        current_sentences = []
        current_start = 0
        char_position = 0
        
        for sentence in sentences:
            current_sentences.append(sentence)
            combined = ' '.join(current_sentences)
            
            if len(combined) >= self.min_clause_length:
                clause = Clause(
                    clause_id=f"clause_{len(clauses) + 1}",
                    text=combined.strip(),
                    start_position=current_start,
                    end_position=char_position + len(sentence)
                )
                clauses.append(clause)
                
                current_sentences = []
                current_start = char_position + len(sentence) + 1
            
            char_position += len(sentence) + 1
        
        # Add remaining sentences
        if current_sentences:
            combined = ' '.join(current_sentences).strip()
            if len(combined) >= self.min_clause_length:
                clause = Clause(
                    clause_id=f"clause_{len(clauses) + 1}",
                    text=combined,
                    start_position=current_start,
                    end_position=char_position
                )
                clauses.append(clause)
        
        return clauses
    
    def _match_section_number(self, line: str) -> Optional[str]:
        """
        Check if line starts with a section number.
        
        Args:
            line: Line of text
            
        Returns:
            Section number if found, None otherwise
        """
        for pattern in self.SECTION_PATTERNS:
            match = re.match(pattern, line)
            if match:
                return match.group(0).strip()
        return None
    
    def _match_heading(self, line: str) -> Optional[str]:
        """
        Check if line is a heading.
        
        Args:
            line: Line of text
            
        Returns:
            Heading text if found, None otherwise
        """
        # Check if line is short enough to be a heading
        if len(line) > 100:
            return None
        
        for pattern in self.HEADING_PATTERNS:
            match = re.match(pattern, line)
            if match:
                return match.group(1).strip()
        
        # Check if entire line is uppercase (common for headings)
        if line.isupper() and len(line.split()) <= 10:
            return line.strip()
        
        return None
    
    def _is_semantic_boundary(self, paragraph: str) -> bool:
        """
        Check if paragraph represents a semantic boundary.
        
        Args:
            paragraph: Paragraph text
            
        Returns:
            True if this is likely a clause boundary
        """
        # Check for concluding phrases
        concluding_phrases = [
            'shall be',
            'agrees to',
            'is required to',
            'must',
            'will',
            'hereby',
            'notwithstanding',
            'provided that',
            'subject to'
        ]
        
        para_lower = paragraph.lower()
        
        # If paragraph starts with a concluding phrase, it's likely a new clause
        for phrase in concluding_phrases:
            if para_lower.startswith(phrase):
                return True
        
        # If paragraph ends with a period and next would start new topic
        if paragraph.endswith('.'):
            return True
        
        return False
