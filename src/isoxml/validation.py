"""Validation helpers for ISOXML task data."""

from __future__ import annotations

from pathlib import Path

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.io.taskdata import dump_taskdata_to_text
from isoxml.resources import xsd_path


def _load_xmlschema():
    try:
        import xmlschema
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        raise ModuleNotFoundError(
            "xmlschema is required for XSD validation. Install optional dependencies "
            "with `pip install .[dev]`."
        ) from exc
    return xmlschema


def validate_taskdata_xsd(
    task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    xml_version: str | int,
) -> Path:
    """Validate generated task data XML against bundled ISOXML XSD schema."""

    xmlschema = _load_xmlschema()
    schema_path = xsd_path(xml_version)
    xmlschema.validate(dump_taskdata_to_text(task_data), schema_path)
    return schema_path


__all__ = ["validate_taskdata_xsd"]
