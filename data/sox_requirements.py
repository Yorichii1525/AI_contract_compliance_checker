"""
SOX (Sarbanes-Oxley) regulatory requirements database.
Defines requirements for SOX compliance checking.
"""
from models.regulatory_requirement import RegulatoryRequirement, RiskLevel


def get_sox_requirements():
    """
    Get all SOX regulatory requirements.
    
    Returns:
        List of RegulatoryRequirement objects for SOX
    """
    requirements = [
        # Internal Controls
        RegulatoryRequirement(
            requirement_id="SOX_404_01",
            framework="SOX",
            article_reference="SOX Section 404",
            clause_type="Security Safeguards",
            description="Internal control over financial reporting - establish and maintain adequate internal control structure",
            mandatory=True,
            keywords=[
                "internal controls", "internal control structure",
                "financial reporting", "control procedures", "control framework",
                "COSO", "control environment", "control activities",
                "monitoring", "assessment"
            ],
            mandatory_elements=[
                "Establish internal control structure",
                "Maintain adequate controls",
                "Assessment of control effectiveness",
                "Documentation of controls"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Data Retention
        RegulatoryRequirement(
            requirement_id="SOX_802_01",
            framework="SOX",
            article_reference="SOX Section 802",
            clause_type="Data Processing",
            description="Document retention - retain audit and review workpapers for specified periods",
            mandatory=True,
            keywords=[
                "retention", "document retention", "records retention",
                "audit records", "workpapers", "7 years", "5 years",
                "preserve", "maintain records", "financial records"
            ],
            mandatory_elements=[
                "Retain audit workpapers for 7 years",
                "Retain review workpapers for 7 years",
                "Systematic retention procedures",
                "Protection against destruction"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Access Controls
        RegulatoryRequirement(
            requirement_id="SOX_404_02",
            framework="SOX",
            article_reference="SOX Section 404",
            clause_type="Security Safeguards",
            description="Access controls - implement controls to restrict access to financial systems and data",
            mandatory=True,
            keywords=[
                "access control", "access restrictions", "user access",
                "authorization", "authentication", "segregation of duties",
                "least privilege", "role-based access", "financial systems",
                "financial data"
            ],
            mandatory_elements=[
                "Restrict access to financial systems",
                "User authentication and authorization",
                "Segregation of duties",
                "Regular access reviews"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Audit Trail
        RegulatoryRequirement(
            requirement_id="SOX_404_03",
            framework="SOX",
            article_reference="SOX Section 404",
            clause_type="Security Safeguards",
            description="Audit trail requirements - maintain comprehensive audit trails of financial transactions and system access",
            mandatory=True,
            keywords=[
                "audit trail", "audit log", "logging", "transaction log",
                "activity log", "system access", "financial transactions",
                "tracking", "monitoring", "record keeping"
            ],
            mandatory_elements=[
                "Log all financial transactions",
                "Log system access and changes",
                "Maintain tamper-proof logs",
                "Regular log review and analysis"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Change Management
        RegulatoryRequirement(
            requirement_id="SOX_404_04",
            framework="SOX",
            article_reference="SOX Section 404",
            clause_type="Security Safeguards",
            description="Change management controls - implement controls for changes to financial systems",
            mandatory=True,
            keywords=[
                "change management", "change control", "system changes",
                "application changes", "approval process", "testing",
                "documentation", "change requests", "financial systems"
            ],
            mandatory_elements=[
                "Formal change approval process",
                "Testing before implementation",
                "Documentation of changes",
                "Segregation of duties in change process"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Data Integrity
        RegulatoryRequirement(
            requirement_id="SOX_404_05",
            framework="SOX",
            article_reference="SOX Section 404",
            clause_type="Security Safeguards",
            description="Data integrity controls - ensure accuracy and completeness of financial data",
            mandatory=True,
            keywords=[
                "data integrity", "accuracy", "completeness", "validation",
                "reconciliation", "financial data", "data quality",
                "error detection", "data validation"
            ],
            mandatory_elements=[
                "Data validation controls",
                "Reconciliation procedures",
                "Error detection and correction",
                "Data quality monitoring"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Backup and Recovery
        RegulatoryRequirement(
            requirement_id="SOX_404_06",
            framework="SOX",
            article_reference="SOX Section 404",
            clause_type="Security Safeguards",
            description="Backup and disaster recovery - implement procedures for data backup and system recovery",
            mandatory=True,
            keywords=[
                "backup", "disaster recovery", "business continuity",
                "recovery procedures", "data backup", "system recovery",
                "contingency plan", "restore", "recovery time"
            ],
            mandatory_elements=[
                "Regular data backups",
                "Tested recovery procedures",
                "Documented contingency plans",
                "Recovery time objectives"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Third-Party Service Providers
        RegulatoryRequirement(
            requirement_id="SOX_404_07",
            framework="SOX",
            article_reference="SOX Section 404",
            clause_type="Data Processing",
            description="Third-party controls - ensure service providers have adequate controls over financial data",
            mandatory=True,
            keywords=[
                "third party", "service provider", "outsourcing",
                "vendor management", "SOC report", "SOC 1", "SOC 2",
                "service organization", "controls assessment"
            ],
            mandatory_elements=[
                "Assess third-party controls",
                "Obtain SOC reports",
                "Monitor third-party performance",
                "Contractual control requirements"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Confidentiality
        RegulatoryRequirement(
            requirement_id="SOX_802_02",
            framework="SOX",
            article_reference="SOX Section 802",
            clause_type="Data Processing",
            description="Confidentiality of financial information - protect confidentiality of financial data and records",
            mandatory=True,
            keywords=[
                "confidentiality", "confidential", "financial information",
                "financial data", "sensitive information", "protect",
                "disclosure", "unauthorized access", "privacy"
            ],
            mandatory_elements=[
                "Protect financial information confidentiality",
                "Restrict unauthorized disclosure",
                "Confidentiality agreements",
                "Data classification procedures"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Reporting and Disclosure
        RegulatoryRequirement(
            requirement_id="SOX_302_01",
            framework="SOX",
            article_reference="SOX Section 302",
            clause_type="Data Processing",
            description="Disclosure controls - establish controls and procedures for timely disclosure of material information",
            mandatory=True,
            keywords=[
                "disclosure", "reporting", "material information",
                "timely disclosure", "financial reporting", "disclosure controls",
                "procedures", "certification"
            ],
            mandatory_elements=[
                "Disclosure controls and procedures",
                "Timely reporting of material information",
                "Evaluation of control effectiveness",
                "CEO/CFO certification"
            ],
            risk_level=RiskLevel.MEDIUM
        )
    ]
    
    return requirements
