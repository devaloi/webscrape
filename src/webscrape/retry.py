"""Exponential backoff with jitter for retry logic."""

from __future__ import annotations

import random

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
NON_RETRYABLE_STATUS_CODES = {400, 401, 403, 404}


def is_retryable_status(status_code: int) -> bool:
    """Check if an HTTP status code should trigger a retry."""
    return status_code in RETRYABLE_STATUS_CODES


def calculate_backoff(
    attempt: int,
    backoff_base: float = 1.0,
    backoff_max: float = 30.0,
) -> float:
    """Calculate backoff delay with exponential increase and jitter."""
    delay = min(backoff_base * (2**attempt) + random.uniform(0, 1), backoff_max)
    return delay


def get_retry_after(headers: dict[str, str]) -> float | None:
    """Extract Retry-After value from response headers."""
    value = headers.get("retry-after") or headers.get("Retry-After")
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
