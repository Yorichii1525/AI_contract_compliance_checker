"""FastAPI application entry point."""

from fastapi import FastAPI

from backend.api.routes import compliance, documents, health, reports

app = FastAPI(
    title="AI Contract Compliance Checker API",
    description="API for regulatory contract compliance analysis",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(documents.router, prefix="/api/v1")
app.include_router(compliance.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "AI Contract Compliance Checker API", "docs": "/docs"}
