"""
Validate ISOXML GRD binary content (GridType1/2) and optionally compare with source shapefile values.

Examples:
    .venv/bin/python examples/maps/validate_grid_bin.py examples/output/big_xml_v4_auto --ddi 6
    .venv/bin/python examples/maps/validate_grid_bin.py examples/output/big_xml_v4_auto --ddi 6 \
        --shp examples/input/big/shp/NDVI_Rx.shp --value-field rate
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.grids import decode_grid_binary
from isoxml.io import load_taskdata_from_path, load_taskdata_from_zip
from isoxml.models.ddi_entities import DDEntity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ISOXML GRD bin consistency and optional shapefile value consistency.",
    )
    parser.add_argument("source", type=Path, help="TASKDATA directory or zip.")
    parser.add_argument("--task-index", type=int, default=0, help="Task index (default: 0).")
    parser.add_argument("--grid-index", type=int, default=0, help="Grid index inside task (default: 0).")
    parser.add_argument("--ddi", type=int, default=6, help="DDI for GridType2 decoding/scaling (default: 6).")
    parser.add_argument("--shp", type=Path, default=None, help="Optional source shapefile for value-set comparison.")
    parser.add_argument("--value-field", type=str, default=None, help="Numeric field name in shapefile.")
    return parser.parse_args()


def load_isoxml(source: Path):
    if source.is_dir():
        return load_taskdata_from_path(source)
    if source.suffix.lower() == ".zip":
        return load_taskdata_from_zip(source)
    raise ValueError(f"Unsupported source: {source}")


def _expected_bin_len(grid, ddi_count: int = 1) -> int:
    cells = int(grid.maximum_row) * int(grid.maximum_column)
    if grid.type in (iso3.GridType.GridType1, iso4.GridType.GridType1):
        return cells
    if grid.type in (iso3.GridType.GridType2, iso4.GridType.GridType2):
        return cells * 4 * ddi_count
    raise ValueError(f"Unsupported grid type: {grid.type}")


def _validate_type1(task, grid, arr: np.ndarray) -> None:
    unique_codes = set(int(v) for v in np.unique(arr))
    tzn_codes = {int(tz.code) for tz in task.treatment_zones}
    missing_in_tzn = unique_codes - tzn_codes
    print("Type1 checks")
    print(f"  unique codes in bin: {sorted(unique_codes)}")
    print(f"  TZN codes in XML:    {sorted(tzn_codes)}")
    if missing_in_tzn:
        print(f"  FAIL: bin has codes not declared in TZN: {sorted(missing_in_tzn)}")
    else:
        print("  OK: all bin codes are declared in TZN.")


def _type1_code_to_pdv_value(task) -> dict[int, float]:
    mapping: dict[int, float] = {}
    for tz in task.treatment_zones:
        if tz.code is None:
            continue
        value = 0.0
        if tz.process_data_variables:
            pdv = tz.process_data_variables[0]
            if pdv.process_data_value is not None:
                value = float(pdv.process_data_value)
        mapping[int(tz.code)] = value
    return mapping


def _validate_type2(task, grid, arr_scaled: np.ndarray, ddi: DDEntity) -> None:
    if arr_scaled.ndim == 3 and arr_scaled.shape[-1] == 1:
        arr_scaled = arr_scaled[:, :, 0]
    print("Type2 checks")
    print(f"  DDI: {ddi.ddi:04d} (bit_resolution={ddi.bit_resolution})")
    print(f"  min/max: {float(np.min(arr_scaled))} / {float(np.max(arr_scaled))}")
    print(f"  unique count: {np.unique(arr_scaled).size}")
    if task.treatment_zones:
        print(f"  note: TZN count={len(task.treatment_zones)} (GridType2 values are primarily in .bin)")


def _compare_with_shp(shp_path: Path, value_field: str, arr: np.ndarray) -> None:
    gdf = gpd.read_file(shp_path)
    if value_field not in gdf.columns:
        raise ValueError(f"Field '{value_field}' not found in {shp_path}")
    if not np.issubdtype(gdf[value_field].dtype, np.number):
        raise ValueError(f"Field '{value_field}' is not numeric.")

    shp_values = np.unique(gdf[value_field].dropna().astype(float).to_numpy())
    grid_values = np.unique(arr.astype(float))
    # Ignore 0 in grid because uncovered cells are often 0.
    grid_nonzero = grid_values[grid_values != 0]
    shp_nonzero = shp_values[shp_values != 0]
    missing_from_grid = [float(v) for v in shp_nonzero if v not in set(grid_nonzero.tolist())]
    extra_in_grid = [float(v) for v in grid_nonzero if v not in set(shp_values.tolist())]

    print("Shapefile comparison")
    print(f"  shp unique values:  {shp_values.tolist()}")
    print(f"  grid unique values: {grid_values.tolist()}")
    if missing_from_grid:
        print(f"  WARN: values in shp not found in grid(non-zero): {missing_from_grid}")
    else:
        print("  OK: all shp values found in grid(non-zero).")
    if extra_in_grid:
        print(f"  WARN: values in grid(non-zero) not found in shp: {extra_in_grid}")
    else:
        print("  OK: no unexpected non-zero values in grid.")


def main() -> None:
    args = parse_args()
    task_data, refs = load_isoxml(args.source)

    if len(task_data.tasks) <= args.task_index:
        raise IndexError(f"Task index {args.task_index} out of range.")
    task = task_data.tasks[args.task_index]
    if len(task.grids) <= args.grid_index:
        raise IndexError(f"Grid index {args.grid_index} out of range.")
    grid = task.grids[args.grid_index]
    grid_bin = refs.get(grid.filename)
    if not isinstance(grid_bin, bytes):
        raise ValueError(f"Missing binary for {grid.filename}.bin")

    ddi = DDEntity.from_id(args.ddi)
    arr_scaled = decode_grid_binary(grid_bin, grid, ddi_list=[ddi], scale=True)

    expected_len = _expected_bin_len(grid, ddi_count=1)
    actual_len = len(grid_bin)

    print("Binary checks")
    print(f"  source: {args.source}")
    print(f"  grid file: {grid.filename}.bin")
    print(f"  grid type: {grid.type}")
    print(f"  rows x cols: {grid.maximum_row} x {grid.maximum_column}")
    print(f"  expected bytes: {expected_len}")
    print(f"  actual bytes:   {actual_len}")
    if expected_len == actual_len:
        print("  OK: binary length matches metadata.")
    else:
        print("  FAIL: binary length mismatch.")

    expected_shape = (int(grid.maximum_row), int(grid.maximum_column))
    arr_shape = arr_scaled.shape[:2]
    print(f"  expected shape: {expected_shape}")
    print(f"  decoded shape:  {arr_shape}")
    if arr_shape == expected_shape:
        print("  OK: decoded shape matches metadata.")
    else:
        print("  FAIL: decoded shape mismatch.")

    if grid.type in (iso3.GridType.GridType1, iso4.GridType.GridType1):
        arr_type1 = decode_grid_binary(grid_bin, grid, scale=False)
        _validate_type1(task, grid, arr_type1)
        code_map = _type1_code_to_pdv_value(task)
        arr_for_compare = np.vectorize(lambda code: code_map.get(int(code), np.nan))(arr_type1)
    else:
        _validate_type2(task, grid, arr_scaled, ddi)
        arr_for_compare = arr_scaled[:, :, 0] if arr_scaled.ndim == 3 and arr_scaled.shape[-1] == 1 else arr_scaled

    if args.shp is not None:
        if args.value_field is None:
            raise ValueError("--value-field is required when --shp is provided.")
        _compare_with_shp(args.shp, args.value_field, arr_for_compare)


if __name__ == "__main__":
    main()
