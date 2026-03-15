"""CLI for validating ISOXML grid binary content against XML metadata."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.cli._common import load_taskdata_bundle, require_grid, require_task
from isoxml.grid import decode
from isoxml.models import DDEntity


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate ISOXML grid binary consistency.")
    parser.add_argument("source", type=Path, help="TASKDATA directory or ZIP.")
    parser.add_argument("--task", type=int, default=0, help="Task index (default: 0).")
    parser.add_argument("--grid", type=int, default=0, help="Grid index within task (default: 0).")
    parser.add_argument("--ddi", type=int, default=6, help="DDI for GridType2 decode (default: 6).")
    parser.add_argument("--shp", type=Path, default=None, help="Source shapefile for value comparison.")
    parser.add_argument("--value-field", type=str, default=None, help="Numeric field name in shapefile.")
    return parser.parse_args(argv)

def _expected_byte_length(grid, ddi_count: int = 1) -> int:
    cells = int(grid.maximum_row) * int(grid.maximum_column)
    if grid.type in (iso3.GridType.GridType1, iso4.GridType.GridType1):
        return cells
    if grid.type in (iso3.GridType.GridType2, iso4.GridType.GridType2):
        return cells * 4 * ddi_count
    raise ValueError(f"Unsupported grid type: {grid.type}")


def _check_type1(task, raw: np.ndarray) -> None:
    bin_codes = {int(value) for value in np.unique(raw)}
    xml_codes = {int(treatment_zone.code) for treatment_zone in task.treatment_zones}
    undeclared = bin_codes - xml_codes
    print("Grid Type 1 checks")
    print(f"  codes in bin: {sorted(bin_codes)}")
    print(f"  codes in XML: {sorted(xml_codes)}")
    if undeclared:
        print(f"  FAIL: bin codes not declared in TZN: {sorted(undeclared)}")
    else:
        print("  OK: all bin codes declared in TZN.")


def _check_type2(task, arr: np.ndarray, ddi: DDEntity) -> None:
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

    missing = [value for value in shp_nonzero if value not in set(grid_nonzero.tolist())]
    extra = [value for value in grid_nonzero if value not in set(shp_vals.tolist())]

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


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    ddi = DDEntity.from_id(args.ddi)

    task_data, refs = load_taskdata_bundle(args.source)
    task = require_task(task_data, args.task)
    grid = require_grid(task, args.grid)

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
        _check_type1(task, raw)
        code_to_val = {
            int(treatment_zone.code): float(treatment_zone.process_data_variables[0].process_data_value or 0)
            for treatment_zone in task.treatment_zones
            if treatment_zone.code is not None and treatment_zone.process_data_variables
        }
        arr_for_compare = np.vectorize(lambda code: code_to_val.get(int(code), np.nan))(raw)
    else:
        _check_type2(task, arr, ddi)
        arr_for_compare = arr[:, :, 0] if arr.ndim == 3 and arr.shape[-1] == 1 else arr

    if args.shp is not None:
        if args.value_field is None:
            raise ValueError("--value-field is required when --shp is provided.")
        _compare_shapefile(args.shp, args.value_field, arr_for_compare)


if __name__ == "__main__":
    main()
