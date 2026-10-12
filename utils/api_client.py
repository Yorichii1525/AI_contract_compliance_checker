"""Streamlit client helpers for the FastAPI backend."""

import os
from typing import Any, Dict, List, Tuple

import requests

from models.clause import Clause
from models.clause_analysis import ClauseAnalysis
from models.processed_document import ProcessedDocument
from models.recommendation import ActionType, Recommendation
from models.regulatory_requirement import (
    ClauseComplianceResult,
    ComplianceReport,
    ComplianceStatus,
    ComplianceSummary,
    RegulatoryRequirement,
    RiskLevel,
)

API_BASE_URL = os.getenv("COMPLIANCE_API_URL", "http://127.0.0.1:8000")


def upload_contract(file_name: str, content: bytes, content_type: str = "application/octet-stream") -> Dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/documents/upload",
        files={"file": (file_name, content, content_type)},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def upload_contract_text(text: str, file_name: str = "Pasted_Contract.txt") -> Dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/documents/text",
        json={"text": text, "filename": file_name},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def analyze_contract(document_id: str, frameworks: List[str]) -> Dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/v1/compliance/analyze",
        json={"document_id": document_id, "frameworks": frameworks},
        timeout=900,
    )
    response.raise_for_status()
    return response.json()


def analyze_processed_document(
    processed_document: ProcessedDocument,
    document_id: str | None,
    frameworks: List[str],
) -> Tuple[Dict[str, Any], str]:
    """Register an in-session document if needed, then analyze it."""
    if not document_id:
        upload = upload_contract_text(
            processed_document.extracted_text,
            processed_document.original_filename,
        )
        document_id = upload["document_id"]

    try:
        return analyze_contract(document_id, frameworks), document_id
    except requests.HTTPError as exc:
        if exc.response is None or exc.response.status_code != 404:
            raise

    # FastAPI keeps documents in memory; a restart clears that registry.
    upload = upload_contract_text(
        processed_document.extracted_text,
        processed_document.original_filename,
    )
    document_id = upload["document_id"]
    return analyze_contract(document_id, frameworks), document_id


def document_from_api(data: Dict[str, Any]) -> ProcessedDocument:
    clauses = [
        Clause(
            clause_id=item["clause_id"],
            text=item["text"],
            start_position=item["start_position"],
            end_position=item["end_position"],
            section_number=item.get("section_number"),
            heading=item.get("heading"),
        )
        for item in data.get("clauses", [])
    ]
    return ProcessedDocument(
        document_id=data["document_id"],
        original_filename=data["original_filename"],
        extracted_text=data["extracted_text"],
        clauses=clauses,
        metadata=data.get("metadata", {}),
        processing_time=data.get("processing_time", 0.0),
    )


def _requirement(data: Dict[str, Any]) -> RegulatoryRequirement:
    return RegulatoryRequirement(
        requirement_id=data["requirement_id"],
        framework=data["framework"],
        article_reference=data["article_reference"],
        clause_type=data["clause_type"],
        description=data["description"],
        mandatory=data["mandatory"],
        keywords=data.get("keywords", []),
        mandatory_elements=data.get("mandatory_elements", []),
        risk_level=RiskLevel(data.get("risk_level", "Medium")),
    )


def analysis_from_api(items: List[Dict[str, Any]]) -> List[ClauseAnalysis]:
    return [
        ClauseAnalysis(
            clause_id=item["clause_id"],
            clause_text=item["clause_text"],
            clause_type=item["clause_type"],
            confidence_score=item["confidence_score"],
            alternative_types=[tuple(value) for value in item.get("alternative_types", [])],
        )
        for item in items
    ]


def report_from_api(data: Dict[str, Any]) -> ComplianceReport:
    def result(item: Dict[str, Any]) -> ClauseComplianceResult:
        return ClauseComplianceResult(
            clause_id=item["clause_id"],
            clause_text=item["clause_text"],
            clause_type=item["clause_type"],
            framework=item["framework"],
            compliance_status=ComplianceStatus(item["compliance_status"]),
            risk_level=RiskLevel(item["risk_level"]),
            matched_requirements=[_requirement(req) for req in item.get("matched_requirements", [])],
            confidence=item.get("confidence", 0.0),
            issues=item.get("issues", []),
        )

    summary_data = data.get("summary")
    summary = ComplianceSummary(**summary_data) if summary_data else None
    return ComplianceReport(
        document_id=data["document_id"],
        frameworks_checked=data["frameworks_checked"],
        overall_score=data["overall_score"],
        clause_results=[result(item) for item in data.get("clause_results", [])],
        missing_requirements=[_requirement(item) for item in data.get("missing_requirements", [])],
        high_risk_items=[result(item) for item in data.get("high_risk_items", [])],
        summary=summary,
    )


def recommendations_from_api(items: List[Dict[str, Any]]) -> List[Recommendation]:
    return [
        Recommendation(
            recommendation_id=item["recommendation_id"],
            clause_id=item.get("clause_id"),
            requirement=_requirement(item["requirement"]),
            priority=item["priority"],
            action_type=ActionType(item["action_type"]),
            description=item["description"],
            rationale=item["rationale"],
            regulatory_reference=item["regulatory_reference"],
            suggested_text=item.get("suggested_text"),
            confidence=item.get("confidence", 0.8),
            estimated_risk_reduction=item.get("estimated_risk_reduction"),
        )
        for item in items
    ]


def result_from_api(data: Dict[str, Any]) -> Tuple[List[ClauseAnalysis], ComplianceReport, List[Recommendation]]:
    return (
        analysis_from_api(data.get("analysis_results", [])),
        report_from_api(data["report"]),
        recommendations_from_api(data.get("recommendations", [])),
    )
