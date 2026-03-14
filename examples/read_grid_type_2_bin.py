"""
Read and inspect an ISOXML Grid Type 2 application map.

Loads TASKDATA from a directory or ZIP, decodes the grid binary, prints
statistics, and exports the values as CSV.

Usage:
    python examples/read_grid_type_2_bin.py <source>
    python examples/read_grid_type_2_bin.py examples/output/example_grid_2/
    python examples/read_grid_type_2_bin.py examples/output/example_grid_2.zip
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from isoxml.grid import decode
from isoxml.io import read_from_path, read_from_zip
from isoxml.models import DDEntity


def load(source: Path):
    if source.is_dir():
        return read_from_path(source)
    if source.suffix.lower() == ".zip":
        return read_from_zip(source)
    raise ValueError(f"Expected a directory or .zip file, got: {source}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inspect an ISOXML Grid Type 2 binary.")
    p.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=Path(__file__).parent / "output" / "example_grid_2.zip",
        help="TASKDATA directory or ZIP file.",
    )
    p.add_argument("--ddi", type=int, default=6, help="DDI for decoding (default: 6).")
    p.add_argument("--task", type=int, default=0, help="Task index (default: 0).")
    p.add_argument("--grid", type=int, default=0, help="Grid index within task (default: 0).")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    ddi = DDEntity.from_id(args.ddi)

    task_data, refs = load(args.source)

    if len(task_data.tasks) <= args.task:
        raise IndexError(f"Task index {args.task} out of range (found {len(task_data.tasks)}).")
    task = task_data.tasks[args.task]

    if len(task.grids) <= args.grid:
        raise IndexError(f"Grid index {args.grid} out of range (found {len(task.grids)}).")
    grid = task.grids[args.grid]

    grid_bin = refs.get(grid.filename)
    if not isinstance(grid_bin, bytes):
        raise ValueError(f"No binary data found for {grid.filename}.bin")

    arr = decode(grid_bin, grid, ddi_list=[ddi], scale=True)
    if arr.ndim == 3 and arr.shape[-1] == 1:
        arr = arr[:, :, 0]

    print("Grid metadata")
    print(f"  file:    {grid.filename}.bin")
    print(f"  type:    {grid.type}")
    print(f"  rows x cols: {grid.maximum_row} x {grid.maximum_column}")
    print(f"  origin (north, east): {grid.minimum_north_position}, {grid.minimum_east_position}")
    print(f"  cell size (north, east): {grid.cell_north_size}, {grid.cell_east_size}")
    print(f"  DDI: {ddi.ddi:04d} ({ddi.name})")

    print("\nDecoded array")
    print(f"  shape:        {arr.shape}")
    print(f"  dtype:        {arr.dtype}")
    print(f"  min / max:    {float(np.min(arr)):.4f} / {float(np.max(arr)):.4f}")
    print(f"  unique vals:  {np.unique(arr).size}")
    print(f"  non-zero:     {int(np.count_nonzero(arr))}")
    print(f"\nArray preview:\n{arr}")

    csv_path = (
        args.source / f"{grid.filename}.csv"
        if args.source.is_dir()
        else args.source.with_name(f"{grid.filename}.csv")
    )
    np.savetxt(csv_path, arr, delimiter=",", fmt="%.6f")
    print(f"\nCSV written: {csv_path}")


if __name__ == "__main__":
    main()
