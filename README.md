# webscrape

An async web scraper with httpx, BeautifulSoup parsing, configurable rate limiting, retry with backoff, robots.txt compliance, multiple export formats, and a CLI with rich output.

## Features

- **Async httpx** — fully async HTTP client with connection pooling and concurrent scraping
- **Configurable rate limiting** — per-domain token bucket algorithm
- **Retry with exponential backoff** — handles 429, 5xx, timeouts with jitter
- **Robots.txt compliance** — fetches and respects robots.txt per domain
- **Multiple parsers** — CSS selectors (BeautifulSoup) and XPath (lxml)
- **Multiple export formats** — JSON, CSV, and SQLite
- **YAML scrape configs** — define targets, selectors, and settings in YAML
- **Rich CLI output** — progress indicators, summary tables, colored output
- **User-agent rotation** — pool of realistic user-agent strings

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick Start

```bash
# Validate a config
webscrape validate configs/example_quotes.yaml

# Run a scrape
webscrape run configs/example_quotes.yaml

# List available configs
webscrape list-configs --dir ./configs
```

## Scrape Config Reference

Configs are YAML files that define what to scrape and how:

```yaml
name: blog-posts
base_url: https://example.com/blog
urls:
  - https://example.com/blog/page/1
  - https://example.com/blog/page/2

pagination:
  enabled: true
  next_selector: "a.next-page::attr(href)"
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

### Config Fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `name` | Yes | — | Name for this scrape job |
| `base_url` | Yes | — | Base URL of the target site |
| `urls` | No | `[base_url]` | List of URLs to scrape |
| `pagination.enabled` | No | `false` | Enable pagination following |
| `pagination.next_selector` | No | `""` | CSS/XPath selector for next page link |
| `pagination.max_pages` | No | `10` | Maximum pages to follow |
| `selectors.parser` | No | `css` | Parser type: `css` or `xpath` |
| `selectors.items` | No | `""` | Selector for item containers |
| `selectors.fields` | No | `{}` | Map of field name → selector |
| `rate_limit.requests_per_second` | No | `2.0` | Requests per second per domain |
| `rate_limit.burst` | No | `5` | Burst capacity |
| `retry.max_attempts` | No | `3` | Maximum retry attempts |
| `retry.backoff_base` | No | `1.0` | Base delay for exponential backoff |
| `retry.backoff_max` | No | `30.0` | Maximum backoff delay |
| `export.format` | No | `json` | Export format: `json`, `csv`, or `sqlite` |
| `export.output` | No | `./output/results.json` | Output file path |
| `headers` | No | `{}` | Custom HTTP headers |

### CSS Pseudo-Selectors

The CSS parser supports custom pseudo-selectors:

- `::text` — extract text content: `h2.title::text`
- `::attr(name)` — extract attribute value: `a.link::attr(href)`

## Rate Limiting

Uses a token bucket algorithm per domain:

- **Bucket capacity** = `burst` (e.g., 5 tokens)
- **Refill rate** = `requests_per_second` (e.g., 2 tokens/sec)
- Each request consumes 1 token
- If bucket is empty, request waits for a token
- Separate bucket per domain — different domains don't block each other
- Respects `Crawl-delay` from robots.txt

## Retry Strategy

Exponential backoff with jitter for transient failures:

- **Retryable:** HTTP 429, 500, 502, 503, 504, connection errors, timeouts
- **Delay:** `min(backoff_base × 2^attempt + random(0,1), backoff_max)`
- **Retry-After:** respects the header on 429 responses
- **Non-retryable:** HTTP 400, 401, 403, 404 — fails immediately

## Robots.txt Compliance

Before fetching any URL, the scraper:

1. Fetches `robots.txt` for the domain (cached per domain)
2. Checks if the URL path is allowed
3. Extracts `Crawl-delay` and applies it to the rate limiter
4. Skips disallowed URLs with a log message

## Export Formats

| Format | Description |
|--------|-------------|
| `json` | Pretty-printed JSON array |
| `csv` | CSV with header row |
| `sqlite` | SQLite database with auto-created table |

## CLI Usage

```bash
# Run a scrape job
webscrape run <config.yaml>

# Validate config without running
webscrape validate <config.yaml>

# List configs in a directory
webscrape list-configs --dir ./configs

# Show version
webscrape --version
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## License

MIT
