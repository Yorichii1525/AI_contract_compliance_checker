"""
LegalBERT-based clause classification service.
"""
import streamlit as st
from typing import Tuple, List
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import torch and transformers, make them optional
try:
    import torch
    from transformers import AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except (ImportError, AttributeError) as e:
    logger.warning(f"torch/transformers not available: {e}")
    TRANSFORMERS_AVAILABLE = False
    torch = None
    AutoTokenizer = None
    AutoModel = None


class LegalBERTClassifier:
    """LegalBERT-based clause classification."""
    
    def __init__(self, model_name: str = "nlpaueb/legal-bert-base-uncased"):
        """
        Initialize LegalBERT classifier.
        
        Args:
            model_name: Hugging Face model identifier
        """
        self.model_name = model_name
        
        if TRANSFORMERS_AVAILABLE and torch is not None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
            # Clause classification currently uses the keyword classifier in
            # predict(); defer the unused transformer weights until callers
            # explicitly request LegalBERT embeddings.
            self.model = None
            self.tokenizer = None
        else:
            self.device = None
            self.model = None
            self.tokenizer = None
            logger.warning("LegalBERTClassifier running in fallback mode - using keyword-based classification")
        
        # Define clause type mappings - EXPANDED WITH CUAD DATASET (41 CATEGORIES)
        # Contract Understanding Atticus Dataset provides comprehensive legal clause taxonomy
        self.clause_types = [
            # Original GDPR/HIPAA focused types (kept for compatibility)
            "Data Processing",
            "Sub-processor Authorization", 
            "Data Subject Rights",
            "Breach Notification",
            "Data Transfer",
            "Security Safeguards",
            "Permitted Uses and Disclosures",
            
            # CUAD Categories - Contract Metadata
            "Document Name",
            "Parties",
            "Agreement Date",
            "Effective Date",
            "Expiration Date",
            "Renewal Term",
            "Notice to Terminate Renewal",
            "Governing Law",
            
            # CUAD Categories - Business Terms
            "Most Favored Nation",
            "Non-Compete",
            "Exclusivity",
            "No-Solicit of Customers",
            "Competitive Restriction Exception",
            "No-Solicit of Employees",
            "Non-Disparagement",
            "Termination for Convenience",
            "ROFR/ROFO/ROFN",
            "Change of Control",
            "Anti-Assignment",
            "Revenue/Profit Sharing",
            "Price Restriction",
            "Minimum Commitment",
            "Volume Restriction",
            
            # CUAD Categories - Intellectual Property
            "IP Ownership Assignment",
            "Joint IP Ownership",
            "License Grant",
            "Non-Transferable License",
            "Affiliate IP License-Licensor",
            "Affiliate IP License-Licensee",
            "Unlimited/All-You-Can-Eat License",
            "Irrevocable or Perpetual License",
            "Source Code Escrow",
            
            # CUAD Categories - Operations & Compliance
            "Post-Termination Services",
            "Audit Rights",
            "Uncapped Liability",
            "Cap on Liability",
            "Liquidated Damages",
            "Warranty Duration",
            "Insurance",
            "Covenant Not to Sue",
            "Third Party Beneficiary"
        ]
        
        # CUAD to Regulatory Clause Type Mapping (v2.0 - 61 mappings)
        # Maps CUAD clause types to original 7 regulatory types for compliance scoring
        # This allows CUAD clauses to be matched against GDPR/HIPAA/SOX/CCPA requirements
        self.cuad_mapping_version = "2.0"  # Version tracking for debugging
        self.cuad_to_regulatory_mapping = {
            # Metadata types -> not directly compliance-related (return None = skip scoring)
            "Document Name": None,
            "Parties": None,
            "Agreement Date": None,
            "Effective Date": None,
            "Expiration Date": None,
            
            # Business/operational terms that relate to data processing
            "Renewal Term": "Data Processing",
            "Notice to Terminate Renewal": "Data Processing",
            "Governing Law": "Data Transfer",
            "Most Favored Nation": "Data Processing",
            "Non-Compete": "Permitted Uses and Disclosures",
            "Exclusivity": "Permitted Uses and Disclosures",
            "No-Solicit of Customers": "Permitted Uses and Disclosures",
            "Competitive Restriction Exception": "Permitted Uses and Disclosures",
            "No-Solicit of Employees": "Permitted Uses and Disclosures",
            "Non-Disparagement": "Permitted Uses and Disclosures",
            "Termination for Convenience": "Data Processing",
            "ROFR/ROFO/ROFN": "Data Processing",
            "Change of Control": "Sub-processor Authorization",
            "Anti-Assignment": "Sub-processor Authorization",
            
            # Financial terms -> Data Processing (contract terms)
            "Revenue/Profit Sharing": "Data Processing",
            "Price Restriction": "Data Processing",
            "Minimum Commitment": "Data Processing",
            "Volume Restriction": "Data Processing",
            
            # IP/License terms -> Data Subject Rights (control/access)
            "IP Ownership Assignment": "Data Subject Rights",
            "IP Ownership": "Data Subject Rights",  # Common variant
            "Joint IP Ownership": "Data Subject Rights",
            "License Grant": "Data Subject Rights",
            "Non-Transferable License": "Data Subject Rights",
            "Affiliate IP License-Licensor": "Sub-processor Authorization",
            "Affiliate IP License-Licensee": "Sub-processor Authorization",
            "Unlimited/All-You-Can-Eat License": "Data Subject Rights",
            "Irrevocable or Perpetual License": "Data Subject Rights",
            "Source Code Escrow": "Security Safeguards",
            
            # Service terms
            "Post-Termination Services": "Data Processing",
            "Audit Rights": "Security Safeguards",
            
            # Liability/Insurance -> Security/Breach related
            "Uncapped Liability": "Breach Notification",
            "Cap on Liability": "Breach Notification",
            "Liquidated Damages": "Breach Notification",
            "Warranty Duration": "Security Safeguards",
            "Insurance": "Security Safeguards",
            "Covenant Not to Sue": "Breach Notification",
            "Third Party Beneficiary": "Sub-processor Authorization",
            
            # Security/Confidentiality -> Security Safeguards
            "Confidentiality": "Security Safeguards",
            "Confidential Information": "Security Safeguards",
            "Data Security": "Security Safeguards",
            "Security Requirements": "Security Safeguards",
            "Encryption": "Security Safeguards",
            
            # Indemnification -> Breach Notification (liability for breaches)
            "Indemnification": "Breach Notification",
            "Mutual Indemnification": "Breach Notification",
            
            # Termination -> Data Processing (processing duration/termination)
            "Termination": "Data Processing",
            "Termination Rights": "Data Processing",
            "Termination for Cause": "Data Processing",
            
            # Payment terms -> Data Processing (service terms)
            "Payment Terms": "Data Processing",
            "Payment": "Data Processing",
            "Fees": "Data Processing",
            
            # Warranties -> Security Safeguards
            "Warranties": "Security Safeguards",
            "Warranty": "Security Safeguards",
            "Disclaimer of Warranties": "Security Safeguards",
            
            # General/catch-all -> Data Processing (contract performance)
            "General": "Data Processing",
            "Miscellaneous": "Data Processing",
            "Definitions": None  # Metadata - just definitions
        }
        
        # Log mapping version for debugging
        logger.info(
            f"CUAD mapping version {self.cuad_mapping_version} loaded "
            f"with {len(self.cuad_to_regulatory_mapping)} entries"
        )
        
        # Keywords for rule-based classification assistance
        # Expanded with CUAD dataset categories for comprehensive contract understanding
        self.clause_keywords = {
            # Original GDPR/HIPAA Categories
            "Data Processing": [
                "process", "processing", "processor", "controller", "instructions",
                "documented instructions", "personal data processing", "data controller",
                "data processor", "processing activities", "lawful basis"
            ],
            "Sub-processor Authorization": [
                "sub-processor", "subprocessor", "sub processor", "authorization", "prior written",
                "notification", "object", "third party processor", "engage third party",
                "downstream processor", "subcontractor"
            ],
            "Data Subject Rights": [
                "data subject", "rights", "access", "rectification", "erasure",
                "portability", "restriction", "objection", "right to", "individual rights",
                "access request", "deletion request", "right to be forgotten"
            ],
            "Breach Notification": [
                "breach", "notification", "notify", "security breach", "incident",
                "data breach", "unauthorized access", "breach response", "incident response",
                "72 hours", "without undue delay", "security incident"
            ],
            "Data Transfer": [
                "transfer", "cross-border", "third country", "international",
                "standard contractual clauses", "adequacy decision", "SCC", "SCCs",
                "international transfer", "outside", "data export", "transfer mechanism"
            ],
            "Security Safeguards": [
                "security", "safeguards", "measures", "technical", "organizational",
                "encryption", "pseudonymization", "confidentiality", "integrity",
                "availability", "security measures", "technical and organizational measures",
                "access controls", "authentication", "backup"
            ],
            "Permitted Uses and Disclosures": [
                "permitted", "allowed", "disclosure", "use", "purpose",
                "authorized use", "permitted disclosure", "lawful purpose",
                "legitimate interest", "specific purpose", "purpose limitation"
            ],
            
            # CUAD Categories - Contract Metadata
            "Document Name": [
                "agreement", "contract", "titled", "entitled", "named",
                "this agreement", "this contract", "hereinafter referred to"
            ],
            "Parties": [
                "party", "parties", "between", "and", "hereinafter",
                "referred to as", "company", "corporation", "entity",
                "individual", "seller", "buyer", "vendor", "customer"
            ],
            "Agreement Date": [
                "dated", "date of", "executed on", "signed on",
                "effective as of", "entered into", "as of"
            ],
            "Effective Date": [
                "effective date", "commencement date", "start date",
                "becomes effective", "shall commence", "beginning on"
            ],
            "Expiration Date": [
                "expiration", "expires", "term ends", "termination date",
                "end date", "concludes", "final date", "expiry"
            ],
            "Renewal Term": [
                "renewal", "renew", "automatic renewal", "extension",
                "successive terms", "additional term", "continuing",
                "automatically extend", "rollover"
            ],
            "Notice to Terminate Renewal": [
                "notice period", "advance notice", "prior notice",
                "written notice", "days notice", "notify in writing",
                "notice of termination", "notice requirement"
            ],
            "Governing Law": [
                "governing law", "jurisdiction", "laws of", "governed by",
                "subject to the laws", "applicable law", "state law",
                "federal law", "legal jurisdiction"
            ],
            
            # CUAD Categories - Business Terms
            "Most Favored Nation": [
                "most favored nation", "MFN", "better terms", "more favorable",
                "no less favorable", "equal terms", "parity", "matching terms"
            ],
            "Non-Compete": [
                "non-compete", "non compete", "compete", "competing",
                "competitive", "restrict", "prohibition", "restricted from",
                "shall not engage", "refraining from"
            ],
            "Exclusivity": [
                "exclusive", "exclusively", "sole", "only", "exclusivity",
                "exclusive rights", "exclusive dealing", "requirements",
                "all requirements", "shall not sell", "shall not license"
            ],
            "No-Solicit of Customers": [
                "solicit", "solicitation", "customers", "clients",
                "no-solicitation", "refrain from soliciting", "not solicit",
                "customer list", "client relationships"
            ],
            "Competitive Restriction Exception": [
                "except", "exception", "carve-out", "carveout", "excluding",
                "does not apply", "not restricted", "permitted to",
                "notwithstanding", "subject to"
            ],
            "No-Solicit of Employees": [
                "solicit employees", "hire employees", "recruit",
                "poach", "employment", "staff", "personnel",
                "not hire", "refrain from hiring", "employee solicitation"
            ],
            "Non-Disparagement": [
                "disparage", "disparagement", "defame", "negative",
                "harmful", "detrimental statements", "refrain from",
                "not make statements", "reputation"
            ],
            "Termination for Convenience": [
                "terminate", "termination", "convenience", "without cause",
                "at will", "for any reason", "sole discretion",
                "upon notice", "may terminate"
            ],
            "ROFR/ROFO/ROFN": [
                "right of first refusal", "ROFR", "right of first offer",
                "ROFO", "first right", "right of first negotiation",
                "ROFN", "matching right", "opportunity to purchase"
            ],
            "Change of Control": [
                "change of control", "merger", "acquisition", "sale of",
                "transfer of ownership", "controlling interest",
                "change in ownership", "successor", "assign"
            ],
            "Anti-Assignment": [
                "assignment", "assign", "transfer", "consent required",
                "prior written consent", "not assignable", "no assignment",
                "binding upon", "successors"
            ],
            "Revenue/Profit Sharing": [
                "revenue", "profit", "sharing", "share", "percentage",
                "royalty", "commission", "split", "distribution",
                "net revenue", "gross revenue"
            ],
            "Price Restriction": [
                "price", "pricing", "fees", "charges", "rate",
                "not exceed", "maximum price", "minimum price",
                "price increase", "price decrease", "adjust"
            ],
            "Minimum Commitment": [
                "minimum", "commitment", "purchase", "order",
                "quantity", "volume", "required to buy",
                "obligation to purchase", "minimum order"
            ],
            "Volume Restriction": [
                "volume", "exceed", "threshold", "limit", "cap",
                "maximum", "usage", "consumption", "overage"
            ],
            
            # CUAD Categories - Intellectual Property
            "IP Ownership Assignment": [
                "intellectual property", "IP", "ownership", "assign",
                "transfer", "belong to", "property of", "title",
                "copyright", "patent", "trademark", "trade secret"
            ],
            "Joint IP Ownership": [
                "joint", "jointly", "co-own", "shared ownership",
                "joint ownership", "both parties", "mutual",
                "co-developed", "collaborative"
            ],
            "License Grant": [
                "license", "grant", "hereby grants", "licensed",
                "permission", "right to use", "authorization",
                "licensed rights", "scope of license"
            ],
            "Non-Transferable License": [
                "non-transferable", "not transferable", "personal",
                "non-assignable", "may not transfer", "restricted",
                "limited to", "licensee only"
            ],
            "Affiliate IP License-Licensor": [
                "affiliate", "licensor", "subsidiary", "parent",
                "related entity", "controlled by", "under common control",
                "licensor's affiliates", "affiliates of licensor"
            ],
            "Affiliate IP License-Licensee": [
                "affiliate", "licensee", "subsidiary", "parent",
                "related entity", "controlled by", "under common control",
                "licensee's affiliates", "affiliates of licensee"
            ],
            "Unlimited/All-You-Can-Eat License": [
                "unlimited", "unrestricted", "all-you-can-eat",
                "enterprise", "site license", "no limit",
                "without limitation", "any number", "as much as"
            ],
            "Irrevocable or Perpetual License": [
                "irrevocable", "perpetual", "forever", "permanent",
                "cannot be revoked", "in perpetuity", "for all time",
                "everlasting", "indefinite"
            ],
            "Source Code Escrow": [
                "source code", "escrow", "deposit", "third party",
                "escrow agent", "release", "bankruptcy", "insolvency",
                "source materials", "code repository"
            ],
            
            # CUAD Categories - Operations & Compliance
            "Post-Termination Services": [
                "post-termination", "after termination", "wind-down",
                "transition", "last buy", "final purchase",
                "obligations survive", "continuing obligations"
            ],
            "Audit Rights": [
                "audit", "inspect", "examination", "review",
                "right to audit", "books and records", "compliance audit",
                "verify", "access to records"
            ],
            "Uncapped Liability": [
                "unlimited liability", "uncapped", "no limit",
                "without limitation", "full liability", "entire",
                "all damages", "no cap"
            ],
            "Cap on Liability": [
                "cap", "limited to", "not exceed", "maximum",
                "limitation of liability", "aggregate liability",
                "capped at", "up to"
            ],
            "Liquidated Damages": [
                "liquidated damages", "penalty", "predetermined",
                "fixed amount", "damages in the amount",
                "termination fee", "breakup fee"
            ],
            "Warranty Duration": [
                "warranty", "warranted", "guarantee", "duration",
                "period", "months", "years", "defect-free",
                "warranty period", "guaranteed for"
            ],
            "Insurance": [
                "insurance", "insure", "coverage", "policy",
                "insured", "liability insurance", "maintain insurance",
                "proof of insurance", "certificate of insurance"
            ],
            "Covenant Not to Sue": [
                "covenant not to sue", "waive", "release", "relinquish",
                "not bring action", "not assert", "forbear",
                "refrain from suing", "no claims"
            ],
            "Third Party Beneficiary": [
                "third party", "beneficiary", "intended beneficiary",
                "enforce", "enforceable by", "benefit of",
                "third-party rights", "non-party"
            ]
        }
        
        # Phrase weights - longer/more specific phrases get higher weight
        # Higher weights = more important/specific legal terms
        self.phrase_weights = {
            # High specificity legal phrases (3.0+)
            "technical and organizational measures": 3.5,
            "standard contractual clauses": 3.5,
            "right of first refusal": 3.5,
            "right of first offer": 3.5,
            "liquidated damages": 3.5,
            "covenant not to sue": 3.5,
            "third party beneficiary": 3.5,
            "change of control": 3.0,
            "most favored nation": 3.0,
            "source code escrow": 3.0,
            "intellectual property": 3.0,
            
            # Medium specificity phrases (2.0-2.9)
            "documented instructions": 2.5,
            "data subject rights": 2.5,
            "security breach": 2.5,
            "prior written consent": 2.5,
            "governing law": 2.5,
            "effective date": 2.5,
            "termination date": 2.5,
            "sub-processor": 2.5,
            "cross-border": 2.5,
            "non-compete": 2.5,
            "non-disparagement": 2.5,
            "post-termination": 2.5,
            "audit rights": 2.5,
            "warranty period": 2.5,
            "license grant": 2.0,
            "revenue sharing": 2.0,
            "minimum commitment": 2.0,
            "perpetual license": 2.0,
            "irrevocable": 2.0,
            
            # Common legal terms (1.5)
            "personal data": 1.5,
            "confidentiality": 1.5,
            "exclusive": 1.5,
            "assignment": 1.5,
            "insurance": 1.5,
            "liability": 1.5,
            
            # Generic terms (1.0)
            "processing": 1.0,
            "security": 1.0,
            "termination": 1.0,
            "agreement": 1.0,
            "party": 1.0
        }
    
    @st.cache_resource
    def _load_model(_self):
        """
        Load LegalBERT model with Streamlit caching.
        
        Returns:
            Loaded model
        """
        if not TRANSFORMERS_AVAILABLE or AutoModel is None:
            logger.warning("Transformers not available, returning None")
            return None
            
        try:
            logger.info(f"Loading LegalBERT model: {_self.model_name}")
            model = AutoModel.from_pretrained(_self.model_name)
            model.to(_self.device)
            model.eval()
            logger.info("LegalBERT model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Error loading LegalBERT model: {e}")
            logger.warning("Falling back to keyword-based classification")
            return None
    
    @st.cache_resource
    def _load_tokenizer(_self):
        """
        Load tokenizer with Streamlit caching.
        
        Returns:
            Loaded tokenizer
        """
        if not TRANSFORMERS_AVAILABLE or AutoTokenizer is None:
            logger.warning("Transformers not available, returning None")
            return None
            
        try:
            logger.info(f"Loading tokenizer: {_self.model_name}")
            tokenizer = AutoTokenizer.from_pretrained(_self.model_name)
            logger.info("Tokenizer loaded successfully")
            return tokenizer
        except Exception as e:
            logger.error(f"Error loading tokenizer: {e}")
            raise
    
    def _keyword_based_classification(self, text: str) -> List[Tuple[str, float]]:
        """
        Perform enhanced keyword-based classification.
        Uses weighted phrase matching for better accuracy.
        
        Args:
            text: Clause text to classify
            
        Returns:
            List of (clause_type, score) tuples sorted by score
        """
        text_lower = text.lower()
        scores = {}
        
        for clause_type, keywords in self.clause_keywords.items():
            total_score = 0.0
            
            # Check each keyword/phrase
            for keyword in keywords:
                if keyword in text_lower:
                    # Apply weight if phrase is in weight dict
                    weight = self.phrase_weights.get(keyword, 1.0)
                    
                    # Bonus for exact phrase match (not just substring)
                    if f" {keyword} " in f" {text_lower} ":
                        weight *= 1.5
                    
                    total_score += weight
            
            # Normalize by total possible score for this category
            max_possible_score = sum(self.phrase_weights.get(kw, 1.0) for kw in keywords)
            normalized_score = total_score / max_possible_score if max_possible_score > 0 else 0.0
            
            scores[clause_type] = normalized_score
        
        # Sort by score descending
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores
    
    def get_regulatory_clause_type(self, cuad_clause_type: str) -> str:
        """
        Get the regulatory clause type for a CUAD clause type.
        
        This maps CUAD-specific clause types (e.g., "Non-Compete", "Audit Rights")
        to the original 7 regulatory clause types that have requirements defined
        in the knowledge base (e.g., "Data Processing", "Security Safeguards").
        
        Args:
            cuad_clause_type: The CUAD clause type from classification
            
        Returns:
            The corresponding regulatory clause type, or the original type if it's
            already a regulatory type, or the original type if no mapping exists.
        """
        # If it's already one of the original 7 types, return as-is
        original_types = {
            "Data Processing",
            "Sub-processor Authorization", 
            "Data Subject Rights",
            "Breach Notification",
            "Data Transfer",
            "Security Safeguards",
            "Permitted Uses and Disclosures"
        }
        
        if cuad_clause_type in original_types:
            return cuad_clause_type
        
        # Check if it's a CUAD type with a mapping
        mapped_type = self.cuad_to_regulatory_mapping.get(cuad_clause_type)
        
        if mapped_type is None:
            # Metadata type - no compliance requirements
            logger.debug(f"Clause type '{cuad_clause_type}' is metadata - no regulatory mapping")
            return None
        elif mapped_type:
            logger.debug(f"Mapped CUAD type '{cuad_clause_type}' -> '{mapped_type}'")
            return mapped_type
        else:
            # Unknown type - return as-is and let matching handle it
            logger.warning(f"No mapping found for clause type: {cuad_clause_type}")
            return cuad_clause_type
    
    def predict(self, text: str, top_k: int = 3) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        Predict clause type with confidence score.
        
        Args:
            text: Clause text to classify
            top_k: Number of alternative predictions to return
            
        Returns:
            Tuple of (predicted_type, confidence, alternatives)
            where alternatives is a list of (type, score) tuples
        """
        try:
            # If transformers not available or model failed to load, use keyword-based only
            if not TRANSFORMERS_AVAILABLE or self.model is None or self.tokenizer is None:
                logger.debug("Using keyword-based classification (transformers unavailable)")
                keyword_scores = self._keyword_based_classification(text)
                
                if not keyword_scores or keyword_scores[0][1] == 0.0:
                    predicted_type = "Other"
                    confidence = 0.5
                    alternatives = [("Other", 0.5)]
                else:
                    predicted_type = keyword_scores[0][0]
                    raw_score = keyword_scores[0][1]
                    confidence = min(0.95, 0.5 + (raw_score * 0.45))
                    alternatives = [(t, min(0.95, 0.5 + (s * 0.45))) 
                                   for t, s in keyword_scores[:top_k]]
                
                return predicted_type, confidence, alternatives
            
            # Use keyword-based classification
            # In a production system, this would use the actual LegalBERT model
            # for sequence classification. For now, we use keyword matching
            # as a practical implementation.
            
            keyword_scores = self._keyword_based_classification(text)
            
            if not keyword_scores or keyword_scores[0][1] == 0.0:
                # No matches found, classify as "Other"
                predicted_type = "Other"
                confidence = 0.5
                alternatives = [("Other", 0.5)]
            else:
                predicted_type = keyword_scores[0][0]
                # Scale confidence based on keyword match ratio
                raw_score = keyword_scores[0][1]
                confidence = min(0.95, 0.5 + (raw_score * 0.45))  # Scale to 0.5-0.95 range
                
                # Get top_k alternatives
                alternatives = [(t, min(0.95, 0.5 + (s * 0.45))) 
                               for t, s in keyword_scores[:top_k]]
            
            logger.info(f"Classified clause as '{predicted_type}' with confidence {confidence:.2f}")
            return predicted_type, confidence, alternatives
            
        except Exception as e:
            logger.error(f"Error in clause classification: {e}")
            # Return safe default
            return "Other", 0.5, [("Other", 0.5)]
    
    def get_embeddings(self, text: str) -> np.ndarray:
        """
        Generate embeddings for text using LegalBERT.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            if TRANSFORMERS_AVAILABLE and (self.model is None or self.tokenizer is None):
                self.model = self._load_model()
                self.tokenizer = self._load_tokenizer()
            if self.model is None or self.tokenizer is None:
                return np.zeros(768)

            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use [CLS] token embedding (first token)
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            logger.debug(f"Generated embeddings with shape: {embeddings.shape}")
            return embeddings[0]
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Return zero vector as fallback
            return np.zeros(768)  # BERT base dimension
