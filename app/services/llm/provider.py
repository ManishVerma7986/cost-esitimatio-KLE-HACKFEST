"""Unified LLM provider with failover and offline resilience."""

from __future__ import annotations

from typing import Tuple

from app.config import get_settings
from app.schemas.llm_responses import RecommendationResponse, ScopeDecomposition
from app.security.input_sanitizer import sanitize_for_prompt
from app.services.llm.gemini import GeminiClient
from app.services.llm.nemotron import NemotronClient
from app.services.llm.offline_decomposer import (
    decompose_scope_offline,
    generate_recommendation_offline,
)
from app.services.llm.prompts import (
    RECOMMENDATION_SYSTEM_PROMPT,
    RECOMMENDATION_USER_TEMPLATE,
    SCOPE_DECOMPOSITION_SYSTEM_PROMPT,
    SCOPE_DECOMPOSITION_USER_TEMPLATE,
)
from app.utils.logging import get_logger

logger = get_logger("llm.provider")


class LLMService:
    """Orchestrator for LLM services with automatic failover."""

    def __init__(self):
        self.settings = get_settings()
        self.nemotron = NemotronClient()
        self.gemini = GeminiClient()

    def decompose_project_scope(
        self,
        name: str,
        description: str,
        product_type: str | None = None,
        industry: str | None = None,
        target_platform: str | None = None,
        expected_users: str | None = None,
        geography: str | None = None,
        technology_constraints: str | None = None,
        required_integrations: str | None = None,
    ) -> Tuple[ScopeDecomposition, str, str]:
        """Decompose project scope using primary provider, fallback, or offline engine.

        Returns:
            Tuple of (ScopeDecomposition, provider_used, model_used)
        """
        # Sanitize user inputs against prompt injection
        safe_name = sanitize_for_prompt(name)
        safe_desc = sanitize_for_prompt(description)

        user_prompt = SCOPE_DECOMPOSITION_USER_TEMPLATE.format(
            name=safe_name,
            description=safe_desc,
            product_type=product_type or "Unspecified",
            industry=industry or "General",
            target_platform=target_platform or "Web / Cloud",
            expected_users=expected_users or "1,000 - 10,000",
            geography=geography or "Global",
            technology_constraints=technology_constraints or "None specified",
            required_integrations=required_integrations or "None specified",
        )

        # 1. Try Nemotron if configured
        if self.settings.llm_provider == "nemotron" and self.nemotron.is_available:
            try:
                res = self.nemotron.generate_structured(
                    SCOPE_DECOMPOSITION_SYSTEM_PROMPT,
                    user_prompt,
                    ScopeDecomposition,
                )
                return res, "nemotron", self.nemotron.model
            except Exception as exc:
                logger.warning("Nemotron failed, attempting Gemini fallback", error=str(exc))

        # 2. Try Gemini fallback
        if self.gemini.is_available:
            try:
                res = self.gemini.generate_structured(
                    SCOPE_DECOMPOSITION_SYSTEM_PROMPT,
                    user_prompt,
                    ScopeDecomposition,
                )
                return res, "gemini", self.gemini.model
            except Exception as exc:
                logger.warning("Gemini failed, switching to offline decomposer", error=str(exc))

        # 3. Deterministic architectural offline decomposer
        logger.info("Using deterministic offline scope decomposer")
        res = decompose_scope_offline(
            name=name,
            description=description,
            product_type=product_type,
            industry=industry,
            target_platform=target_platform,
        )
        return res, "offline_engine", "architectural-rules-v1"

    def generate_recommendation(
        self,
        project_name: str,
        total_cost: float,
        effort_hours: float,
        duration_weeks: float,
        personnel_cost: float,
        tooling_cost: float,
        cloud_cost: float,
        contingency_cost: float,
        p50: float,
        p80: float,
        cost_drivers: str = "Engineering labor, infrastructure scale",
        risks: str = "Integration timelines, scope shifts",
    ) -> RecommendationResponse:
        """Generate structured recommendation referencing calculated results."""
        user_prompt = RECOMMENDATION_USER_TEMPLATE.format(
            project_name=project_name,
            total_cost=total_cost,
            effort_hours=effort_hours,
            effort_person_months=effort_hours / 152.0 if effort_hours > 0 else 0,
            duration_weeks=duration_weeks,
            personnel_cost=personnel_cost,
            tooling_cost=tooling_cost,
            cloud_cost=cloud_cost,
            contingency_cost=contingency_cost,
            p50=p50,
            p80=p80,
            cost_drivers=cost_drivers,
            risks=risks,
        )

        if self.settings.llm_provider == "nemotron" and self.nemotron.is_available:
            try:
                return self.nemotron.generate_structured(
                    RECOMMENDATION_SYSTEM_PROMPT,
                    user_prompt,
                    RecommendationResponse,
                )
            except Exception as exc:
                logger.warning("Nemotron recommendation failed", error=str(exc))

        if self.gemini.is_available:
            try:
                return self.gemini.generate_structured(
                    RECOMMENDATION_SYSTEM_PROMPT,
                    user_prompt,
                    RecommendationResponse,
                )
            except Exception as exc:
                logger.warning("Gemini recommendation failed", error=str(exc))

        return generate_recommendation_offline(
            project_name=project_name,
            total_cost=total_cost,
            effort_hours=effort_hours,
            duration_weeks=duration_weeks,
            p50=p50,
            p80=p80,
        )


_llm_service = LLMService()


def get_llm_service() -> LLMService:
    """Return singleton LLMService instance."""
    return _llm_service
