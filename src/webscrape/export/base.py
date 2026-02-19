"""Exporter protocol (abstract base)."""

from __future__ import annotations

from typing import Protocol


class Exporter(Protocol):
    """Protocol for data exporters."""

    def export(self, data: list[dict[str, str]], output_path: str) -> None:
        """Export data to the given output path."""
        ...
