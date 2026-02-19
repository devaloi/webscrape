"""Robots.txt fetcher and compliance checker."""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Check robots.txt compliance per domain with caching."""

    def __init__(self, user_agent: str = "*") -> None:
        self._user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}
        self._crawl_delays: dict[str, float | None] = {}

    def _get_robots_url(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    async def fetch_robots(self, url: str, client: httpx.AsyncClient | None = None) -> None:
        """Fetch and parse robots.txt for the domain of the given URL."""
        domain = self._get_domain(url)
        if domain in self._parsers:
            return

        robots_url = self._get_robots_url(url)
        parser = RobotFileParser()

        try:
            if client:
                response = await client.get(robots_url, timeout=10.0)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                else:
                    parser.allow_all = True
            else:
                async with httpx.AsyncClient() as temp_client:
                    response = await temp_client.get(robots_url, timeout=10.0)
                    if response.status_code == 200:
                        parser.parse(response.text.splitlines())
                    else:
                        parser.allow_all = True
        except (httpx.ConnectError, httpx.TimeoutException):
            parser.allow_all = True
            logger.warning("Could not fetch robots.txt for %s, allowing all", domain)

        self._parsers[domain] = parser
        delay = parser.crawl_delay(self._user_agent)
        self._crawl_delays[domain] = delay

    def is_allowed(self, url: str) -> bool:
        """Check if a URL is allowed by robots.txt."""
        domain = self._get_domain(url)
        parser = self._parsers.get(domain)
        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)

    def get_crawl_delay(self, url: str) -> float | None:
        """Get the Crawl-delay for the domain of the given URL."""
        domain = self._get_domain(url)
        return self._crawl_delays.get(domain)

    def set_robots_txt(self, domain: str, content: str) -> None:
        """Manually set robots.txt content for a domain (useful for testing)."""
        parser = RobotFileParser()
        parser.parse(content.splitlines())
        self._parsers[domain] = parser
        self._crawl_delays[domain] = parser.crawl_delay(self._user_agent)
