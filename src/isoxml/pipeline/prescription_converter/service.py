"""Orchestration entry point for prescription conversion."""

from __future__ import annotations

from pathlib import Path

from isoxml.pipeline.prescription_converter.grid import (
    convert_task_grids,
    normalize_grid_type,
)
from isoxml.pipeline.prescription_converter.tree import (
    convert_reference,
    convert_tree,
    resolve_target_module,
)
from isoxml.pipeline.prescription_converter.types import (
    GridPrescriptionConversionResult,
    _TaskData,
)
from isoxml.xsd_validation import validate_xsd


def convert_grid_prescriptions(
    task_data: _TaskData,
    refs: dict[str, object],
    *,
    target_xml_version: int | str,
    target_grid_type: int | str,
    validate_output: bool = False,
) -> GridPrescriptionConversionResult:
    """Convert prescription grids to the requested XML version and grid type."""
    target_iso = resolve_target_module(target_xml_version)
    target_grid_type = normalize_grid_type(target_grid_type)

    converted_task_data = convert_tree(task_data, target_iso)
    converted_refs = {
        ref_name: convert_reference(ref_data, target_iso)
        for ref_name, ref_data in refs.items()
    }

    convert_task_grids(converted_task_data, converted_refs, target_iso, target_grid_type)
    validated_xsd_path = None
    if validate_output:
        validated_xsd_path = validate_prescription_xsd(converted_task_data)
    return GridPrescriptionConversionResult(
        task_data=converted_task_data,
        refs=converted_refs,
        validated_xsd_path=validated_xsd_path,
    )


def validate_prescription_xsd(task_data: _TaskData) -> Path:
    """Validate converted task data against the bundled XSD for its XML version."""
    return validate_xsd(task_data)
