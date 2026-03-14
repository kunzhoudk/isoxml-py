"""CLI for reading and inspecting ISOXML grid application maps."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.grid import decode
from isoxml.io import read_from_path, read_from_zip
from isoxml.models import DDEntity


def load(source: Path):
    if source.is_dir():
        return read_from_path(source)
    if source.suffix.lower() == ".zip":
        return read_from_zip(source)
    raise ValueError(f"Expected a directory or .zip file, got: {source}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    default_path = Path(__file__).resolve().parents[3] / "examples" / "output" / "example_grid_2.zip"
    parser = argparse.ArgumentParser(description="Inspect an ISOXML grid binary.")
    parser.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=default_path,
        help="TASKDATA directory or ZIP file.",
    )
    parser.add_argument("--ddi", type=int, default=6, help="DDI for decoding (default: 6).")
    parser.add_argument("--task", type=int, default=0, help="Task index (default: 0).")
    parser.add_argument("--grid", type=int, default=0, help="Grid index within task (default: 0).")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
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
    print(f"  origin (north, east): {grid.minimum_north_position}, {grid.minimum_east_position}")
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

    csv_path = (
        args.source / f"{grid.filename}.csv"
        if args.source.is_dir()
        else args.source.with_name(f"{grid.filename}.csv")
    )
    np.savetxt(csv_path, arr, delimiter=",", fmt="%.6f")
    print(f"\nCSV written: {csv_path}")


if __name__ == "__main__":
    main()
