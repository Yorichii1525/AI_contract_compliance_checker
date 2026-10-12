"""Compliance analysis endpoint backed by the existing service pipeline."""

import uuid

from fastapi import APIRouter, HTTPException, Request

from backend.dependencies import (
    get_compliance_checker,
    get_nlp_analyzer,
    get_recommendation_engine,
)
from backend.schemas.compliance import AnalyzeRequest, AnalyzeResponse

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_contract(payload: AnalyzeRequest, request: Request):
    documents = getattr(request.app.state, "documents", {})
    processed_document = documents.get(payload.document_id)
    if processed_document is None:
        raise HTTPException(status_code=404, detail="Document not found; upload it first")

    try:
        analyses = get_nlp_analyzer().analyze_clauses(processed_document.clauses)
        report = get_compliance_checker().check_compliance(
            analyses, payload.frameworks, processed_document.document_id
        )
        recommendations = get_recommendation_engine().generate_recommendations(report)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Compliance analysis failed") from exc

    report_id = str(uuid.uuid4())
    report_data = report.to_dict()
    recommendation_data = [item.to_dict() for item in recommendations]
    reports = getattr(request.app.state, "reports", None)
    if reports is None:
        reports = request.app.state.reports = {}
    reports[report_id] = {
        "report_id": report_id,
        "document_id": processed_document.document_id,
        "analysis_results": [
            {
                "clause_id": item.clause_id,
                "clause_text": item.clause_text,
                "clause_type": item.clause_type,
                "confidence_score": item.confidence_score,
                "alternative_types": item.alternative_types,
            }
            for item in analyses
        ],
        "report": report_data,
        "recommendations": recommendation_data,
    }
    return reports[report_id]
