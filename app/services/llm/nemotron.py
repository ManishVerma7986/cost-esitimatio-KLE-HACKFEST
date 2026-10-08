"""NVIDIA Nemotron LLM provider client using OpenAI-compatible API."""

from __future__ import annotations

import json
from typing import Any, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from app.config import get_settings
from app.services.llm.validator import parse_and_validate_llm_response
from app.utils.errors import LLMServiceError
from app.utils.logging import get_logger

logger = get_logger("llm.nemotron")
T = TypeVar("T", bound=BaseModel)


class NemotronClient:
    """Client for NVIDIA Nemotron LLM via NVIDIA API catalog."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.nvidia_api_key
        self.model = model or getattr(settings, "nvidia_model", "nvidia/llama-3.1-nemotron-70b-instruct")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.timeout = settings.llm_timeout_seconds
        self.max_retries = settings.llm_max_retries

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("nvapi-"))

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
    ) -> T:
        """Call Nemotron and validate output against Pydantic schema with retry loop."""
        if not self.is_available:
            raise LLMServiceError(
                "NVIDIA_API_KEY is not configured or invalid.", provider="nemotron"
            )

        client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

        last_error = None
        current_user_prompt = user_prompt

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "Calling Nemotron API",
                    model=self.model,
                    attempt=attempt,
                )
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": current_user_prompt},
                    ],
                    temperature=0.2,
                    top_p=0.9,
                    max_tokens=4096,
                )

                content = response.choices[0].message.content or ""
                return parse_and_validate_llm_response(content, response_schema)

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Nemotron generation attempt failed",
                    attempt=attempt,
                    error=str(exc),
                )
                # Correction prompt on retry
                current_user_prompt = (
                    f"{user_prompt}\n\nIMPORTANT: Your previous output caused validation error: {exc}. "
                    "You MUST reply ONLY with valid JSON exactly matching the requested fields."
                )

        raise LLMServiceError(
            f"Nemotron failed after {self.max_retries} attempts: {last_error}",
            provider="nemotron",
        )
