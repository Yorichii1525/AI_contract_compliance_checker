"""
Semantic embedding generation service using Sentence Transformers.
"""
import streamlit as st
import numpy as np
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import sentence_transformers, make it optional
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except (ImportError, AttributeError) as e:
    logger.warning(f"sentence_transformers not available: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


class EmbeddingGenerator:
    """Generate semantic embeddings for clauses using Sentence Transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Sentence Transformer model name
        """
        self.model_name = model_name
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self.model = self._load_model()
        else:
            self.model = None
            logger.warning("EmbeddingGenerator running in fallback mode - embeddings will be zeros")
        self._embedding_cache: Dict[str, np.ndarray] = {}
    
    @st.cache_resource
    def _load_model(_self):
        """
        Load Sentence Transformer model with Streamlit caching.
        
        Returns:
            Loaded SentenceTransformer model
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("SentenceTransformer not available, returning None")
            return None
            
        try:
            logger.info(f"Loading Sentence Transformer model: {_self.model_name}")
            model = SentenceTransformer(_self.model_name)
            logger.info("Sentence Transformer model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Error loading Sentence Transformer model: {e}")
            logger.warning("Falling back to dummy embeddings")
            return None
    
    def generate_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Generate semantic embedding for a single text.
        
        Args:
            text: Text to embed
            use_cache: Whether to use cached embeddings
            
        Returns:
            Embedding vector as numpy array
        """
        # Fallback if model not available
        if not SENTENCE_TRANSFORMERS_AVAILABLE or self.model is None:
            logger.debug("Using fallback zero embedding")
            return np.zeros(384)  # all-MiniLM-L6-v2 dimension
            
        try:
            # Check cache first
            if use_cache and text in self._embedding_cache:
                logger.debug("Using cached embedding")
                return self._embedding_cache[text]
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Cache the result
            if use_cache:
                self._embedding_cache[text] = embedding
            
            logger.debug(f"Generated embedding with shape: {embedding.shape}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(384)  # all-MiniLM-L6-v2 dimension
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        use_cache: bool = True,
        batch_size: int = 32
    ) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cached embeddings
            batch_size: Batch size for encoding
            
        Returns:
            List of embedding vectors
        """
        # Fallback if model not available
        if not SENTENCE_TRANSFORMERS_AVAILABLE or self.model is None:
            logger.debug(f"Using fallback zero embeddings for {len(texts)} texts")
            return [np.zeros(384) for _ in texts]
            
        try:
            embeddings = []
            texts_to_encode = []
            text_indices = []
            
            # Check cache for each text
            for idx, text in enumerate(texts):
                if use_cache and text in self._embedding_cache:
                    embeddings.append(self._embedding_cache[text])
                else:
                    texts_to_encode.append(text)
                    text_indices.append(idx)
                    embeddings.append(None)  # Placeholder
            
            # Encode uncached texts in batch
            if texts_to_encode:
                logger.info(f"Encoding {len(texts_to_encode)} texts in batch")
                new_embeddings = self.model.encode(
                    texts_to_encode,
                    convert_to_numpy=True,
                    batch_size=batch_size,
                    show_progress_bar=len(texts_to_encode) > 10
                )
                
                # Update cache and results
                for idx, text, embedding in zip(text_indices, texts_to_encode, new_embeddings):
                    if use_cache:
                        self._embedding_cache[text] = embedding
                    embeddings[idx] = embedding
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            return [np.zeros(384) for _ in texts]
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Compute cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            # Ensure result is in [0, 1] range
            similarity = (similarity + 1) / 2
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0
    
    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar embeddings to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples sorted by similarity
        """
        try:
            similarities = []
            for idx, candidate in enumerate(candidate_embeddings):
                similarity = self.compute_similarity(query_embedding, candidate)
                similarities.append((idx, similarity))
            
            # Sort by similarity descending
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar embeddings: {e}")
            return []
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_size(self) -> int:
        """Get the number of cached embeddings."""
        return len(self._embedding_cache)
