"""Domain types for the grid-from-shapefile workflow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4

if TYPE_CHECKING:
    import geopandas as gpd
    from isoxml.geometry.shapely import ShapelyConverterV3, ShapelyConverterV4


@dataclass(frozen=True)
class GridFromShpOptions:
    """Conversion options for polygon shapefile -> ISOXML grid."""

    shp_path: Path
    value_field: str | None = None
    ddi: int = 6
    value_unit: Literal["auto", "ddi", "kg/ha"] = "auto"
    grid_type: Literal["1", "2"] = "2"
    xml_version: Literal["3", "4"] = "3"
    cell_size_m: float = 10.0
    boundary_mask: Literal["center", "strict", "touch"] = "touch"
    grid_extent: Literal["rx", "boundary", "union"] = "rx"
    input_crs: str | None = None
    partfield_name: str | None = None
    boundary_shp: Path | None = None
    software_manufacturer: str = "kz_isoxml"
    software_version: str = "0.1.0"


@dataclass(frozen=True)
class GridFromShpResult:
    """Result bundle produced by `build_grid_taskdata_from_shapefile`."""

    task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData
    refs: dict[str, bytes]
    value_field: str
    effective_unit: str
    unit_source: str


@dataclass(frozen=True)
class PreparedGridInputs:
    """Normalized and projected shapefile inputs ready for rasterization."""

    gdf_wgs84: "gpd.GeoDataFrame"
    gdf_boundary_wgs84: "gpd.GeoDataFrame"
    rx_metric_union: object
    rx_wgs84_union: object
    boundary_metric_union: object
    boundary_wgs84_union: object
    value_field: str
    effective_unit: str
    unit_source: str


@dataclass(frozen=True)
class RasterizedGrid:
    """Rasterized grid values and metadata before ISOXML serialization."""

    values: object
    coverage: object
    rows: int
    cols: int
    extent_wgs84_bounds: tuple[float, float, float, float]


@dataclass(frozen=True)
class IsoWorkflowContext:
    """Version-specific ISOXML factories and enums used during assembly."""

    iso_module: object
    shapely_converter: "ShapelyConverterV3 | ShapelyConverterV4"
    task_status: object
    transfer_origin: object
