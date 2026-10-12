"""
CCPA regulatory requirements database.
Defines requirements for CCPA compliance checking.
"""
from models.regulatory_requirement import RegulatoryRequirement, RiskLevel


def get_ccpa_requirements():
    """
    Get all CCPA regulatory requirements.
    
    Returns:
        List of RegulatoryRequirement objects for CCPA
    """
    requirements = [
        # Right to Know
        RegulatoryRequirement(
            requirement_id="CCPA_1798_100_01",
            framework="CCPA",
            article_reference="CCPA §1798.100",
            clause_type="Data Subject Rights",
            description="Right to know - consumers have right to know what personal information is collected, used, shared, or sold",
            mandatory=True,
            keywords=[
                "right to know", "consumer rights", "personal information",
                "collection", "disclosure", "categories", "sources",
                "business purpose", "third parties", "information collected"
            ],
            mandatory_elements=[
                "Disclose categories of personal information collected",
                "Disclose sources of information",
                "Disclose business purposes for collection",
                "Disclose categories of third parties"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Right to Delete
        RegulatoryRequirement(
            requirement_id="CCPA_1798_105_01",
            framework="CCPA",
            article_reference="CCPA §1798.105",
            clause_type="Data Subject Rights",
            description="Right to delete - consumers have right to request deletion of personal information",
            mandatory=True,
            keywords=[
                "right to delete", "deletion", "delete", "consumer request",
                "personal information", "remove", "erase", "deletion request",
                "service providers", "contractors"
            ],
            mandatory_elements=[
                "Delete consumer personal information",
                "Direct service providers to delete",
                "Exceptions for legal obligations",
                "Verify deletion requests"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Right to Opt-Out
        RegulatoryRequirement(
            requirement_id="CCPA_1798_120_01",
            framework="CCPA",
            article_reference="CCPA §1798.120",
            clause_type="Data Subject Rights",
            description="Right to opt-out of sale - consumers have right to opt-out of sale of personal information",
            mandatory=True,
            keywords=[
                "opt-out", "opt out", "sale", "sell", "selling",
                "do not sell", "consumer choice", "personal information",
                "third party sale"
            ],
            mandatory_elements=[
                "Honor opt-out requests",
                "Do not sell personal information after opt-out",
                "Wait 12 months before requesting opt-in",
                "Provide clear opt-out mechanism"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Service Provider Obligations
        RegulatoryRequirement(
            requirement_id="CCPA_1798_140_01",
            framework="CCPA",
            article_reference="CCPA §1798.140(w)",
            clause_type="Data Processing",
            description="Service provider obligations - service providers must not retain, use, or disclose personal information except as necessary",
            mandatory=True,
            keywords=[
                "service provider", "business purpose", "retain", "use",
                "disclose", "personal information", "contract", "agreement",
                "specific business purpose", "direct business relationship"
            ],
            mandatory_elements=[
                "Use only for specific business purpose",
                "No retention outside business purpose",
                "No disclosure outside business purpose",
                "No selling of personal information"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Non-Discrimination
        RegulatoryRequirement(
            requirement_id="CCPA_1798_125_01",
            framework="CCPA",
            article_reference="CCPA §1798.125",
            clause_type="Data Subject Rights",
            description="Non-discrimination - cannot discriminate against consumers for exercising CCPA rights",
            mandatory=True,
            keywords=[
                "non-discrimination", "discriminate", "consumer rights",
                "exercise rights", "deny goods", "deny services",
                "different price", "different quality", "penalize"
            ],
            mandatory_elements=[
                "No denial of goods or services",
                "No different prices or rates",
                "No different quality of goods or services",
                "No suggestion of discrimination"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Security Requirements
        RegulatoryRequirement(
            requirement_id="CCPA_1798_150_01",
            framework="CCPA",
            article_reference="CCPA §1798.150",
            clause_type="Security Safeguards",
            description="Security requirements - implement reasonable security procedures and practices",
            mandatory=True,
            keywords=[
                "security", "reasonable security", "security procedures",
                "security practices", "safeguards", "protect",
                "unauthorized access", "data breach", "security measures"
            ],
            mandatory_elements=[
                "Reasonable security procedures",
                "Appropriate to nature of information",
                "Protect against unauthorized access",
                "Protect against data breaches"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Contractual Restrictions
        RegulatoryRequirement(
            requirement_id="CCPA_1798_140_02",
            framework="CCPA",
            article_reference="CCPA §1798.140(w)(2)",
            clause_type="Data Processing",
            description="Contractual restrictions - contract must prohibit service provider from retaining, using, or disclosing personal information",
            mandatory=True,
            keywords=[
                "contract", "contractual", "prohibit", "restriction",
                "service provider", "retain", "use", "disclose",
                "written contract", "agreement terms"
            ],
            mandatory_elements=[
                "Written contract required",
                "Prohibit retention outside business purpose",
                "Prohibit use outside business purpose",
                "Prohibit disclosure outside business purpose"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Verification Requirements
        RegulatoryRequirement(
            requirement_id="CCPA_1798_140_03",
            framework="CCPA",
            article_reference="CCPA §1798.140",
            clause_type="Data Subject Rights",
            description="Verification requirements - verify identity of consumers making requests",
            mandatory=True,
            keywords=[
                "verify", "verification", "identity", "consumer request",
                "reasonable method", "authenticate", "confirm identity",
                "verification process"
            ],
            mandatory_elements=[
                "Verify consumer identity",
                "Use reasonable verification methods",
                "Match information to existing records",
                "Protect against fraudulent requests"
            ],
            risk_level=RiskLevel.MEDIUM
        )
    ]
    
    return requirements
