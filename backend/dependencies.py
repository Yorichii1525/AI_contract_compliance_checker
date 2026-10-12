"""Shared service dependencies and in-memory API state."""

from functools import lru_cache

@lru_cache(maxsize=1)
def get_document_processor():
    from services.document_processor import DocumentProcessor

    return DocumentProcessor()


@lru_cache(maxsize=1)
def get_nlp_analyzer():
    from services.nlp_analyzer import NLPAnalyzer

    return NLPAnalyzer()


@lru_cache(maxsize=1)
def get_compliance_checker():
    from services.compliance_checker import ComplianceChecker

    return ComplianceChecker()


@lru_cache(maxsize=1)
def get_recommendation_engine():
    from services.recommendation_engine import RecommendationEngine

    # Recommendation generation currently uses the existing non-LLM fallback.
    return RecommendationEngine(use_llama=False)
