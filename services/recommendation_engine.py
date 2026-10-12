"""
Recommendation Engine service.
Main orchestrator for generating recommendations and compliant clause text.
Coordinates LLaMA operations with error handling and timeout management.
"""
import time
import signal
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from models.recommendation import Recommendation
from models.regulatory_requirement import (
    ComplianceReport,
    RegulatoryRequirement,
    ClauseComplianceResult
)
from models.clause_analysis import ClauseAnalysis
# from services.legal_llama import LegalLLaMA  # Temporarily disabled - gated model
from services.prompt_builder import PromptBuilder
from services.recommendation_generator import RecommendationGenerator
from services.clause_generator import ClauseGenerator
from config.settings import config
from utils.logger import get_logger

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Exception raised when operation times out."""
    pass


class RecommendationEngine:
    """
    Main orchestrator for recommendation generation.
    Coordinates LLaMA-based services with comprehensive error handling.
    """
    
    def __init__(
        self,
        llama_model: Optional[Any] = None,  # LegalLLaMA disabled
        use_llama: bool = False  # Disabled by default
    ):
        """
        Initialize RecommendationEngine.
        
        Args:
            llama_model: Pre-initialized LegalLLaMA instance (optional)
            use_llama: Whether to use LLaMA for generation (default True)
        """
        logger.info("Initializing RecommendationEngine...")
        
        self.use_llama = use_llama
        self.timeout = config.llm.generation_timeout
        
        # Initialize components
        self.llama = llama_model
        self.prompt_builder = PromptBuilder()
        
        # Initialize generators (with lazy loading)
        self.recommendation_generator = RecommendationGenerator(
            llama_model=self.llama,
            prompt_builder=self.prompt_builder
        )
        
        self.clause_generator = ClauseGenerator(
            llama_model=self.llama,
            prompt_builder=self.prompt_builder
        )
        
        # Statistics
        self.stats = {
            'recommendations_generated': 0,
            'clauses_generated': 0,
            'errors': 0,
            'timeouts': 0
        }
        
        logger.info(
            f"RecommendationEngine initialized (use_llama={use_llama}, "
            f"timeout={self.timeout}s)"
        )
    
    def generate_recommendations(
        self,
        compliance_report: ComplianceReport
    ) -> List[Recommendation]:
        """
        Generate recommendations for all compliance gaps in a report.
        
        Args:
            compliance_report: Complete compliance analysis report
            
        Returns:
            List of prioritized recommendations
        """
        logger.info(
            f"Generating recommendations for document {compliance_report.document_id}"
        )
        
        start_time = time.time()
        
        try:
            # Extract non-compliant results
            non_compliant_results = [
                result for result in compliance_report.clause_results
                if result.compliance_status.value in ['Non-Compliant', 'Partial']
            ]
            
            logger.info(
                f"Found {len(non_compliant_results)} non-compliant clauses and "
                f"{len(compliance_report.missing_requirements)} missing requirements"
            )
            
            # Generate recommendations with timeout protection
            recommendations = self._generate_with_timeout(
                self.recommendation_generator.generate_recommendations,
                non_compliant_results,
                compliance_report.missing_requirements
            )
            
            # Update statistics
            self.stats['recommendations_generated'] += len(recommendations)
            
            elapsed = time.time() - start_time
            logger.info(
                f"Generated {len(recommendations)} recommendations in {elapsed:.2f}s"
            )
            
            return recommendations
            
        except TimeoutError:
            logger.error("Recommendation generation timed out")
            self.stats['timeouts'] += 1
            return self._generate_fallback_recommendations(compliance_report)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            self.stats['errors'] += 1
            return self._generate_fallback_recommendations(compliance_report)
    
    def generate_clause_for_recommendation(
        self,
        recommendation: Recommendation,
        contract_context: Optional[str] = None,
        existing_clauses: Optional[List[ClauseAnalysis]] = None
    ) -> str:
        """
        Generate compliant clause text for a specific recommendation.
        
        Args:
            recommendation: Recommendation to generate clause for
            contract_context: Context about the contract (optional)
            existing_clauses: Existing clauses for style reference (optional)
            
        Returns:
            Generated clause text
        """
        logger.info(
            f"Generating clause text for recommendation {recommendation.recommendation_id}"
        )
        
        try:
            # Generate with timeout protection
            clause_text = self._generate_with_timeout(
                self.clause_generator.generate_clause_text,
                recommendation.requirement,
                contract_context,
                existing_clauses
            )
            
            # Update recommendation with generated text
            recommendation.suggested_text = clause_text
            
            # Update statistics
            self.stats['clauses_generated'] += 1
            
            logger.info("Clause text generated successfully")
            
            return clause_text
            
        except TimeoutError:
            logger.error("Clause generation timed out")
            self.stats['timeouts'] += 1
            return self._generate_fallback_clause_text(recommendation.requirement)
            
        except Exception as e:
            logger.error(f"Error generating clause text: {e}", exc_info=True)
            self.stats['errors'] += 1
            return self._generate_fallback_clause_text(recommendation.requirement)
    
    def generate_all_missing_clauses(
        self,
        missing_requirements: List[RegulatoryRequirement],
        contract_context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate clause text for all missing requirements.
        
        Args:
            missing_requirements: List of missing requirements
            contract_context: Contract context (optional)
            
        Returns:
            Dictionary mapping requirement IDs to generated clause text
        """
        logger.info(
            f"Generating clauses for {len(missing_requirements)} missing requirements"
        )
        
        generated_clauses = {}
        
        for requirement in missing_requirements:
            try:
                clause_text = self._generate_with_timeout(
                    self.clause_generator.generate_clause_text,
                    requirement,
                    contract_context,
                    None
                )
                
                generated_clauses[requirement.requirement_id] = clause_text
                self.stats['clauses_generated'] += 1
                
            except (TimeoutError, Exception) as e:
                logger.warning(
                    f"Failed to generate clause for {requirement.requirement_id}: {e}"
                )
                generated_clauses[requirement.requirement_id] = self._generate_fallback_clause_text(
                    requirement
                )
                self.stats['errors'] += 1
        
        return generated_clauses
    
    def generate_modification_for_clause(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        issues: List[str]
    ) -> str:
        """
        Generate modification text for a non-compliant clause.
        
        Args:
            clause: Clause to modify
            requirement: Requirement to satisfy
            issues: Issues to address
            
        Returns:
            Modified clause text
        """
        logger.info(f"Generating modification for clause {clause.clause_id}")
        
        try:
            modified_text = self._generate_with_timeout(
                self.clause_generator.generate_modification_text,
                clause,
                requirement,
                issues
            )
            
            return modified_text
            
        except (TimeoutError, Exception) as e:
            logger.error(f"Error generating modification: {e}")
            self.stats['errors'] += 1
            return clause.clause_text  # Return original as fallback
    
    def generate_comprehensive_report(
        self,
        compliance_report: ComplianceReport,
        contract_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recommendation report with clause text.
        
        Args:
            compliance_report: Compliance analysis report
            contract_context: Contract context (optional)
            
        Returns:
            Dictionary with recommendations and generated clauses
        """
        logger.info("Generating comprehensive recommendation report")
        
        start_time = time.time()
        
        try:
            # Generate recommendations
            recommendations = self.generate_recommendations(compliance_report)
            
            # Generate clause text for high-priority recommendations
            high_priority_recs = [r for r in recommendations if r.priority <= 2]
            
            for rec in high_priority_recs:
                if rec.action_type.value in ['Add Clause', 'Modify Clause']:
                    try:
                        clause_text = self.generate_clause_for_recommendation(
                            rec,
                            contract_context
                        )
                        rec.suggested_text = clause_text
                    except Exception as e:
                        logger.warning(
                            f"Could not generate clause for recommendation "
                            f"{rec.recommendation_id}: {e}"
                        )
            
            elapsed = time.time() - start_time
            
            report = {
                'document_id': compliance_report.document_id,
                'frameworks': compliance_report.frameworks_checked,
                'overall_score': compliance_report.overall_score,
                'recommendations': [r.to_dict() for r in recommendations],
                'high_priority_count': len([r for r in recommendations if r.priority <= 2]),
                'medium_priority_count': len([r for r in recommendations if r.priority == 3]),
                'low_priority_count': len([r for r in recommendations if r.priority >= 4]),
                'generation_time': elapsed,
                'statistics': self.get_statistics()
            }
            
            logger.info(
                f"Comprehensive report generated in {elapsed:.2f}s with "
                f"{len(recommendations)} recommendations"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}", exc_info=True)
            return {
                'document_id': compliance_report.document_id,
                'error': str(e),
                'recommendations': []
            }
    
    def _generate_with_timeout(self, func, *args, **kwargs):
        """
        Execute function with timeout protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            TimeoutError: If execution exceeds timeout
        """
        # Note: signal.alarm only works on Unix systems
        # For Windows, we'll use a simpler approach without timeout
        
        try:
            import platform
            if platform.system() != 'Windows':
                # Unix-based timeout using signal
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Operation timed out after {self.timeout}s")
                
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout)
                
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                
                return result
            else:
                # Windows: no timeout protection, just execute
                logger.debug("Timeout protection not available on Windows")
                return func(*args, **kwargs)
                
        except TimeoutError:
            raise
        except Exception as e:
            logger.error(f"Error in timeout-protected execution: {e}")
            raise
    
    def _generate_fallback_recommendations(
        self,
        compliance_report: ComplianceReport
    ) -> List[Recommendation]:
        """
        Generate fallback recommendations without LLaMA.
        
        Args:
            compliance_report: Compliance report
            
        Returns:
            List of basic recommendations
        """
        logger.info("Generating fallback recommendations")
        
        recommendations = []
        
        # Simple recommendations for missing requirements
        for i, requirement in enumerate(compliance_report.missing_requirements):
            from models.recommendation import ActionType
            import uuid
            
            rec = Recommendation(
                recommendation_id=str(uuid.uuid4()),
                clause_id=None,
                requirement=requirement,
                priority=1 if requirement.mandatory else 3,
                action_type=ActionType.ADD_CLAUSE,
                description=f"Add {requirement.clause_type} clause to satisfy {requirement.article_reference}",
                rationale=requirement.description,
                regulatory_reference=requirement.article_reference,
                confidence=0.7
            )
            
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_fallback_clause_text(
        self,
        requirement: RegulatoryRequirement
    ) -> str:
        """
        Generate fallback clause text without LLaMA.
        
        Args:
            requirement: Requirement to address
            
        Returns:
            Basic clause text
        """
        logger.info("Generating fallback clause text")
        
        clause = f"{requirement.clause_type.replace('_', ' ').title()}\n\n"
        clause += f"In accordance with {requirement.article_reference}, "
        clause += f"the parties agree to {requirement.description.lower()}"
        
        if requirement.mandatory_elements:
            clause += ", including:\n\n"
            for element in requirement.mandatory_elements:
                clause += f"• {element}\n"
        else:
            clause += "."
        
        return clause
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get engine statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'recommendations_generated': self.stats['recommendations_generated'],
            'clauses_generated': self.stats['clauses_generated'],
            'errors': self.stats['errors'],
            'timeouts': self.stats['timeouts'],
            'use_llama': self.use_llama,
            'timeout_seconds': self.timeout
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'recommendations_generated': 0,
            'clauses_generated': 0,
            'errors': 0,
            'timeouts': 0
        }
        logger.info("Statistics reset")
    
    def clear_cache(self):
        """Clear all caches to free memory."""
        if self.llama:
            self.llama.clear_cache()
        logger.info("Recommendation engine caches cleared")
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate engine configuration.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check if LLaMA is available when required
        if self.use_llama and not self.llama:
            validation['warnings'].append(
                "LLaMA model not loaded (will use lazy loading)"
            )
        
        # Check timeout configuration
        if self.timeout < 10:
            validation['warnings'].append(
                f"Timeout ({self.timeout}s) may be too short for LLaMA generation"
            )
        
        # Check if components are initialized
        if not self.prompt_builder:
            validation['valid'] = False
            validation['issues'].append("PromptBuilder not initialized")
        
        if not self.recommendation_generator:
            validation['valid'] = False
            validation['issues'].append("RecommendationGenerator not initialized")
        
        if not self.clause_generator:
            validation['valid'] = False
            validation['issues'].append("ClauseGenerator not initialized")
        
        return validation
