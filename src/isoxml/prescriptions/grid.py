"""Public facade for the grid-from-shapefile workflow."""

from isoxml.prescriptions._grid.types import GridFromShpOptions, GridFromShpResult
from isoxml.prescriptions._grid.workflow import build_grid_taskdata_from_shapefile
from isoxml.validation import validate_taskdata_xsd

convert_grid_from_shp = build_grid_taskdata_from_shapefile

__all__ = [
    "GridFromShpOptions",
    "GridFromShpResult",
    "build_grid_taskdata_from_shapefile",
    "convert_grid_from_shp",
    "validate_taskdata_xsd",
]
