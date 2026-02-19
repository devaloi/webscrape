# P04: webscrape — Async Web Scraper in Python

**Catalog ID:** P04 | **Size:** S | **Language:** Python
**Repo name:** `webscrape`
**One-liner:** An async web scraper with httpx, BeautifulSoup parsing, configurable rate limiting, retry with backoff, robots.txt compliance, multiple export formats, and a CLI with rich output.

---

## Why This Stands Out

- **Async httpx** — fully async HTTP client with connection pooling, concurrent scraping across multiple URLs
- **Configurable rate limiting** — per-domain rate limiting with token bucket algorithm, respects site capacity
- **Retry with exponential backoff** — transient failures (429, 5xx, timeouts) retried with increasing delays and jitter
- **Robots.txt compliance** — fetches and parses robots.txt per domain, skips disallowed paths, respects Crawl-delay
- **Multiple parsers** — CSS selectors (BeautifulSoup) and XPath (lxml) — choose per scrape config
- **Multiple export formats** — JSON, CSV, and SQLite — structured data output for any downstream use case
- **YAML scrape configs** — define target URLs, selectors, pagination, rate limits, and export format in YAML — no code changes to scrape new sites
- **Rich CLI output** — progress bars, live tables, colored status indicators via `rich` library
- **User-agent rotation** — configurable pool of user-agent strings, rotated per request

---

## Architecture

```
webscrape/
├── src/
│   └── webscrape/
│       ├── __init__.py
│       ├── cli.py               # CLI entry point: scrape, validate, list-configs
│       ├── config.py            # Load YAML scrape configs, settings
│       ├── scraper.py           # Core scraper: orchestrate fetch → parse → export
│       ├── client.py            # Async httpx client with retry, rate limit, UA rotation
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── base.py          # Parser protocol (abstract base)
│       │   ├── css.py           # BeautifulSoup CSS selector parser
│       │   └── xpath.py         # lxml XPath parser
│       ├── ratelimit.py         # Per-domain token bucket rate limiter
│       ├── retry.py             # Exponential backoff with jitter
│       ├── robots.py            # Robots.txt fetcher and checker
│       ├── export/
│       │   ├── __init__.py
│       │   ├── base.py          # Exporter protocol (abstract base)
│       │   ├── json_export.py   # JSON file exporter
│       │   ├── csv_export.py    # CSV file exporter
│       │   └── sqlite_export.py # SQLite database exporter
│       └── useragent.py         # User-agent string pool with rotation
├── configs/
│   ├── example_blog.yaml        # Example: scrape blog posts
│   ├── example_products.yaml    # Example: scrape product listings
│   └── example_quotes.yaml      # Example: scrape quotes (quotes.toscrape.com)
├── tests/
│   ├── conftest.py              # Fixtures: mock HTTP server, sample HTML
│   ├── test_client.py           # HTTP client with retry and rate limit
│   ├── test_parser_css.py       # CSS selector parsing
│   ├── test_parser_xpath.py     # XPath parsing
│   ├── test_ratelimit.py        # Token bucket rate limiter
│   ├── test_retry.py            # Backoff calculation
│   ├── test_robots.py           # Robots.txt compliance
│   ├── test_export.py           # JSON, CSV, SQLite export
│   └── test_scraper.py          # End-to-end scraper integration
├── pyproject.toml               # Project metadata, dependencies, scripts
├── .env.example
├── .gitignore
├── .python-version              # 3.14
├── ruff.toml                    # Ruff linter config
├── LICENSE
└── README.md
```

---

## Scrape Config (YAML)

```yaml
name: blog-posts
base_url: https://example.com/blog
urls:
  - https://example.com/blog/page/1
  - https://example.com/blog/page/2

pagination:
  enabled: true
  next_selector: "a.next-page"
  max_pages: 10

selectors:
  parser: css  # or xpath
  items: "article.post"
  fields:
    title: "h2.post-title::text"
    date: "time.post-date::attr(datetime)"
    summary: "p.post-summary::text"
    url: "a.post-link::attr(href)"

rate_limit:
  requests_per_second: 2
  burst: 5

retry:
  max_attempts: 3
  backoff_base: 1.0
  backoff_max: 30.0

export:
  format: json  # json, csv, or sqlite
  output: ./output/blog_posts.json

headers:
  Accept-Language: "en-US,en;q=0.9"
```

---

## Rate Limiting

```
Token Bucket Algorithm (per domain):
- Bucket capacity = burst (e.g., 5)
- Refill rate = requests_per_second (e.g., 2/sec)
- Each request consumes 1 token
- If bucket empty → wait until token available
- Separate bucket per domain (not global)
```

---

## Retry Strategy

```
Exponential Backoff with Jitter:
- Retryable: HTTP 429, 500, 502, 503, 504, connection errors, timeouts
- Delay = min(backoff_base * 2^attempt + random(0, 1), backoff_max)
- Respects Retry-After header on 429 responses
- Non-retryable: HTTP 400, 401, 403, 404 → fail immediately
```

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Language | Python 3.14 |
| HTTP Client | httpx 0.28 (async) |
| HTML Parsing | BeautifulSoup4 4.12 (CSS selectors) + lxml (XPath) |
| CLI | click + rich |
| Rate Limiting | Custom token bucket (asyncio) |
| Robots.txt | `urllib.robotparser` (stdlib) |
| Export | json (stdlib), csv (stdlib), sqlite3 (stdlib) |
| Testing | pytest + pytest-asyncio + respx (httpx mocking) |
| Linting | ruff |

---

## Phased Build Plan

### Phase 1: Foundation

**1.1 — Project setup**
- `pyproject.toml` with project metadata, dependencies, CLI script entry point
- Directory structure, `ruff.toml`, `.gitignore`, `.python-version`
- Install: `httpx[http2]`, `beautifulsoup4`, `lxml`, `click`, `rich`, `pyyaml`, `respx`, `pytest`, `pytest-asyncio`

**1.2 — Config loader**
- Parse YAML scrape config into dataclass: name, base_url, urls, pagination, selectors, rate_limit, retry, export, headers
- Validate required fields, default values for optional fields
- Tests: valid config, missing required fields, defaults applied

**1.3 — User-agent rotation**
- Pool of 10+ realistic user-agent strings (Chrome, Firefox, Safari on various OS)
- `get_ua()` returns next UA in rotation (round-robin or random)
- Tests: rotation returns different UAs, pool is not empty

### Phase 2: HTTP Client + Rate Limiting + Retry

**2.1 — Rate limiter**
- Async token bucket: `async def acquire()` waits for available token
- Per-domain buckets: keyed by domain extracted from URL
- Configurable rate (requests/second) and burst
- Tests: burst requests pass immediately, exceeding burst waits, per-domain isolation

**2.2 — Retry logic**
- Exponential backoff calculation: `min(base * 2^attempt + jitter, max)`
- Determine retryable status codes: 429, 5xx
- Respect `Retry-After` header
- Tests: backoff values increase, jitter within range, max cap, retryable vs non-retryable

**2.3 — HTTP client**
- Async httpx client with connection pooling
- Integrates rate limiter (acquire before request) and retry (wrap request with retry loop)
- User-agent rotation on each request
- Custom headers from config
- Tests with respx mock: successful request, retry on 503, rate limit enforcement, UA header set

### Phase 3: Parsers + Robots + Export

**3.1 — CSS selector parser**
- BeautifulSoup-based parser
- Given HTML + selector config, extract items as list of dicts
- Support `::text` (text content) and `::attr(name)` (attribute value) pseudo-selectors
- Tests: extract from sample HTML, missing elements → None, nested selectors

**3.2 — XPath parser**
- lxml-based parser
- Same interface as CSS parser but using XPath expressions
- Tests: extract from sample HTML, XPath axes, attribute extraction

**3.3 — Robots.txt compliance**
- Fetch robots.txt for domain (cached per domain)
- Check if URL path is allowed for our user-agent
- Extract Crawl-delay and apply to rate limiter
- Tests: allowed path, disallowed path, missing robots.txt (allow all), Crawl-delay parsing

**3.4 — Exporters**
- JSON exporter: write list of dicts as JSON array to file (pretty-printed)
- CSV exporter: write list of dicts as CSV with headers
- SQLite exporter: create table from first item's keys, insert all items
- Tests for each: write and read back, verify data integrity, empty data handling

### Phase 4: Scraper + CLI + Polish

**4.1 — Core scraper**
- Orchestrator: load config → check robots → fetch URLs → parse → handle pagination → export
- Pagination: follow next_selector link up to max_pages
- Concurrent fetching with asyncio.gather (respecting rate limits)
- Error handling: log failures, continue with remaining URLs
- Tests: end-to-end with mock HTTP server, pagination follows links, robots.txt blocks URL

**4.2 — CLI**
- `webscrape run <config.yaml>` — run scraper with progress bar (rich)
- `webscrape validate <config.yaml>` — validate config without running
- `webscrape list-configs --dir ./configs` — list available configs with names
- Rich output: progress bar per URL, summary table on completion (URLs scraped, items found, errors, duration)

**4.3 — Example configs**
- `example_quotes.yaml` — scrape quotes.toscrape.com (a safe test target)
- `example_blog.yaml` — example blog structure with pagination
- `example_products.yaml` — example product listing with multiple fields

**4.4 — README**
- Badges, install, quick start
- Scrape config YAML reference
- Rate limiting explanation
- Robots.txt compliance note
- Export formats
- CLI usage examples
- Adding custom parsers

---

## Commit Plan

1. `chore: scaffold project with pyproject.toml and directory structure`
2. `feat: add YAML config loader with validation`
3. `feat: add user-agent rotation pool`
4. `feat: add async token bucket rate limiter`
5. `feat: add retry logic with exponential backoff`
6. `feat: add async httpx client with rate limiting and retry`
7. `feat: add CSS selector parser with BeautifulSoup`
8. `feat: add XPath parser with lxml`
9. `feat: add robots.txt compliance checker`
10. `feat: add JSON, CSV, and SQLite exporters`
11. `feat: add core scraper with pagination and concurrency`
12. `feat: add CLI with rich progress output`
13. `feat: add example scrape configs`
14. `test: add integration tests for end-to-end scraping`
15. `docs: add README with config reference and CLI usage`
