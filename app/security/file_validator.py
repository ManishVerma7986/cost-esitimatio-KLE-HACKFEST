"""File upload validation and security scanning."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from app.config import get_settings


class FileValidationError(ValueError):
    """Raised when an uploaded file fails security or format validation."""
    pass


def validate_uploaded_file(
    filename: str, content: bytes, max_size_mb: int | None = None
) -> Tuple[str, str]:
    """Validate uploaded file for safe extension, size, and filename.

    Returns:
        Tuple of (sanitized_safe_filename, lower_extension)

    Raises:
        FileValidationError if file violates constraints.
    """
    settings = get_settings()
    max_mb = max_size_mb or settings.max_upload_size_mb
    max_bytes = max_mb * 1024 * 1024

    if not filename or not filename.strip():
        raise FileValidationError("Uploaded file has no filename.")

    # Strip directory components to avoid path traversal
    safe_name = Path(filename).name
    ext = Path(safe_name).suffix.lower()

    if ext not in settings.allowed_upload_extensions:
        allowed = ", ".join(settings.allowed_upload_extensions)
        raise FileValidationError(
            f"File extension '{ext}' is not permitted. Allowed: {allowed}"
        )

    if len(content) == 0:
        raise FileValidationError("Uploaded file is empty (0 bytes).")

    if len(content) > max_bytes:
        size_mb = len(content) / (1024 * 1024)
        raise FileValidationError(
            f"File size ({size_mb:.1f} MB) exceeds maximum allowed size ({max_mb} MB)."
        )

    # Basic magic number / header checks
    if ext == ".json":
        import json
        try:
            json.loads(content.decode("utf-8"))
        except Exception as e:
            raise FileValidationError(f"Invalid JSON file format: {e}")

    return safe_name, ext


def defang_csv_formula_injection(cell_value: str) -> str:
    """Neutralize spreadsheet formula injection characters (=, +, -, @, \\t, \\r)."""
    if isinstance(cell_value, str) and len(cell_value) > 0:
        if cell_value[0] in ("=", "+", "-", "@", "\t", "\r"):
            return "'" + cell_value
    return cell_value
