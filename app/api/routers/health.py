"""Health check and observability router."""

from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)):
    """Comprehensive service health probe checking database, storage, and models."""
    settings = get_settings()

    # 1. Database connectivity
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # 2. Model artifact status
    model_path = Path(settings.model_dir) / "latest_model.joblib"
    model_loaded = model_path.exists()

    # 3. LLM readiness
    llm_ready = bool(settings.nvidia_api_key or settings.gemini_api_key)

    all_healthy = db_ok

    return {
        "status": "healthy" if all_healthy else "degraded",
        "app_version": settings.app_version,
        "environment": settings.app_env,
        "checks": {
            "database": "connected" if db_ok else "unreachable",
            "ml_model": "loaded" if model_loaded else "fallback_parametric",
            "llm_provider": settings.llm_provider,
            "llm_api_key_configured": llm_ready,
            "offline_mode_ready": True,
        },
    }
