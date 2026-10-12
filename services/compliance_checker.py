"""
Compliance Checker service.
Main orchestrator for compliance checking across multiple frameworks.
"""
from typing import List, Optional, Dict
import time

from models.clause_analysis import ClauseAnalysis
from models.regulatory_requirement import (
    ComplianceReport,
    ClauseComplianceResult,
    RegulatoryRequirement
)
from services.regulatory_knowledge_base import RegulatoryKnowledgeBase
from services.compliance_rule_engine import ComplianceRuleEngine
from services.compliance_assessor import ComplianceAssessor
from services.compliance_scorer import ComplianceScorer
from services.embedding_generator import EmbeddingGenerator
from utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceChecker:
    """
    Main orchestrator for compliance checking.
    Coordinates all compliance checking services and generates comprehensive reports.
    """
    
    def __init__(
        self,
        knowledge_base: Optional[RegulatoryKnowledgeBase] = None,
        rule_engine: Optional[ComplianceRuleEngine] = None,
        assessor: Optional[ComplianceAssessor] = None,
        scorer: Optional[ComplianceScorer] = None,
        precompute_embeddings: bool = True
    ):
        """
        Initialize Compliance Checker.
        
        Args:
            knowledge_base: Regulatory knowledge base (optional, will create if not provided)
            rule_engine: Compliance rule engine (optional)
            assessor: Compliance assessor (optional)
            scorer: Compliance scorer (optional)
        """
        logger.info("Initializing Compliance Checker...")
        
        # Initialize components
        self.knowledge_base = knowledge_base or RegulatoryKnowledgeBase(
            embedding_generator=EmbeddingGenerator()
        )
        self.rule_engine = rule_engine or ComplianceRuleEngine()
        self.assessor = assessor or ComplianceAssessor(
            self.knowledge_base,
            self.rule_engine
        )
        self.scorer = scorer or ComplianceScorer()
        
        # Precompute embeddings for better performance
        if precompute_embeddings:
            try:
                self.knowledge_base.precompute_embeddings()
            except Exception as e:
                logger.warning(f"Could not precompute embeddings: {e}")
        
        logger.info("Compliance Checker initialized successfully")
    
    def check_compliance(
        self,
        clauses: List[ClauseAnalysis],
        frameworks: List[str],
        document_id: str = "unknown"
    ) -> ComplianceReport:
        """
        Check compliance of clauses against multiple regulatory frameworks.
        
        Args:
            clauses: List of analyzed clauses with embeddings
            frameworks: List of frameworks to check (e.g., ['GDPR', 'HIPAA'])
            document_id: Document identifier for the report
            
        Returns:
            ComplianceReport with comprehensive analysis
        """
        start_time = time.time()
        
        logger.info(
            f"\n\n{'#'*80}\n"
            f"# STARTING COMPLIANCE CHECK\n"
            f"# Document ID: {document_id}\n"
            f"# Frameworks: {', '.join(frameworks)}\n"
            f"# Number of clauses: {len(clauses)}\n"
            f"{'#'*80}\n"
        )
        
        try:
            # Validate inputs
            if not clauses:
                logger.warning("No clauses provided for compliance checking")
                return self._create_empty_report(document_id, frameworks)
            
            if not frameworks:
                logger.error("No frameworks specified for compliance checking")
                raise ValueError("At least one framework must be specified")
            
            # Validate frameworks
            valid_frameworks = self._validate_frameworks(frameworks)
            if not valid_frameworks:
                logger.error(f"No valid frameworks found in: {frameworks}")
                raise ValueError(
                    f"Invalid frameworks. Supported: GDPR, HIPAA, CCPA, SOX"
                )
            
            # Assess each clause against each framework
            all_results = []
            for framework in valid_frameworks:
                logger.info(
                    f"\n{'*'*60}\n"
                    f"Assessing {len(clauses)} clauses against {framework}...\n"
                    f"{'*'*60}"
                )
                framework_results = self.assessor.assess_multiple_clauses(
                    clauses,
                    framework
                )
                all_results.extend(framework_results)
                
                # Log framework summary
                compliant = sum(1 for r in framework_results if r.compliance_status.value == 'Compliant')
                partial = sum(1 for r in framework_results if r.compliance_status.value == 'Partial')
                non_compliant = sum(1 for r in framework_results if r.compliance_status.value == 'Non-Compliant')
                not_applicable = sum(1 for r in framework_results if r.compliance_status.value == 'Not Applicable')
                
                logger.info(
                    f"\n{framework} Assessment Summary:\n"
                    f"  Compliant: {compliant}\n"
                    f"  Partial: {partial}\n"
                    f"  Non-Compliant: {non_compliant}\n"
                    f"  Not Applicable: {not_applicable}\n"
                )
            
            logger.info(
                f"\n{'='*60}\n"
                f"Generated {len(all_results)} total compliance assessments\n"
                f"{'='*60}"
            )
            
            # Identify missing requirements for each framework
            all_missing_requirements = []
            for framework in valid_frameworks:
                logger.info(f"Identifying missing requirements for {framework}...")
                missing = self.knowledge_base.find_missing_requirements(
                    clauses,
                    framework
                )
                all_missing_requirements.extend(missing)
            
            logger.info(
                f"Identified {len(all_missing_requirements)} missing requirements"
            )
            
            # Generate comprehensive report
            report = self.scorer.generate_compliance_report(
                document_id=document_id,
                frameworks_checked=valid_frameworks,
                clause_results=all_results,
                missing_requirements=all_missing_requirements
            )
            
            elapsed_time = time.time() - start_time
            logger.info(
                f"\n\n{'#'*80}\n"
                f"# COMPLIANCE CHECK COMPLETED\n"
                f"# Time elapsed: {elapsed_time:.2f}s\n"
                f"# Overall score: {report.overall_score:.2f}\n"
                f"# Total assessments: {len(all_results)}\n"
                f"# Missing requirements: {len(all_missing_requirements)}\n"
                f"# High-risk items: {len(report.high_risk_items)}\n"
                f"{'#'*80}\n\n"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error during compliance checking: {e}", exc_info=True)
            # Return a report with error information
            return self._create_error_report(document_id, frameworks, str(e))
    
    def check_single_framework(
        self,
        clauses: List[ClauseAnalysis],
        framework: str,
        document_id: str = "unknown"
    ) -> ComplianceReport:
        """
        Check compliance against a single framework.
        
        Args:
            clauses: List of analyzed clauses
            framework: Framework to check against
            document_id: Document identifier
            
        Returns:
            ComplianceReport for the specified framework
        """
        return self.check_compliance(clauses, [framework], document_id)
    
    def quick_check(
        self,
        clauses: List[ClauseAnalysis],
        frameworks: List[str]
    ) -> Dict[str, float]:
        """
        Perform a quick compliance check and return scores only.
        
        Args:
            clauses: List of analyzed clauses
            frameworks: List of frameworks to check
            
        Returns:
            Dictionary mapping framework names to compliance scores
        """
        logger.info("Performing quick compliance check...")
        
        try:
            valid_frameworks = self._validate_frameworks(frameworks)
            scores = {}
            
            for framework in valid_frameworks:
                # Assess clauses
                results = self.assessor.assess_multiple_clauses(clauses, framework)
                
                # Find missing requirements
                missing = self.knowledge_base.find_missing_requirements(
                    clauses,
                    framework
                )
                
                # Calculate score
                score = self.scorer.calculate_overall_score(results, missing)
                scores[framework] = score
            
            logger.info(f"Quick check completed: {scores}")
            return scores
            
        except Exception as e:
            logger.error(f"Error during quick check: {e}")
            return {fw: 0.0 for fw in frameworks}
    
    def get_framework_statistics(self) -> Dict[str, any]:
        """
        Get statistics about available frameworks and requirements.
        
        Returns:
            Dictionary with framework statistics
        """
        return self.knowledge_base.get_statistics()
    
    def validate_clause_against_requirement(
        self,
        clause: ClauseAnalysis,
        requirement_id: str
    ) -> ClauseComplianceResult:
        """
        Validate a specific clause against a specific requirement.
        
        Args:
            clause: Analyzed clause
            requirement_id: ID of requirement to check against
            
        Returns:
            ClauseComplianceResult for the specific validation
        """
        logger.debug(
            f"Validating clause {clause.clause_id} against "
            f"requirement {requirement_id}"
        )
        
        try:
            # Get the requirement
            requirement = self.knowledge_base.get_requirement_by_id(requirement_id)
            
            if not requirement:
                logger.error(f"Requirement not found: {requirement_id}")
                raise ValueError(f"Requirement not found: {requirement_id}")
            
            # Calculate similarity
            clause_embedding = clause.embeddings
            req_embedding = self.knowledge_base.get_requirement_embedding(requirement)
            
            similarity = self.knowledge_base._cosine_similarity(
                clause_embedding,
                req_embedding
            )
            
            # Evaluate compliance
            status, risk, issues = self.rule_engine.evaluate_compliance(
                clause,
                requirement,
                similarity
            )
            
            # Create result
            result = ClauseComplianceResult(
                clause_id=clause.clause_id,
                clause_text=clause.clause_text,
                clause_type=clause.clause_type,
                framework=requirement.framework,
                compliance_status=status,
                risk_level=risk,
                matched_requirements=[requirement],
                confidence=similarity,
                issues=issues
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating clause against requirement: {e}")
            raise
    
    def get_missing_requirements_for_framework(
        self,
        clauses: List[ClauseAnalysis],
        framework: str
    ) -> List[RegulatoryRequirement]:
        """
        Get missing requirements for a specific framework.
        
        Args:
            clauses: List of analyzed clauses
            framework: Framework to check
            
        Returns:
            List of missing mandatory requirements
        """
        try:
            framework_upper = framework.upper()
            missing = self.knowledge_base.find_missing_requirements(
                clauses,
                framework_upper
            )
            
            logger.info(
                f"Found {len(missing)} missing requirements for {framework_upper}"
            )
            
            return missing
            
        except Exception as e:
            logger.error(f"Error getting missing requirements: {e}")
            return []
    
    def set_similarity_threshold(self, threshold: float):
        """
        Update the similarity threshold for requirement matching.
        
        Args:
            threshold: New similarity threshold (0.0 to 1.0)
        """
        self.knowledge_base.set_similarity_threshold(threshold)
        logger.info(f"Similarity threshold updated to {threshold}")
    
    # Private helper methods
    
    def _validate_frameworks(self, frameworks: List[str]) -> List[str]:
        """
        Validate and normalize framework names.
        
        Args:
            frameworks: List of framework names
            
        Returns:
            List of valid, normalized framework names
        """
        valid_frameworks = {'GDPR', 'HIPAA', 'CCPA', 'SOX'}
        normalized = []
        
        for framework in frameworks:
            framework_upper = framework.upper().strip()
            if framework_upper in valid_frameworks:
                normalized.append(framework_upper)
            else:
                logger.warning(f"Invalid framework ignored: {framework}")
        
        return normalized
    
    def _create_empty_report(
        self,
        document_id: str,
        frameworks: List[str]
    ) -> ComplianceReport:
        """
        Create an empty compliance report.
        
        Args:
            document_id: Document identifier
            frameworks: List of frameworks
            
        Returns:
            Empty ComplianceReport
        """
        from models.regulatory_requirement import ComplianceSummary
        
        return ComplianceReport(
            document_id=document_id,
            frameworks_checked=frameworks,
            overall_score=0.0,
            clause_results=[],
            missing_requirements=[],
            high_risk_items=[],
            summary=ComplianceSummary(
                total_clauses=0,
                compliant_clauses=0,
                non_compliant_clauses=0,
                partial_clauses=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0
            )
        )
    
    def _create_error_report(
        self,
        document_id: str,
        frameworks: List[str],
        error_message: str
    ) -> ComplianceReport:
        """
        Create an error compliance report.
        
        Args:
            document_id: Document identifier
            frameworks: List of frameworks
            error_message: Error message
            
        Returns:
            ComplianceReport with error information
        """
        from models.regulatory_requirement import ComplianceSummary
        
        logger.error(f"Creating error report: {error_message}")
        
        return ComplianceReport(
            document_id=document_id,
            frameworks_checked=frameworks,
            overall_score=0.0,
            clause_results=[],
            missing_requirements=[],
            high_risk_items=[],
            summary=ComplianceSummary(
                total_clauses=0,
                compliant_clauses=0,
                non_compliant_clauses=0,
                partial_clauses=0,
                high_risk_count=0,
                medium_risk_count=0,
                low_risk_count=0
            )
        )
    
    def get_supported_frameworks(self) -> List[str]:
        """
        Get list of supported regulatory frameworks.
        
        Returns:
            List of supported framework names
        """
        return ['GDPR', 'HIPAA', 'CCPA', 'SOX']
    
    def clear_cache(self):
        """Clear all caches to free memory."""
        self.knowledge_base.clear_embedding_cache()
        logger.info("Compliance checker caches cleared")
