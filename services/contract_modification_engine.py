"""
Contract Modification Module
Automatically applies relevant regulatory updates to active contracts
and suggests amendments for compliance
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import difflib
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ContractModificationEngine:
    """
    Engine for tracking regulatory changes and suggesting contract modifications.
    Implements automated clause mapping and amendment generation.
    """
    
    def __init__(self):
        """Initialize contract modification engine."""
        self.logger = logging.getLogger(__name__)
        self.modifications_dir = Path(__file__).parent.parent / "data" / "modifications"
        self.modifications_dir.mkdir(parents=True, exist_ok=True)
        
        # Thresholds from environment or defaults
        self.auto_apply_threshold = 0.95  # 95% confidence for auto-apply
        self.similarity_threshold = 0.75   # 75% similarity for clause matching
    
    def map_regulation_to_clauses(
        self,
        regulation: Dict[str, Any],
        contract_clauses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Map a regulatory change to affected contract clauses.
        
        Args:
            regulation: Regulatory update dictionary
            contract_clauses: List of contract clause dictionaries
            
        Returns:
            List of mappings with clause and match score
        """
        mappings = []
        
        # Extract regulation keywords
        reg_keywords = set(regulation.get('keywords', []))
        reg_text = regulation.get('description', '').lower()
        reg_domain = regulation.get('applicable_domain', '').lower()
        
        for clause in contract_clauses:
            # Calculate match score
            match_score = self._calculate_clause_match_score(
                clause=clause,
                reg_keywords=reg_keywords,
                reg_text=reg_text,
                reg_domain=reg_domain
            )
            
            if match_score >= self.similarity_threshold:
                mappings.append({
                    'clause_id': clause.get('id'),
                    'clause_number': clause.get('clause_number'),
                    'clause_title': clause.get('clause_title'),
                    'clause_text': clause.get('clause_text'),
                    'clause_type': clause.get('clause_type'),
                    'match_score': match_score,
                    'regulation_id': regulation.get('regulation_id'),
                    'regulation_title': regulation.get('title'),
                    'reason': self._explain_match(clause, regulation, match_score)
                })
        
        # Sort by match score
        mappings.sort(key=lambda x: x['match_score'], reverse=True)
        
        self.logger.info(f"Mapped regulation to {len(mappings)} clauses")
        return mappings
    
    def _calculate_clause_match_score(
        self,
        clause: Dict[str, Any],
        reg_keywords: set,
        reg_text: str,
        reg_domain: str
    ) -> float:
        """
        Calculate how well a clause matches a regulation.
        
        Args:
            clause: Clause dictionary
            reg_keywords: Set of regulation keywords
            reg_text: Regulation description text
            reg_domain: Applicable regulatory domain
            
        Returns:
            Match score (0-1)
        """
        score = 0.0
        
        clause_text = clause.get('clause_text', '').lower()
        clause_type = clause.get('clause_type', '').lower()
        
        # 1. Check domain match (30% weight)
        if reg_domain:
            if reg_domain in clause_type or reg_domain in clause_text:
                score += 0.3
        
        # 2. Check keyword overlap (40% weight)
        if reg_keywords:
            clause_words = set(clause_text.split())
            keyword_overlap = len(reg_keywords & clause_words)
            keyword_score = min(keyword_overlap / len(reg_keywords), 1.0)
            score += keyword_score * 0.4
        
        # 3. Check text similarity (30% weight)
        if reg_text:
            # Use difflib for text similarity
            similarity = difflib.SequenceMatcher(None, reg_text, clause_text).ratio()
            score += similarity * 0.3
        
        return min(score, 1.0)
    
    def _explain_match(
        self,
        clause: Dict[str, Any],
        regulation: Dict[str, Any],
        score: float
    ) -> str:
        """
        Generate explanation for why clause matches regulation.
        
        Args:
            clause: Clause dictionary
            regulation: Regulation dictionary
            score: Match score
            
        Returns:
            Explanation string
        """
        reasons = []
        
        if score >= 0.9:
            reasons.append("High confidence match")
        elif score >= 0.75:
            reasons.append("Probable match")
        
        # Check specific criteria
        reg_domain = regulation.get('applicable_domain', '')
        clause_type = clause.get('clause_type', '')
        
        if reg_domain and reg_domain.lower() in clause_type.lower():
            reasons.append(f"Clause type matches {reg_domain}")
        
        reg_keywords = set(regulation.get('keywords', []))
        clause_text = clause.get('clause_text', '').lower()
        matching_keywords = [kw for kw in reg_keywords if kw in clause_text]
        
        if matching_keywords:
            reasons.append(f"Contains keywords: {', '.join(matching_keywords[:3])}")
        
        return " | ".join(reasons) if reasons else "Similarity-based match"
    
    def generate_amendment_suggestion(
        self,
        clause: Dict[str, Any],
        regulation: Dict[str, Any],
        use_ai: bool = False
    ) -> Dict[str, Any]:
        """
        Generate suggested amendment for a clause based on regulatory change.
        
        Args:
            clause: Clause dictionary
            regulation: Regulation dictionary
            use_ai: Whether to use AI for generation (requires OpenAI API)
            
        Returns:
            Amendment suggestion dictionary
        """
        amendment = {
            'amendment_id': self._generate_amendment_id(clause, regulation),
            'clause_id': clause.get('id'),
            'clause_number': clause.get('clause_number'),
            'clause_title': clause.get('clause_title'),
            'original_text': clause.get('clause_text'),
            'regulation_id': regulation.get('regulation_id'),
            'regulation_title': regulation.get('title'),
            'severity': regulation.get('severity', 'medium'),
            'status': 'pending_review',
            'created_at': datetime.now().isoformat(),
            'confidence_score': 0.0
        }
        
        if use_ai:
            # Use AI to generate amendment
            ai_suggestion = self._generate_ai_amendment(clause, regulation)
            amendment.update(ai_suggestion)
        else:
            # Use template-based generation
            template_suggestion = self._generate_template_amendment(clause, regulation)
            amendment.update(template_suggestion)
        
        return amendment
    
    def _generate_ai_amendment(
        self,
        clause: Dict[str, Any],
        regulation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate amendment using AI (OpenAI API).
        
        Args:
            clause: Clause dictionary
            regulation: Regulation dictionary
            
        Returns:
            Amendment details dictionary
        """
        try:
            import openai
            import os
            
            # Configure OpenAI
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            if not openai.api_key:
                self.logger.warning("OpenAI API key not configured, using template")
                return self._generate_template_amendment(clause, regulation)
            
            # Build prompt
            prompt = f"""You are a legal compliance expert. Generate an amended version of the following contract clause to comply with a new regulatory requirement.

**Original Clause:**
{clause.get('clause_text', '')}

**New Regulatory Requirement:**
Title: {regulation.get('title', '')}
Description: {regulation.get('description', '')}
Jurisdiction: {regulation.get('jurisdiction', '')}
Domain: {regulation.get('applicable_domain', '')}

**Instructions:**
1. Provide the amended clause text that incorporates the regulatory requirements
2. Explain what changes were made and why
3. Highlight any remaining compliance considerations

**Response Format:**
Amended Text: [Your amended clause here]
Changes Made: [Brief explanation]
Rationale: [Legal reasoning]
Remaining Considerations: [Any additional notes]
"""
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                messages=[
                    {"role": "system", "content": "You are a legal compliance expert specializing in contract amendments."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '2000')),
                temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.3'))
            )
            
            # Parse response
            ai_response = response.choices[0].message.content
            
            # Extract sections (simplified parsing)
            suggested_text = self._extract_section(ai_response, "Amended Text:")
            changes_made = self._extract_section(ai_response, "Changes Made:")
            rationale = self._extract_section(ai_response, "Rationale:")
            considerations = self._extract_section(ai_response, "Remaining Considerations:")
            
            return {
                'suggested_text': suggested_text or clause.get('clause_text'),
                'changes_made': changes_made,
                'rationale': rationale,
                'remaining_considerations': considerations,
                'confidence_score': 0.85,  # High confidence for AI-generated
                'generation_method': 'ai'
            }
            
        except ImportError:
            self.logger.warning("OpenAI library not installed, using template")
            return self._generate_template_amendment(clause, regulation)
        except Exception as e:
            self.logger.error(f"Error generating AI amendment: {e}")
            return self._generate_template_amendment(clause, regulation)
    
    def _extract_section(self, text: str, section_header: str) -> str:
        """Extract a section from AI response."""
        try:
            start = text.find(section_header)
            if start == -1:
                return ""
            
            start += len(section_header)
            
            # Find next section or end
            next_headers = ["Amended Text:", "Changes Made:", "Rationale:", "Remaining Considerations:"]
            end = len(text)
            
            for header in next_headers:
                header_pos = text.find(header, start)
                if header_pos != -1 and header_pos < end:
                    end = header_pos
            
            return text[start:end].strip()
        except:
            return ""
    
    def _generate_template_amendment(
        self,
        clause: Dict[str, Any],
        regulation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate amendment using templates.
        
        Args:
            clause: Clause dictionary
            regulation: Regulation dictionary
            
        Returns:
            Amendment details dictionary
        """
        original_text = clause.get('clause_text', '')
        reg_domain = regulation.get('applicable_domain', '').upper()
        
        # Generate suggested text based on domain
        suggested_text = original_text
        changes_made = []
        
        if 'GDPR' in reg_domain or 'privacy' in regulation.get('title', '').lower():
            suggested_text += f"\n\n[GDPR Compliance Addition]\nThe parties shall comply with {regulation.get('title')} including but not limited to the requirements for {regulation.get('description', 'data protection')}."
            changes_made.append("Added GDPR compliance clause")
        
        elif 'HIPAA' in reg_domain or 'health' in regulation.get('title', '').lower():
            suggested_text += f"\n\n[HIPAA Compliance Addition]\nIn accordance with {regulation.get('title')}, all health information handling shall comply with the specified requirements."
            changes_made.append("Added HIPAA compliance requirements")
        
        else:
            suggested_text += f"\n\n[Compliance Update]\nThis clause is amended to comply with {regulation.get('title')}."
            changes_made.append("Added general compliance reference")
        
        return {
            'suggested_text': suggested_text,
            'changes_made': "; ".join(changes_made),
            'rationale': f"Template-based amendment to address {regulation.get('title')}",
            'remaining_considerations': "AI-assisted review recommended for accuracy",
            'confidence_score': 0.60,  # Lower confidence for templates
            'generation_method': 'template'
        }
    
    def _generate_amendment_id(self, clause: Dict, regulation: Dict) -> str:
        """Generate unique amendment ID."""
        import hashlib
        content = f"{clause.get('id', '')}{regulation.get('regulation_id', '')}{datetime.now().isoformat()}"
        return f"AMD-{hashlib.md5(content.encode()).hexdigest()[:12].upper()}"
    
    def save_amendment(self, amendment: Dict[str, Any]) -> str:
        """
        Save amendment to file system.
        
        Args:
            amendment: Amendment dictionary
            
        Returns:
            Path to saved amendment file
        """
        try:
            amendment_id = amendment['amendment_id']
            filepath = self.modifications_dir / f"{amendment_id}.json"
            
            with open(filepath, 'w') as f:
                json.dump(amendment, f, indent=2)
            
            self.logger.info(f"Saved amendment to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error saving amendment: {e}")
            return ""
    
    def can_auto_apply(self, amendment: Dict[str, Any]) -> bool:
        """
        Determine if amendment can be automatically applied.
        
        Args:
            amendment: Amendment dictionary
            
        Returns:
            True if safe to auto-apply
        """
        # Check confidence score
        if amendment.get('confidence_score', 0) < self.auto_apply_threshold:
            return False
        
        # Check if it's a simple change
        original = amendment.get('original_text', '')
        suggested = amendment.get('suggested_text', '')
        
        # Simple numeric change detection
        import re
        original_numbers = set(re.findall(r'\d+', original))
        suggested_numbers = set(re.findall(r'\d+', suggested))
        
        # If only numbers changed and nothing else, could be auto-applied
        if original_numbers != suggested_numbers:
            # Remove numbers and compare
            original_no_nums = re.sub(r'\d+', 'NUM', original)
            suggested_no_nums = re.sub(r'\d+', 'NUM', suggested)
            
            if original_no_nums == suggested_no_nums:
                self.logger.info("Simple numeric change detected - eligible for auto-apply")
                return True
        
        # For now, require human approval for all substantive changes
        return False
    
    def create_comparison(
        self,
        original_text: str,
        suggested_text: str
    ) -> Dict[str, Any]:
        """
        Create side-by-side comparison of original and suggested text.
        
        Args:
            original_text: Original clause text
            suggested_text: Suggested amended text
            
        Returns:
            Comparison dictionary with diff
        """
        # Generate unified diff
        diff = list(difflib.unified_diff(
            original_text.splitlines(keepends=True),
            suggested_text.splitlines(keepends=True),
            fromfile='Original',
            tofile='Suggested',
            lineterm=''
        ))
        
        # Generate HTML diff
        html_diff = difflib.HtmlDiff().make_file(
            original_text.splitlines(),
            suggested_text.splitlines(),
            'Original Clause',
            'Suggested Amendment'
        )
        
        return {
            'original': original_text,
            'suggested': suggested_text,
            'unified_diff': ''.join(diff),
            'html_diff': html_diff,
            'change_summary': self._summarize_changes(original_text, suggested_text)
        }
    
    def _summarize_changes(self, original: str, suggested: str) -> Dict[str, Any]:
        """Summarize what changed between texts."""
        return {
            'original_length': len(original),
            'suggested_length': len(suggested),
            'length_change': len(suggested) - len(original),
            'similarity_ratio': difflib.SequenceMatcher(None, original, suggested).ratio()
        }


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize engine
    engine = ContractModificationEngine()
    
    # Sample data
    regulation = {
        'regulation_id': 'GDPR-2024-001',
        'title': 'Updated Data Processing Requirements',
        'description': 'New requirements for data processor agreements including breach notification timelines',
        'keywords': ['data', 'processing', 'breach', 'notification', 'processor'],
        'applicable_domain': 'GDPR',
        'jurisdiction': 'EU',
        'severity': 'high'
    }
    
    clause = {
        'id': 'clause-123',
        'clause_number': '5.2',
        'clause_title': 'Data Processing',
        'clause_text': 'The Processor shall process personal data only on documented instructions from the Controller.',
        'clause_type': 'data_processing'
    }
    
    # Generate amendment
    amendment = engine.generate_amendment_suggestion(clause, regulation, use_ai=False)
    
    print("\nAmendment Generated:")
    print(f"ID: {amendment['amendment_id']}")
    print(f"Confidence: {amendment['confidence_score']}")
    print(f"Method: {amendment['generation_method']}")
    print(f"\nOriginal: {amendment['original_text'][:100]}...")
    print(f"\nSuggested: {amendment['suggested_text'][:100]}...")
    print(f"\nAuto-apply eligible: {engine.can_auto_apply(amendment)}")
