"""lxml XPath parser."""

from __future__ import annotations

from lxml import html as lxml_html


class XPathParser:
    """Parse HTML using XPath expressions with lxml."""

    def parse(self, html: str, items_selector: str, fields: dict[str, str]) -> list[dict[str, str]]:
        """Parse HTML and extract items as a list of dicts."""
        tree = lxml_html.fromstring(html)
        items = tree.xpath(items_selector)
        results: list[dict[str, str]] = []
        for item in items:
            row: dict[str, str] = {}
            for field_name, xpath_expr in fields.items():
                values = item.xpath(xpath_expr)
                if values:
                    val = values[0]
                    row[field_name] = val.strip() if isinstance(val, str) else val.text_content().strip()
                else:
                    row[field_name] = ""
            results.append(row)
        return results

    def select_one(self, html: str, xpath_expr: str) -> str | None:
        """Select a single value using an XPath expression."""
        tree = lxml_html.fromstring(html)
        values = tree.xpath(xpath_expr)
        if not values:
            return None
        val = values[0]
        return val.strip() if isinstance(val, str) else val.text_content().strip()
