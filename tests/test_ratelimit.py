"""Tests for async token bucket rate limiter."""

import asyncio
import time

import pytest

from webscrape.ratelimit import RateLimiter, TokenBucket


class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_burst_requests_pass_immediately(self):
        bucket = TokenBucket(rate=2.0, burst=3)
        start = time.monotonic()
        for _ in range(3):
            await bucket.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_exceeding_burst_waits(self):
        bucket = TokenBucket(rate=10.0, burst=1)
        await bucket.acquire()
        start = time.monotonic()
        await bucket.acquire()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05

    @pytest.mark.asyncio
    async def test_tokens_refill(self):
        bucket = TokenBucket(rate=100.0, burst=2)
        await bucket.acquire()
        await bucket.acquire()
        await asyncio.sleep(0.05)
        start = time.monotonic()
        await bucket.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_per_domain_isolation(self):
        limiter = RateLimiter(default_rate=10.0, default_burst=1)
        await limiter.acquire("https://example.com/page1")
        start = time.monotonic()
        await limiter.acquire("https://other.com/page1")
        elapsed = time.monotonic() - start
        assert elapsed < 0.05

    @pytest.mark.asyncio
    async def test_same_domain_shares_bucket(self):
        limiter = RateLimiter(default_rate=10.0, default_burst=1)
        await limiter.acquire("https://example.com/page1")
        start = time.monotonic()
        await limiter.acquire("https://example.com/page2")
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05

    def test_set_domain_rate(self):
        limiter = RateLimiter(default_rate=2.0, default_burst=5)
        limiter.set_domain_rate("example.com", 10.0)
        bucket = limiter.get_bucket("https://example.com/test")
        assert bucket.rate == 10.0
