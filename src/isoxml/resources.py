"""Project resource location helpers."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_ROOT = PACKAGE_ROOT / "data"
XSD_ROOT = DATA_ROOT / "xsd"


def xsd_path(xml_version: str | int) -> Path:
    """Return the bundled packaged XSD path for the requested ISOXML major version."""

    version = str(xml_version)
    if version == "4":
        filename = "ISO11783_TaskFile_V4-3.xsd"
    elif version == "3":
        filename = "ISO11783_TaskFile_V3-3.xsd"
    else:
        raise ValueError(f"Unsupported XML version: {xml_version}")

    path = XSD_ROOT / filename
    if not path.exists():
        raise FileNotFoundError(f"XSD file not found: {path}")
    return path


__all__ = ["DATA_ROOT", "PACKAGE_ROOT", "XSD_ROOT", "xsd_path"]
