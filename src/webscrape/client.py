"""Async httpx client with rate limiting, retry, and user-agent rotation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import httpx

from webscrape.ratelimit import RateLimiter
from webscrape.retry import calculate_backoff, get_retry_after, is_retryable_status
from webscrape.useragent import UserAgentRotator

logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    url: str
    status_code: int
    text: str
    headers: dict[str, str]
    success: bool


class HttpClient:
    """Async HTTP client with rate limiting, retry, and UA rotation."""

    def __init__(
        self,
        rate_limiter: RateLimiter,
        ua_rotator: UserAgentRotator | None = None,
        max_attempts: int = 3,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
        timeout: float = 30.0,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self._rate_limiter = rate_limiter
        self._ua_rotator = ua_rotator or UserAgentRotator()
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base
        self._backoff_max = backoff_max
        self._timeout = timeout
        self._extra_headers = extra_headers or {}
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> HttpClient:
        self._client = httpx.AsyncClient(
            timeout=self._timeout,
            follow_redirects=True,
            http2=True,
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch(self, url: str) -> FetchResult:
        """Fetch a URL with rate limiting, retry, and UA rotation."""
        if self._client is None:
            msg = "Client not initialized. Use 'async with' context manager."
            raise RuntimeError(msg)

        last_error: Exception | None = None
        for attempt in range(self._max_attempts):
            await self._rate_limiter.acquire(url)

            headers = {
                "User-Agent": self._ua_rotator.get_ua(),
                **self._extra_headers,
            }

            try:
                response = await self._client.get(url, headers=headers)

                if response.status_code == 200:
                    return FetchResult(
                        url=url,
                        status_code=response.status_code,
                        text=response.text,
                        headers=dict(response.headers),
                        success=True,
                    )

                if is_retryable_status(response.status_code):
                    retry_after = get_retry_after(dict(response.headers))
                    if retry_after is not None:
                        delay = retry_after
                    else:
                        delay = calculate_backoff(attempt, self._backoff_base, self._backoff_max)
                    logger.warning(
                        "Retryable status %d for %s, attempt %d/%d, waiting %.1fs",
                        response.status_code,
                        url,
                        attempt + 1,
                        self._max_attempts,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue

                return FetchResult(
                    url=url,
                    status_code=response.status_code,
                    text=response.text,
                    headers=dict(response.headers),
                    success=False,
                )

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = exc
                delay = calculate_backoff(attempt, self._backoff_base, self._backoff_max)
                logger.warning(
                    "Connection error for %s, attempt %d/%d: %s",
                    url,
                    attempt + 1,
                    self._max_attempts,
                    exc,
                )
                if attempt < self._max_attempts - 1:
                    await asyncio.sleep(delay)

        return FetchResult(
            url=url,
            status_code=0,
            text=str(last_error) if last_error else "Max retries exceeded",
            headers={},
            success=False,
        )
