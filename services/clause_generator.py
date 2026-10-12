"""
Clause Generator service.
Generates compliant clause text for missing requirements using OpenAI.
"""
import os
import re
from typing import List, Optional, Dict, Any

from models.regulatory_requirement import RegulatoryRequirement
from models.clause_analysis import ClauseAnalysis
from services.prompt_builder import PromptBuilder
from utils.logger import get_logger

logger = get_logger(__name__)


class ClauseGenerator:
    """
    Generate compliant clause text using OpenAI API.
    Provides context-aware clause generation with legal formatting.
    Uses gpt-4o-mini for cost-effective, accurate generation.
    """
    
    def __init__(
        self,
        llama_model: Optional[Any] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        use_groq: bool = True  # kept for API compatibility, now uses OpenAI
    ):
        """
        Initialize ClauseGenerator with OpenAI.
        
        Args:
            llama_model: Unused (kept for API compatibility)
            prompt_builder: PromptBuilder instance (optional)
            use_groq: Unused (kept for API compatibility)
        """
        logger.info("Initializing ClauseGenerator...")
        
        self.llama = None
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.openai_client = None
        self.use_openai = False
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY', '').strip()
        if api_key and api_key not in ('', 'your_openai_api_key_here'):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=api_key)
                self.use_openai = True
                logger.info("ClauseGenerator using OpenAI gpt-4o-mini")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            logger.warning("No OpenAI API key found. Clause generation will use template fallback.")
        
        logger.info(f"ClauseGenerator initialized (OpenAI: {self.use_openai})")
    
    def _ensure_llama_loaded(self):
        """Ensure an LLM API client is available."""
        if self.use_openai and self.openai_client:
            return
        # No API available - generate_clause_text will catch the exception and use fallback
        raise RuntimeError(
            "No LLM API configured. Set OPENAI_API_KEY in your .env file. "
            "Falling back to template-based generation."
        )
    
    def generate_clause_text(
        self,
        requirement: RegulatoryRequirement,
        contract_context: Optional[str] = None,
        existing_clauses: Optional[List[ClauseAnalysis]] = None
    ) -> str:
        """
        Generate compliant clause text for a missing requirement.
        
        Args:
            requirement: Regulatory requirement to address
            contract_context: Context about the contract (optional)
            existing_clauses: Existing clauses for style reference (optional)
            
        Returns:
            Generated clause text
        """
        logger.info(
            f"Generating clause text for {requirement.article_reference}"
        )
        
        try:
            self._ensure_llama_loaded()
            
            # Prepare context
            context = contract_context or self._build_default_context(requirement)
            
            # Extract existing clause texts
            existing_texts = None
            if existing_clauses:
                existing_texts = [c.clause_text for c in existing_clauses[:3]]
            
            # Build prompt
            prompt = self.prompt_builder.build_generation_prompt(
                requirement,
                context,
                existing_texts
            )
            
            # Generate with OpenAI API
            if self.use_openai and self.openai_client:
                generated_text = self._generate_with_openai(prompt, max_tokens=400)
            else:
                raise RuntimeError("No LLM API available")
            
            # Post-process for legal formatting
            formatted_text = self._post_process_clause(generated_text, requirement)
            
            logger.info("Clause text generated successfully")
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error generating clause text: {e}", exc_info=True)
            # Return fallback template
            return self._generate_fallback_clause(requirement)
    
    def _generate_with_openai(self, prompt: str, max_tokens: int = 400) -> str:
        """
        Generate text using OpenAI API with gpt-4o-mini.
        
        gpt-4o-mini is chosen for:
        - ~50x cheaper than GPT-4 ($0.15/1M input, $0.60/1M output)
        - Very accurate for structured legal text generation
        - Fast response times
        
        Args:
            prompt: Generation prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert legal contract writer specializing in regulatory compliance. "
                            "Generate clear, precise, and legally sound contract clauses that comply with "
                            "all applicable regulations. Use professional legal language and structure. "
                            "Output ONLY the clause text without explanations or commentary."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for consistent legal text
                max_tokens=max_tokens
            )
            
            generated_text = response.choices[0].message.content
            return generated_text
            
        except Exception as e:
            logger.error(f"OpenAI API generation failed: {e}")
            raise
    
    def generate_modification_text(
        self,
        original_clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        issues: List[str]
    ) -> str:
        """
        Generate modified clause text to address specific issues.
        
        Args:
            original_clause: Original clause that needs modification
            requirement: Regulatory requirement to satisfy
            issues: Specific issues to address
            
        Returns:
            Modified clause text
        """
        logger.info(
            f"Generating modification for clause {original_clause.clause_id}"
        )
        
        try:
            self._ensure_llama_loaded()
            
            # Build modification prompt
            prompt = self.prompt_builder.build_modification_prompt(
                original_clause,
                requirement,
                issues
            )
            
            # Generate with OpenAI API
            if self.use_openai and self.openai_client:
                modified_text = self._generate_with_openai(prompt, max_tokens=400)
            else:
                raise RuntimeError("No LLM API available")
            
            # Post-process
            formatted_text = self._post_process_modification(
                modified_text,
                original_clause.clause_text
            )
            
            logger.info("Modification text generated successfully")
            
            return formatted_text
            
        except Exception as e:
            logger.error(f"Error generating modification: {e}")
            return self._generate_fallback_modification(
                original_clause.clause_text,
                issues
            )
    
    def generate_batch_clauses(
        self,
        requirements: List[RegulatoryRequirement],
        contract_context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate clause text for multiple requirements.
        
        Args:
            requirements: List of requirements to generate clauses for
            contract_context: Contract context (optional)
            
        Returns:
            Dictionary mapping requirement IDs to generated clause text
        """
        logger.info(f"Generating clauses for {len(requirements)} requirements")
        
        generated_clauses = {}
        
        for requirement in requirements:
            try:
                clause_text = self.generate_clause_text(
                    requirement,
                    contract_context
                )
                generated_clauses[requirement.requirement_id] = clause_text
            except Exception as e:
                logger.error(
                    f"Failed to generate clause for {requirement.requirement_id}: {e}"
                )
                generated_clauses[requirement.requirement_id] = self._generate_fallback_clause(
                    requirement
                )
        
        return generated_clauses
    
    def _post_process_clause(
        self,
        generated_text: str,
        requirement: RegulatoryRequirement
    ) -> str:
        """
        Post-process generated clause for legal formatting.
        
        Args:
            generated_text: Raw generated text
            requirement: Requirement being addressed
            
        Returns:
            Formatted clause text
        """
        # Clean up the text
        text = generated_text.strip()
        
        # Remove any prompt artifacts
        text = self._remove_prompt_artifacts(text)
        
        # Ensure proper capitalization
        if text and not text[0].isupper():
            text = text[0].upper() + text[1:]
        
        # Ensure ends with period
        if text and not text.endswith('.'):
            text += '.'
        
        # Add section heading if appropriate
        if requirement.clause_type and not self._has_heading(text):
            heading = self._generate_heading(requirement.clause_type)
            text = f"{heading}\n\n{text}"
        
        # Format paragraphs
        text = self._format_paragraphs(text)
        
        return text
    
    def _post_process_modification(
        self,
        modified_text: str,
        original_text: str
    ) -> str:
        """
        Post-process modified clause text.
        
        Args:
            modified_text: Generated modification
            original_text: Original clause text
            
        Returns:
            Formatted modified text
        """
        # Clean up
        text = modified_text.strip()
        
        # Remove prompt artifacts
        text = self._remove_prompt_artifacts(text)
        
        # If the modification includes explanation, extract just the clause
        text = self._extract_clause_from_explanation(text)
        
        # Preserve original formatting style where possible
        if original_text.startswith('"'):
            text = f'"{text}"'
        
        # Ensure proper ending
        if text and not text.endswith(('.', '"')):
            text += '.'
        
        return text
    
    def _remove_prompt_artifacts(self, text: str) -> str:
        """
        Remove common prompt artifacts from generated text.
        
        Args:
            text: Generated text
            
        Returns:
            Cleaned text
        """
        # Remove common prefixes
        prefixes_to_remove = [
            'GENERATED CLAUSE:',
            'MODIFIED CLAUSE:',
            'Here is',
            'The clause',
            'Response:',
            'RECOMMENDATION:',
            'ANALYSIS:'
        ]
        
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Italic
        
        return text
    
    def _extract_clause_from_explanation(self, text: str) -> str:
        """
        Extract clause text from text that includes explanation.
        
        Args:
            text: Text potentially containing clause and explanation
            
        Returns:
            Just the clause text
        """
        # Look for explanation markers
        explanation_markers = [
            'Explanation:',
            'Changes:',
            'Rationale:',
            'This modification',
            'The changes'
        ]
        
        for marker in explanation_markers:
            if marker in text:
                # Take everything before the marker
                text = text.split(marker)[0].strip()
                break
        
        return text
    
    def _has_heading(self, text: str) -> bool:
        """
        Check if text already has a section heading.
        
        Args:
            text: Text to check
            
        Returns:
            True if heading is present
        """
        lines = text.split('\n')
        if len(lines) > 1:
            first_line = lines[0].strip()
            # Check if first line looks like a heading
            if (first_line.isupper() or 
                first_line.endswith(':') or
                len(first_line.split()) <= 5):
                return True
        
        return False
    
    def _generate_heading(self, clause_type: str) -> str:
        """
        Generate appropriate heading for clause type.
        
        Args:
            clause_type: Type of clause
            
        Returns:
            Formatted heading
        """
        # Convert clause type to title case heading
        heading = clause_type.replace('_', ' ').title()
        return f"{heading}"
    
    def _format_paragraphs(self, text: str) -> str:
        """
        Format text into proper paragraphs.
        
        Args:
            text: Text to format
            
        Returns:
            Formatted text
        """
        # Split on double newlines
        paragraphs = text.split('\n\n')
        
        # Clean up each paragraph
        formatted_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if para:
                # Remove single newlines within paragraphs
                para = ' '.join(para.split('\n'))
                formatted_paragraphs.append(para)
        
        # Rejoin with double newlines
        return '\n\n'.join(formatted_paragraphs)
    
    def _build_default_context(self, requirement: RegulatoryRequirement) -> str:
        """
        Build default contract context based on requirement.
        
        Args:
            requirement: Regulatory requirement
            
        Returns:
            Default context string
        """
        context = (
            f"This is a data processing agreement subject to {requirement.framework} "
            f"regulations. The agreement is between a data controller and a data processor."
        )
        
        return context
    
    def _generate_fallback_clause(self, requirement: RegulatoryRequirement) -> str:
        """
        Generate fallback clause text using templates.
        
        Args:
            requirement: Regulatory requirement
            
        Returns:
            Template-based clause text
        """
        logger.info("Using fallback template for clause generation")
        
        # Basic template structure
        clause = f"{requirement.clause_type.replace('_', ' ').title()}\n\n"
        
        clause += f"In accordance with {requirement.article_reference}, "
        clause += f"{requirement.description.lower()} "
        
        # Add mandatory elements if available
        if requirement.mandatory_elements:
            clause += "This includes:\n\n"
            for element in requirement.mandatory_elements:
                clause += f"• {element}\n"
        
        clause += (
            f"\n\nThe parties agree to comply with all requirements set forth in "
            f"{requirement.article_reference} and maintain appropriate documentation "
            f"of such compliance."
        )
        
        return clause
    
    def _generate_fallback_modification(
        self,
        original_text: str,
        issues: List[str]
    ) -> str:
        """
        Generate fallback modification text.
        
        Args:
            original_text: Original clause text
            issues: Issues to address
            
        Returns:
            Modified text
        """
        logger.info("Using fallback for modification")
        
        # Simple approach: append addressing of issues
        modified = original_text.rstrip('.')
        
        modified += ". Additionally, "
        
        # Add generic language to address issues
        if any('missing' in issue.lower() for issue in issues):
            modified += "all required elements shall be included, "
        
        if any('unclear' in issue.lower() or 'ambiguous' in issue.lower() for issue in issues):
            modified += "with clear and unambiguous language, "
        
        modified += "in full compliance with applicable regulatory requirements."
        
        return modified
    
    def validate_generated_clause(
        self,
        clause_text: str,
        requirement: RegulatoryRequirement
    ) -> Dict[str, Any]:
        """
        Validate that generated clause meets basic requirements.
        
        Args:
            clause_text: Generated clause text
            requirement: Requirement it should address
            
        Returns:
            Validation results dictionary
        """
        validation = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check minimum length
        if len(clause_text) < 50:
            validation['valid'] = False
            validation['issues'].append("Clause text is too short")
        
        # Check for mandatory keywords
        clause_lower = clause_text.lower()
        missing_keywords = []
        
        for keyword in requirement.keywords[:5]:  # Check first 5 keywords
            if keyword.lower() not in clause_lower:
                missing_keywords.append(keyword)
        
        if len(missing_keywords) > len(requirement.keywords) * 0.5:
            validation['warnings'].append(
                f"Many expected keywords missing: {', '.join(missing_keywords[:3])}"
            )
        
        # Check for proper formatting
        if not clause_text.strip().endswith('.'):
            validation['warnings'].append("Clause should end with period")
        
        return validation
