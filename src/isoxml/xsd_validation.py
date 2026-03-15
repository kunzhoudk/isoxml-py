"""XSD-based validation helpers for ISOXML task data."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Final

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
import xmlschema
from isoxml.io.writer import to_xml
from isoxml.models.base import get_version_module

TaskData = iso3.Iso11783TaskData | iso4.Iso11783TaskData
SCHEMA_PACKAGE: Final[str] = "isoxml.reference.xsd"

__all__ = ["validate_xsd"]


def validate_xsd(
    task_data: TaskData,
    xml_version: int | str | None = None,
) -> Path:
    """Validate ISOXML task data against the bundled task-file XSD."""
    version = resolve_xml_version(task_data, xml_version)
    schema_ref = resolve_taskdata_schema(version)

    with resources.as_file(schema_ref) as schema_path:
        xmlschema.validate(to_xml(task_data), schema_path)

    return Path(str(schema_ref))


def resolve_xml_version(
    task_data: TaskData,
    xml_version: int | str | None,
) -> str:
    """Return the supported XML major version for validation."""
    if xml_version is not None:
        return normalize_xml_version(xml_version)

    version_major = getattr(task_data, "version_major", None)
    if version_major is None:
        raise ValueError("Task data has no version_major; cannot resolve XSD version.")
    return normalize_xml_version(version_major.value)


def normalize_xml_version(xml_version: int | str) -> str:
    """Normalize and validate a supported XML major version."""
    version = str(xml_version)
    try:
        get_version_module(version)
    except ValueError as exc:
        raise ValueError(f"Unsupported XML version for XSD validation: {xml_version!r}") from exc
    return version


def resolve_taskdata_schema(xml_version: str):
    """Resolve the bundled task-file schema for the requested XML version."""
    schema_name = f"ISO11783_TaskFile_V{xml_version}-3.xsd"
    schema_ref = resources.files(SCHEMA_PACKAGE).joinpath(schema_name)
    with resources.as_file(schema_ref) as schema_path:
        if not schema_path.exists():
            raise FileNotFoundError(f"Bundled XSD not found: {schema_name}")
    return schema_ref
