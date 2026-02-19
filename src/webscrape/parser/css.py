"""BeautifulSoup CSS selector parser with ::text and ::attr pseudo-selectors."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

_PSEUDO_TEXT = re.compile(r"^(.+?)::text$")
_PSEUDO_ATTR = re.compile(r"^(.+?)::attr\(([^)]+)\)$")


def _extract_field(element: Tag, selector: str) -> str | None:
    """Extract a field value from an element using a CSS selector with pseudo-selectors."""
    text_match = _PSEUDO_TEXT.match(selector)
    if text_match:
        css = text_match.group(1)
        found = element.select_one(css)
        if found is None:
            return None
        return found.get_text(strip=True)

    attr_match = _PSEUDO_ATTR.match(selector)
    if attr_match:
        css = attr_match.group(1)
        attr_name = attr_match.group(2)
        found = element.select_one(css)
        if found is None:
            return None
        val = found.get(attr_name)
        if isinstance(val, list):
            return " ".join(val)
        return val

    found = element.select_one(selector)
    if found is None:
        return None
    return found.get_text(strip=True)


class CssParser:
    """Parse HTML using CSS selectors with BeautifulSoup."""

    def parse(self, html: str, items_selector: str, fields: dict[str, str]) -> list[dict[str, str]]:
        """Parse HTML and extract items as a list of dicts."""
        soup = BeautifulSoup(html, "lxml")
        items = soup.select(items_selector)
        results: list[dict[str, str]] = []
        for item in items:
            row: dict[str, str] = {}
            for field_name, selector in fields.items():
                value = _extract_field(item, selector)
                row[field_name] = value if value is not None else ""
            results.append(row)
        return results

    def select_one(self, html: str, selector: str) -> str | None:
        """Select a single element and return its text or attribute."""
        soup = BeautifulSoup(html, "lxml")
        # Create a wrapper tag for _extract_field
        body = soup.find("body") or soup
        if not isinstance(body, Tag):
            return None
        return _extract_field(body, selector)
