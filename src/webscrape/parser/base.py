"""Parser protocol (abstract base)."""

from __future__ import annotations

from typing import Protocol


class Parser(Protocol):
    """Protocol for HTML parsers."""

    def parse(self, html: str, items_selector: str, fields: dict[str, str]) -> list[dict[str, str]]:
        """Parse HTML and extract items as a list of dicts."""
        ...
