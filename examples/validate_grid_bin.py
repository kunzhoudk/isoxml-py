"""
Validate ISOXML grid binary content against XML metadata.

Checks:
  - Binary file length matches rows x cols x bytes-per-cell
  - Decoded array shape matches XML grid dimensions
  - Grid Type 1: all bin codes are declared as TreatmentZone codes in XML
  - Grid Type 2: basic min/max/unique statistics
  - Optional: compare decoded values against a source shapefile

Usage:
    python examples/validate_grid_bin.py examples/output/rx_grid --ddi 6
    python examples/validate_grid_bin.py examples/output/rx_grid --ddi 6 \\
        --shp examples/input/small/shp/Rx.shp --value-field rate
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.grid import decode
from isoxml.io import read_from_path, read_from_zip
from isoxml.models import DDEntity


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate ISOXML grid binary consistency.")
    p.add_argument("source", type=Path, help="TASKDATA directory or ZIP.")
    p.add_argument("--task", type=int, default=0, help="Task index (default: 0).")
    p.add_argument("--grid", type=int, default=0, help="Grid index within task (default: 0).")
    p.add_argument("--ddi", type=int, default=6, help="DDI for GridType2 decode (default: 6).")
    p.add_argument("--shp", type=Path, default=None, help="Source shapefile for value comparison.")
    p.add_argument("--value-field", type=str, default=None, help="Numeric field name in shapefile.")
    return p.parse_args()


def load(source: Path):
    if source.is_dir():
        return read_from_path(source)
    if source.suffix.lower() == ".zip":
        return read_from_zip(source)
    raise ValueError(f"Expected a directory or .zip file, got: {source}")


def _expected_byte_length(grid, ddi_count: int = 1) -> int:
    cells = int(grid.maximum_row) * int(grid.maximum_column)
    if grid.type in (iso3.GridType.GridType1, iso4.GridType.GridType1):
        return cells  # 1 byte per cell (uint8 zone code)
    if grid.type in (iso3.GridType.GridType2, iso4.GridType.GridType2):
        return cells * 4 * ddi_count  # 4 bytes per cell per DDI (int32)
    raise ValueError(f"Unsupported grid type: {grid.type}")


def _check_type1(task, grid, raw: np.ndarray) -> None:
    bin_codes = {int(v) for v in np.unique(raw)}
    xml_codes = {int(tz.code) for tz in task.treatment_zones}
    undeclared = bin_codes - xml_codes
    print("Grid Type 1 checks")
    print(f"  codes in bin: {sorted(bin_codes)}")
    print(f"  codes in XML: {sorted(xml_codes)}")
    if undeclared:
        print(f"  FAIL: bin codes not declared in TZN: {sorted(undeclared)}")
    else:
        print("  OK: all bin codes declared in TZN.")


def _check_type2(task, grid, arr: np.ndarray, ddi: DDEntity) -> None:
    if arr.ndim == 3 and arr.shape[-1] == 1:
        arr = arr[:, :, 0]
    print("Grid Type 2 checks")
    print(f"  DDI: {ddi.ddi:04d} ({ddi.name}, bit_resolution={ddi.bit_resolution})")
    print(f"  min / max: {float(np.min(arr)):.4f} / {float(np.max(arr)):.4f}")
    print(f"  unique values: {np.unique(arr).size}")
    if task.treatment_zones:
        print(f"  note: {len(task.treatment_zones)} TZN entries (values are in .bin, not TZN)")


def _compare_shapefile(shp_path: Path, value_field: str, arr: np.ndarray) -> None:
    import geopandas as gpd

    gdf = gpd.read_file(shp_path)
    if value_field not in gdf.columns:
        raise ValueError(f"Field '{value_field}' not found in {shp_path}")
    if not np.issubdtype(gdf[value_field].dtype, np.number):
        raise ValueError(f"Field '{value_field}' is not numeric.")

    shp_vals = np.unique(gdf[value_field].dropna().astype(float).to_numpy())
    grid_vals = np.unique(arr.astype(float))
    grid_nonzero = grid_vals[grid_vals != 0]
    shp_nonzero = shp_vals[shp_vals != 0]

    missing = [v for v in shp_nonzero if v not in set(grid_nonzero.tolist())]
    extra = [v for v in grid_nonzero if v not in set(shp_vals.tolist())]

    print("Shapefile comparison")
    print(f"  shp values:  {shp_vals.tolist()}")
    print(f"  grid values: {grid_vals.tolist()}")
    if missing:
        print(f"  WARN: shp values missing from grid (non-zero): {missing}")
    else:
        print("  OK: all shp values found in grid.")
    if extra:
        print(f"  WARN: grid has non-zero values not in shp: {extra}")
    else:
        print("  OK: no unexpected non-zero grid values.")


def main() -> None:
    args = parse_args()
    ddi = DDEntity.from_id(args.ddi)

    task_data, refs = load(args.source)

    if len(task_data.tasks) <= args.task:
        raise IndexError(f"Task index {args.task} out of range.")
    task = task_data.tasks[args.task]

    if len(task.grids) <= args.grid:
        raise IndexError(f"Grid index {args.grid} out of range.")
    grid = task.grids[args.grid]

    grid_bin = refs.get(grid.filename)
    if not isinstance(grid_bin, bytes):
        raise ValueError(f"No binary data found for {grid.filename}.bin")

    expected_len = _expected_byte_length(grid)
    actual_len = len(grid_bin)

    print(f"Binary checks  [{args.source}]")
    print(f"  grid file:      {grid.filename}.bin")
    print(f"  type:           {grid.type}")
    print(f"  rows x cols:    {grid.maximum_row} x {grid.maximum_column}")
    print(f"  expected bytes: {expected_len}")
    print(f"  actual bytes:   {actual_len}")
    print(f"  length: {'OK' if expected_len == actual_len else 'FAIL (mismatch)'}")

    arr = decode(grid_bin, grid, ddi_list=[ddi], scale=True)
    expected_shape = (int(grid.maximum_row), int(grid.maximum_column))
    actual_shape = arr.shape[:2]
    print(f"  expected shape: {expected_shape}")
    print(f"  decoded shape:  {actual_shape}")
    print(f"  shape: {'OK' if actual_shape == expected_shape else 'FAIL (mismatch)'}")

    is_type1 = grid.type in (iso3.GridType.GridType1, iso4.GridType.GridType1)
    if is_type1:
        raw = decode(grid_bin, grid, scale=False)
        _check_type1(task, grid, raw)
        # Map zone codes to PDV values for shapefile comparison
        code_to_val = {
            int(tz.code): float(tz.process_data_variables[0].process_data_value or 0)
            for tz in task.treatment_zones
            if tz.code is not None and tz.process_data_variables
        }
        arr_for_compare = np.vectorize(lambda c: code_to_val.get(int(c), np.nan))(raw)
    else:
        _check_type2(task, grid, arr, ddi)
        arr_for_compare = arr[:, :, 0] if arr.ndim == 3 and arr.shape[-1] == 1 else arr

    if args.shp is not None:
        if args.value_field is None:
            raise ValueError("--value-field is required when --shp is provided.")
        _compare_shapefile(args.shp, args.value_field, arr_for_compare)


if __name__ == "__main__":
    main()
