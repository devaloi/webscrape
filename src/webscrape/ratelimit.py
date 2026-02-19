"""Per-domain async token bucket rate limiter."""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlparse


class TokenBucket:
    """Async token bucket rate limiter."""

    def __init__(self, rate: float, burst: int) -> None:
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait_time = (1.0 - self._tokens) / self._rate
            await asyncio.sleep(wait_time)

    @property
    def rate(self) -> float:
        return self._rate

    @rate.setter
    def rate(self, value: float) -> None:
        self._rate = value


class RateLimiter:
    """Manages per-domain token bucket rate limiters."""

    def __init__(self, default_rate: float = 2.0, default_burst: int = 5) -> None:
        self._default_rate = default_rate
        self._default_burst = default_burst
        self._buckets: dict[str, TokenBucket] = {}

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    def get_bucket(self, url: str) -> TokenBucket:
        """Get or create a token bucket for the given URL's domain."""
        domain = self._get_domain(url)
        if domain not in self._buckets:
            self._buckets[domain] = TokenBucket(self._default_rate, self._default_burst)
        return self._buckets[domain]

    def set_domain_rate(self, domain: str, rate: float) -> None:
        """Set a custom rate for a specific domain."""
        if domain in self._buckets:
            self._buckets[domain].rate = rate
        else:
            self._buckets[domain] = TokenBucket(rate, self._default_burst)

    async def acquire(self, url: str) -> None:
        """Acquire a token for the given URL's domain."""
        bucket = self.get_bucket(url)
        await bucket.acquire()
