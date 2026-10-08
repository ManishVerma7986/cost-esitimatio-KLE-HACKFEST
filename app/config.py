"""Centralized application configuration using pydantic-settings.

All configuration is loaded from environment variables or .env file.
No secrets are ever hardcoded.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────
    database_url: str = "sqlite:///./data/costimator.db"

    # ── LLM Providers ─────────────────────────────────────────────
    nvidia_api_key: str = ""
    gemini_api_key: str = ""
    llm_provider: str = "nemotron"  # "nemotron" | "gemini"
    gemini_model: str = "gemini-3.8-flash"
    nvidia_model: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    llm_max_retries: int = 3
    llm_timeout_seconds: int = 60

    # ── Security ──────────────────────────────────────────────────
    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    dev_user_email: str = "dev@costimator.local"
    dev_user_password: str = "development_pass_123"

    # ── Application ───────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    app_version: str = "0.1.0"

    # ── File Uploads ──────────────────────────────────────────────
    max_upload_size_mb: int = 50
    allowed_upload_extensions: list[str] = [".csv", ".xlsx", ".xls", ".json"]
    upload_dir: str = "data/uploads"

    # ── ML / Estimation ───────────────────────────────────────────
    monte_carlo_simulations: int = 10_000
    model_dir: str = "data/models"
    dataset_dir: str = "data/datasets"

    # ── API ────────────────────────────────────────────────────────
    api_rate_limit_per_minute: int = 60
    max_request_size_bytes: int = 10 * 1024 * 1024  # 10 MB

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def model_path(self) -> Path:
        p = Path(self.model_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def dataset_path(self) -> Path:
        p = Path(self.dataset_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton settings instance."""
    return Settings()
