"""
HIPAA regulatory requirements database.
Defines requirements for HIPAA compliance checking with same structure as GDPR.
Comprehensive BAA requirements based on Privacy Rule, Security Rule, Breach Notification, and HITECH Act.
"""
from models.regulatory_requirement import RegulatoryRequirement, RiskLevel


def get_hipaa_requirements():
    """
    Get all HIPAA regulatory requirements.
    
    Returns:
        List of RegulatoryRequirement objects for HIPAA
    """
    requirements = [
        # ==================== SECTION 1: PRIVACY RULE & GENERAL OBLIGATIONS ====================
        
        # Definitions & Scope
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_01",
            framework="HIPAA",
            article_reference="45 CFR §160.103",
            clause_type="Definitions",
            description="Clearly defines Protected Health Information (PHI) and ePHI consistent with HIPAA legal definitions",
            mandatory=True,
            keywords=[
                "PHI", "protected health information", "ePHI", "electronic protected health information",
                "individually identifiable", "health information", "definition", "scope"
            ],
            mandatory_elements=[
                "Definition of PHI",
                "Definition of ePHI",
                "Individually identifiable health information",
                "Scope of protected data"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_02",
            framework="HIPAA",
            article_reference="45 CFR §160.103",
            clause_type="Party Definitions",
            description="Clearly defines Business Associate (BA) and Covered Entity (CE) roles and responsibilities",
            mandatory=True,
            keywords=[
                "business associate", "covered entity", "BA", "CE", "roles",
                "responsibilities", "party identification", "entity definition"
            ],
            mandatory_elements=[
                "Business Associate identification",
                "Covered Entity identification",
                "Role and responsibility definition",
                "Legal relationship establishment"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_03",
            framework="HIPAA",
            article_reference="45 CFR §160.103",
            clause_type="Subcontractor Definition",
            description="Defines subcontractor as any entity to whom BA delegates functions involving PHI",
            mandatory=True,
            keywords=[
                "subcontractor", "sub-processor", "delegation", "third party",
                "downstream", "subcontractor definition", "delegated functions"
            ],
            mandatory_elements=[
                "Subcontractor definition",
                "Delegation of PHI functions",
                "Flow-down of compliance obligations"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_04",
            framework="HIPAA",
            article_reference="45 CFR §164.502",
            clause_type="Data Processing",
            description="Establishes specific permitted uses of PHI by BA for service performance",
            mandatory=True,
            keywords=[
                "permitted uses", "authorized use", "scope of work", "PHI use",
                "service performance", "data processing", "allowed activities",
                "processing", "instructions", "documented instructions"
            ],
            mandatory_elements=[
                "Specific permitted uses listed",
                "Scope of work definition",
                "Purpose limitation",
                "Service-related activities only"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_05",
            framework="HIPAA",
            article_reference="45 CFR §164.504",
            clause_type="Use Restrictions",
            description="Explicitly forbids any use or disclosure of PHI not permitted by contract or law",
            mandatory=True,
            keywords=[
                "prohibited use", "restriction", "forbidden", "not permitted",
                "use limitation", "disclosure restriction", "unlawful use"
            ],
            mandatory_elements=[
                "Explicit prohibition of unauthorized use",
                "Disclosure restrictions",
                "Required by law exception only"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_06",
            framework="HIPAA",
            article_reference="45 CFR §164.502(b)",
            clause_type="Minimum Necessary",
            description="Requires BA to adhere to minimum necessary principle for PHI access and use",
            mandatory=True,
            keywords=[
                "minimum necessary", "least privilege", "data minimization",
                "need to know", "limited access", "proportionate use"
            ],
            mandatory_elements=[
                "Minimum necessary principle",
                "Limited data access",
                "Purpose-appropriate use",
                "Reasonable limitations"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # Prohibited Uses
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_07",
            framework="HIPAA",
            article_reference="45 CFR §164.508",
            clause_type="Marketing Prohibition",
            description="Prohibits BA from using PHI for marketing without explicit authorization",
            mandatory=True,
            keywords=[
                "marketing", "prohibited marketing", "authorization required",
                "promotional use", "advertising", "commercial communication"
            ],
            mandatory_elements=[
                "Marketing prohibition",
                "Authorization requirement",
                "Exception conditions"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_08",
            framework="HIPAA",
            article_reference="45 CFR §164.502(a)(5)(ii)",
            clause_type="Sale Prohibition",
            description="Prohibits BA from sale of PHI without explicit authorization (Omnibus Rule)",
            mandatory=True,
            keywords=[
                "sale of PHI", "prohibited sale", "remuneration", "exchange",
                "commercial transaction", "authorization required"
            ],
            mandatory_elements=[
                "Explicit sale prohibition",
                "Individual authorization requirement",
                "Remuneration restrictions"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_09",
            framework="HIPAA",
            article_reference="45 CFR §164.508(a)(2)",
            clause_type="Psychotherapy Notes",
            description="Prohibits use or disclosure of psychotherapy notes unless specifically authorized",
            mandatory=True,
            keywords=[
                "psychotherapy notes", "mental health", "therapy notes",
                "special protection", "separate authorization"
            ],
            mandatory_elements=[
                "Psychotherapy notes identification",
                "Separate authorization requirement",
                "Enhanced protections"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # Individual Rights
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_10",
            framework="HIPAA",
            article_reference="45 CFR §164.524",
            clause_type="Data Subject Rights",
            description="Requires BA to assist CE with individual's right of access within 30 days",
            mandatory=True,
            keywords=[
                "right of access", "individual access", "data access request",
                "30 days", "timely response", "PHI availability",
                "data subject", "rights", "assist", "assistance"
            ],
            mandatory_elements=[
                "Assistance with access requests",
                "30-day response timeframe",
                "PHI availability to CE",
                "Cooperation obligation"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_11",
            framework="HIPAA",
            article_reference="45 CFR §164.526",
            clause_type="Right to Amend",
            description="Requires BA to assist CE with right to amend PHI",
            mandatory=True,
            keywords=[
                "right to amend", "amendment", "correction", "data accuracy",
                "rectification", "update PHI", "incorporate changes"
            ],
            mandatory_elements=[
                "Amendment assistance",
                "PHI amendment incorporation",
                "Timely implementation"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_12",
            framework="HIPAA",
            article_reference="45 CFR §164.528",
            clause_type="Accounting of Disclosures",
            description="Requires BA to assist CE with accounting of disclosures",
            mandatory=True,
            keywords=[
                "accounting of disclosures", "disclosure tracking", "disclosure log",
                "audit trail", "PHI disclosure record", "disclosure history"
            ],
            mandatory_elements=[
                "Disclosure tracking mechanism",
                "Disclosure information to CE",
                "6-year retention period"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_PRIVACY_13",
            framework="HIPAA",
            article_reference="45 CFR §164.522",
            clause_type="Restriction Requests",
            description="Requires BA to comply with restrictions agreed between CE and individual",
            mandatory=True,
            keywords=[
                "request restriction", "use restriction", "disclosure restriction",
                "agreed limitations", "individual request", "out-of-pocket payment"
            ],
            mandatory_elements=[
                "Compliance with CE-individual restrictions",
                "Restriction implementation",
                "Cooperation with CE"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # ==================== SECTION 2: SECURITY RULE - ADMINISTRATIVE SAFEGUARDS ====================
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_01",
            framework="HIPAA",
            article_reference="45 CFR §164.308",
            clause_type="Security Safeguards",
            description="Requires BA to implement all Administrative Safeguards of Security Rule",
            mandatory=True,
            keywords=[
                "administrative safeguards", "policies", "procedures", "workforce",
                "security management", "administrative controls"
            ],
            mandatory_elements=[
                "Security management process",
                "Assigned security responsibility",
                "Workforce security",
                "Information access management",
                "Security awareness and training",
                "Security incident procedures",
                "Contingency plan",
                "Evaluation"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_02",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(1)(ii)(A)",
            clause_type="Risk Analysis",
            description="Requires BA to conduct formal, periodic risk analysis",
            mandatory=True,
            keywords=[
                "risk analysis", "risk assessment", "vulnerability assessment",
                "threat analysis", "periodic review", "documented assessment"
            ],
            mandatory_elements=[
                "Accurate and thorough risk assessment",
                "Potential risks to ePHI",
                "Vulnerabilities identification",
                "Periodic updates"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_03",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(1)(ii)(B)",
            clause_type="Risk Management",
            description="Requires BA to implement risk management plan based on risk analysis",
            mandatory=True,
            keywords=[
                "risk management", "mitigation", "security measures",
                "risk reduction", "appropriate safeguards", "risk treatment"
            ],
            mandatory_elements=[
                "Security measures implementation",
                "Risk reduction to reasonable level",
                "Risk mitigation strategies"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_04",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(1)(ii)(C)",
            clause_type="Sanction Policy",
            description="Requires BA to maintain sanction policy for workforce violations",
            mandatory=True,
            keywords=[
                "sanction policy", "disciplinary action", "workforce sanctions",
                "policy violations", "enforcement", "consequences"
            ],
            mandatory_elements=[
                "Sanction policy existence",
                "Appropriate sanctions application",
                "Workforce accountability"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_05",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(1)(ii)(D)",
            clause_type="Activity Review",
            description="Requires BA to implement information system activity review",
            mandatory=True,
            keywords=[
                "activity review", "log review", "audit logs", "access reports",
                "monitoring", "system activity", "regular review"
            ],
            mandatory_elements=[
                "Regular log reviews",
                "Access report monitoring",
                "Security incident tracking"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_06",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(2)",
            clause_type="Security Officer",
            description="Warrants BA has appointed designated Security Officer",
            mandatory=True,
            keywords=[
                "security officer", "security official", "designated individual",
                "security responsibility", "appointed officer"
            ],
            mandatory_elements=[
                "Designated Security Officer",
                "Named individual or role",
                "Security policy responsibility"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_07",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(3)",
            clause_type="Workforce Access",
            description="Requires BA to manage workforce access authorization and supervision",
            mandatory=True,
            keywords=[
                "workforce access", "authorization", "supervision", "access control",
                "appropriate access", "workforce management"
            ],
            mandatory_elements=[
                "Authorization procedures",
                "Workforce supervision",
                "Appropriate access levels"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_08",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(3)(ii)(C)",
            clause_type="Termination Procedures",
            description="Requires BA to have workforce termination procedures for access removal",
            mandatory=True,
            keywords=[
                "termination procedures", "access removal", "offboarding",
                "employment termination", "access revocation", "immediate termination"
            ],
            mandatory_elements=[
                "Termination procedures",
                "Immediate access removal",
                "Systematic offboarding"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_09",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(4)",
            clause_type="Role-Based Access",
            description="Requires BA to implement role-based access controls",
            mandatory=True,
            keywords=[
                "role-based access", "RBAC", "access management", "need to know",
                "least privilege", "job function", "authorized access"
            ],
            mandatory_elements=[
                "Role-based access policies",
                "Access limited to job functions",
                "Need-to-know principle"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_10",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(5)",
            clause_type="Security Training",
            description="Requires BA to provide security awareness training to workforce",
            mandatory=True,
            keywords=[
                "security training", "awareness training", "workforce training",
                "ongoing training", "security education", "staff training"
            ],
            mandatory_elements=[
                "Security awareness program",
                "Training for all workforce",
                "Ongoing training updates"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_11",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(5)(ii)(B)",
            clause_type="Malware Protection Training",
            description="Requires BA to provide training on malware detection and protection",
            mandatory=True,
            keywords=[
                "malware", "virus", "ransomware", "phishing", "malicious software",
                "threat detection", "cybersecurity training"
            ],
            mandatory_elements=[
                "Malware detection training",
                "Protection procedures",
                "Reporting mechanisms"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_12",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(5)(ii)(C)",
            clause_type="Password Management Training",
            description="Requires BA to provide training on password management best practices",
            mandatory=True,
            keywords=[
                "password management", "password security", "password policy",
                "strong passwords", "password changes", "credential protection"
            ],
            mandatory_elements=[
                "Password best practices",
                "Password creation guidelines",
                "Password safeguarding"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_13",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(6)",
            clause_type="Incident Procedures",
            description="Requires BA to have formal security incident procedures",
            mandatory=True,
            keywords=[
                "security incident", "incident response", "incident procedures",
                "identify and respond", "incident mitigation", "incident documentation"
            ],
            mandatory_elements=[
                "Incident identification",
                "Response procedures",
                "Mitigation strategies",
                "Documentation requirements"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_14",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(7)(ii)(A)",
            clause_type="Data Backup Plan",
            description="Requires BA to have data backup plan for contingency",
            mandatory=True,
            keywords=[
                "data backup", "backup plan", "exact copies", "retrievable copies",
                "contingency", "data recovery", "backup procedures"
            ],
            mandatory_elements=[
                "Formal backup plan",
                "Exact retrievable copies",
                "Regular backup schedule"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_15",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(7)(ii)(B)",
            clause_type="Disaster Recovery",
            description="Requires BA to have disaster recovery plan",
            mandatory=True,
            keywords=[
                "disaster recovery", "recovery plan", "data restoration",
                "business continuity", "disaster preparedness", "system recovery"
            ],
            mandatory_elements=[
                "Disaster recovery plan",
                "Data restoration procedures",
                "System recovery processes"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_16",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(7)(ii)(C)",
            clause_type="Emergency Mode Operation",
            description="Requires BA to have emergency mode operation plan",
            mandatory=True,
            keywords=[
                "emergency mode", "emergency operations", "critical business processes",
                "continuity", "emergency procedures", "critical operations"
            ],
            mandatory_elements=[
                "Emergency mode procedures",
                "Critical process continuation",
                "ePHI protection during emergency"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_17",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(8)",
            clause_type="Security Evaluation",
            description="Requires BA to conduct periodic evaluations of security program",
            mandatory=True,
            keywords=[
                "evaluation", "periodic evaluation", "security assessment",
                "effectiveness review", "technical evaluation", "non-technical evaluation"
            ],
            mandatory_elements=[
                "Periodic evaluations",
                "Technical assessments",
                "Non-technical assessments",
                "Compliance verification"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        # ==================== SECTION 3: SECURITY RULE - PHYSICAL SAFEGUARDS ====================
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_18",
            framework="HIPAA",
            article_reference="45 CFR §164.310",
            clause_type="Physical Safeguards",
            description="Requires BA to implement all Physical Safeguards of Security Rule",
            mandatory=True,
            keywords=[
                "physical safeguards", "facility security", "physical access",
                "physical protection", "hardware security"
            ],
            mandatory_elements=[
                "Facility access controls",
                "Workstation use policies",
                "Workstation security",
                "Device and media controls"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_19",
            framework="HIPAA",
            article_reference="45 CFR §164.310(a)(1)",
            clause_type="Facility Access Controls",
            description="Requires BA to limit physical facility access",
            mandatory=True,
            keywords=[
                "facility access", "physical access control", "datacenter security",
                "building access", "access limitations", "authorized personnel"
            ],
            mandatory_elements=[
                "Access control policies",
                "Physical access limitations",
                "Authorized personnel only"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_20",
            framework="HIPAA",
            article_reference="45 CFR §164.310(a)(2)(ii)",
            clause_type="Facility Security Plan",
            description="Requires BA to have facility security plan",
            mandatory=True,
            keywords=[
                "facility security plan", "security safeguards", "physical security",
                "unauthorized access prevention", "theft prevention", "environmental hazards"
            ],
            mandatory_elements=[
                "Facility security policies",
                "Unauthorized access prevention",
                "Equipment protection",
                "Environmental hazard protection"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_21",
            framework="HIPAA",
            article_reference="45 CFR §164.310(a)(2)(iii)",
            clause_type="Access Validation",
            description="Requires BA to validate access with badges, keys, or similar controls",
            mandatory=True,
            keywords=[
                "access validation", "identity verification", "badges", "keys",
                "access control", "visitor management", "authorization verification"
            ],
            mandatory_elements=[
                "Identity verification procedures",
                "Authorization validation",
                "Access control mechanisms"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_22",
            framework="HIPAA",
            article_reference="45 CFR §164.310(a)(2)(iv)",
            clause_type="Maintenance Records",
            description="Requires BA to maintain maintenance records for physical security",
            mandatory=True,
            keywords=[
                "maintenance records", "repair documentation", "modification log",
                "physical security maintenance", "security component maintenance"
            ],
            mandatory_elements=[
                "Maintenance documentation",
                "Repair records",
                "Security-related modifications"
            ],
            risk_level=RiskLevel.LOW
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_23",
            framework="HIPAA",
            article_reference="45 CFR §164.310(b)",
            clause_type="Workstation Use",
            description="Requires BA to have policies defining appropriate workstation use",
            mandatory=True,
            keywords=[
                "workstation use", "workstation policy", "appropriate use",
                "proper functions", "device usage", "endpoint policy"
            ],
            mandatory_elements=[
                "Workstation use policies",
                "Proper function specifications",
                "Usage manner definition"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_24",
            framework="HIPAA",
            article_reference="45 CFR §164.310(c)",
            clause_type="Workstation Security",
            description="Requires BA to implement physical workstation safeguards",
            mandatory=True,
            keywords=[
                "workstation security", "physical workstation protection", "laptop security",
                "desktop security", "unauthorized physical access", "device theft"
            ],
            mandatory_elements=[
                "Workstation protection policies",
                "Unauthorized access prevention",
                "Theft prevention measures"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_25",
            framework="HIPAA",
            article_reference="45 CFR §164.310(c)",
            clause_type="Screen Visibility",
            description="Requires BA to control workstation screen visibility",
            mandatory=True,
            keywords=[
                "screen visibility", "privacy screens", "visual privacy",
                "unauthorized viewing", "screen positioning", "display protection"
            ],
            mandatory_elements=[
                "Screen positioning policies",
                "Visual privacy measures",
                "Unauthorized viewing prevention"
            ],
            risk_level=RiskLevel.LOW
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_26",
            framework="HIPAA",
            article_reference="45 CFR §164.310(d)(1)",
            clause_type="Media Disposal",
            description="Requires BA to have policies for secure disposal of media containing ePHI",
            mandatory=True,
            keywords=[
                "media disposal", "secure disposal", "data destruction", "hardware disposal",
                "unreadable", "irretrievable", "hard drive destruction"
            ],
            mandatory_elements=[
                "Disposal policies",
                "Unreadable rendering",
                "Irretrievable destruction"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_27",
            framework="HIPAA",
            article_reference="45 CFR §164.310(d)(2)(i)",
            clause_type="Media Re-Use",
            description="Requires BA to have procedures for media sanitization before re-use",
            mandatory=True,
            keywords=[
                "media re-use", "sanitization", "degaussing", "wiping",
                "data removal", "secure erasure", "media cleaning"
            ],
            mandatory_elements=[
                "Sanitization procedures",
                "Secure wiping methods",
                "Re-use authorization"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_28",
            framework="HIPAA",
            article_reference="45 CFR §164.310(d)(2)(ii)",
            clause_type="Media Accountability",
            description="Requires BA to maintain accountability logs for media movement",
            mandatory=True,
            keywords=[
                "media accountability", "media tracking", "hardware movement",
                "backup tape log", "media inventory", "responsible person"
            ],
            mandatory_elements=[
                "Media movement records",
                "Hardware tracking",
                "Responsible party identification"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_29",
            framework="HIPAA",
            article_reference="45 CFR §164.310(d)(2)(iii)",
            clause_type="Media Transport",
            description="Requires BA to have policies for secure transport of devices and media",
            mandatory=True,
            keywords=[
                "media transport", "device transport", "physical transport",
                "encryption in transit", "secure transportation", "mobile device"
            ],
            mandatory_elements=[
                "Transport protection policies",
                "Encryption during transport",
                "Secure handling procedures"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # ==================== SECTION 4: SECURITY RULE - TECHNICAL SAFEGUARDS ====================
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_30",
            framework="HIPAA",
            article_reference="45 CFR §164.312",
            clause_type="Technical Safeguards",
            description="Requires BA to implement all Technical Safeguards of Security Rule",
            mandatory=True,
            keywords=[
                "technical safeguards", "access control", "audit controls",
                "integrity controls", "transmission security", "technical controls"
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
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_31",
            framework="HIPAA",
            article_reference="45 CFR §164.312(a)(2)(i)",
            clause_type="Unique User IDs",
            description="Requires BA to use unique user IDs for workforce identification",
            mandatory=True,
            keywords=[
                "unique user ID", "user identification", "tracking identity",
                "individual accounts", "no shared accounts", "unique identifiers"
            ],
            mandatory_elements=[
                "Unique user identification",
                "No shared logins",
                "Activity tracking capability"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_32",
            framework="HIPAA",
            article_reference="45 CFR §164.312(a)(2)(ii)",
            clause_type="Emergency Access",
            description="Requires BA to have emergency access procedures",
            mandatory=True,
            keywords=[
                "emergency access", "break glass", "emergency procedures",
                "authorized emergency", "system administrator", "emergency situations"
            ],
            mandatory_elements=[
                "Emergency access procedures",
                "Authorized personnel list",
                "Emergency access logging"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_33",
            framework="HIPAA",
            article_reference="45 CFR §164.312(a)(2)(iii)",
            clause_type="Automatic Logoff",
            description="Requires BA to use automatic logoff mechanisms",
            mandatory=True,
            keywords=[
                "automatic logoff", "session timeout", "auto-logout",
                "inactivity timeout", "automatic termination", "idle timeout"
            ],
            mandatory_elements=[
                "Automatic logoff implementation",
                "Predetermined timeout period",
                "Unattended workstation protection"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_34",
            framework="HIPAA",
            article_reference="45 CFR §164.312(a)(2)(iv)",
            clause_type="Encryption",
            description="Requires BA to encrypt ePHI at rest (addressable but modern standard)",
            mandatory=True,
            keywords=[
                "encryption at rest", "data encryption", "encrypted storage",
                "database encryption", "hard drive encryption", "AES encryption",
                "encrypt", "encryption"
            ],
            mandatory_elements=[
                "Encryption mechanism",
                "ePHI encryption at rest",
                "Strong encryption standards"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_35",
            framework="HIPAA",
            article_reference="45 CFR §164.312(e)(1)",
            clause_type="Transmission Security",
            description="Requires BA to encrypt ePHI during transmission",
            mandatory=True,
            keywords=[
                "encryption in transit", "transmission security", "TLS", "SSL",
                "VPN", "encrypted transmission", "network encryption"
            ],
            mandatory_elements=[
                "Transmission encryption",
                "TLS/SSL implementation",
                "Secure network transmission"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_36",
            framework="HIPAA",
            article_reference="45 CFR §164.312(b)",
            clause_type="Audit Controls",
            description="Requires BA to implement audit controls and system activity logging",
            mandatory=True,
            keywords=[
                "audit controls", "logging", "system logs", "activity logs",
                "audit trail", "access logs", "security logging"
            ],
            mandatory_elements=[
                "Audit logging mechanisms",
                "Activity recording",
                "Log examination capability"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_37",
            framework="HIPAA",
            article_reference="45 CFR §164.312(c)(1)",
            clause_type="Integrity Controls",
            description="Requires BA to implement integrity controls to detect tampering",
            mandatory=True,
            keywords=[
                "integrity controls", "data integrity", "tampering detection",
                "checksums", "hash validation", "alteration detection"
            ],
            mandatory_elements=[
                "Integrity protection policies",
                "Tampering detection mechanisms",
                "Improper alteration prevention"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_SECURITY_38",
            framework="HIPAA",
            article_reference="45 CFR §164.312(d)",
            clause_type="Authentication",
            description="Requires BA to use person/entity authentication (passwords, 2FA)",
            mandatory=True,
            keywords=[
                "authentication", "multi-factor", "2FA", "MFA", "passwords",
                "identity verification", "strong authentication"
            ],
            mandatory_elements=[
                "Authentication procedures",
                "Identity verification",
                "Multi-factor authentication recommended"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # ==================== SECTION 5: BREACH, HITECH & OMNIBUS RULE ====================
        
        RegulatoryRequirement(
            requirement_id="HIPAA_BREACH_01",
            framework="HIPAA",
            article_reference="45 CFR §164.308(b)",
            clause_type="BA Direct Liability",
            description="Acknowledges BA's direct liability for HIPAA violations (Omnibus Rule)",
            mandatory=True,
            keywords=[
                "direct liability", "omnibus rule", "BA liability", "HIPAA compliance",
                "security rule compliance", "privacy rule compliance"
            ],
            mandatory_elements=[
                "Direct liability acknowledgment",
                "No liability waiver",
                "Omnibus Rule compliance"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_BREACH_02",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(6)",
            clause_type="Security Incident Reporting",
            description="Requires BA to report all security incidents to CE",
            mandatory=True,
            keywords=[
                "security incident", "incident reporting", "failed attempts",
                "monthly report", "incident notification", "near misses"
            ],
            mandatory_elements=[
                "All incidents reported",
                "Reporting timeframe specified",
                "Reporting format defined"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_BREACH_03",
            framework="HIPAA",
            article_reference="45 CFR §164.410",
            clause_type="Breach Notification",
            description="Requires BA to report breach of unsecured PHI to CE without undue delay",
            mandatory=True,
            keywords=[
                "breach notification", "unsecured PHI", "data breach",
                "breach reporting", "PHI compromise", "unauthorized access",
                "breach", "notify", "security breach", "personal data breach",
                "72 hours", "incident", "inform", "without delay"
            ],
            mandatory_elements=[
                "Breach notification requirement",
                "Unsecured PHI definition",
                "Immediate reporting",
                "Notification without undue delay",
                "Notification timeframe (72 hours)",
                "Description of breach nature",
                "Contact point information"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_BREACH_04",
            framework="HIPAA",
            article_reference="45 CFR §164.410(b)",
            clause_type="Breach Reporting Timeline",
            description="Specifies breach reporting timeframe (without unreasonable delay, max 60 days)",
            mandatory=True,
            keywords=[
                "without unreasonable delay", "60 days", "breach timeline",
                "reporting deadline", "discovery", "immediate notification"
            ],
            mandatory_elements=[
                "Without unreasonable delay",
                "Maximum 60 days from discovery",
                "Faster timeframe often contractually required"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_BREACH_05",
            framework="HIPAA",
            article_reference="45 CFR §164.410(c)",
            clause_type="Breach Investigation Assistance",
            description="Requires BA to assist CE in breach investigation and individual notification",
            mandatory=True,
            keywords=[
                "breach investigation", "investigation assistance", "individual notification",
                "breach cooperation", "HHS notification", "media notification"
            ],
            mandatory_elements=[
                "Full cooperation requirement",
                "Information provision",
                "Notification assistance"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_BREACH_06",
            framework="HIPAA",
            article_reference="45 CFR §164.308(a)(6)(ii)",
            clause_type="Breach Mitigation",
            description="Requires BA to mitigate harmful effects of any breach",
            mandatory=True,
            keywords=[
                "mitigation", "harmful effects", "breach mitigation", "damage control",
                "risk mitigation", "to the extent practicable"
            ],
            mandatory_elements=[
                "Active mitigation requirement",
                "Harm reduction efforts",
                "Practicable measures"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        # ==================== SECTION 6: SUBCONTRACTORS & TERMINATION ====================
        
        RegulatoryRequirement(
            requirement_id="HIPAA_CONTRACT_01",
            framework="HIPAA",
            article_reference="45 CFR §164.504(e)",
            clause_type="Sub-processor Authorization",
            description="Requires BA to have compliant BAAs with all subcontractors (flow-down)",
            mandatory=True,
            keywords=[
                "subcontractor BAA", "flow-down", "downstream agreement",
                "subcontractor agreement", "third party BAA", "compliance flow",
                "sub-processor", "subprocessor", "authorization", "notification",
                "prior written", "engage", "third party", "sub-contractor"
            ],
            mandatory_elements=[
                "BAA with all subcontractors",
                "HIPAA-compliant agreements",
                "Same obligations flow-down",
                "Prior written authorization",
                "Notification period (typically 30 days)",
                "Right to object"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_CONTRACT_02",
            framework="HIPAA",
            article_reference="45 CFR §164.308(b)",
            clause_type="Subcontractor Direct Liability",
            description="Acknowledges subcontractor's direct liability under Omnibus Rule",
            mandatory=True,
            keywords=[
                "subcontractor liability", "direct liability", "omnibus rule",
                "downstream liability", "subcontractor compliance"
            ],
            mandatory_elements=[
                "Subcontractor direct liability",
                "No liability waiver",
                "HIPAA compliance obligation"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_CONTRACT_03",
            framework="HIPAA",
            article_reference="45 CFR §164.504(e)(2)(iii)",
            clause_type="Termination for Breach",
            description="Allows CE to terminate BAA if BA commits material breach",
            mandatory=True,
            keywords=[
                "termination", "material breach", "contract termination",
                "breach cure", "termination rights", "violation termination"
            ],
            mandatory_elements=[
                "CE termination right",
                "Material breach definition",
                "Cure period"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_CONTRACT_04",
            framework="HIPAA",
            article_reference="45 CFR §164.504(e)(2)(ii)(I)",
            clause_type="Data Deletion",
            description="Requires BA to return or destroy all PHI upon contract termination",
            mandatory=True,
            keywords=[
                "return PHI", "destroy PHI", "data return", "secure destruction",
                "termination obligations", "PHI disposal", "all copies",
                "deletion", "erasure"
            ],
            mandatory_elements=[
                "Return or destroy all PHI",
                "CE choice of method",
                "All copies included",
                "Deletion or return of data"
            ],
            risk_level=RiskLevel.HIGH
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_CONTRACT_05",
            framework="HIPAA",
            article_reference="45 CFR §164.504(e)(2)(ii)(J)",
            clause_type="Infeasibility Exception",
            description="Extends PHI protections indefinitely if return/destruction infeasible",
            mandatory=True,
            keywords=[
                "infeasibility", "indefinite protection", "retention requirement",
                "backup archives", "protections survive", "continued protection"
            ],
            mandatory_elements=[
                "Infeasibility determination",
                "Protections survive termination",
                "Indefinite continuation"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
        
        RegulatoryRequirement(
            requirement_id="HIPAA_CONTRACT_06",
            framework="HIPAA",
            article_reference="45 CFR §164.504(e)(2)(ii)(H)",
            clause_type="HHS Audit Access",
            description="Requires BA to make practices and records available to HHS for audits",
            mandatory=True,
            keywords=[
                "HHS audit", "secretary access", "audit access", "records available",
                "compliance audit", "HHS inspection", "books and records"
            ],
            mandatory_elements=[
                "HHS access to practices",
                "Records availability",
                "Compliance determination cooperation"
            ],
            risk_level=RiskLevel.MEDIUM
        ),
    ]
    
    return requirements
