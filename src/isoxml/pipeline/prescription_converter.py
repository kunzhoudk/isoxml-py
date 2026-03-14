"""High-level conversion for ISOXML prescription grids across XML versions and grid types."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4

_TaskData = iso3.Iso11783TaskData | iso4.Iso11783TaskData
_Task = iso3.Task | iso4.Task
_Grid = iso3.Grid | iso4.Grid
_TZN = iso3.TreatmentZone | iso4.TreatmentZone
_PDV = iso3.ProcessDataVariable | iso4.ProcessDataVariable

_FIELD_RENAMES_TO_V4: dict[str, dict[str, str]] = {
    "Customer": {"designator": "last_name"},
    "Worker": {"designator": "last_name"},
    "Device": {"working_set_master_name": "client_name"},
    "DeviceAllocation": {
        "working_set_master_name_value": "client_name_value",
        "working_set_master_name_mask": "client_name_mask",
    },
    "ProductAllocation": {
        "amount_ddi": "quantity_ddi",
        "amount_value": "quantity_value",
    },
}

_FIELD_RENAMES_TO_V3: dict[str, dict[str, str]] = {
    "Customer": {"last_name": "designator"},
    "Worker": {"last_name": "designator"},
    "Device": {"client_name": "working_set_master_name"},
    "DeviceAllocation": {
        "client_name_value": "working_set_master_name_value",
        "client_name_mask": "working_set_master_name_mask",
    },
    "ProductAllocation": {
        "quantity_ddi": "amount_ddi",
        "quantity_value": "amount_value",
    },
}


@dataclass
class GridPrescriptionConversionResult:
    """Converted task data and its associated binary/external references."""

    task_data: _TaskData
    refs: dict[str, Any]
    validated_xsd_path: Path | None = None


def convert_grid_prescriptions(
        task_data: _TaskData,
        refs: dict[str, Any],
        *,
        target_xml_version: int | str,
        target_grid_type: int | str,
        validate_output: bool = False,
) -> GridPrescriptionConversionResult:
    """Convert prescription grids to the requested XML version and grid type.

    This implementation is intentionally self-contained and does not call the
    existing version/grid conversion modules.
    """
    target_iso = _resolve_target_module(target_xml_version)
    target_grid_type = _normalize_grid_type(target_grid_type)

    converted_task_data = _convert_tree(task_data, target_iso)
    converted_refs = {
        ref_name: _convert_reference(ref_data, target_iso)
        for ref_name, ref_data in refs.items()
    }

    _convert_task_grids(converted_task_data, converted_refs, target_iso, target_grid_type)
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
    from isoxml.pipeline.shp_to_grid import validate_xsd

    xml_version = _task_data_xml_version(task_data)
    return validate_xsd(task_data, xml_version)


def _resolve_target_module(target_xml_version: int | str):
    version = str(target_xml_version)
    if version == "3":
        return iso3
    if version == "4":
        return iso4
    raise ValueError(f"Unsupported target XML version: {target_xml_version!r}")


def _normalize_grid_type(target_grid_type: int | str) -> int:
    grid_type = int(str(target_grid_type))
    if grid_type not in (1, 2):
        raise ValueError(f"Unsupported target grid type: {target_grid_type!r}")
    return grid_type


def _task_data_xml_version(task_data: _TaskData) -> str:
    version_major = getattr(task_data, "version_major", None)
    if version_major is None:
        raise ValueError("Task data has no version_major; cannot resolve XSD version.")
    return str(version_major.value)


def _module_indexes(target_iso) -> tuple[dict[str, type], dict[str, type[Enum]]]:
    classes = {
        name: obj
        for name, obj in vars(target_iso).items()
        if isinstance(obj, type) and dataclasses.is_dataclass(obj)
    }
    enums = {
        name: obj
        for name, obj in vars(target_iso).items()
        if isinstance(obj, type) and issubclass(obj, Enum) and obj is not Enum
    }
    return classes, enums


def _convert_tree(value: Any, target_iso) -> Any:
    classes, enums = _module_indexes(target_iso)
    return _convert_value(value, target_iso, classes, enums)


def _convert_reference(ref_data: Any, target_iso) -> Any:
    if isinstance(ref_data, bytes):
        return ref_data
    if dataclasses.is_dataclass(ref_data) and not isinstance(ref_data, type):
        return _convert_tree(ref_data, target_iso)
    return ref_data


def _convert_value(
        value: Any,
        target_iso,
        classes: dict[str, type],
        enums: dict[str, type[Enum]],
) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        converted_items = [
            _convert_value(item, target_iso, classes, enums)
            for item in value
        ]
        return [item for item in converted_items if item is not None]
    if isinstance(value, Enum):
        return _convert_enum(value, target_iso, enums)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _convert_dataclass(value, target_iso, classes, enums)
    return value


def _convert_enum(
        value: Enum,
        target_iso,
        enums: dict[str, type[Enum]],
) -> Enum | None:
    target_enum = enums.get(type(value).__name__)
    if target_enum is None:
        if type(value).__module__.startswith(target_iso.__name__):
            return value
        return None
    try:
        return target_enum(value.value)
    except ValueError:
        return None


def _convert_dataclass(
        source_obj: Any,
        target_iso,
        classes: dict[str, type],
        enums: dict[str, type[Enum]],
) -> Any:
    cls_name = type(source_obj).__name__
    target_cls = classes.get(cls_name)
    if target_cls is None:
        if type(source_obj).__module__.startswith(target_iso.__name__):
            target_cls = type(source_obj)
        else:
            return None

    source_fields = {field.name for field in dataclasses.fields(source_obj)}
    kwargs: dict[str, Any] = {}

    for target_field in dataclasses.fields(target_cls):
        if not target_field.init:
            continue

        source_field_name = _source_field_name(
            cls_name,
            target_field.name,
            target_iso,
        )

        if source_field_name not in source_fields:
            continue

        converted = _convert_value(
            getattr(source_obj, source_field_name),
            target_iso,
            classes,
            enums,
        )

        if cls_name == "Point" and target_field.name == "colour":
            if target_iso is iso4 and isinstance(converted, int):
                converted = str(converted)
            elif target_iso is iso3 and isinstance(converted, str):
                try:
                    converted = int(converted)
                except (TypeError, ValueError):
                    converted = None

        kwargs[target_field.name] = converted

    _patch_special_field_mappings(source_obj, target_cls, kwargs, target_iso, classes, enums)
    return target_cls(**kwargs)


def _source_field_name(cls_name: str, target_field_name: str, target_iso) -> str:
    rename_map = _FIELD_RENAMES_TO_V4 if target_iso is iso4 else _FIELD_RENAMES_TO_V3
    reverse_map = {
        target_name: source_name
        for source_name, target_name in rename_map.get(cls_name, {}).items()
    }
    return reverse_map.get(target_field_name, target_field_name)


def _patch_special_field_mappings(
        source_obj: Any,
        target_cls: type,
        kwargs: dict[str, Any],
        target_iso,
        classes: dict[str, type],
        enums: dict[str, type[Enum]],
) -> None:
    cls_name = type(source_obj).__name__

    if cls_name == "AllocationStamp":
        if target_iso is iso4 and getattr(source_obj, "position", None) is not None:
            kwargs["positions"] = [
                _convert_value(source_obj.position, target_iso, classes, enums)
            ]
        elif target_iso is iso3 and getattr(source_obj, "positions", None):
            kwargs["position"] = _convert_value(
                source_obj.positions[0],
                target_iso,
                classes,
                enums,
            )


def _convert_task_grids(
        task_data: _TaskData,
        refs: dict[str, Any],
        target_iso,
        target_grid_type: int,
) -> None:
    target_grid_enum = (
        target_iso.GridType.GridType1
        if target_grid_type == 1
        else target_iso.GridType.GridType2
    )

    for task in task_data.tasks:
        used_zone_codes = {
            int(tzn.code)
            for tzn in task.treatment_zones
            if tzn.code is not None
        }

        for grid in task.grids:
            if grid.filename not in refs:
                raise KeyError(f"Missing binary payload for grid '{grid.filename}'.")
            if not isinstance(refs[grid.filename], bytes):
                raise ValueError(
                    f"Reference '{grid.filename}' is not binary data."
                )

            source_bin = refs[grid.filename]
            current_type = int(grid.type.value)

            if current_type == target_grid_type:
                grid.type = target_grid_enum
                grid.filelength = len(source_bin)
                continue

            if current_type == 1:
                new_bin = _convert_type1_bin_to_type2(source_bin, grid, task)
                grid.type = target_grid_enum
                grid.treatment_zone_code = None
                grid.filelength = len(new_bin)
                refs[grid.filename] = new_bin
                continue

            new_bin, new_tzns = _convert_type2_bin_to_type1(
                source_bin,
                grid,
                task,
                target_iso,
                used_zone_codes,
            )
            task.treatment_zones.extend(new_tzns)
            used_zone_codes.update(int(tzn.code) for tzn in new_tzns if tzn.code is not None)
            grid.type = target_grid_enum
            grid.treatment_zone_code = None
            grid.filelength = len(new_bin)
            refs[grid.filename] = new_bin


def _grid_shape(grid: _Grid) -> tuple[int, int]:
    return int(grid.maximum_row), int(grid.maximum_column)


def _convert_type1_bin_to_type2(grid_bin: bytes, grid: _Grid, task: _Task) -> bytes:
    rows, cols = _grid_shape(grid)
    raw_codes = np.frombuffer(grid_bin, dtype=np.uint8)
    if raw_codes.size != rows * cols:
        raise ValueError(
            f"Grid BIN size for '{grid.filename}' does not match {rows}x{cols} Type 1 layout."
        )
    codes = raw_codes.reshape(rows, cols)

    zone_map: dict[int, list[int]] = {}
    for tzn in task.treatment_zones:
        if tzn.code is None:
            continue
        values: list[int] = []
        for pdv in tzn.process_data_variables:
            if pdv.process_data_value is None:
                raise ValueError(
                    f"TreatmentZone {tzn.code} has PDV without process_data_value."
                )
            values.append(int(pdv.process_data_value))
        zone_map[int(tzn.code)] = values

    if not zone_map:
        raise ValueError("Task has no TreatmentZones for Type 1 to Type 2 conversion.")

    pdv_counts = {len(values) for values in zone_map.values()}
    if len(pdv_counts) != 1:
        raise ValueError(
            f"TreatmentZones expose inconsistent PDV counts: {sorted(pdv_counts)}."
        )
    pdv_count = pdv_counts.pop()

    missing_codes = set(np.unique(codes).tolist()) - set(zone_map)
    if missing_codes:
        raise ValueError(
            f"Grid uses unknown TreatmentZone code(s): {sorted(missing_codes)}."
        )

    lookup = np.zeros((256, pdv_count), dtype=np.int32)
    for code, values in zone_map.items():
        lookup[code] = values

    expanded = lookup[codes]
    if pdv_count == 1:
        expanded = expanded[:, :, 0]
    return expanded.tobytes(order="C")


def _convert_type2_bin_to_type1(
        grid_bin: bytes,
        grid: _Grid,
        task: _Task,
        target_iso,
        used_zone_codes: set[int],
) -> tuple[bytes, list[_TZN]]:
    rows, cols = _grid_shape(grid)
    total_cells = rows * cols
    raw_values = np.frombuffer(grid_bin, dtype=np.int32)
    if total_cells == 0 or raw_values.size % total_cells != 0:
        raise ValueError(
            f"Grid BIN size for '{grid.filename}' does not match its Type 2 layout."
        )

    pdv_count = raw_values.size // total_cells
    flat = raw_values.reshape(total_cells, pdv_count)
    unique_values, inverse = np.unique(flat, axis=0, return_inverse=True)

    available_codes = [code for code in range(255) if code not in used_zone_codes]
    if len(unique_values) > len(available_codes):
        raise ValueError(
            f"Need {len(unique_values)} TreatmentZone codes, but only "
            f"{len(available_codes)} are available."
        )

    pdv_templates = _pdv_templates(task, grid, pdv_count)
    assigned_codes = np.array(available_codes[:len(unique_values)], dtype=np.uint8)

    TZNCls = target_iso.TreatmentZone
    PDVCls = target_iso.ProcessDataVariable
    new_tzns: list[_TZN] = []

    for zone_code, value_row in zip(assigned_codes.tolist(), unique_values.tolist(), strict=True):
        pdvs: list[_PDV] = []
        for idx, raw_value in enumerate(value_row):
            template = pdv_templates[idx]
            pdv_kwargs = {
                "process_data_ddi": template["process_data_ddi"],
                "process_data_value": int(raw_value),
                "product_id_ref": template["product_id_ref"],
                "device_element_id_ref": template["device_element_id_ref"],
                "value_presentation_id_ref": template["value_presentation_id_ref"],
            }
            pdvs.append(PDVCls(**pdv_kwargs))
        new_tzns.append(TZNCls(code=zone_code, process_data_variables=pdvs))

    zone_codes = assigned_codes[inverse].reshape(rows, cols)
    return zone_codes.tobytes(order="C"), new_tzns


def _pdv_templates(task: _Task, grid: _Grid, pdv_count: int) -> list[dict[str, Any]]:
    template_zone = None

    if grid.treatment_zone_code is not None:
        template_zone = next(
            (
                tzn for tzn in task.treatment_zones
                if tzn.code == grid.treatment_zone_code
                and len(tzn.process_data_variables) == pdv_count
            ),
            None,
        )

    if template_zone is None:
        template_zone = next(
            (
                tzn for tzn in task.treatment_zones
                if len(tzn.process_data_variables) == pdv_count
            ),
            None,
        )

    if template_zone is None:
        return [
            {
                "process_data_ddi": None,
                "product_id_ref": None,
                "device_element_id_ref": None,
                "value_presentation_id_ref": None,
            }
            for _ in range(pdv_count)
        ]

    templates: list[dict[str, Any]] = []
    for pdv in template_zone.process_data_variables:
        templates.append(
            {
                "process_data_ddi": pdv.process_data_ddi,
                "product_id_ref": pdv.product_id_ref,
                "device_element_id_ref": pdv.device_element_id_ref,
                "value_presentation_id_ref": pdv.value_presentation_id_ref,
            }
        )
    return templates
