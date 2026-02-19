"""Tests for CSS selector parser."""

from webscrape.parser.css import CssParser


class TestCssParser:
    def setup_method(self):
        self.parser = CssParser()
        self.fields = {
            "title": "h2.title::text",
            "summary": "p.summary::text",
            "url": "a.link::attr(href)",
            "date": "time.date::attr(datetime)",
        }

    def test_extract_items(self, sample_html):
        results = self.parser.parse(sample_html, "article.item", self.fields)
        assert len(results) == 3
        assert results[0]["title"] == "First Item"
        assert results[1]["title"] == "Second Item"
        assert results[2]["title"] == "Third Item"

    def test_extract_text(self, sample_html):
        results = self.parser.parse(sample_html, "article.item", self.fields)
        assert results[0]["summary"] == "Summary of first item"

    def test_extract_attr(self, sample_html):
        results = self.parser.parse(sample_html, "article.item", self.fields)
        assert results[0]["url"] == "/item/1"
        assert results[0]["date"] == "2025-01-15"

    def test_missing_elements_return_empty(self, sample_html):
        fields = {"missing": "span.nonexistent::text"}
        results = self.parser.parse(sample_html, "article.item", fields)
        assert results[0]["missing"] == ""

    def test_select_one(self, sample_html):
        result = self.parser.select_one(sample_html, "a.next-page::attr(href)")
        assert result == "/page/2"

    def test_select_one_text(self, sample_html):
        result = self.parser.select_one(sample_html, "a.next-page::text")
        assert result == "Next"

    def test_plain_selector(self, sample_html):
        results = self.parser.parse(sample_html, "article.item", {"title": "h2.title"})
        assert results[0]["title"] == "First Item"
