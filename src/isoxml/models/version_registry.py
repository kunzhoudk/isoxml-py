"""Registry for supported ISOXML model versions."""

from __future__ import annotations

import re
from types import ModuleType

__all__ = ["detect_from_xml", "get", "register"]

_VERSION_MAJOR_RE = re.compile(r"""\bVersionMajor\s*=\s*["'](?P<version>\d+)["']""")
_registry: dict[str, ModuleType] = {}


def register(version: str, module: ModuleType) -> None:
    """Register a versioned ISOXML model module."""
    _registry[str(version)] = module


def get(version: str | int) -> ModuleType:
    """Return the registered model module for a supported ISOXML version."""
    normalized = str(version)
    if normalized not in _registry:
        raise ValueError(f"Unsupported ISOXML version: {normalized!r}")
    return _registry[normalized]


def detect_from_xml(xml_head: str) -> ModuleType:
    """Detect the ISOXML model module from XML content containing VersionMajor."""
    match = _VERSION_MAJOR_RE.search(xml_head)
    if match is None:
        raise ValueError("No registered ISOXML version found in XML header.")
    return get(match.group("version"))
