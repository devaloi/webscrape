"""Core scraper: orchestrate fetch → parse → export with pagination and concurrency."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

from webscrape.client import FetchResult, HttpClient
from webscrape.config import ScrapeConfig
from webscrape.export.csv_export import CsvExporter
from webscrape.export.json_export import JsonExporter
from webscrape.export.sqlite_export import SqliteExporter
from webscrape.parser.css import CssParser
from webscrape.parser.xpath import XPathParser
from webscrape.ratelimit import RateLimiter
from webscrape.robots import RobotsChecker
from webscrape.useragent import UserAgentRotator

logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    urls_scraped: int = 0
    items_found: int = 0
    errors: int = 0
    duration: float = 0.0
    data: list[dict[str, str]] = field(default_factory=list)


def _get_parser(parser_type: str) -> CssParser | XPathParser:
    if parser_type == "xpath":
        return XPathParser()
    return CssParser()


def _get_exporter(fmt: str) -> JsonExporter | CsvExporter | SqliteExporter:
    if fmt == "csv":
        return CsvExporter()
    if fmt == "sqlite":
        return SqliteExporter()
    return JsonExporter()


async def scrape(config: ScrapeConfig, on_progress: object = None) -> ScrapeResult:
    """Run a scrape job based on the given config."""
    start_time = time.monotonic()
    result = ScrapeResult()

    rate_limiter = RateLimiter(
        default_rate=config.rate_limit.requests_per_second,
        default_burst=config.rate_limit.burst,
    )
    ua_rotator = UserAgentRotator()
    robots_checker = RobotsChecker()
    parser = _get_parser(config.selectors.parser)
    exporter = _get_exporter(config.export.format)

    async with HttpClient(
        rate_limiter=rate_limiter,
        ua_rotator=ua_rotator,
        max_attempts=config.retry.max_attempts,
        backoff_base=config.retry.backoff_base,
        backoff_max=config.retry.backoff_max,
        extra_headers=config.headers,
    ) as client:
        urls_to_scrape = list(config.urls)
        if not urls_to_scrape and config.base_url:
            urls_to_scrape = [config.base_url]

        # Fetch robots.txt for each unique domain
        domains_checked: set[str] = set()
        for url in urls_to_scrape:
            from urllib.parse import urlparse

            domain = urlparse(url).netloc
            if domain not in domains_checked:
                await robots_checker.fetch_robots(url, client._client)
                crawl_delay = robots_checker.get_crawl_delay(url)
                if crawl_delay is not None:
                    rate_limiter.set_domain_rate(domain, 1.0 / crawl_delay)
                domains_checked.add(domain)

        all_data: list[dict[str, str]] = []

        async def scrape_url(url: str) -> list[dict[str, str]]:
            items: list[dict[str, str]] = []
            current_url: str | None = url
            pages_fetched = 0
            max_pages = config.pagination.max_pages if config.pagination.enabled else 1

            while current_url and pages_fetched < max_pages:
                if not robots_checker.is_allowed(current_url):
                    logger.info("Blocked by robots.txt: %s", current_url)
                    break

                fetch_result: FetchResult = await client.fetch(current_url)
                if not fetch_result.success:
                    logger.warning("Failed to fetch %s: %d", current_url, fetch_result.status_code)
                    result.errors += 1
                    break

                result.urls_scraped += 1
                pages_fetched += 1

                page_items = parser.parse(
                    fetch_result.text,
                    config.selectors.items,
                    config.selectors.fields,
                )
                items.extend(page_items)

                if on_progress and hasattr(on_progress, "__call__"):
                    on_progress(current_url, len(page_items))

                if config.pagination.enabled and config.pagination.next_selector:
                    if hasattr(parser, "select_one"):
                        next_link = parser.select_one(
                            fetch_result.text, config.pagination.next_selector
                        )
                        if next_link:
                            current_url = urljoin(current_url, next_link)
                        else:
                            current_url = None
                    else:
                        current_url = None
                else:
                    current_url = None

            return items

        tasks = [scrape_url(url) for url in urls_to_scrape]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, Exception):
                logger.error("Scrape task failed: %s", r)
                result.errors += 1
            else:
                all_data.extend(r)

        result.items_found = len(all_data)
        result.data = all_data

        if all_data:
            exporter.export(all_data, config.export.output)
            logger.info("Exported %d items to %s", len(all_data), config.export.output)

    result.duration = time.monotonic() - start_time
    return result
