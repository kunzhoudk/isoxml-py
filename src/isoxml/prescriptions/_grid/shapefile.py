"""Shapefile loading and normalization services for grid workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import shapely as shp

from isoxml.prescriptions._grid.types import GridFromShpOptions, PreparedGridInputs

if TYPE_CHECKING:
    import geopandas as gpd


def load_geopandas():
    try:
        import geopandas as gpd
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        raise ModuleNotFoundError(
            "geopandas is required for shapefile conversion. Install optional dependencies "
            "with `pip install .[dev]`."
        ) from exc
    return gpd


def iter_polygons(geom):
    if geom is None or geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        yield geom
        return
    if geom.geom_type == "MultiPolygon":
        for polygon in geom.geoms:
            yield polygon
        return
    if geom.geom_type == "GeometryCollection":
        for sub_geom in geom.geoms:
            yield from iter_polygons(sub_geom)


def ensure_polygon_geometries(gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf["geometry"] = gdf.geometry.apply(shp.make_valid)

    polygonal = []
    for geom in gdf.geometry:
        polygons = list(iter_polygons(geom))
        polygonal.append(shp.unary_union(polygons) if polygons else None)

    gdf["geometry"] = polygonal
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    if gdf.empty:
        raise ValueError("No polygon geometry found in shapefile.")
    return gdf


def auto_value_field(gdf: "gpd.GeoDataFrame") -> str:
    numeric_cols = list(gdf.select_dtypes(include=["number"]).columns)
    if not numeric_cols:
        raise ValueError("No numeric field found. Please pass --value-field.")

    priority_keywords = ["rate", "dose", "value", "amount", "kg", "fert", "app"]
    for keyword in priority_keywords:
        for col in numeric_cols:
            if keyword in col.lower():
                return col
    return numeric_cols[0]


def resolve_value_field(gdf: "gpd.GeoDataFrame", requested: str | None) -> str:
    if requested is None:
        return auto_value_field(gdf)
    if requested not in gdf.columns:
        raise ValueError(f"Field '{requested}' does not exist in shapefile.")
    if not np.issubdtype(gdf[requested].dtype, np.number):
        raise ValueError(f"Field '{requested}' is not numeric.")
    return requested


def normalize_unit_text(raw_unit: str | None) -> str | None:
    if raw_unit is None:
        return None
    token = str(raw_unit).strip().lower()
    if not token:
        return None
    compact = token.replace(" ", "").replace("_", "").replace("-", "")
    compact = compact.replace("²", "2")

    if compact in {"kg/ha", "kg/ha1", "kgha", "kg/hm2", "kg/hm^2", "kg/公顷"}:
        return "kg/ha"
    if compact in {"mg/m2", "mg/m^2", "mgm2"}:
        return "ddi"
    return None


def detect_unit_from_shp(
    gdf: "gpd.GeoDataFrame",
    value_field: str,
) -> tuple[str | None, str | None]:
    candidate_cols: list[str] = []
    paired_col = f"{value_field}_unit"
    if paired_col in gdf.columns:
        candidate_cols.append(paired_col)

    preferred = {
        "unit",
        "units",
        "uom",
        "value_unit",
        "rate_unit",
        "dose_unit",
        "app_unit",
        "application_unit",
    }
    for col in gdf.columns:
        if col == "geometry":
            continue
        col_lower = col.lower()
        if col_lower in preferred or col_lower.endswith("_unit"):
            if col not in candidate_cols:
                candidate_cols.append(col)

    for col in candidate_cols:
        series = gdf[col].dropna()
        if series.empty:
            continue
        normalized = {
            unit
            for unit in (normalize_unit_text(v) for v in series.unique())
            if unit is not None
        }
        if len(normalized) == 1:
            return next(iter(normalized)), col
    return None, None


def resolve_value_unit(
    gdf: "gpd.GeoDataFrame",
    requested_unit: str,
    value_field: str,
) -> tuple[str, str]:
    if requested_unit != "auto":
        return requested_unit, "cli"

    detected, column = detect_unit_from_shp(gdf, value_field)
    if detected is not None:
        return detected, f"shp:{column}"
    return "ddi", "default"


def _read_polygon_shapefile(
    path,
    input_crs: str | None,
):
    gpd = load_geopandas()
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        if input_crs:
            gdf = gdf.set_crs(input_crs)
        else:
            raise ValueError("Input shapefile has no CRS. Pass --input-crs.")
    return ensure_polygon_geometries(gdf)


def prepare_grid_inputs(options: GridFromShpOptions) -> PreparedGridInputs:
    """Load and normalize shapefile inputs for the grid workflow."""

    if not options.shp_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {options.shp_path}")
    if options.boundary_shp is None:
        raise ValueError("Missing --boundary-shp. Boundary shapefile is required for PFD.")
    if not options.boundary_shp.exists():
        raise FileNotFoundError(f"Boundary shapefile not found: {options.boundary_shp}")

    gdf = _read_polygon_shapefile(options.shp_path, options.input_crs)
    value_field = resolve_value_field(gdf, options.value_field)
    effective_unit, unit_source = resolve_value_unit(gdf, options.value_unit, value_field)

    gdf_boundary = _read_polygon_shapefile(options.boundary_shp, options.input_crs)
    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    gdf_boundary_wgs84 = gdf_boundary.to_crs("EPSG:4326")
    metric_crs = gdf_wgs84.estimate_utm_crs()
    if metric_crs is None:
        raise ValueError("Could not estimate a projected CRS from input geometry.")

    gdf_metric = gdf_wgs84.to_crs(metric_crs)
    gdf_boundary_metric = gdf_boundary_wgs84.to_crs(metric_crs)
    rx_metric_union = shp.unary_union(gdf_metric.geometry.values)
    rx_wgs84_union = shp.unary_union(gdf_wgs84.geometry.values)
    boundary_metric_union = shp.unary_union(gdf_boundary_metric.geometry.values)
    boundary_wgs84_union = shp.unary_union(gdf_boundary_wgs84.geometry.values)
    if boundary_metric_union.is_empty:
        raise ValueError("Boundary geometry is empty after projection.")
    if rx_metric_union.is_empty or rx_wgs84_union.is_empty:
        raise ValueError("Prescription geometry is empty after projection.")

    return PreparedGridInputs(
        gdf_wgs84=gdf_wgs84,
        gdf_boundary_wgs84=gdf_boundary_wgs84,
        rx_metric_union=rx_metric_union,
        rx_wgs84_union=rx_wgs84_union,
        boundary_metric_union=boundary_metric_union,
        boundary_wgs84_union=boundary_wgs84_union,
        value_field=value_field,
        effective_unit=effective_unit,
        unit_source=unit_source,
    )
