from typing import Any, Dict, List

from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    document_id: str = Field(min_length=1)
    frameworks: List[str] = Field(min_length=1)

    @field_validator("frameworks")
    @classmethod
    def validate_frameworks(cls, values: List[str]) -> List[str]:
        allowed = {"GDPR", "HIPAA", "CCPA", "SOX"}
        normalized = list(dict.fromkeys(value.strip().upper() for value in values))
        invalid = [value for value in normalized if value not in allowed]
        if invalid:
            raise ValueError(f"Unsupported framework(s): {', '.join(invalid)}")
        if not normalized:
            raise ValueError("At least one framework is required")
        return normalized


class AnalyzeResponse(BaseModel):
    report_id: str
    document_id: str
    analysis_results: List[Dict[str, Any]]
    report: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
