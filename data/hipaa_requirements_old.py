"""
HIPAA regulatory requirements database.
Defines requirements for HIPAA compliance checking.
"""
from models.regulatory_requirement import RegulatoryRequirement, RiskLevel


def get_hipaa_requirements():
    """
    Get all HIPAA regulatory requirements.
    
    Returns:
        List of RegulatoryRequirement objects for HIPAA
    """
    requirements = [
        # Administrative Safeguards
        RegulatoryRequirement(
            requirement_id="HIPAA_164_308_01",
            framework="HIPAA",
            article_reference="HIPAA §164.308",
            clause_type="Security Safeguards",
            description="Administrative safeguards - implement policies and procedures to prevent, detect, contain, and correct security violations",
            mandatory=True,
            keywords=[
                "administrative safeguards", "security management",
                "policies", "procedures", "workforce security",
                "information access", "security awareness", "training",
                "risk analysis", "risk management", "sanction policy"
            ],
            mandatory_elements=[
                "Security management process",
                "Workforce security",
                "Information access management",
                "Security awareness and training",
                "Security incident procedures",
                "Contingency plan"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Physical Safeguards
        RegulatoryRequirement(
            requirement_id="HIPAA_164_310_01",
            framework="HIPAA",
            article_reference="HIPAA §164.310",
            clause_type="Security Safeguards",
            description="Physical safeguards - implement policies and procedures to limit physical access to electronic information systems",
            mandatory=True,
            keywords=[
                "physical safeguards", "facility access", "workstation use",
                "workstation security", "device controls", "media controls",
                "physical access", "access control", "facility security"
            ],
            mandatory_elements=[
                "Facility access controls",
                "Workstation use policies",
                "Workstation security",
                "Device and media controls"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Technical Safeguards
        RegulatoryRequirement(
            requirement_id="HIPAA_164_312_01",
            framework="HIPAA",
            article_reference="HIPAA §164.312",
            clause_type="Security Safeguards",
            description="Technical safeguards - implement technology and policies to protect ePHI and control access",
            mandatory=True,
            keywords=[
                "technical safeguards", "access control", "audit controls",
                "integrity controls", "transmission security", "encryption",
                "authentication", "unique user identification", "automatic logoff",
                "encryption and decryption"
            ],
            mandatory_elements=[
                "Access control",
                "Audit controls",
                "Integrity controls",
                "Person or entity authentication",
                "Transmission security"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Breach Notification
        RegulatoryRequirement(
            requirement_id="HIPAA_164_410_01",
            framework="HIPAA",
            article_reference="HIPAA §164.410",
            clause_type="Breach Notification",
            description="Breach notification requirements - notify covered entity of breaches of unsecured PHI",
            mandatory=True,
            keywords=[
                "breach", "notification", "notify", "breach notification",
                "unsecured PHI", "security incident", "discovery",
                "60 days", "without unreasonable delay", "breach discovery",
                "covered entity notification"
            ],
            mandatory_elements=[
                "Notification without unreasonable delay",
                "Notification within 60 days of discovery",
                "Description of breach",
                "Types of information involved",
                "Mitigation steps taken"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Permitted Uses and Disclosures
        RegulatoryRequirement(
            requirement_id="HIPAA_164_502_01",
            framework="HIPAA",
            article_reference="HIPAA §164.502",
            clause_type="Permitted Uses and Disclosures",
            description="Permitted uses and disclosures - business associate may only use or disclose PHI as permitted by the agreement",
            mandatory=True,
            keywords=[
                "permitted uses", "permitted disclosures", "use and disclosure",
                "PHI", "protected health information", "business associate",
                "covered entity", "authorization", "minimum necessary",
                "treatment", "payment", "healthcare operations"
            ],
            mandatory_elements=[
                "Use only as permitted by agreement",
                "Disclose only as permitted by agreement",
                "Minimum necessary standard",
                "No further use or disclosure"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Subcontractor Requirements
        RegulatoryRequirement(
            requirement_id="HIPAA_164_502_02",
            framework="HIPAA",
            article_reference="HIPAA §164.502(e)(1)(ii)",
            clause_type="Sub-processor Authorization",
            description="Subcontractor requirements - ensure subcontractors agree to same restrictions and conditions",
            mandatory=True,
            keywords=[
                "subcontractor", "sub-contractor", "agent", "downstream",
                "same restrictions", "same conditions", "business associate agreement",
                "BAA", "subcontractor agreement", "third party"
            ],
            mandatory_elements=[
                "Written agreement with subcontractors",
                "Same restrictions and conditions apply",
                "Subcontractor compliance with HIPAA"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Safeguard Requirements
        RegulatoryRequirement(
            requirement_id="HIPAA_164_308_02",
            framework="HIPAA",
            article_reference="HIPAA §164.308(b)(1)",
            clause_type="Security Safeguards",
            description="Safeguard requirements - implement appropriate safeguards to prevent use or disclosure of PHI",
            mandatory=True,
            keywords=[
                "safeguards", "appropriate safeguards", "prevent",
                "unauthorized use", "unauthorized disclosure", "protect",
                "security measures", "reasonable safeguards"
            ],
            mandatory_elements=[
                "Appropriate administrative safeguards",
                "Appropriate physical safeguards",
                "Appropriate technical safeguards",
                "Prevent unauthorized use or disclosure"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Reporting Requirements
        RegulatoryRequirement(
            requirement_id="HIPAA_164_308_03",
            framework="HIPAA",
            article_reference="HIPAA §164.308(b)(2)",
            clause_type="Breach Notification",
            description="Reporting requirements - report to covered entity any security incident or unauthorized use/disclosure",
            mandatory=True,
            keywords=[
                "report", "reporting", "security incident", "unauthorized use",
                "unauthorized disclosure", "covered entity", "notify",
                "become aware", "knowledge"
            ],
            mandatory_elements=[
                "Report security incidents",
                "Report unauthorized uses or disclosures",
                "Timely reporting to covered entity"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Access and Availability
        RegulatoryRequirement(
            requirement_id="HIPAA_164_524_01",
            framework="HIPAA",
            article_reference="HIPAA §164.524",
            clause_type="Data Subject Rights",
            description="Access to PHI - make PHI available to covered entity for access by individuals",
            mandatory=True,
            keywords=[
                "access", "individual access", "right of access",
                "designated record set", "make available", "provide access",
                "individual rights", "patient rights"
            ],
            mandatory_elements=[
                "Make PHI available to covered entity",
                "Enable individual access rights",
                "Timely response to access requests"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Termination
        RegulatoryRequirement(
            requirement_id="HIPAA_164_504_01",
            framework="HIPAA",
            article_reference="HIPAA §164.504(e)(2)(ii)(I)",
            clause_type="Data Processing",
            description="Termination provisions - return or destroy PHI upon termination of agreement",
            mandatory=True,
            keywords=[
                "termination", "return", "destroy", "end of agreement",
                "cessation", "PHI", "protected health information",
                "retention", "disposal"
            ],
            mandatory_elements=[
                "Return or destroy PHI at termination",
                "Retain only if required by law",
                "Extend protections to retained information"
            ],
            risk_level=RiskLevel.MEDIUM
        )
    ]
    
    return requirements
