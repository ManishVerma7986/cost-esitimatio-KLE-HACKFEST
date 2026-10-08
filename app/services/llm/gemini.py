"""Google Gemini LLM provider client using official google-genai SDK."""

from __future__ import annotations

import json
from typing import Type, TypeVar

from pydantic import BaseModel

from app.config import get_settings
from app.services.llm.validator import parse_and_validate_llm_response
from app.utils.errors import LLMServiceError
from app.utils.logging import get_logger

logger = get_logger("llm.gemini")
T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or getattr(settings, "gemini_model", "gemini-3.8-flash")
        self.timeout = settings.llm_timeout_seconds
        self.max_retries = settings.llm_max_retries

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
    ) -> T:
        """Call Gemini API with structured JSON output and schema validation."""
        if not self.is_available:
            raise LLMServiceError("GEMINI_API_KEY is not configured.", provider="gemini")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=self.api_key,
                http_options={"timeout": self.timeout * 1000},
            )
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.2,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )

            response = client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=config,
            )

            text = response.text or ""
            return parse_and_validate_llm_response(text, response_schema)

        except Exception as exc:
            logger.error("Gemini API call failed", error=str(exc))
            raise LLMServiceError(f"Gemini call failed: {exc}", provider="gemini") from exc
