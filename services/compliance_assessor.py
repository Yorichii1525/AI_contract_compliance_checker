"""
Compliance Assessor service.
Assesses individual clauses against regulatory requirements.
"""
from typing import List, Optional

from models.clause_analysis import ClauseAnalysis
from models.regulatory_requirement import (
    RegulatoryRequirement,
    ClauseComplianceResult,
    ComplianceStatus,
    RiskLevel
)
from services.regulatory_knowledge_base import RegulatoryKnowledgeBase
from services.compliance_rule_engine import ComplianceRuleEngine
from utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceAssessor:
    """
    Assesses clause compliance against regulatory requirements.
    Combines semantic matching with rule-based evaluation.
    """
    
    def __init__(
        self,
        knowledge_base: RegulatoryKnowledgeBase,
        rule_engine: Optional[ComplianceRuleEngine] = None
    ):
        """
        Initialize Compliance Assessor.
        
        Args:
            knowledge_base: Regulatory knowledge base for requirement matching
            rule_engine: Compliance rule engine for evaluation (optional)
        """
        self.knowledge_base = knowledge_base
        self.rule_engine = rule_engine or ComplianceRuleEngine()
        logger.info("Compliance Assessor initialized")
    
    def assess_clause_compliance(
        self,
        clause: ClauseAnalysis,
        framework: str
    ) -> ClauseComplianceResult:
        """
        Assess a single clause's compliance against a regulatory framework.
        
        Args:
            clause: Analyzed clause with embeddings
            framework: Regulatory framework to check against (GDPR, HIPAA, etc.)
            
        Returns:
            ClauseComplianceResult with compliance status, risk level, and issues
        """
        try:
            logger.info(
                f"\n{'='*60}\n"
                f"Assessing clause {clause.clause_id} against {framework}\n"
                f"Clause type: {clause.clause_type}\n"
                f"Clause text preview: {clause.clause_text[:100]}...\n"
                f"{'='*60}"
            )
            
            # Match clause to requirements using semantic similarity
            matches = self.knowledge_base.match_clause_to_requirements(
                clause,
                framework,
                top_k=3  # Get top 3 matches
            )
            
            if not matches:
                # No matching requirements found
                logger.warning(
                    f"\u274c No matching requirements found for clause {clause.clause_id} "
                    f"in {framework}. Setting status to NOT_APPLICABLE."
                )
                return ClauseComplianceResult(
                    clause_id=clause.clause_id,
                    clause_text=clause.clause_text,
                    clause_type=clause.clause_type,
                    framework=framework,
                    compliance_status=ComplianceStatus.NOT_APPLICABLE,
                    risk_level=RiskLevel.LOW,
                    matched_requirements=[],
                    confidence=0.0,
                    issues=["No matching requirements found for this clause type"]
                )
            
            # Get the best match
            best_requirement, best_similarity = matches[0]
            
            logger.info(
                f"\u2713 Best match: {best_requirement.requirement_id} "
                f"(similarity: {best_similarity:.4f})\n"
                f"  Requirement: {best_requirement.description[:100]}..."
            )
            
            # Evaluate compliance using rule engine
            status, risk, issues = self.rule_engine.evaluate_compliance(
                clause,
                best_requirement,
                best_similarity
            )
            
            # Collect all matched requirements
            matched_requirements = [req for req, _ in matches]
            
            logger.info(
                f"\nCompliance Evaluation Result:\n"
                f"  Status: {status.value}\n"
                f"  Risk: {risk.value}\n"
                f"  Matched Requirements: {len(matched_requirements)}\n"
                f"  Issues: {len(issues)}"
            )
            
            # Create compliance result
            result = ClauseComplianceResult(
                clause_id=clause.clause_id,
                clause_text=clause.clause_text,
                clause_type=clause.clause_type,
                framework=framework,
                compliance_status=status,
                risk_level=risk,
                matched_requirements=matched_requirements,
                confidence=best_similarity,
                issues=issues
            )
            
            logger.info(
                f"\n{'='*60}\n"
                f"Assessment Complete for {clause.clause_id}\n"
                f"Status: {status.value}, Risk: {risk.value}, Confidence: {best_similarity:.2f}\n"
                f"{'='*60}\n"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error assessing clause compliance: {e}", exc_info=True)
            # Return a safe default result
            return ClauseComplianceResult(
                clause_id=clause.clause_id,
                clause_text=clause.clause_text,
                clause_type=clause.clause_type,
                framework=framework,
                compliance_status=ComplianceStatus.NOT_APPLICABLE,
                risk_level=RiskLevel.MEDIUM,
                matched_requirements=[],
                confidence=0.0,
                issues=[f"Error during assessment: {str(e)}"]
            )
    
    def assess_multiple_clauses(
        self,
        clauses: List[ClauseAnalysis],
        framework: str
    ) -> List[ClauseComplianceResult]:
        """
        Assess multiple clauses against a framework.
        
        Args:
            clauses: List of analyzed clauses
            framework: Regulatory framework to check against
            
        Returns:
            List of compliance results
        """
        logger.info(
            f"Assessing {len(clauses)} clauses against {framework}"
        )
        
        results = []
        for clause in clauses:
            result = self.assess_clause_compliance(clause, framework)
            results.append(result)
        
        logger.info(
            f"Completed assessment of {len(results)} clauses for {framework}"
        )
        
        return results
    
    def assess_clause_against_multiple_frameworks(
        self,
        clause: ClauseAnalysis,
        frameworks: List[str]
    ) -> List[ClauseComplianceResult]:
        """
        Assess a single clause against multiple frameworks.
        
        Args:
            clause: Analyzed clause
            frameworks: List of frameworks to check against
            
        Returns:
            List of compliance results (one per framework)
        """
        logger.debug(
            f"Assessing clause {clause.clause_id} against "
            f"{len(frameworks)} frameworks"
        )
        
        results = []
        for framework in frameworks:
            result = self.assess_clause_compliance(clause, framework)
            results.append(result)
        
        return results
    
    def determine_overall_clause_risk(
        self,
        results: List[ClauseComplianceResult]
    ) -> RiskLevel:
        """
        Determine overall risk level for a clause across multiple frameworks.
        
        Args:
            results: List of compliance results for the same clause
            
        Returns:
            Overall risk level (highest risk found)
        """
        if not results:
            return RiskLevel.LOW
        
        # Return the highest risk level found
        risk_priority = {
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 1
        }
        
        highest_risk = max(results, key=lambda r: risk_priority[r.risk_level])
        return highest_risk.risk_level
    
    def filter_results_by_status(
        self,
        results: List[ClauseComplianceResult],
        status: ComplianceStatus
    ) -> List[ClauseComplianceResult]:
        """
        Filter compliance results by status.
        
        Args:
            results: List of compliance results
            status: Status to filter by
            
        Returns:
            Filtered list of results
        """
        filtered = [r for r in results if r.compliance_status == status]
        logger.debug(
            f"Filtered {len(filtered)} results with status {status.value}"
        )
        return filtered
    
    def filter_results_by_risk(
        self,
        results: List[ClauseComplianceResult],
        risk_level: RiskLevel
    ) -> List[ClauseComplianceResult]:
        """
        Filter compliance results by risk level.
        
        Args:
            results: List of compliance results
            risk_level: Risk level to filter by
            
        Returns:
            Filtered list of results
        """
        filtered = [r for r in results if r.risk_level == risk_level]
        logger.debug(
            f"Filtered {len(filtered)} results with risk level {risk_level.value}"
        )
        return filtered
    
    def get_high_risk_results(
        self,
        results: List[ClauseComplianceResult]
    ) -> List[ClauseComplianceResult]:
        """
        Get all high-risk compliance results.
        
        Args:
            results: List of compliance results
            
        Returns:
            List of high-risk results
        """
        return self.filter_results_by_risk(results, RiskLevel.HIGH)
    
    def get_non_compliant_results(
        self,
        results: List[ClauseComplianceResult]
    ) -> List[ClauseComplianceResult]:
        """
        Get all non-compliant results.
        
        Args:
            results: List of compliance results
            
        Returns:
            List of non-compliant results
        """
        return self.filter_results_by_status(results, ComplianceStatus.NON_COMPLIANT)
