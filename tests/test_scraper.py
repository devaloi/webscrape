"""Tests for core scraper with pagination and concurrency."""

import httpx
import pytest
import respx

from webscrape.config import load_config_from_dict
from webscrape.scraper import scrape


def _make_config(**overrides):
    base = {
        "name": "test",
        "base_url": "https://example.com",
        "urls": ["https://example.com/page/1"],
        "selectors": {
            "parser": "css",
            "items": "article.item",
            "fields": {
                "title": "h2.title::text",
                "url": "a.link::attr(href)",
            },
        },
        "rate_limit": {"requests_per_second": 100, "burst": 100},
        "retry": {"max_attempts": 1, "backoff_base": 0.01, "backoff_max": 0.01},
        "export": {"format": "json", "output": "./output/test.json"},
    }
    base.update(overrides)
    return load_config_from_dict(base)


class TestScraper:
    @pytest.mark.asyncio
    @respx.mock
    async def test_basic_scrape(self, sample_html, tmp_path):
        respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
        respx.get("https://example.com/page/1").mock(
            return_value=httpx.Response(200, text=sample_html)
        )
        output = str(tmp_path / "out.json")
        config = _make_config(export={"format": "json", "output": output})
        result = await scrape(config)
        assert result.urls_scraped == 1
        assert result.items_found == 3
        assert result.errors == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_pagination(self, sample_html, sample_html_page2, tmp_path):
        respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
        respx.get("https://example.com/page/1").mock(
            return_value=httpx.Response(200, text=sample_html)
        )
        respx.get("https://example.com/page/2").mock(
            return_value=httpx.Response(200, text=sample_html_page2)
        )
        output = str(tmp_path / "out.json")
        config = _make_config(
            pagination={
                "enabled": True,
                "next_selector": "a.next-page::attr(href)",
                "max_pages": 5,
            },
            export={"format": "json", "output": output},
        )
        result = await scrape(config)
        assert result.urls_scraped == 2
        assert result.items_found == 4

    @pytest.mark.asyncio
    @respx.mock
    async def test_robots_blocks_url(self, tmp_path):
        respx.get("https://example.com/robots.txt").mock(
            return_value=httpx.Response(200, text="User-agent: *\nDisallow: /page/\n")
        )
        output = str(tmp_path / "out.json")
        config = _make_config(export={"format": "json", "output": output})
        result = await scrape(config)
        assert result.urls_scraped == 0
        assert result.items_found == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_failure(self, tmp_path):
        respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
        respx.get("https://example.com/page/1").mock(return_value=httpx.Response(500, text="Error"))
        output = str(tmp_path / "out.json")
        config = _make_config(export={"format": "json", "output": output})
        result = await scrape(config)
        assert result.errors >= 1
        assert result.items_found == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_csv_export(self, sample_html, tmp_path):
        respx.get("https://example.com/robots.txt").mock(return_value=httpx.Response(404))
        respx.get("https://example.com/page/1").mock(
            return_value=httpx.Response(200, text=sample_html)
        )
        output = str(tmp_path / "out.csv")
        config = _make_config(export={"format": "csv", "output": output})
        result = await scrape(config)
        assert result.items_found == 3
        import csv

        with open(output, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 3
