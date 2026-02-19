"""Tests for robots.txt compliance checker."""

import httpx
import pytest
import respx

from webscrape.robots import RobotsChecker


class TestRobotsChecker:
    def test_allowed_path(self):
        checker = RobotsChecker()
        checker.set_robots_txt(
            "example.com",
            "User-agent: *\nAllow: /\nDisallow: /private/",
        )
        assert checker.is_allowed("https://example.com/public/page") is True

    def test_disallowed_path(self):
        checker = RobotsChecker()
        checker.set_robots_txt(
            "example.com",
            "User-agent: *\nDisallow: /private/",
        )
        assert checker.is_allowed("https://example.com/private/secret") is False

    def test_missing_robots_allows_all(self):
        checker = RobotsChecker()
        assert checker.is_allowed("https://example.com/anything") is True

    def test_crawl_delay_parsing(self):
        checker = RobotsChecker()
        checker.set_robots_txt(
            "example.com",
            "User-agent: *\nCrawl-delay: 5\nDisallow: /admin/",
        )
        assert checker.get_crawl_delay("https://example.com/page") == 5

    def test_no_crawl_delay(self):
        checker = RobotsChecker()
        checker.set_robots_txt(
            "example.com",
            "User-agent: *\nDisallow: /private/",
        )
        assert checker.get_crawl_delay("https://example.com/page") is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_robots_success(self):
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(
                200,
                text="User-agent: *\nDisallow: /secret/\n",
            )
        )
        checker = RobotsChecker()
        await checker.fetch_robots("https://example.com/page")
        assert checker.is_allowed("https://example.com/public") is True
        assert checker.is_allowed("https://example.com/secret/data") is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_robots_404_allows_all(self):
        respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
        checker = RobotsChecker()
        await checker.fetch_robots("https://example.com/page")
        assert checker.is_allowed("https://example.com/anything") is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_robots_cached(self):
        route = respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text="User-agent: *\nDisallow:\n")
        )
        checker = RobotsChecker()
        await checker.fetch_robots("https://example.com/page1")
        await checker.fetch_robots("https://example.com/page2")
        assert route.call_count == 1
