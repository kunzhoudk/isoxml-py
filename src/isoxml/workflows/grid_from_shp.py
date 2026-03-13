"""Compatibility wrapper for the legacy `isoxml.workflows.grid_from_shp` module."""

from isoxml.prescriptions.grid import (
    GridFromShpOptions,
    GridFromShpResult,
    build_grid_taskdata_from_shapefile,
    convert_grid_from_shp,
    validate_taskdata_xsd,
)

__all__ = [
    "GridFromShpOptions",
    "GridFromShpResult",
    "build_grid_taskdata_from_shapefile",
    "convert_grid_from_shp",
    "validate_taskdata_xsd",
]
