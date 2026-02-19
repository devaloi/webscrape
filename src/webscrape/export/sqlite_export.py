"""SQLite database exporter."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class SqliteExporter:
    """Export data to a SQLite database table."""

    def __init__(self, table_name: str = "scraped_data") -> None:
        self._table_name = table_name

    def export(self, data: list[dict[str, str]], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not data:
            conn = sqlite3.connect(str(path))
            conn.close()
            return

        columns = list(data[0].keys())
        col_defs = ", ".join(f'"{col}" TEXT' for col in columns)
        placeholders = ", ".join("?" for _ in columns)

        conn = sqlite3.connect(str(path))
        try:
            conn.execute(f'CREATE TABLE IF NOT EXISTS "{self._table_name}" ({col_defs})')
            for row in data:
                values = [row.get(col, "") for col in columns]
                conn.execute(
                    f'INSERT INTO "{self._table_name}" ({", ".join(f"{c!r}" for c in columns)}) VALUES ({placeholders})',
                    values,
                )
            conn.commit()
        finally:
            conn.close()
