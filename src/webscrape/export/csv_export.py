"""CSV file exporter."""

from __future__ import annotations

import csv
from pathlib import Path


class CsvExporter:
    """Export data as CSV with headers."""

    def export(self, data: list[dict[str, str]], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not data:
            path.write_text("")
            return
        fieldnames = list(data[0].keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
