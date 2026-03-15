"""Shared public types for the vector-to-taskdata pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import isoxml.models.base.v3 as iso
import isoxml.models.base.v4 as iso4


@dataclass(frozen=True)
class VectorToTaskDataOptions:
    """Conversion options for polygon vector data to ISOXML task data."""

    source_path: Path
    value_field: str | None = None
    ddi: int = 6
    value_unit: Literal["auto", "ddi", "kg/ha"] = "auto"
    grid_type: Literal["1", "2"] = "2"
    xml_version: Literal["3", "4"] = "3"
    cell_size_m: float = 10.0
    boundary_mask: Literal["center", "strict", "touch"] = "touch"
    grid_extent: Literal["rx", "boundary", "union"] = "rx"
    input_crs: str | None = None
    partfield_name: str | None = None
    boundary_path: Path | None = None
    software_manufacturer: str = "kz_isoxml"
    software_version: str = "0.1.0"


@dataclass(frozen=True)
class VectorToTaskDataResult:
    """Result bundle produced by :func:`convert`."""

    task_data: iso.Iso11783TaskData | iso4.Iso11783TaskData
    refs: dict[str, bytes]
    value_field: str
    effective_unit: str
    unit_source: str
