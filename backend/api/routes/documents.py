"""Document upload and extraction endpoints."""

import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

from backend.dependencies import get_document_processor

router = APIRouter(prefix="/documents", tags=["Documents"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".txt", ".docx"}


class TextUpload(BaseModel):
    text: str = Field(min_length=50)
    filename: str = "Pasted_Contract.txt"


def _store_document(request: Request, processed):
    documents = getattr(request.app.state, "documents", None)
    if documents is None:
        documents = request.app.state.documents = {}
    documents[processed.document_id] = processed
    return {
        "document_id": processed.document_id,
        "filename": processed.original_filename,
        "num_clauses": processed.num_clauses,
        "total_words": processed.total_words,
        "processing_time": processed.processing_time,
        "metadata": processed.metadata,
        "document": processed.to_dict(),
    }


@router.post("/upload", status_code=201)
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Extract and segment an uploaded contract for a later analysis request."""
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Unsupported file type")

    temp_path = None
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds the 10 MB upload limit")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        from services.document_processor import DocumentProcessingError

        try:
            processed = get_document_processor().process_document(temp_path)
        except (DocumentProcessingError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        processed.original_filename = filename

        return _store_document(request, processed)
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/text", status_code=201)
def upload_text(payload: TextUpload, request: Request):
    """Process pasted or externally imported contract text."""
    from services.document_processor import DocumentProcessingError

    try:
        processed = get_document_processor().process_text(
            payload.text, filename=Path(payload.filename).name
        )
    except (DocumentProcessingError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _store_document(request, processed)
