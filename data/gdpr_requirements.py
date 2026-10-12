"""
GDPR regulatory requirements database.
Defines requirements for GDPR compliance checking.
"""
from models.regulatory_requirement import RegulatoryRequirement, RiskLevel


def get_gdpr_requirements():
    """
    Get all GDPR regulatory requirements.
    
    Returns:
        List of RegulatoryRequirement objects for GDPR
    """
    requirements = [
        # GDPR Article 28 - Data Processing
        RegulatoryRequirement(
            requirement_id="GDPR_ART28_01",
            framework="GDPR",
            article_reference="GDPR Article 28",
            clause_type="Data Processing",
            description="Processor obligations and data processing terms - processor shall process personal data only on documented instructions from the controller",
            mandatory=True,
            keywords=[
                "processor", "processing", "instructions", "controller",
                "documented instructions", "personal data", "data controller",
                "data processor", "process only", "written authorization"
            ],
            mandatory_elements=[
                "Processing only on documented instructions",
                "Confidentiality obligations",
                "Security measures",
                "Sub-processor authorization",
                "Assistance with data subject rights",
                "Deletion or return of data"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Sub-processor Authorization
        RegulatoryRequirement(
            requirement_id="GDPR_ART28_02",
            framework="GDPR",
            article_reference="GDPR Article 28(2)",
            clause_type="Sub-processor Authorization",
            description="Sub-processor authorization and notification requirements - processor must obtain prior written authorization before engaging sub-processors",
            mandatory=True,
            keywords=[
                "sub-processor", "subprocessor", "authorization", "notification",
                "prior written", "engage", "third party", "sub-contractor",
                "notification period", "object", "objection", "30 days"
            ],
            mandatory_elements=[
                "Prior written authorization",
                "Notification period (typically 30 days)",
                "Right to object"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Data Subject Rights
        RegulatoryRequirement(
            requirement_id="GDPR_ART28_03",
            framework="GDPR",
            article_reference="GDPR Article 28(3)(e)",
            clause_type="Data Subject Rights",
            description="Assistance with data subject rights - processor must assist controller in responding to data subject requests",
            mandatory=True,
            keywords=[
                "data subject", "rights", "assist", "assistance", "request",
                "access", "rectification", "erasure", "portability",
                "right to be forgotten", "data subject request", "DSR",
                "respond", "facilitate"
            ],
            mandatory_elements=[
                "Obligation to assist controller",
                "Timely response to requests",
                "Technical and organizational measures"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Breach Notification
        RegulatoryRequirement(
            requirement_id="GDPR_ART33_01",
            framework="GDPR",
            article_reference="GDPR Article 33",
            clause_type="Breach Notification",
            description="Personal data breach notification - processor must notify controller without undue delay upon becoming aware of a breach",
            mandatory=True,
            keywords=[
                "breach", "notification", "notify", "security breach",
                "data breach", "personal data breach", "undue delay",
                "72 hours", "incident", "security incident", "inform",
                "without delay"
            ],
            mandatory_elements=[
                "Notification without undue delay",
                "Notification timeframe (72 hours)",
                "Description of breach nature",
                "Contact point information"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Security Measures
        RegulatoryRequirement(
            requirement_id="GDPR_ART32_01",
            framework="GDPR",
            article_reference="GDPR Article 32",
            clause_type="Security Safeguards",
            description="Security of processing - implement appropriate technical and organizational measures",
            mandatory=True,
            keywords=[
                "security", "safeguards", "technical measures",
                "organizational measures", "encryption", "pseudonymization",
                "confidentiality", "integrity", "availability", "resilience",
                "security measures", "appropriate security"
            ],
            mandatory_elements=[
                "Pseudonymization and encryption",
                "Ongoing confidentiality and integrity",
                "Availability and resilience",
                "Regular testing and assessment"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Data Transfer
        RegulatoryRequirement(
            requirement_id="GDPR_ART44_01",
            framework="GDPR",
            article_reference="GDPR Article 44-46",
            clause_type="Data Transfer",
            description="International data transfers - ensure adequate protection when transferring data outside EEA",
            mandatory=True,
            keywords=[
                "transfer", "international", "third country", "cross-border",
                "adequacy decision", "standard contractual clauses", "SCC",
                "binding corporate rules", "BCR", "data transfer",
                "outside EEA", "non-EEA"
            ],
            mandatory_elements=[
                "Legal basis for transfer",
                "Adequate level of protection",
                "Standard contractual clauses or other safeguards"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Confidentiality
        RegulatoryRequirement(
            requirement_id="GDPR_ART28_04",
            framework="GDPR",
            article_reference="GDPR Article 28(3)(b)",
            clause_type="Data Processing",
            description="Confidentiality obligations - ensure persons authorized to process personal data are committed to confidentiality",
            mandatory=True,
            keywords=[
                "confidentiality", "confidential", "authorized persons",
                "commitment", "secrecy", "non-disclosure", "NDA",
                "confidentiality obligation", "staff", "personnel"
            ],
            mandatory_elements=[
                "Confidentiality commitment",
                "Applies to all authorized persons",
                "Statutory obligation or contractual duty"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Deletion or Return of Data
        RegulatoryRequirement(
            requirement_id="GDPR_ART28_05",
            framework="GDPR",
            article_reference="GDPR Article 28(3)(g)",
            clause_type="Data Processing",
            description="Deletion or return of personal data - at the end of provision of services, delete or return all personal data",
            mandatory=True,
            keywords=[
                "deletion", "delete", "return", "end of service",
                "termination", "destroy", "erasure", "remove",
                "personal data", "copies", "existing copies"
            ],
            mandatory_elements=[
                "Delete or return all personal data",
                "Delete existing copies",
                "Exception for legal storage requirements"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Audit Rights
        RegulatoryRequirement(
            requirement_id="GDPR_ART28_06",
            framework="GDPR",
            article_reference="GDPR Article 28(3)(h)",
            clause_type="Data Processing",
            description="Audit and inspection rights - make available information necessary to demonstrate compliance and allow audits",
            mandatory=True,
            keywords=[
                "audit", "inspection", "demonstrate compliance",
                "information", "contribute", "audits", "inspections",
                "controller audit", "third party audit", "audit rights"
            ],
            mandatory_elements=[
                "Make information available",
                "Allow and contribute to audits",
                "Allow inspections by controller or auditor"
            ],
            risk_level=RiskLevel.LOW
        )
    ]
    
    return requirements
