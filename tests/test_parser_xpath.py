"""Tests for XPath parser."""

from webscrape.parser.xpath import XPathParser


class TestXPathParser:
    def setup_method(self):
        self.parser = XPathParser()
        self.fields = {
            "title": ".//h2[@class='title']/text()",
            "url": ".//a[@class='link']/@href",
            "date": ".//time[@class='date']/@datetime",
        }

    def test_extract_items(self, sample_html):
        results = self.parser.parse(sample_html, "//article[@class='item']", self.fields)
        assert len(results) == 3
        assert results[0]["title"] == "First Item"
        assert results[1]["title"] == "Second Item"
        assert results[2]["title"] == "Third Item"

    def test_extract_attribute(self, sample_html):
        results = self.parser.parse(sample_html, "//article[@class='item']", self.fields)
        assert results[0]["url"] == "/item/1"
        assert results[0]["date"] == "2025-01-15"

    def test_missing_elements(self, sample_html):
        fields = {"missing": ".//span[@class='nonexistent']/text()"}
        results = self.parser.parse(sample_html, "//article[@class='item']", fields)
        assert results[0]["missing"] == ""

    def test_select_one(self, sample_html):
        result = self.parser.select_one(sample_html, "//a[@class='next-page']/@href")
        assert result == "/page/2"

    def test_select_one_text(self, sample_html):
        result = self.parser.select_one(sample_html, "//a[@class='next-page']/text()")
        assert result == "Next"

    def test_select_one_missing(self, sample_html):
        result = self.parser.select_one(sample_html, "//span[@class='nonexistent']/text()")
        assert result is None
