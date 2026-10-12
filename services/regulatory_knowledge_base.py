"""
Regulatory Knowledge Base service.
Manages regulatory requirements and provides semantic similarity matching.
"""
from typing import List, Dict, Tuple, Optional
import numpy as np
import json
from pathlib import Path
from functools import lru_cache

from models.regulatory_requirement import RegulatoryRequirement
from models.clause_analysis import ClauseAnalysis
from data.gdpr_requirements import get_gdpr_requirements
from data.hipaa_requirements import get_hipaa_requirements
from data.ccpa_requirements import get_ccpa_requirements
from data.sox_requirements import get_sox_requirements
from services.embedding_generator import EmbeddingGenerator
from utils.logger import get_logger

logger = get_logger(__name__)


class RegulatoryKnowledgeBase:
    """
    Manages regulatory requirements and provides semantic matching capabilities.
    Supports GDPR, HIPAA, CCPA, and SOX frameworks.
    """
    
    def __init__(
        self,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        similarity_threshold: float = 0.20
    ):
        """
        Initialize Regulatory Knowledge Base.
        
        Args:
            embedding_generator: Embedding generator for semantic matching
            similarity_threshold: Minimum similarity score for matching (default 0.20)
        """
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        self.similarity_threshold = similarity_threshold
        
        logger.info(f"Regulatory Knowledge Base initialized with similarity threshold: {similarity_threshold}")
        
        # Load requirements for all frameworks using curated Python modules
        # Note: data/regulatory_requirements.json contains raw articles that are too
        # broad for contract compliance checking. The Python modules contain curated,
        # contract-specific requirements that produce accurate results.
        logger.info("Loading curated regulatory requirements from Python modules...")
        self.gdpr_requirements = get_gdpr_requirements()
        self.hipaa_requirements = get_hipaa_requirements()
        self.ccpa_requirements = get_ccpa_requirements()
        self.sox_requirements = get_sox_requirements()
        
        # Create framework mapping
        self.framework_requirements = {
            'GDPR': self.gdpr_requirements,
            'HIPAA': self.hipaa_requirements,
            'CCPA': self.ccpa_requirements,
            'SOX': self.sox_requirements
        }
        
        # Cache for requirement embeddings
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
        logger.info(
            f"Regulatory Knowledge Base initialized with "
            f"{len(self.gdpr_requirements)} GDPR, "
            f"{len(self.hipaa_requirements)} HIPAA, "
            f"{len(self.ccpa_requirements)} CCPA, "
            f"{len(self.sox_requirements)} SOX requirements"
        )
    
    def _load_from_json(self, json_path: Path) -> Dict[str, List[RegulatoryRequirement]]:
        """Load requirements from JSON file and convert to RegulatoryRequirement objects"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            result = {}
            frameworks = data.get('frameworks', {})
            
            for framework, framework_data in frameworks.items():
                requirements_data = framework_data.get('requirements', [])
                requirements = []
                
                for req_data in requirements_data:
                    # Map risk level string to RiskLevel enum
                    risk_level_str = req_data.get('risk_level', 'Medium')
                    if risk_level_str == 'Critical':
                        risk_level_str = 'High'  # Map Critical to High
                    
                    from models.regulatory_requirement import RiskLevel
                    try:
                        risk_level = RiskLevel[risk_level_str.upper()]
                    except (KeyError, AttributeError):
                        risk_level = RiskLevel.MEDIUM
                    
                    # Convert JSON dict to RegulatoryRequirement object
                    req = RegulatoryRequirement(
                        requirement_id=req_data.get('requirement_id', ''),
                        framework=req_data.get('framework', framework),
                        article_reference=req_data.get('article_number', req_data.get('article_reference', '')),
                        clause_type=req_data.get('clause_type', 'General'),
                        description=req_data.get('description', req_data.get('title', '')),
                        mandatory=req_data.get('is_mandatory', req_data.get('mandatory', False)),
                        keywords=req_data.get('tags', []),
                        risk_level=risk_level,
                        mandatory_elements=[]
                    )
                    requirements.append(req)
                
                result[framework] = requirements
                logger.info(f"Loaded {len(requirements)} {framework} requirements from JSON")
            
            return result
            
        except Exception as e:
            logger.error(f"Error loading requirements from JSON: {e}")
            return {}
    
    def get_requirements(self, framework: str) -> List[RegulatoryRequirement]:
        """
        Get all requirements for a specific framework.
        
        Args:
            framework: Framework name (GDPR, HIPAA, CCPA, SOX)
            
        Returns:
            List of regulatory requirements
        """
        framework_upper = framework.upper()
        if framework_upper not in self.framework_requirements:
            logger.warning(f"Unknown framework: {framework}")
            return []
        
        requirements = self.framework_requirements[framework_upper]
        logger.debug(f"Retrieved {len(requirements)} requirements for {framework_upper}")
        return requirements
    
    def get_all_requirements(self) -> List[RegulatoryRequirement]:
        """
        Get all requirements across all frameworks.
        
        Returns:
            List of all regulatory requirements
        """
        all_reqs = []
        for reqs in self.framework_requirements.values():
            all_reqs.extend(reqs)
        
        logger.debug(f"Retrieved {len(all_reqs)} total requirements")
        return all_reqs
    
    def get_requirements_by_clause_type(
        self,
        clause_type: str,
        framework: Optional[str] = None
    ) -> List[RegulatoryRequirement]:
        """
        Get requirements filtered by clause type.
        
        Args:
            clause_type: Type of clause to filter by
            framework: Optional framework to filter by
            
        Returns:
            List of matching requirements
        """
        if framework:
            requirements = self.get_requirements(framework)
        else:
            requirements = self.get_all_requirements()
        
        # Use case-insensitive matching with whitespace normalization
        clause_type_normalized = clause_type.strip().lower()
        filtered = [
            req for req in requirements 
            if req.clause_type.strip().lower() == clause_type_normalized
        ]
        logger.debug(
            f"Found {len(filtered)} requirements for clause type '{clause_type}'"
            f"{' in ' + framework if framework else ''}"
        )
        return filtered
    
    def get_requirement_embedding(
        self,
        requirement: RegulatoryRequirement,
        use_cache: bool = True
    ) -> np.ndarray:
        """
        Get or generate embedding for a requirement.
        
        Args:
            requirement: Regulatory requirement
            use_cache: Whether to use cached embeddings
            
        Returns:
            Embedding vector
        """
        # Check if requirement already has embedding
        if requirement.embeddings is not None:
            return requirement.embeddings
        
        # Check cache
        if use_cache and requirement.requirement_id in self._embedding_cache:
            logger.debug(f"Using cached embedding for {requirement.requirement_id}")
            return self._embedding_cache[requirement.requirement_id]
        
        # Generate embedding from description and keywords
        text = f"{requirement.description} {' '.join(requirement.keywords)}"
        embedding = self.embedding_generator.generate_embedding(text)
        
        # Cache the embedding
        if use_cache:
            self._embedding_cache[requirement.requirement_id] = embedding
            logger.debug(f"Cached embedding for {requirement.requirement_id}")
        
        # Also store in requirement object
        requirement.embeddings = embedding
        
        return embedding
    
    def precompute_embeddings(self, frameworks: Optional[List[str]] = None):
        """
        Precompute embeddings for all requirements to improve performance.
        
        Args:
            frameworks: Optional list of frameworks to precompute (default: all)
        """
        logger.info("Precomputing requirement embeddings...")
        
        if frameworks:
            requirements = []
            for framework in frameworks:
                requirements.extend(self.get_requirements(framework))
        else:
            requirements = self.get_all_requirements()
        
        # Generate embeddings in batch
        texts = [
            f"{req.description} {' '.join(req.keywords)}"
            for req in requirements
        ]
        
        try:
            embeddings = self.embedding_generator.generate_embeddings_batch(
                texts,
                use_cache=True
            )
            
            # Store embeddings
            for req, embedding in zip(requirements, embeddings):
                req.embeddings = embedding
                self._embedding_cache[req.requirement_id] = embedding
            
            logger.info(f"Precomputed {len(embeddings)} requirement embeddings")
            
        except Exception as e:
            logger.error(f"Error precomputing embeddings: {e}")
            # Fallback to individual generation
            for req in requirements:
                try:
                    self.get_requirement_embedding(req, use_cache=True)
                except Exception as emb_error:
                    logger.error(
                        f"Error generating embedding for {req.requirement_id}: {emb_error}"
                    )
    
    def match_clause_to_requirements(
        self,
        clause_analysis: ClauseAnalysis,
        framework: str,
        top_k: int = 3
    ) -> List[Tuple[RegulatoryRequirement, float]]:
        """
        Find matching requirements for a clause using semantic similarity.
        
        Args:
            clause_analysis: Analyzed clause with embeddings
            framework: Framework to match against
            top_k: Number of top matches to return
            
        Returns:
            List of (requirement, similarity_score) tuples, sorted by score
        """
        try:
            logger.info(
                f"Matching clause {clause_analysis.clause_id} (type: {clause_analysis.clause_type}) "
                f"to {framework} requirements..."
            )
            
            # First try to get requirements for framework and clause type
            requirements = self.get_requirements_by_clause_type(
                clause_analysis.clause_type,
                framework
            )
            
            # If no requirements found for specific clause type, fall back to all framework requirements
            if not requirements:
                logger.info(
                    f"No requirements found for {framework} / {clause_analysis.clause_type}, "
                    f"searching all {framework} requirements. "
                    f"Available clause types: {self._get_available_clause_types(framework)}"
                )
                requirements = self.get_requirements(framework)
                
            if not requirements:
                logger.warning(
                    f"\u274c No requirements found for {framework}"
                )
                return []
            
            logger.info(f"Found {len(requirements)} requirements to match against")
            
            # Check if clause has embeddings
            if clause_analysis.embeddings is None:
                logger.warning(f"\u274c Clause {clause_analysis.clause_id} has no embeddings")
                return []
            
            # Calculate similarity scores
            all_similarities = []
            matches = []
            for req in requirements:
                try:
                    req_embedding = self.get_requirement_embedding(req)
                    similarity = self._cosine_similarity(
                        clause_analysis.embeddings,
                        req_embedding
                    )
                    
                    all_similarities.append((req.requirement_id, similarity))
                    
                    # Only include matches above threshold
                    if similarity >= self.similarity_threshold:
                        matches.append((req, similarity))
                        logger.info(f"\u2713 Match found: {req.requirement_id} with similarity {similarity:.4f}")
                    else:
                        logger.debug(f"\u2717 Below threshold: {req.requirement_id} with similarity {similarity:.4f}")
                        
                except Exception as e:
                    logger.error(
                        f"Error calculating similarity for {req.requirement_id}: {e}"
                    )
                    continue
            
            # Log statistics
            if all_similarities:
                max_sim = max(s[1] for s in all_similarities)
                avg_sim = sum(s[1] for s in all_similarities) / len(all_similarities)
                logger.info(
                    f"Similarity stats - Max: {max_sim:.4f}, Avg: {avg_sim:.4f}, "
                    f"Threshold: {self.similarity_threshold:.4f}, Matches: {len(matches)}/{len(requirements)}"
                )
                
                # Fallback to keyword matching when embeddings produce zero similarity
                # (happens when embedding model falls back to zero vectors)
                if len(matches) == 0 and max_sim == 0.0:
                    logger.warning(
                        "Zero-vector embeddings detected. Using keyword-based matching fallback."
                    )
                    clause_text_lower = (clause_analysis.clause_text or '').lower()
                    for req in requirements:
                        if not req.keywords:
                            continue
                        keyword_hits = sum(
                            1 for kw in req.keywords
                            if kw.lower() in clause_text_lower
                        )
                        if keyword_hits > 0:
                            keyword_score = min(keyword_hits / max(len(req.keywords), 1), 1.0)
                            if keyword_score >= 0.15:
                                matches.append((req, keyword_score))
                                logger.info(
                                    f"Keyword match: {req.requirement_id} with score {keyword_score:.4f} "
                                    f"({keyword_hits}/{len(req.keywords)} keywords)"
                                )
                elif len(matches) == 0:
                    logger.warning(
                        f"No matches above threshold! Best similarity was {max_sim:.4f}. "
                        f"Consider lowering threshold from {self.similarity_threshold:.4f}"
                    )
            
            # Sort by similarity score (descending) and return top_k
            matches.sort(key=lambda x: x[1], reverse=True)
            top_matches = matches[:top_k]
            
            logger.info(
                f"Returning {len(top_matches)} top matches for clause {clause_analysis.clause_id} "
                f"in {framework}"
            )
            
            return top_matches
            
        except Exception as e:
            logger.error(f"Error matching clause to requirements: {e}")
            return []
    
    def find_missing_requirements(
        self,
        analyzed_clauses: List[ClauseAnalysis],
        framework: str
    ) -> List[RegulatoryRequirement]:
        """
        Identify mandatory requirements that are not covered by any clause.
        
        Args:
            analyzed_clauses: List of analyzed clauses
            framework: Framework to check
            
        Returns:
            List of missing mandatory requirements
        """
        try:
            # Get all mandatory requirements for framework
            all_requirements = self.get_requirements(framework)
            mandatory_requirements = [req for req in all_requirements if req.mandatory]
            
            # Track which requirements are covered
            covered_requirement_ids = set()
            
            # Check each clause against requirements
            for clause in analyzed_clauses:
                matches = self.match_clause_to_requirements(
                    clause,
                    framework,
                    top_k=5  # Check more matches to ensure coverage
                )
                
                for req, score in matches:
                    covered_requirement_ids.add(req.requirement_id)
            
            # Find missing requirements
            missing = [
                req for req in mandatory_requirements
                if req.requirement_id not in covered_requirement_ids
            ]
            
            logger.info(
                f"Found {len(missing)} missing mandatory requirements for {framework}"
            )
            
            return missing
            
        except Exception as e:
            logger.error(f"Error finding missing requirements: {e}")
            return []
    
    def get_requirement_by_id(
        self,
        requirement_id: str
    ) -> Optional[RegulatoryRequirement]:
        """
        Get a specific requirement by ID.
        
        Args:
            requirement_id: Requirement ID to find
            
        Returns:
            RegulatoryRequirement if found, None otherwise
        """
        all_reqs = self.get_all_requirements()
        for req in all_reqs:
            if req.requirement_id == requirement_id:
                return req
        
        logger.warning(f"Requirement not found: {requirement_id}")
        return None
    
    def search_requirements_by_keyword(
        self,
        keyword: str,
        framework: Optional[str] = None
    ) -> List[RegulatoryRequirement]:
        """
        Search requirements by keyword.
        
        Args:
            keyword: Keyword to search for
            framework: Optional framework to filter by
            
        Returns:
            List of matching requirements
        """
        if framework:
            requirements = self.get_requirements(framework)
        else:
            requirements = self.get_all_requirements()
        
        keyword_lower = keyword.lower()
        matches = []
        
        for req in requirements:
            # Search in keywords, description, and article reference
            if (keyword_lower in ' '.join(req.keywords).lower() or
                keyword_lower in req.description.lower() or
                keyword_lower in req.article_reference.lower()):
                matches.append(req)
        
        logger.debug(f"Found {len(matches)} requirements matching keyword '{keyword}'")
        return matches
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_requirements': len(self.get_all_requirements()),
            'frameworks': {}
        }
        
        for framework in self.framework_requirements.keys():
            reqs = self.get_requirements(framework)
            mandatory_count = sum(1 for req in reqs if req.mandatory)
            
            stats['frameworks'][framework] = {
                'total': len(reqs),
                'mandatory': mandatory_count,
                'optional': len(reqs) - mandatory_count
            }
        
        stats['cached_embeddings'] = len(self._embedding_cache)
        
        return stats
    
    def _get_available_clause_types(self, framework: str) -> List[str]:
        """
        Get list of available clause types for a framework.
        
        Args:
            framework: Framework name
            
        Returns:
            List of unique clause types
        """
        requirements = self.get_requirements(framework)
        clause_types = list(set(req.clause_type for req in requirements))
        return sorted(clause_types)
    
    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Normalize vectors
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-10)
        
        # Calculate cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)
        
        # Ensure result is in [0, 1] range
        return float(max(0.0, min(1.0, similarity)))
    
    def set_similarity_threshold(self, threshold: float):
        """
        Update the similarity threshold.
        
        Args:
            threshold: New similarity threshold (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        
        self.similarity_threshold = threshold
        logger.info(f"Similarity threshold updated to {threshold}")
    
    def clear_embedding_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")
