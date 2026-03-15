"""CLI for reading and inspecting ISOXML grid application maps."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.cli._common import (
    default_sidecar_path,
    load_taskdata_bundle,
    require_grid,
    require_task,
)
from isoxml.grid import decode
from isoxml.models import DDEntity


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    default_path = (
        Path(__file__).resolve().parents[3]
        / "examples"
        / "output"
        / "example_grid_2.zip"
    )
    parser = argparse.ArgumentParser(description="Inspect an ISOXML grid binary.")
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=default_path,
        help="TASKDATA directory or ZIP file.",
    )
    parser.add_argument(
        "--ddi", type=int, default=6, help="DDI for decoding (default: 6)."
    )
    parser.add_argument("--task", type=int, default=0, help="Task index (default: 0).")
    parser.add_argument(
        "--grid", type=int, default=0, help="Grid index within task (default: 0)."
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    ddi = DDEntity.from_id(args.ddi)

    task_data, refs = load_taskdata_bundle(args.source)
    task = require_task(task_data, args.task)
    grid = require_grid(task, args.grid)

    grid_bin = refs.get(grid.filename)
    if not isinstance(grid_bin, bytes):
        raise ValueError(f"No binary data found for {grid.filename}.bin")

    is_type1 = grid.type in (iso3.GridType.GridType1, iso4.GridType.GridType1)
    if is_type1:
        arr = decode(grid_bin, grid, scale=False)
    else:
        arr = decode(grid_bin, grid, ddi_list=[ddi], scale=True)
    if arr.ndim == 3 and arr.shape[-1] == 1:
        arr = arr[:, :, 0]

    print("Grid metadata")
    print(f"  file:    {grid.filename}.bin")
    print(f"  type:    {grid.type}")
    print(f"  rows x cols: {grid.maximum_row} x {grid.maximum_column}")
    print(
        f"  origin (north, east): {grid.minimum_north_position}, {grid.minimum_east_position}"
    )
    print(f"  cell size (north, east): {grid.cell_north_size}, {grid.cell_east_size}")
    if is_type1:
        print("  mode: zone codes (Grid Type 1)")
    else:
        print(f"  DDI: {ddi.ddi:04d} ({ddi.name})")

    print("\nDecoded array")
    print(f"  shape:        {arr.shape}")
    print(f"  dtype:        {arr.dtype}")
    print(f"  min / max:    {float(np.min(arr)):.4f} / {float(np.max(arr)):.4f}")
    print(f"  unique vals:  {np.unique(arr).size}")
    print(f"  non-zero:     {int(np.count_nonzero(arr))}")
    print(f"\nArray preview:\n{arr}")

    csv_path = default_sidecar_path(args.source, f"{grid.filename}.csv")
    np.savetxt(csv_path, arr, delimiter=",", fmt="%.6f")
    print(f"\nCSV written: {csv_path}")


if __name__ == "__main__":
    main()
