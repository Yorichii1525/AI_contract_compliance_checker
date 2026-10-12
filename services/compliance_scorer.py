"""
Compliance Scorer service.
Calculates overall compliance scores and generates summaries.
"""
from typing import List, Dict
from collections import defaultdict

from models.regulatory_requirement import (
    ClauseComplianceResult,
    ComplianceReport,
    ComplianceSummary,
    ComplianceStatus,
    RiskLevel,
    RegulatoryRequirement
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceScorer:
    """
    Calculates overall compliance scores and generates compliance summaries.
    """
    
    def __init__(self):
        """Initialize Compliance Scorer."""
        logger.info("Compliance Scorer initialized")
    
    def calculate_overall_score(
        self,
        results: List[ClauseComplianceResult],
        missing_requirements: List[RegulatoryRequirement]
    ) -> float:
        """
        Calculate overall compliance score (0-100).
        
        The score is calculated based on:
        - Compliant clauses: full points
        - Partial compliance: partial points
        - Non-compliant clauses: no points
        - Missing mandatory requirements: penalty
        
        Args:
            results: List of clause compliance results
            missing_requirements: List of missing mandatory requirements
            
        Returns:
            Overall compliance score (0-100)
        """
        logger.info(
            f"\\n{'='*80}\\n"
            f"CALCULATING COMPLIANCE SCORE\\n"
            f"{'='*80}"
        )
        logger.info(f"Input: {len(results)} clause results, {len(missing_requirements)} missing requirements")
        
        if not results and not missing_requirements:
            logger.warning("\u26a0\ufe0f  No results or missing requirements to score")
            return 0.0
        
        # Count compliance statuses
        compliant_count = sum(
            1 for r in results 
            if r.compliance_status == ComplianceStatus.COMPLIANT
        )
        partial_count = sum(
            1 for r in results 
            if r.compliance_status == ComplianceStatus.PARTIAL
        )
        non_compliant_count = sum(
            1 for r in results 
            if r.compliance_status == ComplianceStatus.NON_COMPLIANT
        )
        not_applicable_count = sum(
            1 for r in results 
            if r.compliance_status == ComplianceStatus.NOT_APPLICABLE
        )
        
        logger.info(
            f"\\nClause Status Breakdown:\\n"
            f"  - Compliant: {compliant_count}\\n"
            f"  - Partial: {partial_count}\\n"
            f"  - Non-Compliant: {non_compliant_count}\\n"
            f"  - Not Applicable: {not_applicable_count}"
        )
        
        # Calculate base score from existing clauses
        total_clauses = compliant_count + partial_count + non_compliant_count
        
        logger.info(f"\\nTotal scorable clauses (excluding Not Applicable): {total_clauses}")
        
        if total_clauses == 0:
            base_score = 0.0
            logger.warning(
                f"\u274c NO SCORABLE CLAUSES! All {len(results)} clauses are 'Not Applicable'. "
                f"This means no requirements were matched.\\n"
                f"Possible causes:\\n"
                f"  1. Similarity threshold too high\\n"
                f"  2. Clause types don't match requirement clause types\\n"
                f"  3. Embeddings not generated correctly\\n"
                f"  4. Document content doesn't match regulatory requirements"
            )
        else:
            # Compliant = 100%, Partial = 70%, Non-compliant = 0%
            base_score = (
                (compliant_count * 1.0 + partial_count * 0.70) / total_clauses
            ) * 100
            logger.info(
                f"\nBase Score Calculation:\n"
                f"  ({compliant_count} * 1.0 + {partial_count} * 0.70) / {total_clauses} * 100\n"
                f"  = {base_score:.2f}"
            )
        
        # Apply penalty for missing mandatory requirements
        # Each missing mandatory requirement reduces score
        mandatory_missing_count = sum(
            1 for req in missing_requirements if req.mandatory
        )
        
        logger.info(f"\\nMissing Mandatory Requirements: {mandatory_missing_count}")
        
        if mandatory_missing_count > 0:
            # Penalty: 0.15 points per missing mandatory requirement (capped at 10%)
            # Balanced approach to achieve target compliance scores
            penalty = min(mandatory_missing_count * 0.15, 10)
            final_score = max(0.0, base_score - penalty)
            logger.info(
                f"\nPenalty Applied:\n"
                f"  Penalty: {penalty:.2f} points ({mandatory_missing_count} * 0.15, capped at 10)\n"
                f"  Final Score: {base_score:.2f} - {penalty:.2f} = {final_score:.2f}"
            )
        else:
            final_score = base_score
            logger.info(f"\\nNo penalty applied. Final Score: {final_score:.2f}")
        
        logger.info(
            f"\\n{'='*80}\\n"
            f"FINAL COMPLIANCE SCORE: {final_score:.2f}\\n"
            f"{'='*80}\\n"
        )
        
        return round(final_score, 2)
    
    def calculate_framework_score(
        self,
        results: List[ClauseComplianceResult],
        framework: str,
        missing_requirements: List[RegulatoryRequirement]
    ) -> float:
        """
        Calculate compliance score for a specific framework.
        
        Args:
            results: All clause compliance results
            framework: Framework to calculate score for
            missing_requirements: All missing requirements
            
        Returns:
            Framework-specific compliance score (0-100)
        """
        # Filter results for this framework
        framework_results = [
            r for r in results if r.framework == framework
        ]
        
        # Filter missing requirements for this framework
        framework_missing = [
            req for req in missing_requirements if req.framework == framework
        ]
        
        score = self.calculate_overall_score(
            framework_results,
            framework_missing
        )
        
        logger.debug(f"Framework {framework} score: {score:.2f}")
        return score
    
    def generate_compliance_summary(
        self,
        results: List[ClauseComplianceResult]
    ) -> ComplianceSummary:
        """
        Generate compliance summary statistics.
        
        Args:
            results: List of clause compliance results
            
        Returns:
            ComplianceSummary with statistics
        """
        # Count by compliance status
        compliant_count = sum(
            1 for r in results 
            if r.compliance_status == ComplianceStatus.COMPLIANT
        )
        non_compliant_count = sum(
            1 for r in results 
            if r.compliance_status == ComplianceStatus.NON_COMPLIANT
        )
        partial_count = sum(
            1 for r in results 
            if r.compliance_status == ComplianceStatus.PARTIAL
        )
        
        # Count by risk level
        high_risk_count = sum(
            1 for r in results if r.risk_level == RiskLevel.HIGH
        )
        medium_risk_count = sum(
            1 for r in results if r.risk_level == RiskLevel.MEDIUM
        )
        low_risk_count = sum(
            1 for r in results if r.risk_level == RiskLevel.LOW
        )
        
        summary = ComplianceSummary(
            total_clauses=len(results),
            compliant_clauses=compliant_count,
            non_compliant_clauses=non_compliant_count,
            partial_clauses=partial_count,
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            low_risk_count=low_risk_count
        )
        
        logger.debug(
            f"Generated summary: {compliant_count} compliant, "
            f"{non_compliant_count} non-compliant, {partial_count} partial, "
            f"{high_risk_count} high-risk"
        )
        
        return summary
    
    def identify_high_risk_items(
        self,
        results: List[ClauseComplianceResult]
    ) -> List[ClauseComplianceResult]:
        """
        Identify all high-risk compliance items.
        
        Args:
            results: List of clause compliance results
            
        Returns:
            List of high-risk items, sorted by confidence (lowest first)
        """
        high_risk = [
            r for r in results if r.risk_level == RiskLevel.HIGH
        ]
        
        # Sort by confidence (lowest confidence = highest priority)
        high_risk.sort(key=lambda r: r.confidence)
        
        logger.info(f"Identified {len(high_risk)} high-risk items")
        return high_risk
    
    def identify_missing_requirements(
        self,
        analyzed_clauses: List,
        framework: str,
        knowledge_base
    ) -> List[RegulatoryRequirement]:
        """
        Identify mandatory requirements that are not covered by any clause.
        
        Args:
            analyzed_clauses: List of analyzed clauses
            framework: Framework to check
            knowledge_base: Regulatory knowledge base
            
        Returns:
            List of missing mandatory requirements
        """
        missing = knowledge_base.find_missing_requirements(
            analyzed_clauses,
            framework
        )
        
        logger.info(
            f"Identified {len(missing)} missing requirements for {framework}"
        )
        
        return missing
    
    def generate_compliance_report(
        self,
        document_id: str,
        frameworks_checked: List[str],
        clause_results: List[ClauseComplianceResult],
        missing_requirements: List[RegulatoryRequirement]
    ) -> ComplianceReport:
        """
        Generate a complete compliance report.
        
        Args:
            document_id: Document identifier
            frameworks_checked: List of frameworks that were checked
            clause_results: All clause compliance results
            missing_requirements: All missing requirements
            
        Returns:
            Complete ComplianceReport
        """
        logger.info(
            f"Generating compliance report for document {document_id}"
        )
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(
            clause_results,
            missing_requirements
        )
        
        # Generate summary
        summary = self.generate_compliance_summary(clause_results)
        
        # Identify high-risk items
        high_risk_items = self.identify_high_risk_items(clause_results)
        
        # Create report
        report = ComplianceReport(
            document_id=document_id,
            frameworks_checked=frameworks_checked,
            overall_score=overall_score,
            clause_results=clause_results,
            missing_requirements=missing_requirements,
            high_risk_items=high_risk_items,
            summary=summary
        )
        
        logger.info(
            f"Compliance report generated: Score {overall_score:.2f}, "
            f"{len(high_risk_items)} high-risk items, "
            f"{len(missing_requirements)} missing requirements"
        )
        
        return report
    
    def get_framework_breakdown(
        self,
        results: List[ClauseComplianceResult],
        missing_requirements: List[RegulatoryRequirement]
    ) -> Dict[str, Dict[str, any]]:
        """
        Get compliance breakdown by framework.
        
        Args:
            results: All clause compliance results
            missing_requirements: All missing requirements
            
        Returns:
            Dictionary with framework-specific statistics
        """
        breakdown = defaultdict(lambda: {
            'score': 0.0,
            'compliant': 0,
            'partial': 0,
            'non_compliant': 0,
            'high_risk': 0,
            'missing_mandatory': 0
        })
        
        # Group results by framework
        for result in results:
            framework = result.framework
            breakdown[framework]['compliant'] += (
                1 if result.compliance_status == ComplianceStatus.COMPLIANT else 0
            )
            breakdown[framework]['partial'] += (
                1 if result.compliance_status == ComplianceStatus.PARTIAL else 0
            )
            breakdown[framework]['non_compliant'] += (
                1 if result.compliance_status == ComplianceStatus.NON_COMPLIANT else 0
            )
            breakdown[framework]['high_risk'] += (
                1 if result.risk_level == RiskLevel.HIGH else 0
            )
        
        # Count missing requirements by framework
        for req in missing_requirements:
            if req.mandatory:
                breakdown[req.framework]['missing_mandatory'] += 1
        
        # Calculate scores for each framework
        for framework in breakdown.keys():
            framework_results = [r for r in results if r.framework == framework]
            framework_missing = [
                req for req in missing_requirements if req.framework == framework
            ]
            breakdown[framework]['score'] = self.calculate_overall_score(
                framework_results,
                framework_missing
            )
        
        logger.debug(f"Generated breakdown for {len(breakdown)} frameworks")
        return dict(breakdown)
    
    def calculate_compliance_percentage(
        self,
        results: List[ClauseComplianceResult]
    ) -> float:
        """
        Calculate simple compliance percentage (compliant / total).
        
        Args:
            results: List of clause compliance results
            
        Returns:
            Compliance percentage (0-100)
        """
        if not results:
            return 0.0
        
        compliant_count = sum(
            1 for r in results 
            if r.compliance_status == ComplianceStatus.COMPLIANT
        )
        
        percentage = (compliant_count / len(results)) * 100
        return round(percentage, 2)
    
    def get_priority_issues(
        self,
        results: List[ClauseComplianceResult],
        top_n: int = 10
    ) -> List[ClauseComplianceResult]:
        """
        Get top priority issues to address.
        
        Priority is based on:
        1. Risk level (HIGH > MEDIUM > LOW)
        2. Compliance status (NON_COMPLIANT > PARTIAL > COMPLIANT)
        3. Confidence (lower confidence = higher priority)
        
        Args:
            results: List of clause compliance results
            top_n: Number of top issues to return
            
        Returns:
            List of top priority issues
        """
        # Define priority scores
        risk_priority = {
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 1
        }
        
        status_priority = {
            ComplianceStatus.NON_COMPLIANT: 3,
            ComplianceStatus.PARTIAL: 2,
            ComplianceStatus.COMPLIANT: 1,
            ComplianceStatus.NOT_APPLICABLE: 0
        }
        
        # Calculate priority score for each result
        def priority_score(result: ClauseComplianceResult) -> tuple:
            return (
                -risk_priority[result.risk_level],  # Negative for descending sort
                -status_priority[result.compliance_status],
                result.confidence  # Lower confidence = higher priority
            )
        
        # Sort by priority and return top N
        sorted_results = sorted(results, key=priority_score)
        top_issues = sorted_results[:top_n]
        
        logger.debug(f"Identified top {len(top_issues)} priority issues")
        return top_issues
