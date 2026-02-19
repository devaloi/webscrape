"""Tests for JSON, CSV, and SQLite exporters."""

import csv
import json
import sqlite3

from webscrape.export.csv_export import CsvExporter
from webscrape.export.json_export import JsonExporter
from webscrape.export.sqlite_export import SqliteExporter


SAMPLE_DATA = [
    {"title": "First", "url": "/1"},
    {"title": "Second", "url": "/2"},
    {"title": "Third", "url": "/3"},
]


class TestJsonExporter:
    def test_export_and_read(self, tmp_path):
        output = str(tmp_path / "test.json")
        JsonExporter().export(SAMPLE_DATA, output)
        with open(output) as f:
            loaded = json.load(f)
        assert loaded == SAMPLE_DATA

    def test_empty_data(self, tmp_path):
        output = str(tmp_path / "empty.json")
        JsonExporter().export([], output)
        with open(output) as f:
            loaded = json.load(f)
        assert loaded == []

    def test_creates_parent_dirs(self, tmp_path):
        output = str(tmp_path / "sub" / "dir" / "test.json")
        JsonExporter().export(SAMPLE_DATA, output)
        with open(output) as f:
            loaded = json.load(f)
        assert len(loaded) == 3


class TestCsvExporter:
    def test_export_and_read(self, tmp_path):
        output = str(tmp_path / "test.csv")
        CsvExporter().export(SAMPLE_DATA, output)
        with open(output, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["title"] == "First"
        assert rows[2]["url"] == "/3"

    def test_empty_data(self, tmp_path):
        output = str(tmp_path / "empty.csv")
        CsvExporter().export([], output)
        with open(output) as f:
            assert f.read() == ""

    def test_creates_parent_dirs(self, tmp_path):
        output = str(tmp_path / "sub" / "dir" / "test.csv")
        CsvExporter().export(SAMPLE_DATA, output)
        with open(output, newline="") as f:
            reader = csv.DictReader(f)
            assert len(list(reader)) == 3


class TestSqliteExporter:
    def test_export_and_read(self, tmp_path):
        output = str(tmp_path / "test.db")
        SqliteExporter().export(SAMPLE_DATA, output)
        conn = sqlite3.connect(output)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM scraped_data").fetchall()
        conn.close()
        assert len(rows) == 3
        assert dict(rows[0])["title"] == "First"

    def test_empty_data(self, tmp_path):
        output = str(tmp_path / "empty.db")
        SqliteExporter().export([], output)
        conn = sqlite3.connect(output)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
        assert len(tables) == 0

    def test_custom_table_name(self, tmp_path):
        output = str(tmp_path / "custom.db")
        SqliteExporter(table_name="items").export(SAMPLE_DATA, output)
        conn = sqlite3.connect(output)
        rows = conn.execute("SELECT * FROM items").fetchall()
        conn.close()
        assert len(rows) == 3
