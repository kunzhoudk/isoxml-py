"""Update the bundled DDI registry from the ISOBUS completeTXT export."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import requests

EXPORT_URL = "https://www.isobus.net/isobus/exports/completeTXT"
OUTPUT_PATH = Path(__file__).with_name("ddi_entities.json")

_ENTITY_RE = re.compile(r"DD Entity: (\d+) (.+)")
_UNIT_RE = re.compile(r"Unit: (.+) - (.+)")
_RESOLUTION_RE = re.compile(r"Resolution: (.+)")


@dataclass
class RegistryEntry:
    """Parsed DDI entry before serialisation to the bundled JSON layout."""

    ddi: int
    name: str
    unit: str = "n.a."
    bit_resolution: float | None = None

    def to_dict(self) -> dict[str, object]:
        """Return the historical JSON structure used by ``ddi_entities.json``."""
        payload: dict[str, object] = {
            "DDI": self.ddi,
            "name": self.name,
            "unit": self.unit,
        }
        if self.bit_resolution is not None:
            payload["bitResolution"] = self.bit_resolution
        return payload


def fetch_export_text(url: str = EXPORT_URL, *, timeout: int = 30) -> str:
    """Download the raw ISOBUS completeTXT export."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def build_registry(text: str) -> dict[int, dict[str, object]]:
    """Parse the ISOBUS completeTXT export into the bundled JSON structure."""
    registry: dict[int, dict[str, object]] = {}
    current: RegistryEntry | None = None
    started = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("DD Entity:"):
            started = True

        if not started or not line:
            continue

        entity_match = _ENTITY_RE.fullmatch(line)
        if entity_match:
            if current is not None:
                registry[current.ddi] = current.to_dict()
            current = RegistryEntry(
                ddi=int(entity_match.group(1)),
                name=entity_match.group(2),
            )
            continue

        if current is None:
            continue

        unit_match = _UNIT_RE.fullmatch(line)
        if unit_match:
            unit = unit_match.group(1)
            if unit != "not defined":
                current.unit = unit
            continue

        resolution_match = _RESOLUTION_RE.fullmatch(line)
        if resolution_match:
            current.bit_resolution = float(resolution_match.group(1).replace(",", "."))

    if current is not None:
        registry[current.ddi] = current.to_dict()

    return registry


def write_registry(
    registry: dict[int, dict[str, object]],
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Write the parsed registry to the bundled JSON file."""
    output_path.write_text(
        json.dumps(registry, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    """Refresh ``ddi_entities.json`` in place."""
    registry = build_registry(fetch_export_text())
    written_path = write_registry(registry)
    print(f"Updated: {written_path}")


if __name__ == "__main__":
    main()
