"""Grid binary conversion helpers for task-data version conversion."""

from __future__ import annotations

from typing import Any

import numpy as np

from isoxml.pipeline.taskdata_version_converter.types import (
    _Grid,
    _PDV,
    _Task,
    _TaskData,
    _TZN,
)


def normalize_grid_type(target_grid_type: int | str) -> int:
    grid_type = int(str(target_grid_type))
    if grid_type not in (1, 2):
        raise ValueError(f"Unsupported target grid type: {target_grid_type!r}")
    return grid_type


def convert_task_grids(
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
            int(tzn.code) for tzn in task.treatment_zones if tzn.code is not None
        }

        for grid in task.grids:
            if grid.filename not in refs:
                raise KeyError(f"Missing binary payload for grid '{grid.filename}'.")
            if not isinstance(refs[grid.filename], bytes):
                raise ValueError(f"Reference '{grid.filename}' is not binary data.")

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
            used_zone_codes.update(
                int(tzn.code) for tzn in new_tzns if tzn.code is not None
            )
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
    assigned_codes = np.array(available_codes[: len(unique_values)], dtype=np.uint8)

    TZNCls = target_iso.TreatmentZone
    PDVCls = target_iso.ProcessDataVariable
    new_tzns: list[_TZN] = []

    for zone_code, value_row in zip(
        assigned_codes.tolist(), unique_values.tolist(), strict=True
    ):
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
                tzn
                for tzn in task.treatment_zones
                if tzn.code == grid.treatment_zone_code
                and len(tzn.process_data_variables) == pdv_count
            ),
            None,
        )

    if template_zone is None:
        template_zone = next(
            (
                tzn
                for tzn in task.treatment_zones
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
