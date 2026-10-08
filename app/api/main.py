"""FastAPI application factory and middleware configuration."""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, benchmarks, datasets, estimates, export, health, projects, scenarios
from app.config import get_settings
from app.db.base import Base
from app.db.session import engine
import app.db.models  # noqa: F401
from app.utils.errors import AppException, app_exception_handler
from app.utils.logging import configure_logging, get_logger

logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown events."""
    configure_logging()
    logger.info("Initializing Costimator API backend")

    # Ensure tables exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified")
    except Exception as exc:
        logger.error("Database schema initialization error", error=str(exc))

    yield

    logger.info("Shutting down Costimator API backend")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="Costimator API",
        description="Production-Ready AI-Powered Software Project Cost Estimation Platform",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows Streamlit frontend and local dev tools
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)

    # Register Routers
    api_prefix = "/api"
    app.include_router(health.router, prefix=api_prefix)
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(projects.router, prefix=api_prefix)
    app.include_router(estimates.router, prefix=api_prefix)
    app.include_router(scenarios.router, prefix=api_prefix)
    app.include_router(datasets.router, prefix=api_prefix)
    app.include_router(benchmarks.router, prefix=api_prefix)
    app.include_router(export.router, prefix=api_prefix)

    return app


app = create_app()
