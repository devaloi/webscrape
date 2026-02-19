"""Tests for async httpx client with retry and rate limiting."""

import httpx
import pytest
import respx

from webscrape.client import HttpClient
from webscrape.ratelimit import RateLimiter
from webscrape.useragent import UserAgentRotator


@pytest.fixture
def rate_limiter():
    return RateLimiter(default_rate=100.0, default_burst=100)


@pytest.fixture
def ua_rotator():
    return UserAgentRotator(["TestBot/1.0", "TestBot/2.0"])


class TestHttpClient:
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_request(self, rate_limiter, ua_rotator):
        respx.get("https://example.com/test").mock(
            return_value=httpx.Response(200, text="Hello World")
        )
        async with HttpClient(rate_limiter, ua_rotator) as client:
            result = await client.fetch("https://example.com/test")
        assert result.success is True
        assert result.status_code == 200
        assert result.text == "Hello World"

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_on_503(self, rate_limiter, ua_rotator):
        route = respx.get("https://example.com/test")
        route.side_effect = [
            httpx.Response(503, text="Service Unavailable"),
            httpx.Response(200, text="OK"),
        ]
        async with HttpClient(
            rate_limiter, ua_rotator, max_attempts=3, backoff_base=0.01, backoff_max=0.05
        ) as client:
            result = await client.fetch("https://example.com/test")
        assert result.success is True
        assert result.status_code == 200

    @pytest.mark.asyncio
    @respx.mock
    async def test_non_retryable_status(self, rate_limiter, ua_rotator):
        respx.get("https://example.com/test").mock(
            return_value=httpx.Response(404, text="Not Found")
        )
        async with HttpClient(rate_limiter, ua_rotator) as client:
            result = await client.fetch("https://example.com/test")
        assert result.success is False
        assert result.status_code == 404

    @pytest.mark.asyncio
    @respx.mock
    async def test_ua_header_set(self, rate_limiter, ua_rotator):
        route = respx.get("https://example.com/test").mock(
            return_value=httpx.Response(200, text="OK")
        )
        async with HttpClient(rate_limiter, ua_rotator) as client:
            await client.fetch("https://example.com/test")
        request = route.calls[0].request
        assert request.headers["user-agent"] == "TestBot/1.0"

    @pytest.mark.asyncio
    @respx.mock
    async def test_max_retries_exceeded(self, rate_limiter, ua_rotator):
        respx.get("https://example.com/test").mock(return_value=httpx.Response(503, text="Down"))
        async with HttpClient(
            rate_limiter, ua_rotator, max_attempts=2, backoff_base=0.01, backoff_max=0.02
        ) as client:
            result = await client.fetch("https://example.com/test")
        assert result.success is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_extra_headers(self, rate_limiter, ua_rotator):
        route = respx.get("https://example.com/test").mock(
            return_value=httpx.Response(200, text="OK")
        )
        async with HttpClient(
            rate_limiter, ua_rotator, extra_headers={"Accept-Language": "en-US"}
        ) as client:
            await client.fetch("https://example.com/test")
        request = route.calls[0].request
        assert request.headers["accept-language"] == "en-US"

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_after_header(self, rate_limiter, ua_rotator):
        route = respx.get("https://example.com/test")
        route.side_effect = [
            httpx.Response(429, text="Too Many", headers={"Retry-After": "0.01"}),
            httpx.Response(200, text="OK"),
        ]
        async with HttpClient(
            rate_limiter, ua_rotator, max_attempts=3, backoff_base=0.01
        ) as client:
            result = await client.fetch("https://example.com/test")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_context_manager_required(self, rate_limiter, ua_rotator):
        client = HttpClient(rate_limiter, ua_rotator)
        with pytest.raises(RuntimeError, match="not initialized"):
            await client.fetch("https://example.com/test")
