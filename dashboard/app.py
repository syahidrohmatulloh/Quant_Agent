"""
Phase 14 dashboard FastAPI application factory.
Local-only by default. No auth required (read-only research dashboard).
"""
from fastapi import FastAPI
from dashboard.routes import router as phase14_router


def create_phase14_app() -> FastAPI:
    app = FastAPI(
        title="Quant_Agent Local Dashboard",
        description="Local research dashboard for Quant_Agent. Paper-only. Data-only.",
        version="14.0.0",
    )
    app.include_router(phase14_router)
    return app


# Standalone app instance for uvicorn
app = create_phase14_app()
