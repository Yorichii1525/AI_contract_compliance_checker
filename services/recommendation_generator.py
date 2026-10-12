"""
Recommendation Generator service.
Generates recommendations for compliance gaps using LLaMA.
"""
import re
import uuid
from typing import List, Optional, Tuple, Any

from models.recommendation import Recommendation, ActionType
from models.regulatory_requirement import (
    RegulatoryRequirement,
    ClauseComplianceResult,
    RiskLevel,
    ComplianceStatus
)
from models.clause_analysis import ClauseAnalysis
# from services.legal_llama import LegalLLaMA  # Temporarily disabled - gated model
from services.prompt_builder import PromptBuilder
from utils.logger import get_logger

logger = get_logger(__name__)


class RecommendationGenerator:
    """
    Generate compliance recommendations using LLaMA.
    Processes compliance gaps and creates actionable recommendations.
    """
    
    def __init__(
        self,
        llama_model: Optional[Any] = None,  # LegalLLaMA disabled
        prompt_builder: Optional[PromptBuilder] = None
    ):
        """
        Initialize RecommendationGenerator.
        
        Args:
            llama_model: LegalLLaMA instance (optional, will create if not provided)
            prompt_builder: PromptBuilder instance (optional)
        """
        logger.info("Initializing RecommendationGenerator...")
        
        self.llama = llama_model
        self.prompt_builder = prompt_builder or PromptBuilder()
        
        # Lazy loading flag for LLaMA
        self._llama_loaded = llama_model is not None
        
        logger.info("RecommendationGenerator initialized")
    
    def _ensure_llama_loaded(self):
        """Ensure LLaMA model is loaded (lazy loading) - DISABLED."""
        # LLaMA model disabled - using fallback mode
        # if not self._llama_loaded:
        #     logger.info("Loading LLaMA model (lazy initialization)...")
        #     try:
        #         self.llama = LegalLLaMA()
        #         self._llama_loaded = True
        #     except Exception as e:
        #         logger.error(f"Failed to load LLaMA model: {e}")
        #         raise RuntimeError(f"Cannot generate recommendations without LLaMA: {e}")
        logger.warning("LLaMA model is disabled - using fallback recommendations")
        self._llama_loaded = False
    
    def generate_recommendations(
        self,
        compliance_results: List[ClauseComplianceResult],
        missing_requirements: List[RegulatoryRequirement]
    ) -> List[Recommendation]:
        """
        Generate recommendations for all compliance gaps.
        
        Args:
            compliance_results: List of clause compliance results
            missing_requirements: List of missing requirements
            
        Returns:
            List of prioritized recommendations
        """
        logger.info(
            f"Generating recommendations for {len(compliance_results)} "
            f"non-compliant clauses and {len(missing_requirements)} missing requirements"
        )
        
        recommendations = []
        
        try:
            # Generate recommendations for non-compliant clauses
            for result in compliance_results:
                if result.compliance_status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL]:
                    recs = self._generate_clause_recommendations(result)
                    recommendations.extend(recs)
            
            # Generate recommendations for missing requirements
            for requirement in missing_requirements:
                rec = self._generate_missing_requirement_recommendation(requirement)
                if rec:
                    recommendations.append(rec)
            
            # Sort by priority
            recommendations.sort(key=lambda r: r.priority)
            
            logger.info(f"Generated {len(recommendations)} recommendations")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return []
    
    def _generate_clause_recommendations(
        self,
        result: ClauseComplianceResult
    ) -> List[Recommendation]:
        """
        Generate recommendations for a non-compliant clause.
        
        Args:
            result: Clause compliance result
            
        Returns:
            List of recommendations for this clause
        """
        recommendations = []
        
        try:
            # For each matched requirement that has issues
            for requirement in result.matched_requirements:
                # Determine action type based on issues
                action_type = self._determine_action_type(result.issues)
                
                # Determine priority based on risk level
                priority = self._risk_to_priority(result.risk_level)
                
                # Create clause analysis object for prompt
                clause = ClauseAnalysis(
                    clause_id=result.clause_id,
                    clause_text=result.clause_text,
                    clause_type=result.clause_type,
                    confidence_score=result.confidence,
                    embeddings=None,
                    alternative_types=[]
                )
                
                # Generate recommendation using LLaMA
                if self._should_use_llama(priority):
                    self._ensure_llama_loaded()
                    
                    prompt = self.prompt_builder.build_recommendation_prompt(
                        clause,
                        requirement,
                        result.issues
                    )
                    
                    try:
                        llama_response = self.llama.generate(
                            prompt,
                            max_tokens=300,
                            temperature=0.7
                        )
                        
                        # Parse LLaMA response
                        description, rationale = self._parse_recommendation_response(
                            llama_response
                        )
                        
                    except Exception as e:
                        logger.warning(f"LLaMA generation failed, using fallback: {e}")
                        description, rationale = self._generate_fallback_recommendation(
                            result.issues,
                            requirement
                        )
                else:
                    # Use rule-based fallback for lower priority
                    description, rationale = self._generate_fallback_recommendation(
                        result.issues,
                        requirement
                    )
                
                # Create recommendation
                rec = Recommendation(
                    recommendation_id=str(uuid.uuid4()),
                    clause_id=result.clause_id,
                    requirement=requirement,
                    priority=priority,
                    action_type=action_type,
                    description=description,
                    rationale=rationale,
                    regulatory_reference=requirement.article_reference,
                    suggested_text=None,  # Will be generated separately if needed
                    confidence=0.8,
                    estimated_risk_reduction=result.risk_level.value
                )
                
                recommendations.append(rec)
                
        except Exception as e:
            logger.error(f"Error generating clause recommendations: {e}")
        
        return recommendations
    
    def _generate_missing_requirement_recommendation(
        self,
        requirement: RegulatoryRequirement
    ) -> Optional[Recommendation]:
        """
        Generate recommendation for a missing requirement.
        
        Args:
            requirement: Missing regulatory requirement
            
        Returns:
            Recommendation to add the missing clause
        """
        try:
            # Priority based on requirement risk level
            priority = self._risk_to_priority(requirement.risk_level)
            
            # Description
            description = (
                f"Add a {requirement.clause_type} clause to address "
                f"{requirement.article_reference}. "
                f"This clause is {'mandatory' if requirement.mandatory else 'recommended'} "
                f"for {requirement.framework} compliance."
            )
            
            # Rationale
            rationale = (
                f"{requirement.article_reference} requires: {requirement.description}. "
                f"The contract currently lacks this required clause, creating a compliance gap."
            )
            
            # Create recommendation
            rec = Recommendation(
                recommendation_id=str(uuid.uuid4()),
                clause_id=None,  # No existing clause
                requirement=requirement,
                priority=priority,
                action_type=ActionType.ADD_CLAUSE,
                description=description,
                rationale=rationale,
                regulatory_reference=requirement.article_reference,
                suggested_text=None,  # Will be generated separately
                confidence=0.9,
                estimated_risk_reduction=requirement.risk_level.value
            )
            
            return rec
            
        except Exception as e:
            logger.error(f"Error generating missing requirement recommendation: {e}")
            return None
    
    def generate_recommendation_with_llama(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        issues: List[str]
    ) -> Recommendation:
        """
        Generate a detailed recommendation using LLaMA.
        
        Args:
            clause: Clause to improve
            requirement: Requirement to satisfy
            issues: List of issues to address
            
        Returns:
            Detailed recommendation
        """
        self._ensure_llama_loaded()
        
        try:
            # Build prompt
            prompt = self.prompt_builder.build_recommendation_prompt(
                clause,
                requirement,
                issues
            )
            
            # Generate with LLaMA
            response = self.llama.generate(
                prompt,
                max_tokens=400,
                temperature=0.7
            )
            
            # Parse response
            priority_level, action, description, rationale = self._parse_detailed_response(
                response
            )
            
            # Convert priority level to number
            priority = self._priority_label_to_number(priority_level)
            
            # Convert action to ActionType
            action_type = self._action_string_to_type(action)
            
            # Create recommendation
            rec = Recommendation(
                recommendation_id=str(uuid.uuid4()),
                clause_id=clause.clause_id,
                requirement=requirement,
                priority=priority,
                action_type=action_type,
                description=description,
                rationale=rationale,
                regulatory_reference=requirement.article_reference,
                confidence=0.85
            )
            
            return rec
            
        except Exception as e:
            logger.error(f"Error generating LLaMA recommendation: {e}")
            # Fallback to rule-based
            return self._generate_fallback_recommendation_object(
                clause,
                requirement,
                issues
            )
    
    def extract_regulatory_references(self, text: str) -> List[str]:
        """
        Extract regulatory references from LLaMA output.
        
        Args:
            text: Generated text to parse
            
        Returns:
            List of regulatory references found
        """
        references = []
        
        # Patterns for common regulatory references
        patterns = [
            r'GDPR Article \d+(?:\(\d+\))?',
            r'Article \d+(?:\(\d+\))?',
            r'HIPAA §\d+\.\d+',
            r'§\d+\.\d+',
            r'CCPA §\d+',
            r'SOX Section \d+'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_refs = []
        for ref in references:
            if ref not in seen:
                seen.add(ref)
                unique_refs.append(ref)
        
        return unique_refs
    
    # Helper methods
    
    def _determine_action_type(self, issues: List[str]) -> ActionType:
        """
        Determine action type based on issues.
        
        Args:
            issues: List of issues
            
        Returns:
            Appropriate ActionType
        """
        issues_text = " ".join(issues).lower()
        
        if any(word in issues_text for word in ['missing', 'lacks', 'absent', 'not found']):
            return ActionType.ADD_CLAUSE
        elif any(word in issues_text for word in ['unclear', 'ambiguous', 'vague']):
            return ActionType.CLARIFY_CLAUSE
        elif any(word in issues_text for word in ['incomplete', 'insufficient', 'partial']):
            return ActionType.MODIFY_CLAUSE
        else:
            return ActionType.MODIFY_CLAUSE
    
    def _risk_to_priority(self, risk_level: RiskLevel) -> int:
        """
        Convert risk level to priority number.
        
        Args:
            risk_level: Risk level
            
        Returns:
            Priority number (1-5)
        """
        risk_priority_map = {
            RiskLevel.HIGH: 1,
            RiskLevel.MEDIUM: 3,
            RiskLevel.LOW: 4
        }
        return risk_priority_map.get(risk_level, 3)
    
    def _priority_label_to_number(self, label: str) -> int:
        """
        Convert priority label to number.
        
        Args:
            label: Priority label (HIGH, MEDIUM, LOW, etc.)
            
        Returns:
            Priority number (1-5)
        """
        label_upper = label.upper()
        
        if 'HIGH' in label_upper or 'CRITICAL' in label_upper:
            return 1
        elif 'MEDIUM' in label_upper:
            return 3
        elif 'LOW' in label_upper:
            return 4
        else:
            return 3
    
    def _action_string_to_type(self, action: str) -> ActionType:
        """
        Convert action string to ActionType.
        
        Args:
            action: Action string
            
        Returns:
            ActionType enum value
        """
        action_upper = action.upper()
        
        if 'ADD' in action_upper:
            return ActionType.ADD_CLAUSE
        elif 'MODIFY' in action_upper or 'UPDATE' in action_upper:
            return ActionType.MODIFY_CLAUSE
        elif 'CLARIFY' in action_upper:
            return ActionType.CLARIFY_CLAUSE
        elif 'REMOVE' in action_upper or 'DELETE' in action_upper:
            return ActionType.REMOVE_CLAUSE
        else:
            return ActionType.MODIFY_CLAUSE
    
    def _should_use_llama(self, priority: int) -> bool:
        """
        Determine if LLaMA should be used based on priority.
        
        Args:
            priority: Priority level
            
        Returns:
            True if LLaMA should be used
        """
        # Use LLaMA for high priority items (1-2)
        return priority <= 2
    
    def _parse_recommendation_response(self, response: str) -> Tuple[str, str]:
        """
        Parse LLaMA recommendation response.
        
        Args:
            response: Generated response
            
        Returns:
            Tuple of (description, rationale)
        """
        # Simple parsing - split on common markers
        lines = response.strip().split('\n')
        
        description_lines = []
        rationale_lines = []
        in_rationale = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if 'rationale' in line.lower() or 'reason' in line.lower():
                in_rationale = True
                continue
            
            if in_rationale:
                rationale_lines.append(line)
            else:
                description_lines.append(line)
        
        description = " ".join(description_lines) if description_lines else response[:200]
        rationale = " ".join(rationale_lines) if rationale_lines else "See regulatory requirement"
        
        return description, rationale
    
    def _parse_detailed_response(self, response: str) -> Tuple[str, str, str, str]:
        """
        Parse detailed LLaMA response with priority, action, description, rationale.
        
        Args:
            response: Generated response
            
        Returns:
            Tuple of (priority, action, description, rationale)
        """
        # Default values
        priority = "MEDIUM"
        action = "MODIFY"
        description = response[:200]
        rationale = "See regulatory requirement"
        
        # Try to extract structured information
        lines = response.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            if 'priority' in line_lower:
                if 'high' in line_lower or 'critical' in line_lower:
                    priority = "HIGH"
                elif 'low' in line_lower:
                    priority = "LOW"
            
            if 'action' in line_lower:
                if 'add' in line_lower:
                    action = "ADD"
                elif 'modify' in line_lower:
                    action = "MODIFY"
                elif 'clarify' in line_lower:
                    action = "CLARIFY"
        
        return priority, action, description, rationale
    
    def _generate_fallback_recommendation(
        self,
        issues: List[str],
        requirement: RegulatoryRequirement
    ) -> Tuple[str, str]:
        """
        Generate fallback recommendation without LLaMA.
        
        Args:
            issues: List of issues
            requirement: Regulatory requirement
            
        Returns:
            Tuple of (description, rationale)
        """
        issues_text = "; ".join(issues)
        
        description = (
            f"Update the clause to address the following issues: {issues_text}. "
            f"Ensure all mandatory elements from {requirement.article_reference} are included."
        )
        
        rationale = (
            f"{requirement.article_reference} requires: {requirement.description}. "
            f"The current clause does not fully satisfy these requirements."
        )
        
        return description, rationale
    
    def _generate_fallback_recommendation_object(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        issues: List[str]
    ) -> Recommendation:
        """
        Generate fallback recommendation object.
        
        Args:
            clause: Clause analysis
            requirement: Regulatory requirement
            issues: List of issues
            
        Returns:
            Recommendation object
        """
        description, rationale = self._generate_fallback_recommendation(
            issues,
            requirement
        )
        
        action_type = self._determine_action_type(issues)
        priority = self._risk_to_priority(requirement.risk_level)
        
        return Recommendation(
            recommendation_id=str(uuid.uuid4()),
            clause_id=clause.clause_id,
            requirement=requirement,
            priority=priority,
            action_type=action_type,
            description=description,
            rationale=rationale,
            regulatory_reference=requirement.article_reference,
            confidence=0.7
        )
