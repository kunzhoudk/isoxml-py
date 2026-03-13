"""
Read an ISOXML Grid Type 2 application map from a TASKDATA directory or zip.

Outputs:
- grid metadata from XML
- decoded numpy array from GRD00000.BIN
- basic statistics
- optional CSV export
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from isoxml.grids import decode_grid_binary
from isoxml.io import load_taskdata_from_path, load_taskdata_from_zip
from isoxml.models.ddi_entities import DDEntity


def load_isoxml(source: Path):
    if source.is_dir():
        return load_taskdata_from_path(source)
    if source.suffix.lower() == ".zip":
        return load_taskdata_from_zip(source)
    raise ValueError(f"Unsupported source: {source}")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]

    # Change this path to your TASKDATA folder or zip file.
    source = base_dir / "output" / "small_xml_v3_auto"

    # Change this if the grid uses a different DDI.
    ddi = DDEntity.from_id(6)

    task_data, ext_refs = load_isoxml(source)

    if not task_data.tasks:
        raise ValueError("No task found in TASKDATA.")

    task = task_data.tasks[0]
    if not task.grids:
        raise ValueError("No GRD element found in task.")

    grid = task.grids[0]
    grid_bin = ext_refs.get(grid.filename)
    if not isinstance(grid_bin, bytes):
        raise ValueError(f"Missing binary data for {grid.filename}.bin")

    grid_data = decode_grid_binary(grid_bin, grid, ddi_list=[ddi], scale=True)
    if grid_data.ndim == 3 and grid_data.shape[-1] == 1:
        grid_data = grid_data[:, :, 0]

    print("Grid metadata")
    print(f"  filename: {grid.filename}.bin")
    print(f"  type: {grid.type}")
    print(f"  rows x cols: {grid.maximum_row} x {grid.maximum_column}")
    print(
        f"  origin north/east: {grid.minimum_north_position}, {grid.minimum_east_position}"
    )
    print(f"  cell north/east: {grid.cell_north_size}, {grid.cell_east_size}")
    print(f"  DDI: {int(ddi.ddi):04d}")

    print("\nDecoded array")
    print(f"  shape: {grid_data.shape}")
    print(f"  dtype: {grid_data.dtype}")
    print(f"  min: {float(np.min(grid_data))}")
    print(f"  max: {float(np.max(grid_data))}")
    print(f"  unique values: {np.unique(grid_data).size}")
    print(f"  non-zero cells: {int(np.count_nonzero(grid_data))}")

    rows_to_show = max(0, grid_data.shape[0])
    cols_to_show = max(8, grid_data.shape[1])
    print(f"\nTop-left preview ({rows_to_show} x {cols_to_show})")
    print(grid_data[:rows_to_show, :cols_to_show])

    csv_path = (
        source / f"{grid.filename}.csv"
        if source.is_dir()
        else base_dir / f"{grid.filename}.csv"
    )
    np.savetxt(csv_path, grid_data, delimiter=",", fmt="%.6f")
    print(f"\nCSV written: {csv_path}")


if __name__ == "__main__":
    main()
