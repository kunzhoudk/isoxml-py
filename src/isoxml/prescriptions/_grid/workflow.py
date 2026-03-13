"""Workflow orchestration for grid-from-shapefile conversions."""

from __future__ import annotations

from isoxml.prescriptions._grid.rasterize import rasterize_grid
from isoxml.prescriptions._grid.shapefile import prepare_grid_inputs
from isoxml.prescriptions._grid.taskdata import assemble_grid_taskdata_result
from isoxml.prescriptions._grid.types import GridFromShpOptions, GridFromShpResult


def build_grid_taskdata_from_shapefile(options: GridFromShpOptions) -> GridFromShpResult:
    """Build ISOXML task data and binary refs from a prescription shapefile."""

    prepared = prepare_grid_inputs(options)
    rasterized = rasterize_grid(
        prepared,
        grid_extent=options.grid_extent,
        boundary_mask_mode=options.boundary_mask,
        cell_size_m=options.cell_size_m,
    )
    return assemble_grid_taskdata_result(options, prepared, rasterized)
