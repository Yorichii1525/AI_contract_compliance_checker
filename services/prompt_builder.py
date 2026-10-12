"""
Prompt Builder service for creating LLaMA prompts.
Provides templates for compliance analysis, clause generation, and modification suggestions.
"""
from typing import List, Dict, Any, Optional

from models.clause_analysis import ClauseAnalysis
from models.regulatory_requirement import RegulatoryRequirement, ClauseComplianceResult
from utils.logger import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """
    Build structured prompts for LLaMA-based legal reasoning.
    Provides templates for different types of legal analysis tasks.
    """
    
    def __init__(self):
        """Initialize PromptBuilder."""
        logger.info("PromptBuilder initialized")
    
    def build_recommendation_prompt(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        issues: List[str]
    ) -> str:
        """
        Build prompt for generating recommendations to fix compliance issues.
        
        Args:
            clause: Analyzed clause with issues
            requirement: Regulatory requirement not met
            issues: List of specific issues identified
            
        Returns:
            Formatted prompt for recommendation generation
        """
        issues_text = "\n".join([f"- {issue}" for issue in issues])
        
        prompt = f"""You are a legal compliance expert specializing in {requirement.framework} regulations.

REGULATORY REQUIREMENT:
Reference: {requirement.article_reference}
Description: {requirement.description}
Mandatory Elements:
{self._format_mandatory_elements(requirement.mandatory_elements)}

CURRENT CONTRACT CLAUSE:
{clause.clause_text}

IDENTIFIED ISSUES:
{issues_text}

TASK:
Provide specific, actionable recommendations to make this clause compliant with {requirement.article_reference}.

Your response should include:
1. Priority level (HIGH/MEDIUM/LOW) based on legal risk
2. Specific action required (ADD/MODIFY/CLARIFY)
3. Detailed recommendation explaining what needs to change
4. Rationale referencing the specific regulatory requirement

RECOMMENDATION:"""
        
        return prompt
    
    def build_generation_prompt(
        self,
        requirement: RegulatoryRequirement,
        contract_context: str,
        existing_clauses: Optional[List[str]] = None
    ) -> str:
        """
        Build prompt for generating compliant clause text from scratch.
        
        Args:
            requirement: Regulatory requirement to address
            contract_context: Context about the contract (type, parties, etc.)
            existing_clauses: List of existing clause texts for context
            
        Returns:
            Formatted prompt for clause generation
        """
        context_section = f"\nCONTRACT CONTEXT:\n{contract_context}\n" if contract_context else ""
        
        existing_section = ""
        if existing_clauses:
            existing_text = "\n\n".join(existing_clauses[:3])  # Limit to 3 for context
            existing_section = f"\nEXISTING CLAUSES (for style reference):\n{existing_text}\n"
        
        prompt = f"""You are a legal drafting expert specializing in {requirement.framework} compliance.

REGULATORY REQUIREMENT:
Reference: {requirement.article_reference}
Description: {requirement.description}
Mandatory Elements Required:
{self._format_mandatory_elements(requirement.mandatory_elements)}
{context_section}{existing_section}
TASK:
Draft a complete, legally sound contract clause that satisfies {requirement.article_reference}.

Requirements for the clause:
1. Include ALL mandatory elements listed above
2. Use clear, professional legal language
3. Be specific and unambiguous
4. Match the style of existing clauses if provided
5. Be comprehensive but concise

GENERATED CLAUSE:"""
        
        return prompt
    
    def build_modification_prompt(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        issues: List[str]
    ) -> str:
        """
        Build prompt for suggesting specific modifications to an existing clause.
        
        Args:
            clause: Current clause that needs modification
            requirement: Regulatory requirement to satisfy
            issues: Specific issues to address
            
        Returns:
            Formatted prompt for modification suggestions
        """
        issues_text = "\n".join([f"- {issue}" for issue in issues])
        
        prompt = f"""You are a legal editor specializing in {requirement.framework} compliance.

REGULATORY REQUIREMENT:
Reference: {requirement.article_reference}
Description: {requirement.description}
Mandatory Elements:
{self._format_mandatory_elements(requirement.mandatory_elements)}

CURRENT CLAUSE TEXT:
{clause.clause_text}

ISSUES TO ADDRESS:
{issues_text}

TASK:
Suggest specific modifications to the current clause to make it compliant with {requirement.article_reference}.

Your response should:
1. Preserve the original structure and intent where possible
2. Add missing mandatory elements
3. Clarify ambiguous language
4. Highlight what changed and why

Provide the modified clause text followed by a brief explanation of changes.

MODIFIED CLAUSE:"""
        
        return prompt
    
    def build_compliance_analysis_prompt(
        self,
        clause_text: str,
        framework: str,
        requirements: List[RegulatoryRequirement]
    ) -> str:
        """
        Build prompt for comprehensive compliance analysis of a clause.
        
        Args:
            clause_text: Text of clause to analyze
            framework: Regulatory framework (GDPR, HIPAA, etc.)
            requirements: List of relevant requirements to check against
            
        Returns:
            Formatted prompt for compliance analysis
        """
        requirements_text = "\n\n".join([
            f"{req.article_reference}:\n{req.description}\nMandatory: {req.mandatory}"
            for req in requirements
        ])
        
        prompt = f"""You are a legal compliance analyst specializing in {framework} regulations.

RELEVANT {framework} REQUIREMENTS:
{requirements_text}

CONTRACT CLAUSE TO ANALYZE:
{clause_text}

TASK:
Analyze this clause for compliance with the {framework} requirements listed above.

Your analysis should include:
1. Compliance status (COMPLIANT/PARTIAL/NON-COMPLIANT)
2. Which requirements are satisfied
3. Which requirements are missing or incomplete
4. Specific issues or gaps identified
5. Risk level (HIGH/MEDIUM/LOW)

ANALYSIS:"""
        
        return prompt
    
    def build_gap_analysis_prompt(
        self,
        framework: str,
        found_clauses: List[ClauseAnalysis],
        missing_requirements: List[RegulatoryRequirement]
    ) -> str:
        """
        Build prompt for analyzing gaps in contract coverage.
        
        Args:
            framework: Regulatory framework
            found_clauses: Clauses found in the contract
            missing_requirements: Requirements not covered
            
        Returns:
            Formatted prompt for gap analysis
        """
        found_types = list(set([c.clause_type for c in found_clauses]))
        found_text = ", ".join(found_types)
        
        missing_text = "\n".join([
            f"- {req.article_reference}: {req.description}"
            for req in missing_requirements
        ])
        
        prompt = f"""You are a legal compliance consultant specializing in {framework}.

CONTRACT COVERAGE:
The contract currently includes clauses for: {found_text}

MISSING REQUIREMENTS:
{missing_text}

TASK:
Provide a gap analysis and prioritized recommendations for addressing the missing requirements.

Your response should include:
1. Risk assessment for each missing requirement
2. Priority order for addressing gaps (HIGH/MEDIUM/LOW)
3. Brief explanation of why each requirement is important
4. Suggested approach for remediation

GAP ANALYSIS:"""
        
        return prompt
    
    def build_batch_recommendation_prompt(
        self,
        compliance_results: List[ClauseComplianceResult],
        missing_requirements: List[RegulatoryRequirement],
        framework: str
    ) -> str:
        """
        Build prompt for generating recommendations for multiple issues at once.
        
        Args:
            compliance_results: List of non-compliant clause results
            missing_requirements: List of missing requirements
            framework: Regulatory framework
            
        Returns:
            Formatted prompt for batch recommendations
        """
        # Summarize non-compliant clauses
        non_compliant_summary = []
        for result in compliance_results[:5]:  # Limit to top 5
            non_compliant_summary.append(
                f"Clause: {result.clause_text[:100]}...\n"
                f"Issues: {', '.join(result.issues)}\n"
                f"Risk: {result.risk_level.value}"
            )
        
        non_compliant_text = "\n\n".join(non_compliant_summary)
        
        # Summarize missing requirements
        missing_text = "\n".join([
            f"- {req.article_reference}: {req.description}"
            for req in missing_requirements[:5]  # Limit to top 5
        ])
        
        prompt = f"""You are a legal compliance consultant providing recommendations for {framework} compliance.

NON-COMPLIANT CLAUSES:
{non_compliant_text}

MISSING REQUIREMENTS:
{missing_text}

TASK:
Provide a prioritized action plan to achieve full {framework} compliance.

Your response should include:
1. Top 3-5 priority actions
2. For each action: what needs to be done and why
3. Estimated risk reduction for each action
4. Suggested order of implementation

ACTION PLAN:"""
        
        return prompt
    
    def build_regulatory_context_injection(
        self,
        requirement: RegulatoryRequirement
    ) -> str:
        """
        Build regulatory context section for injection into prompts.
        
        Args:
            requirement: Regulatory requirement
            
        Returns:
            Formatted regulatory context text
        """
        context = f"""REGULATORY CONTEXT:
Framework: {requirement.framework}
Reference: {requirement.article_reference}
Requirement: {requirement.description}
Mandatory: {'Yes' if requirement.mandatory else 'No'}
Risk Level: {requirement.risk_level.value}
"""
        
        if requirement.mandatory_elements:
            context += f"\nMandatory Elements:\n"
            context += self._format_mandatory_elements(requirement.mandatory_elements)
        
        if requirement.keywords:
            context += f"\nKey Terms: {', '.join(requirement.keywords)}\n"
        
        return context
    
    # Helper methods
    
    def _format_mandatory_elements(self, elements: List[str]) -> str:
        """
        Format mandatory elements as a bulleted list.
        
        Args:
            elements: List of mandatory elements
            
        Returns:
            Formatted string
        """
        if not elements:
            return "None specified"
        
        return "\n".join([f"  • {element}" for element in elements])
    
    def _truncate_text(self, text: str, max_length: int = 500) -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length] + "..."
    
    def validate_prompt(self, prompt: str, max_length: int = 4000) -> bool:
        """
        Validate that prompt is within acceptable length.
        
        Args:
            prompt: Prompt to validate
            max_length: Maximum allowed length
            
        Returns:
            True if valid, False otherwise
        """
        if len(prompt) > max_length:
            logger.warning(
                f"Prompt length ({len(prompt)}) exceeds maximum ({max_length})"
            )
            return False
        
        return True
    
    def get_prompt_stats(self, prompt: str) -> Dict[str, Any]:
        """
        Get statistics about a prompt.
        
        Args:
            prompt: Prompt to analyze
            
        Returns:
            Dictionary with prompt statistics
        """
        return {
            'length': len(prompt),
            'lines': prompt.count('\n') + 1,
            'words': len(prompt.split()),
            'estimated_tokens': len(prompt.split()) * 1.3  # Rough estimate
        }
