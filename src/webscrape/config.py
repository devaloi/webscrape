"""YAML scrape config loader with dataclass validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PaginationConfig:
    enabled: bool = False
    next_selector: str = ""
    max_pages: int = 10


@dataclass
class SelectorConfig:
    parser: str = "css"
    items: str = ""
    fields: dict[str, str] = field(default_factory=dict)


@dataclass
class RateLimitConfig:
    requests_per_second: float = 2.0
    burst: int = 5


@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_base: float = 1.0
    backoff_max: float = 30.0


@dataclass
class ExportConfig:
    format: str = "json"
    output: str = "./output/results.json"


@dataclass
class ScrapeConfig:
    name: str
    base_url: str
    urls: list[str] = field(default_factory=list)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    selectors: SelectorConfig = field(default_factory=SelectorConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    headers: dict[str, str] = field(default_factory=dict)


class ConfigError(Exception):
    """Raised when a scrape config is invalid."""


def _build_nested(cls: type, data: dict[str, Any] | None) -> Any:
    if data is None:
        return cls()
    return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def load_config(path: str | Path) -> ScrapeConfig:
    """Load and validate a YAML scrape config file."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ConfigError("Config must be a YAML mapping")

    if "name" not in raw:
        raise ConfigError("Config missing required field: name")
    if "base_url" not in raw:
        raise ConfigError("Config missing required field: base_url")

    return ScrapeConfig(
        name=raw["name"],
        base_url=raw["base_url"],
        urls=raw.get("urls", []),
        pagination=_build_nested(PaginationConfig, raw.get("pagination")),
        selectors=_build_nested(SelectorConfig, raw.get("selectors")),
        rate_limit=_build_nested(RateLimitConfig, raw.get("rate_limit")),
        retry=_build_nested(RetryConfig, raw.get("retry")),
        export=_build_nested(ExportConfig, raw.get("export")),
        headers=raw.get("headers", {}),
    )


def load_config_from_dict(data: dict[str, Any]) -> ScrapeConfig:
    """Load and validate a scrape config from a dictionary."""
    if "name" not in data:
        raise ConfigError("Config missing required field: name")
    if "base_url" not in data:
        raise ConfigError("Config missing required field: base_url")

    return ScrapeConfig(
        name=data["name"],
        base_url=data["base_url"],
        urls=data.get("urls", []),
        pagination=_build_nested(PaginationConfig, data.get("pagination")),
        selectors=_build_nested(SelectorConfig, data.get("selectors")),
        rate_limit=_build_nested(RateLimitConfig, data.get("rate_limit")),
        retry=_build_nested(RetryConfig, data.get("retry")),
        export=_build_nested(ExportConfig, data.get("export")),
        headers=data.get("headers", {}),
    )
