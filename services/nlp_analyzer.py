"""
NLP Analyzer orchestrator that coordinates clause classification and embedding generation.
"""
from typing import List, Optional
from models.clause import Clause
from models.clause_analysis import ClauseAnalysis
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import transformers-based services, but make them optional
try:
    from services.legal_bert_classifier import LegalBERTClassifier
    from services.embedding_generator import EmbeddingGenerator
    TRANSFORMERS_AVAILABLE = True
except (ImportError, AttributeError) as e:
    logger.warning(f"Transformers library not available or incompatible: {e}")
    logger.warning("NLP analysis will use fallback mode")
    TRANSFORMERS_AVAILABLE = False
    LegalBERTClassifier = None
    EmbeddingGenerator = None


class NLPAnalyzer:
    """
    Main NLP analysis orchestrator that coordinates classification and embedding.
    Handles batch processing and error handling for clause analysis.
    """
    
    def __init__(
        self,
        classifier: Optional[object] = None,
        embedding_generator: Optional[object] = None,
        confidence_threshold: float = 0.75
    ):
        """
        Initialize NLP Analyzer.
        
        Args:
            classifier: LegalBERT classifier instance (creates new if None)
            embedding_generator: Embedding generator instance (creates new if None)
            confidence_threshold: Minimum confidence for predictions (default 0.75)
        """
        if TRANSFORMERS_AVAILABLE:
            self.classifier = classifier or LegalBERTClassifier()
            self.embedding_generator = embedding_generator or EmbeddingGenerator()
        else:
            self.classifier = None
            self.embedding_generator = None
            logger.warning("Running in fallback mode - transformers library not available")
        self.confidence_threshold = confidence_threshold
        logger.info(f"NLPAnalyzer initialized with confidence threshold: {confidence_threshold}")
    
    def analyze_clause(self, clause: Clause) -> ClauseAnalysis:
        """
        Analyze a single clause with classification and embedding.
        
        Args:
            clause: Clause to analyze
            
        Returns:
            ClauseAnalysis with classification and embedding results
        """
        try:
            logger.debug(f"Analyzing clause: {clause.clause_id}")
            
            # Fallback mode if transformers not available
            if not TRANSFORMERS_AVAILABLE or not self.classifier or not self.embedding_generator:
                logger.warning(f"Using fallback analysis for clause {clause.clause_id}")
                return ClauseAnalysis(
                    clause_id=clause.clause_id,
                    predicted_type="general",
                    confidence=0.5,
                    alternative_predictions=[],
                    embedding=[0.0] * 384,  # Empty embedding
                    analysis_metadata={
                        "method": "fallback",
                        "reason": "transformers_unavailable"
                    }
                )
            
            # Classify clause type
            clause_type, confidence, alternatives = self.classifier.predict(clause.text)
            
            # Map CUAD types to regulatory types for compliance scoring
            regulatory_type = self.classifier.get_regulatory_clause_type(clause_type)
            
            # If no regulatory mapping (metadata type), use original type
            final_clause_type = regulatory_type if regulatory_type is not None else clause_type
            
            # Log mapping if different
            if clause_type != final_clause_type:
                logger.debug(
                    f"Clause {clause.clause_id}: CUAD type '{clause_type}' "
                    f"mapped to regulatory type '{final_clause_type}' for compliance scoring"
                )
            
            # Generate embedding
            embedding = self.embedding_generator.generate_embedding(clause.text)
            
            # Check if confidence is below threshold
            if confidence < self.confidence_threshold:
                logger.warning(
                    f"Low confidence ({confidence:.2f}) for clause {clause.clause_id}. "
                    f"Classified as '{clause_type}'. Consider manual review."
                )
            
            # Create analysis result with regulatory type for matching
            analysis = ClauseAnalysis(
                clause_id=clause.clause_id,
                clause_text=clause.text,
                clause_type=final_clause_type,  # Use regulatory type for matching
                confidence_score=confidence,
                embeddings=embedding,
                alternative_types=alternatives
            )
            
            logger.info(
                f"Clause {clause.clause_id} analyzed: original_type='{clause_type}', "
                f"regulatory_type='{final_clause_type}', confidence={confidence:.2f}"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing clause {clause.clause_id}: {e}")
            # Return safe default analysis
            return self._create_fallback_analysis(clause, str(e))
    
    def analyze_clauses(
        self,
        clauses: List[Clause],
        batch_size: int = 32
    ) -> List[ClauseAnalysis]:
        """
        Analyze multiple clauses with batch processing for efficiency.
        
        Args:
            clauses: List of clauses to analyze
            batch_size: Batch size for embedding generation
            
        Returns:
            List of ClauseAnalysis results
        """
        try:
            logger.info(f"Starting batch analysis of {len(clauses)} clauses")
            
            if not clauses:
                logger.warning("No clauses provided for analysis")
                return []
            
            analyses = []
            
            # Step 1: Classify all clauses
            logger.info("Step 1: Classifying clauses...")
            classifications = []
            for clause in clauses:
                try:
                    clause_type, confidence, alternatives = self.classifier.predict(clause.text)
                    classifications.append((clause_type, confidence, alternatives))
                    
                    # Log low confidence predictions
                    if confidence < self.confidence_threshold:
                        logger.warning(
                            f"Low confidence ({confidence:.2f}) for clause {clause.clause_id}"
                        )
                except Exception as e:
                    logger.error(f"Error classifying clause {clause.clause_id}: {e}")
                    classifications.append(("Other", 0.5, [("Other", 0.5)]))
            
            # Step 2: Generate embeddings in batch
            logger.info("Step 2: Generating embeddings in batch...")
            clause_texts = [clause.text for clause in clauses]
            try:
                embeddings = self.embedding_generator.generate_embeddings_batch(
                    clause_texts,
                    use_cache=True,
                    batch_size=batch_size
                )
            except Exception as e:
                logger.error(f"Error in batch embedding generation: {e}")
                # Fallback to individual embedding generation
                embeddings = []
                for clause in clauses:
                    try:
                        emb = self.embedding_generator.generate_embedding(clause.text)
                        embeddings.append(emb)
                    except Exception as emb_error:
                        logger.error(f"Error generating embedding for {clause.clause_id}: {emb_error}")
                        embeddings.append(None)
            
            # Step 3: Combine results into ClauseAnalysis objects
            logger.info("Step 3: Combining results...")
            for clause, (clause_type, confidence, alternatives), embedding in zip(
                clauses, classifications, embeddings
            ):
                try:
                    # Map CUAD types to regulatory types for compliance scoring
                    regulatory_type = self.classifier.get_regulatory_clause_type(clause_type)
                    
                    # If no regulatory mapping (metadata type), use original type
                    final_clause_type = regulatory_type if regulatory_type is not None else clause_type
                    
                    # Log mapping if different
                    if clause_type != final_clause_type:
                        logger.debug(
                            f"Clause {clause.clause_id}: CUAD type '{clause_type}' "
                            f"mapped to regulatory type '{final_clause_type}'"
                        )
                    
                    analysis = ClauseAnalysis(
                        clause_id=clause.clause_id,
                        clause_text=clause.text,
                        clause_type=final_clause_type,  # Use regulatory type for matching
                        confidence_score=confidence,
                        embeddings=embedding,
                        alternative_types=alternatives
                    )
                    analyses.append(analysis)
                except Exception as e:
                    logger.error(f"Error creating analysis for clause {clause.clause_id}: {e}")
                    analyses.append(self._create_fallback_analysis(clause, str(e)))
            
            # Log summary statistics
            low_confidence_count = sum(
                1 for a in analyses if a.confidence_score < self.confidence_threshold
            )
            logger.info(
                f"Batch analysis complete: {len(analyses)} clauses analyzed, "
                f"{low_confidence_count} with low confidence"
            )
            
            return analyses
            
        except Exception as e:
            logger.error(f"Critical error in batch analysis: {e}")
            # Return fallback analyses for all clauses
            return [self._create_fallback_analysis(clause, str(e)) for clause in clauses]
    
    def get_low_confidence_clauses(
        self,
        analyses: List[ClauseAnalysis]
    ) -> List[ClauseAnalysis]:
        """
        Filter clauses with confidence below threshold.
        
        Args:
            analyses: List of clause analyses
            
        Returns:
            List of analyses with low confidence scores
        """
        low_confidence = [
            a for a in analyses 
            if a.confidence_score < self.confidence_threshold
        ]
        logger.info(
            f"Found {len(low_confidence)} clauses with confidence below "
            f"{self.confidence_threshold}"
        )
        return low_confidence
    
    def get_clauses_by_type(
        self,
        analyses: List[ClauseAnalysis],
        clause_type: str
    ) -> List[ClauseAnalysis]:
        """
        Filter clauses by type.
        
        Args:
            analyses: List of clause analyses
            clause_type: Clause type to filter by
            
        Returns:
            List of analyses matching the specified type
        """
        filtered = [a for a in analyses if a.clause_type == clause_type]
        logger.info(f"Found {len(filtered)} clauses of type '{clause_type}'")
        return filtered
    
    def _create_fallback_analysis(self, clause: Clause, error_msg: str) -> ClauseAnalysis:
        """
        Create a fallback analysis when processing fails.
        
        Args:
            clause: Original clause
            error_msg: Error message
            
        Returns:
            ClauseAnalysis with safe default values
        """
        logger.warning(f"Creating fallback analysis for clause {clause.clause_id}: {error_msg}")
        return ClauseAnalysis(
            clause_id=clause.clause_id,
            clause_text=clause.text,
            clause_type="Other",
            confidence_score=0.0,
            embeddings=None,
            alternative_types=[("Other", 0.0)]
        )
    
    def set_confidence_threshold(self, threshold: float):
        """
        Update the confidence threshold.
        
        Args:
            threshold: New confidence threshold (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        
        self.confidence_threshold = threshold
        logger.info(f"Confidence threshold updated to {threshold}")
    
    def get_analysis_summary(self, analyses: List[ClauseAnalysis]) -> dict:
        """
        Get summary statistics for a list of analyses.
        
        Args:
            analyses: List of clause analyses
            
        Returns:
            Dictionary with summary statistics
        """
        if not analyses:
            return {
                "total_clauses": 0,
                "avg_confidence": 0.0,
                "low_confidence_count": 0,
                "clause_type_distribution": {}
            }
        
        # Calculate statistics
        total = len(analyses)
        avg_confidence = sum(a.confidence_score for a in analyses) / total
        low_confidence_count = sum(
            1 for a in analyses if a.confidence_score < self.confidence_threshold
        )
        
        # Count clause types
        type_distribution = {}
        for analysis in analyses:
            clause_type = analysis.clause_type
            type_distribution[clause_type] = type_distribution.get(clause_type, 0) + 1
        
        summary = {
            "total_clauses": total,
            "avg_confidence": round(avg_confidence, 3),
            "low_confidence_count": low_confidence_count,
            "clause_type_distribution": type_distribution
        }
        
        logger.info(f"Analysis summary: {summary}")
        return summary
