"""Convert between Grid Type 1 and Grid Type 2 binary formats.

Grid Type 1 — one ``uint8`` zone-code per cell referencing a ``TreatmentZone``.
Grid Type 2 — one ``int32`` per PDV per cell storing actual process-data values.

Type 1 → Type 2 is **lossless** (PDV values are read directly from the Task's
TreatmentZone elements).

Type 2 → Type 1 is **lossy** in the sense that continuous values are quantised
into discrete zones.  Each unique combination of int32 values across all PDVs
becomes one new TreatmentZone.  The caller is responsible for adding the
returned TreatmentZone list to ``task.treatment_zones``.
"""

from __future__ import annotations

import dataclasses
from typing import Union

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4

_Task = Union[iso3.Task, iso4.Task]
_Grid = Union[iso3.Grid, iso4.Grid]
_TZN = Union[iso3.TreatmentZone, iso4.TreatmentZone]

_GRIDTYPE1_V3 = iso3.GridType.GridType1
_GRIDTYPE2_V3 = iso3.GridType.GridType2
_GRIDTYPE1_V4 = iso4.GridType.GridType1
_GRIDTYPE2_V4 = iso4.GridType.GridType2


def _is_v4(obj) -> bool:
    module = type(obj).__module__
    return "v4" in module


def _make_grid(grid: _Grid, **overrides) -> _Grid:
    return dataclasses.replace(grid, **overrides)


# ---------------------------------------------------------------------------
# Type 1 → Type 2
# ---------------------------------------------------------------------------

def grid_type1_to_type2(
        grid_bin: bytes,
        grid: _Grid,
        task: _Task,
) -> tuple[bytes, _Grid]:
    """Convert a Grid Type 1 BIN + XML to Type 2.

    For each cell the zone code is looked up in ``task.treatment_zones`` and
    the associated ``ProcessDataVariable.process_data_value`` integers are
    written as ``int32`` values.  All TreatmentZones in the task must expose
    the **same number of PDVs** (i.e. consistent PDV count across zones).

    Args:
        grid_bin: Raw bytes from the Type 1 ``.bin`` file.
        grid: Matching ``Grid`` element (must have ``type == GridType1``).
        task: The parent ``Task`` element that owns the grid and its
              ``TreatmentZone`` children.

    Returns:
        A ``(new_bin, new_grid)`` tuple where *new_bin* is the Type 2 binary
        payload and *new_grid* is a copy of *grid* with ``type`` updated to
        ``GridType2``.

    Raises:
        ValueError: If *grid* is not Type 1, if no TreatmentZones are found,
            if zones have different PDV counts, or if a zone code in the BIN
            has no matching TreatmentZone.
    """
    if grid.type not in (_GRIDTYPE1_V3, _GRIDTYPE1_V4):
        raise ValueError(f"Expected GridType1, got {grid.type!r}")

    # Decode zone codes
    codes = np.frombuffer(grid_bin, dtype=np.uint8).reshape(
        (grid.maximum_row, grid.maximum_column)
    )

    # Build mapping: zone_code → [pdv_value, ...]
    tzn_map: dict[int, list[int]] = {}
    for tzn in task.treatment_zones:
        tzn_map[tzn.code] = [
            pdv.process_data_value for pdv in tzn.process_data_variables
        ]

    if not tzn_map:
        raise ValueError("Task has no TreatmentZones – cannot determine PDV layout.")

    n_pdv_counts = {len(v) for v in tzn_map.values()}
    if len(n_pdv_counts) != 1:
        raise ValueError(
            f"All TreatmentZones must have the same PDV count; found {n_pdv_counts}."
        )
    n_pdv = n_pdv_counts.pop()

    # Verify all codes present in the BIN exist in the map
    unique_codes = set(np.unique(codes).tolist())
    missing = unique_codes - tzn_map.keys()
    if missing:
        raise ValueError(
            f"Zone code(s) {missing} appear in the BIN but have no TreatmentZone."
        )

    # Build LUT (256 × n_pdv) for vectorised lookup
    lut = np.zeros((256, n_pdv), dtype=np.int32)
    for code, values in tzn_map.items():
        lut[code] = values

    # Vectorised expand: (rows, cols) → (rows, cols, n_pdv)
    out = lut[codes]  # shape (rows, cols, n_pdv)
    if n_pdv == 1:
        out = out[:, :, 0]  # squeeze to (rows, cols)

    new_bin = out.tobytes(order="C")
    new_grid = _make_grid(
        grid,
        type=_GRIDTYPE2_V4 if _is_v4(grid) else _GRIDTYPE2_V3,
    )
    return new_bin, new_grid


# ---------------------------------------------------------------------------
# Type 2 → Type 1
# ---------------------------------------------------------------------------

def grid_type2_to_type1(
        grid_bin: bytes,
        grid: _Grid,
        task: _Task,
) -> tuple[bytes, _Grid, list[_TZN]]:
    """Convert a Grid Type 2 BIN + XML to Type 1.

    Each unique combination of ``int32`` PDV values across all cells is mapped
    to a new ``TreatmentZone``.  DDI and cross-reference attributes (product,
    device element, value presentation) are inherited from the TreatmentZone
    referenced by ``grid.treatment_zone_code`` (if present) or from the first
    zone in ``task.treatment_zones`` (if any).

    Args:
        grid_bin: Raw bytes from the Type 2 ``.bin`` file.
        grid: Matching ``Grid`` element (must have ``type == GridType2``).
        task: The parent ``Task`` element.  Its TreatmentZones are used as a
              DDI template.  The caller must add the returned zones to
              ``task.treatment_zones`` after calling this function.

    Returns:
        A ``(new_bin, new_grid, new_treatment_zones)`` tuple where:

        - *new_bin* – Type 1 binary payload (uint8 zone codes).
        - *new_grid* – Copy of *grid* with ``type`` set to ``GridType1``.
        - *new_treatment_zones* – List of ``TreatmentZone`` objects to insert
          into the task; each unique value combination becomes one zone.

    Raises:
        ValueError: If *grid* is not Type 2 or if more than 254 unique value
            combinations are found (Type 1 zone codes are 0–254).
    """
    if grid.type not in (_GRIDTYPE2_V3, _GRIDTYPE2_V4):
        raise ValueError(f"Expected GridType2, got {grid.type!r}")

    total_cells = grid.maximum_row * grid.maximum_column
    n_ints = len(grid_bin) // 4
    if n_ints % total_cells != 0:
        raise ValueError(
            f"BIN size ({len(grid_bin)} bytes) is not consistent with "
            f"{total_cells} cells ({grid.maximum_row}×{grid.maximum_column})."
        )
    n_pdv = n_ints // total_cells

    # Decode Type 2 → (rows, cols, n_pdv) or (rows, cols)
    raw = np.frombuffer(grid_bin, dtype=np.int32)
    if n_pdv == 1:
        arr = raw.reshape(grid.maximum_row, grid.maximum_column)
        flat = raw.reshape(-1, 1)
    else:
        arr = raw.reshape(grid.maximum_row, grid.maximum_column, n_pdv)
        flat = arr.reshape(-1, n_pdv)

    # Find unique value-tuples and the inverse index
    unique_vals, inverse = np.unique(flat, axis=0, return_inverse=True)
    n_zones = len(unique_vals)

    if n_zones > 255:
        raise ValueError(
            f"Type 2 grid has {n_zones} unique value combinations; "
            "Type 1 supports at most 254 zones (codes 0–254)."
        )

    # Determine the "template" TreatmentZone for DDI / ref attributes
    ref_tzn: _TZN | None = None
    if grid.treatment_zone_code is not None:
        ref_tzn = next(
            (t for t in task.treatment_zones if t.code == grid.treatment_zone_code),
            None,
        )
    if ref_tzn is None and task.treatment_zones:
        ref_tzn = task.treatment_zones[0]

    # Extract per-PDV metadata from the template
    pdv_ddis: list[bytes | None] = [None] * n_pdv
    pdv_product_refs: list[str | None] = [None] * n_pdv
    pdv_det_refs: list[str | None] = [None] * n_pdv
    pdv_vpn_refs: list[str | None] = [None] * n_pdv

    if ref_tzn is not None and len(ref_tzn.process_data_variables) == n_pdv:
        for i, pdv in enumerate(ref_tzn.process_data_variables):
            pdv_ddis[i] = pdv.process_data_ddi
            pdv_product_refs[i] = pdv.product_id_ref
            pdv_det_refs[i] = pdv.device_element_id_ref
            pdv_vpn_refs[i] = pdv.value_presentation_id_ref

    # Build TreatmentZone + PDV instances (v3 or v4 depending on task type)
    v4 = _is_v4(task)
    TZNCls = iso4.TreatmentZone if v4 else iso3.TreatmentZone
    PDVCls = iso4.ProcessDataVariable if v4 else iso3.ProcessDataVariable

    new_tzns: list[_TZN] = []
    for zone_idx, vals in enumerate(unique_vals):
        pdvs = []
        for pdv_idx, raw_val in enumerate(vals):
            pdv_kwargs: dict = dict(
                process_data_ddi=pdv_ddis[pdv_idx],
                process_data_value=int(raw_val),
                product_id_ref=pdv_product_refs[pdv_idx],
                device_element_id_ref=pdv_det_refs[pdv_idx],
                value_presentation_id_ref=pdv_vpn_refs[pdv_idx],
            )
            pdvs.append(PDVCls(**pdv_kwargs))
        new_tzns.append(TZNCls(code=zone_idx, process_data_variables=pdvs))

    # Encode Type 1 BIN
    zone_codes = inverse.reshape(grid.maximum_row, grid.maximum_column).astype(np.uint8)
    new_bin = zone_codes.tobytes(order="C")

    new_grid = _make_grid(
        grid,
        type=_GRIDTYPE1_V4 if v4 else _GRIDTYPE1_V3,
        treatment_zone_code=None,
    )
    return new_bin, new_grid, new_tzns
