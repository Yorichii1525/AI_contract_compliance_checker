"""
Compliance Rule Engine service.
Evaluates clauses against framework-specific compliance rules.
"""
from typing import List, Dict, Optional
import re

from models.regulatory_requirement import (
    RegulatoryRequirement,
    ComplianceStatus,
    RiskLevel
)
from models.clause_analysis import ClauseAnalysis
from utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceRuleEngine:
    """
    Evaluates clauses against regulatory framework rules.
    Implements framework-specific logic for GDPR, HIPAA, CCPA, and SOX.
    """
    
    def __init__(self):
        """Initialize Compliance Rule Engine."""
        logger.info("Compliance Rule Engine initialized")
    
    def evaluate_compliance(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        similarity_score: float
    ) -> tuple[ComplianceStatus, RiskLevel, List[str]]:
        """
        Evaluate compliance of a clause against a requirement.
        
        Args:
            clause: Analyzed clause
            requirement: Regulatory requirement to check against
            similarity_score: Semantic similarity score between clause and requirement
            
        Returns:
            Tuple of (compliance_status, risk_level, issues)
        """
        framework = requirement.framework.upper()
        
        # Route to framework-specific evaluation
        if framework == 'GDPR':
            return self.evaluate_gdpr_compliance(clause, requirement, similarity_score)
        elif framework == 'HIPAA':
            return self.evaluate_hipaa_compliance(clause, requirement, similarity_score)
        elif framework == 'CCPA':
            return self.evaluate_ccpa_compliance(clause, requirement, similarity_score)
        elif framework == 'SOX':
            return self.evaluate_sox_compliance(clause, requirement, similarity_score)
        else:
            logger.warning(f"Unknown framework: {framework}")
            return ComplianceStatus.NOT_APPLICABLE, RiskLevel.LOW, []
    
    def evaluate_gdpr_compliance(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        similarity_score: float
    ) -> tuple[ComplianceStatus, RiskLevel, List[str]]:
        """
        Evaluate GDPR-specific compliance rules.
        
        Args:
            clause: Analyzed clause
            requirement: GDPR requirement
            similarity_score: Semantic similarity score
            
        Returns:
            Tuple of (compliance_status, risk_level, issues)
        """
        issues = []
        clause_text_lower = clause.clause_text.lower()
        
        # Check mandatory elements presence
        missing_elements = []
        for element in requirement.mandatory_elements:
            element_keywords = self._extract_keywords_from_element(element)
            if not any(keyword in clause_text_lower for keyword in element_keywords):
                missing_elements.append(element)
        
        # Determine compliance status based on similarity and missing elements
        if similarity_score >= 0.55 and not missing_elements:
            # High similarity and all elements present
            status = ComplianceStatus.COMPLIANT
            risk = RiskLevel.LOW
            
        elif similarity_score >= 0.40 and len(missing_elements) <= len(requirement.mandatory_elements) * 0.5:
            # Good similarity with most elements present
            status = ComplianceStatus.PARTIAL
            risk = RiskLevel.MEDIUM
            issues.append(f"Missing or unclear elements: {', '.join(missing_elements)}")
            
        elif similarity_score >= 0.40:
            # Good similarity but many missing elements
            status = ComplianceStatus.PARTIAL
            risk = RiskLevel.MEDIUM
            issues.append(f"Missing mandatory elements: {', '.join(missing_elements)}")
            
        else:
            # Low similarity
            status = ComplianceStatus.NON_COMPLIANT
            risk = RiskLevel.HIGH
            issues.append(f"Clause does not adequately address requirement: {requirement.description}")
            if missing_elements:
                issues.append(f"Missing mandatory elements: {', '.join(missing_elements)}")
        
        # GDPR-specific checks
        if requirement.clause_type == "Data Processing":
            issues.extend(self._check_gdpr_data_processing(clause_text_lower))
        elif requirement.clause_type == "Sub-processor Authorization":
            issues.extend(self._check_gdpr_subprocessor(clause_text_lower))
        elif requirement.clause_type == "Data Subject Rights":
            issues.extend(self._check_gdpr_data_subject_rights(clause_text_lower))
        elif requirement.clause_type == "Breach Notification":
            issues.extend(self._check_gdpr_breach_notification(clause_text_lower))
        
        # Adjust risk based on issues found
        if issues and status == ComplianceStatus.COMPLIANT:
            status = ComplianceStatus.PARTIAL
            risk = RiskLevel.MEDIUM
        
        return status, risk, issues
    
    def evaluate_hipaa_compliance(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        similarity_score: float
    ) -> tuple[ComplianceStatus, RiskLevel, List[str]]:
        """
        Evaluate HIPAA-specific compliance rules.
        
        Args:
            clause: Analyzed clause
            requirement: HIPAA requirement
            similarity_score: Semantic similarity score
            
        Returns:
            Tuple of (compliance_status, risk_level, issues)
        """
        issues = []
        clause_text_lower = clause.clause_text.lower()
        
        # Check mandatory elements presence
        missing_elements = []
        for element in requirement.mandatory_elements:
            element_keywords = self._extract_keywords_from_element(element)
            if not any(keyword in clause_text_lower for keyword in element_keywords):
                missing_elements.append(element)
        
        # Determine compliance status
        if similarity_score >= 0.55 and not missing_elements:
            status = ComplianceStatus.COMPLIANT
            risk = RiskLevel.LOW
            
        elif similarity_score >= 0.40 and len(missing_elements) <= len(requirement.mandatory_elements) * 0.5:
            status = ComplianceStatus.PARTIAL
            risk = RiskLevel.MEDIUM
            issues.append(f"Missing or unclear elements: {', '.join(missing_elements)}")
            
        elif similarity_score >= 0.40:
            status = ComplianceStatus.PARTIAL
            risk = RiskLevel.MEDIUM
            issues.append(f"Missing mandatory elements: {', '.join(missing_elements)}")
            
        else:
            status = ComplianceStatus.NON_COMPLIANT
            risk = RiskLevel.HIGH
            issues.append(f"Clause does not adequately address requirement: {requirement.description}")
            if missing_elements:
                issues.append(f"Missing mandatory elements: {', '.join(missing_elements)}")
        
        # HIPAA-specific checks
        if requirement.clause_type == "Security Safeguards":
            issues.extend(self._check_hipaa_safeguards(clause_text_lower))
        elif requirement.clause_type == "Breach Notification":
            issues.extend(self._check_hipaa_breach_notification(clause_text_lower))
        elif requirement.clause_type == "Permitted Uses and Disclosures":
            issues.extend(self._check_hipaa_permitted_uses(clause_text_lower))
        
        # Adjust risk based on issues found
        if issues and status == ComplianceStatus.COMPLIANT:
            status = ComplianceStatus.PARTIAL
            risk = RiskLevel.MEDIUM
        
        return status, risk, issues
    
    def evaluate_ccpa_compliance(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        similarity_score: float
    ) -> tuple[ComplianceStatus, RiskLevel, List[str]]:
        """
        Evaluate CCPA-specific compliance rules.
        
        Args:
            clause: Analyzed clause
            requirement: CCPA requirement
            similarity_score: Semantic similarity score
            
        Returns:
            Tuple of (compliance_status, risk_level, issues)
        """
        issues = []
        clause_text_lower = clause.clause_text.lower()
        
        # Check mandatory elements
        missing_elements = []
        for element in requirement.mandatory_elements:
            element_keywords = self._extract_keywords_from_element(element)
            if not any(keyword in clause_text_lower for keyword in element_keywords):
                missing_elements.append(element)
        
        # Determine compliance status
        if similarity_score >= 0.55 and not missing_elements:
            status = ComplianceStatus.COMPLIANT
            risk = RiskLevel.LOW
        elif similarity_score >= 0.40:
            status = ComplianceStatus.PARTIAL
            risk = RiskLevel.MEDIUM
            if missing_elements:
                issues.append(f"Missing elements: {', '.join(missing_elements)}")
        else:
            status = ComplianceStatus.NON_COMPLIANT
            risk = RiskLevel.HIGH
            issues.append(f"Clause does not adequately address requirement: {requirement.description}")
        
        return status, risk, issues
    
    def evaluate_sox_compliance(
        self,
        clause: ClauseAnalysis,
        requirement: RegulatoryRequirement,
        similarity_score: float
    ) -> tuple[ComplianceStatus, RiskLevel, List[str]]:
        """
        Evaluate SOX-specific compliance rules.
        
        Args:
            clause: Analyzed clause
            requirement: SOX requirement
            similarity_score: Semantic similarity score
            
        Returns:
            Tuple of (compliance_status, risk_level, issues)
        """
        issues = []
        clause_text_lower = clause.clause_text.lower()
        
        # Check mandatory elements
        missing_elements = []
        for element in requirement.mandatory_elements:
            element_keywords = self._extract_keywords_from_element(element)
            if not any(keyword in clause_text_lower for keyword in element_keywords):
                missing_elements.append(element)
        
        # Determine compliance status
        if similarity_score >= 0.30 and not missing_elements:
            status = ComplianceStatus.COMPLIANT
            risk = RiskLevel.LOW
        elif similarity_score >= 0.20:
            status = ComplianceStatus.PARTIAL
            risk = RiskLevel.MEDIUM
            if missing_elements:
                issues.append(f"Missing elements: {', '.join(missing_elements)}")
        else:
            status = ComplianceStatus.NON_COMPLIANT
            risk = RiskLevel.HIGH
            issues.append(f"Clause does not adequately address requirement: {requirement.description}")
        
        return status, risk, issues
    
    def detect_missing_mandatory_elements(
        self,
        clause_text: str,
        mandatory_elements: List[str]
    ) -> List[str]:
        """
        Detect which mandatory elements are missing from a clause.
        
        Args:
            clause_text: Text of the clause
            mandatory_elements: List of mandatory elements to check
            
        Returns:
            List of missing elements
        """
        clause_text_lower = clause_text.lower()
        missing = []
        
        for element in mandatory_elements:
            element_keywords = self._extract_keywords_from_element(element)
            if not any(keyword in clause_text_lower for keyword in element_keywords):
                missing.append(element)
        
        return missing
    
    # GDPR-specific checks
    
    def _check_gdpr_data_processing(self, clause_text: str) -> List[str]:
        """Check GDPR Data Processing clause requirements."""
        issues = []
        
        required_terms = {
            'instructions': ['instruction', 'instruct', 'directed'],
            'confidentiality': ['confidential', 'confidentiality', 'secret'],
            'security': ['security', 'secure', 'safeguard', 'protect'],
            'controller': ['controller', 'data controller']
        }
        
        for term_type, keywords in required_terms.items():
            if not any(keyword in clause_text for keyword in keywords):
                issues.append(f"Missing reference to {term_type}")
        
        return issues
    
    def _check_gdpr_subprocessor(self, clause_text: str) -> List[str]:
        """Check GDPR Sub-processor Authorization requirements."""
        issues = []
        
        if 'authorization' not in clause_text and 'authorisation' not in clause_text:
            issues.append("Missing explicit authorization requirement")
        
        if 'notification' not in clause_text and 'notify' not in clause_text:
            issues.append("Missing notification requirement")
        
        # Check for timeframe (e.g., "30 days", "prior notice")
        if not re.search(r'\d+\s*(day|week|month)', clause_text):
            if 'prior' not in clause_text and 'advance' not in clause_text:
                issues.append("Missing notification timeframe")
        
        return issues
    
    def _check_gdpr_data_subject_rights(self, clause_text: str) -> List[str]:
        """Check GDPR Data Subject Rights requirements."""
        issues = []
        
        rights_keywords = ['access', 'rectification', 'erasure', 'deletion', 'portability']
        found_rights = sum(1 for keyword in rights_keywords if keyword in clause_text)
        
        if found_rights < 2:
            issues.append("Insufficient coverage of data subject rights")
        
        if 'assist' not in clause_text and 'support' not in clause_text:
            issues.append("Missing assistance obligation")
        
        return issues
    
    def _check_gdpr_breach_notification(self, clause_text: str) -> List[str]:
        """Check GDPR Breach Notification requirements."""
        issues = []
        
        if 'breach' not in clause_text:
            issues.append("Missing breach reference")
        
        if 'notification' not in clause_text and 'notify' not in clause_text:
            issues.append("Missing notification obligation")
        
        # Check for timeframe (72 hours for GDPR)
        if not re.search(r'\d+\s*hour', clause_text):
            issues.append("Missing or unclear notification timeframe")
        
        return issues
    
    # HIPAA-specific checks
    
    def _check_hipaa_safeguards(self, clause_text: str) -> List[str]:
        """Check HIPAA Safeguards requirements."""
        issues = []
        
        safeguard_types = {
            'administrative': ['administrative', 'management', 'policy'],
            'physical': ['physical', 'facility', 'access control'],
            'technical': ['technical', 'encryption', 'authentication']
        }
        
        for safeguard_type, keywords in safeguard_types.items():
            if not any(keyword in clause_text for keyword in keywords):
                issues.append(f"Missing {safeguard_type} safeguards reference")
        
        return issues
    
    def _check_hipaa_breach_notification(self, clause_text: str) -> List[str]:
        """Check HIPAA Breach Notification requirements."""
        issues = []
        
        if 'breach' not in clause_text:
            issues.append("Missing breach reference")
        
        if 'notification' not in clause_text and 'notify' not in clause_text:
            issues.append("Missing notification obligation")
        
        # HIPAA requires notification within 60 days
        if not re.search(r'\d+\s*(day|calendar day)', clause_text):
            issues.append("Missing or unclear notification timeframe")
        
        return issues
    
    def _check_hipaa_permitted_uses(self, clause_text: str) -> List[str]:
        """Check HIPAA Permitted Uses and Disclosures requirements."""
        issues = []
        
        if 'permitted' not in clause_text and 'authorized' not in clause_text:
            issues.append("Missing permitted uses specification")
        
        if 'disclosure' not in clause_text and 'disclose' not in clause_text:
            issues.append("Missing disclosure terms")
        
        if 'minimum necessary' not in clause_text:
            issues.append("Missing minimum necessary standard")
        
        return issues
    
    # Helper methods
    
    @staticmethod
    def _extract_keywords_from_element(element: str) -> List[str]:
        """
        Extract searchable keywords from a mandatory element description.
        
        Args:
            element: Mandatory element description
            
        Returns:
            List of keywords to search for
        """
        # Convert to lowercase and extract key terms
        element_lower = element.lower()
        
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'of', 'to', 'in', 'for', 'on', 'with'}
        words = element_lower.split()
        keywords = [word.strip('.,;:()[]{}') for word in words if word not in stop_words]
        
        # Also include the full phrase
        keywords.append(element_lower)
        
        return keywords
