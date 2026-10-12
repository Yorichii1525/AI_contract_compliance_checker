"""Report retrieval endpoint."""

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{report_id}")
def get_report(report_id: str, request: Request):
    report = getattr(request.app.state, "reports", {}).get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
