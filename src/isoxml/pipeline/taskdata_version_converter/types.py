"""Shared types for task-data version conversion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4

_TaskData = iso3.Iso11783TaskData | iso4.Iso11783TaskData
_Task = iso3.Task | iso4.Task
_Grid = iso3.Grid | iso4.Grid
_TZN = iso3.TreatmentZone | iso4.TreatmentZone
_PDV = iso3.ProcessDataVariable | iso4.ProcessDataVariable


@dataclass
class TaskDataVersionConversionResult:
    """Converted task data and its associated binary/external references."""

    task_data: _TaskData
    refs: dict[str, Any]
    validated_xsd_path: Path | None = None
