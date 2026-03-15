"""Shared XSD validation helpers for ISOXML task data."""

from __future__ import annotations

from importlib import resources as _pkg_resources
from pathlib import Path

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml._optional_deps import require_xmlschema
from isoxml.io.writer import to_xml

_TaskData = iso3.Iso11783TaskData | iso4.Iso11783TaskData

__all__ = ["validate_xsd"]


def validate_xsd(
    task_data: _TaskData,
    xml_version: int | str | None = None,
) -> Path:
    """Validate task data XML against the bundled ISOXML XSD schema."""
    xmlschema = require_xmlschema()
    version = _resolve_xml_version(task_data, xml_version)
    xsd_name = f"ISO11783_TaskFile_V{version}-3.xsd"
    xsd_ref = _pkg_resources.files("isoxml.reference.xsd").joinpath(xsd_name)
    with _pkg_resources.as_file(xsd_ref) as xsd_path:
        if not xsd_path.exists():
            raise FileNotFoundError(f"Bundled XSD not found: {xsd_name}")
        xmlschema.validate(to_xml(task_data), xsd_path)
    return Path(str(xsd_ref))


def _resolve_xml_version(
    task_data: _TaskData,
    xml_version: int | str | None,
) -> str:
    if xml_version is not None:
        version = str(xml_version)
        if version in {"3", "4"}:
            return version
        raise ValueError(f"Unsupported XML version for XSD validation: {xml_version!r}")

    version_major = getattr(task_data, "version_major", None)
    if version_major is None:
        raise ValueError("Task data has no version_major; cannot resolve XSD version.")
    version = str(version_major.value)
    if version not in {"3", "4"}:
        raise ValueError(f"Unsupported XML version for XSD validation: {version!r}")
    return version
