"""In-memory rate limiter using sliding window log."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, status

from app.config import get_settings


class SlidingWindowRateLimiter:
    """Thread-safe sliding window in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60.0
        self._history: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request for key is allowed within the rolling window."""
        now = time.time()
        window_start = now - self.window_seconds

        # Filter out timestamps older than rolling window
        timestamps = [t for t in self._history[key] if t > window_start]

        if len(timestamps) >= self.requests_per_minute:
            self._history[key] = timestamps
            return False

        timestamps.append(now)
        self._history[key] = timestamps
        return True


_global_limiter = SlidingWindowRateLimiter(
    requests_per_minute=get_settings().api_rate_limit_per_minute
)


async def check_rate_limit(request: Request) -> None:
    """FastAPI dependency to enforce rate limiting by client IP."""
    client_ip = request.client.host if request.client else "unknown"
    if not _global_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before making more requests.",
        )
