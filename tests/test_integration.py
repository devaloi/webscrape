"""Integration tests for end-to-end scraping."""

import csv
import json
import sqlite3

import httpx
import pytest
import respx

from webscrape.config import load_config_from_dict
from webscrape.scraper import scrape

INTEGRATION_HTML = """<!DOCTYPE html>
<html><body>
<div class="items">
  <div class="item">
    <h2 class="name">Widget A</h2>
    <span class="price">$9.99</span>
    <a class="link" href="/item/a">Details</a>
  </div>
  <div class="item">
    <h2 class="name">Widget B</h2>
    <span class="price">$19.99</span>
    <a class="link" href="/item/b">Details</a>
  </div>
</div>
<a class="next" href="/items?page=2">Next</a>
</body></html>"""

INTEGRATION_HTML_PAGE2 = """<!DOCTYPE html>
<html><body>
<div class="items">
  <div class="item">
    <h2 class="name">Widget C</h2>
    <span class="price">$29.99</span>
    <a class="link" href="/item/c">Details</a>
  </div>
</div>
</body></html>"""


def _make_config(tmp_path, fmt="json", pagination=False):
    output_ext = {"json": "json", "csv": "csv", "sqlite": "db"}[fmt]
    return load_config_from_dict({
        "name": "integration-test",
        "base_url": "https://shop.example.com",
        "urls": ["https://shop.example.com/items?page=1"],
        "pagination": {
            "enabled": pagination,
            "next_selector": "a.next::attr(href)",
            "max_pages": 5,
        },
        "selectors": {
            "parser": "css",
            "items": "div.item",
            "fields": {
                "name": "h2.name::text",
                "price": "span.price::text",
                "url": "a.link::attr(href)",
            },
        },
        "rate_limit": {"requests_per_second": 100, "burst": 100},
        "retry": {"max_attempts": 1, "backoff_base": 0.01, "backoff_max": 0.01},
        "export": {"format": fmt, "output": str(tmp_path / f"result.{output_ext}")},
    })


class TestEndToEndJson:
    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape_to_json(self, tmp_path):
        respx.get("https://shop.example.com/robots.txt").mock(
            return_value=httpx.Response(404)
        )
        respx.get("https://shop.example.com/items?page=1").mock(
            return_value=httpx.Response(200, text=INTEGRATION_HTML)
        )
        config = _make_config(tmp_path, fmt="json")
        result = await scrape(config)
        assert result.items_found == 2
        assert result.errors == 0
        with open(tmp_path / "result.json") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["name"] == "Widget A"
        assert data[1]["price"] == "$19.99"


class TestEndToEndCsv:
    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape_to_csv(self, tmp_path):
        respx.get("https://shop.example.com/robots.txt").mock(
            return_value=httpx.Response(404)
        )
        respx.get("https://shop.example.com/items?page=1").mock(
            return_value=httpx.Response(200, text=INTEGRATION_HTML)
        )
        config = _make_config(tmp_path, fmt="csv")
        result = await scrape(config)
        assert result.items_found == 2
        with open(tmp_path / "result.csv", newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["name"] == "Widget A"


class TestEndToEndSqlite:
    @pytest.mark.asyncio
    @respx.mock
    async def test_scrape_to_sqlite(self, tmp_path):
        respx.get("https://shop.example.com/robots.txt").mock(
            return_value=httpx.Response(404)
        )
        respx.get("https://shop.example.com/items?page=1").mock(
            return_value=httpx.Response(200, text=INTEGRATION_HTML)
        )
        config = _make_config(tmp_path, fmt="sqlite")
        result = await scrape(config)
        assert result.items_found == 2
        conn = sqlite3.connect(str(tmp_path / "result.db"))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM scraped_data").fetchall()
        conn.close()
        assert len(rows) == 2
        assert dict(rows[0])["name"] == "Widget A"


class TestEndToEndPagination:
    @pytest.mark.asyncio
    @respx.mock
    async def test_pagination_follows_links(self, tmp_path):
        respx.get("https://shop.example.com/robots.txt").mock(
            return_value=httpx.Response(404)
        )
        respx.get("https://shop.example.com/items?page=1").mock(
            return_value=httpx.Response(200, text=INTEGRATION_HTML)
        )
        respx.get("https://shop.example.com/items?page=2").mock(
            return_value=httpx.Response(200, text=INTEGRATION_HTML_PAGE2)
        )
        config = _make_config(tmp_path, fmt="json", pagination=True)
        result = await scrape(config)
        assert result.urls_scraped == 2
        assert result.items_found == 3
        with open(tmp_path / "result.json") as f:
            data = json.load(f)
        names = [d["name"] for d in data]
        assert "Widget A" in names
        assert "Widget C" in names


class TestEndToEndRobotsBlocked:
    @pytest.mark.asyncio
    @respx.mock
    async def test_robots_blocks_scrape(self, tmp_path):
        respx.get("https://shop.example.com/robots.txt").mock(
            return_value=httpx.Response(
                200, text="User-agent: *\nDisallow: /items\n"
            )
        )
        config = _make_config(tmp_path, fmt="json")
        result = await scrape(config)
        assert result.items_found == 0
        assert result.urls_scraped == 0
