"""Validation and sanitization of LLM responses against Pydantic schemas."""

from __future__ import annotations

import json
import re
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.utils.errors import LLMServiceError

T = TypeVar("T", bound=BaseModel)


def clean_json_text(text: str) -> str:
    """Strip markdown code fence blocks and extraneous whitespace."""
    cleaned = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    return cleaned


def parse_and_validate_llm_response(raw_text: str, schema_cls: Type[T]) -> T:
    """Parse JSON text from LLM response and strictly validate against target schema.

    Raises:
        LLMServiceError: If JSON cannot be parsed or fails schema validation.
    """
    cleaned = clean_json_text(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMServiceError(
            f"Failed to parse LLM response as JSON: {exc}",
            provider="unknown",
            raw_response=raw_text,
        ) from exc

    try:
        return schema_cls.model_validate(data)
    except ValidationError as exc:
        raise LLMServiceError(
            f"LLM response failed schema validation: {exc}",
            provider="unknown",
            raw_response=raw_text,
        ) from exc
