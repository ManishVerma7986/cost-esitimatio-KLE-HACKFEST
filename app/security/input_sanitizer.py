"""Input sanitization and injection prevention utilities."""

from __future__ import annotations

import html
import re


# Common patterns for prompt injection attempts
_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(previous|all|above)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?prior\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an?\s+)?unrestricted", re.IGNORECASE),
]


def sanitize_text(value: str) -> str:
    """Sanitize arbitrary user text to prevent XSS and control character injection."""
    if not value:
        return ""
    # Strip null bytes and control chars (except newline, tab, cr)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    # Escape HTML to prevent XSS
    return html.escape(cleaned.strip())


def sanitize_for_prompt(value: str) -> str:
    """Sanitize user input before interpolating into LLM prompts.

    Defends against prompt injection and instruction overrides.
    """
    if not value:
        return ""

    cleaned = value.strip()

    # Neutralize injection attempts by defanging keywords
    for pattern in _PROMPT_INJECTION_PATTERNS:
        cleaned = pattern.sub("[REDACTED_INSTRUCTION]", cleaned)

    # Restrict excessive repeating delimiters that attempt to break JSON framing
    cleaned = re.sub(r'["\']{3,}', '""', cleaned)
    cleaned = re.sub(r"[`]{3,}", "```", cleaned)

    return cleaned


def is_safe_identifier(value: str) -> bool:
    """Check if a string is a safe alphanumeric identifier (e.g. for filenames/keys)."""
    return bool(re.match(r"^[a-zA-Z0-9_\-\.]+$", value))
