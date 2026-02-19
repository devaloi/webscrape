"""JSON file exporter."""

from __future__ import annotations

import json
from pathlib import Path


class JsonExporter:
    """Export data as a pretty-printed JSON array."""

    def export(self, data: list[dict[str, str]], output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
