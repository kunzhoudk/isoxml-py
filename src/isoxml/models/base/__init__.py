"""Versioned ISOXML base-model packages."""

from __future__ import annotations

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.models.version_registry import get, register

__all__ = ["get_version_module", "normalize_model_version"]

register("3", iso3)
register("4", iso4)


def normalize_model_version(xml_version: int | str) -> str:
    """Normalize an ISOXML model major version to its string form."""
    return str(xml_version)


def get_version_module(xml_version: int | str):
    """Return the versioned base-model module for a supported XML major version."""
    return get(normalize_model_version(xml_version))
