# Build webscrape — Async Web Scraper in Python

You are building a **portfolio project** for a Senior AI Engineer's public GitHub. It must be impressive, clean, and production-grade. Read these docs before writing any code:

1. **`P04-python-web-scraper.md`** — Complete project spec: architecture, YAML config format, rate limiting design, retry strategy, parser interface, export formats, CLI, phased build plan, commit plan. This is your primary blueprint. Follow it phase by phase.
2. **`github-portfolio.md`** — Portfolio goals and Definition of Done (Level 1 + Level 2). Understand the quality bar.
3. **`github-portfolio-checklist.md`** — Pre-publish checklist. Every item must pass before you're done.

---

## Instructions

### Read first, build second
Read all three docs completely before writing a single line of code. Understand the async httpx client with connection pooling, the per-domain token bucket rate limiter, the exponential backoff retry logic, the dual parser approach (CSS + XPath), the three export formats, the YAML scrape config structure, and the robots.txt compliance layer.

### Follow the phases in order
The project spec has 4 phases. Do them in order:
1. **Foundation** — project setup with pyproject.toml, YAML config loader with dataclass parsing and validation, user-agent rotation pool
2. **HTTP Client + Rate Limiting + Retry** — async token bucket rate limiter (per-domain), exponential backoff with jitter, async httpx client integrating rate limiter + retry + UA rotation
3. **Parsers + Robots + Export** — CSS selector parser (BeautifulSoup), XPath parser (lxml), robots.txt compliance checker, JSON/CSV/SQLite exporters
4. **Scraper + CLI + Polish** — core scraper orchestrator with pagination and concurrency, CLI with rich progress output, example configs, README

### Commit frequently
Follow the commit plan in the spec. Use **conventional commits**. Each commit should be a logical unit.

### Quality non-negotiables
- **Fully async.** The HTTP client, rate limiter, and scraper core must use `async`/`await`. Use `httpx.AsyncClient` with connection pooling. Concurrent fetching via `asyncio.gather` bounded by rate limits.
- **Per-domain rate limiting.** Token bucket rate limiter keyed by domain. Each domain gets its own bucket with configurable rate and burst. The rate limiter is async — `await acquire()` blocks until a token is available.
- **Exponential backoff with jitter.** Retry transient failures (429, 5xx, connection errors, timeouts). Formula: `min(base * 2^attempt + random(0, 1), max)`. Respect `Retry-After` header on 429 responses. Non-retryable errors (4xx except 429) fail immediately.
- **Robots.txt compliance.** Fetch and cache robots.txt per domain. Check every URL against it before requesting. Respect `Crawl-delay` if specified. If robots.txt cannot be fetched (404, timeout), default to allow.
- **Both CSS and XPath parsers.** CSS selectors via BeautifulSoup4, XPath via lxml. Same interface (Protocol/ABC). Parser choice is per-config. Support `::text` and `::attr(name)` pseudo-selectors in CSS mode.
- **Three export formats.** JSON (pretty-printed array), CSV (with headers), SQLite (auto-create table from data keys). All exporters implement the same interface. Exporter choice is per-config.
- **YAML scrape configs.** All scraping behavior is defined in YAML — URLs, selectors, pagination, rate limits, retry, export format. No code changes to scrape a new site.
- **Tests use respx mocking.** No real HTTP requests in tests. Use `respx` to mock httpx responses. Use pytest-asyncio for async test support.
- **Lint clean.** `ruff check` and `ruff format --check` must pass.

### What NOT to do
- Don't use `requests` or `aiohttp`. Use `httpx` with async client — it's the modern choice with HTTP/2 support.
- Don't use a global rate limiter. Rate limiting must be per-domain to avoid one slow domain throttling all others.
- Don't skip robots.txt checking. Responsible scraping is a portfolio differentiator.
- Don't make real HTTP requests in tests. Use `respx` to mock all httpx calls.
- Don't hardcode selectors or URLs in Python code. Everything comes from YAML config.
- Don't leave `# TODO` or `# FIXME` comments anywhere.

---

## GitHub Username

The GitHub username is **devaloi**. The repository is `github.com/devaloi/webscrape`. Python package name is `webscrape`.

## Start

Read the three docs. Then begin Phase 1 from `P04-python-web-scraper.md`.
