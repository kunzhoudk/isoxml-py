"""Geometry preparation and rasterisation helpers for vector-to-taskdata conversion."""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import shapely as shp
from pandas.api.types import is_numeric_dtype

from isoxml.pipeline.vector_to_taskdata.inputs import trim

if TYPE_CHECKING:
    import geopandas as gpd

_BOUNDARY_LABELS = {
    "border",
    "boundary",
    "fieldboundary",
    "partfieldboundary",
    "fieldborder",
}


def _coerce_numeric_column(gdf: "gpd.GeoDataFrame", column: str) -> bool:
    series = gdf[column]
    if is_numeric_dtype(series):
        return True

    converted = pd.to_numeric(series, errors="coerce")
    non_null_mask = series.notna()
    if not bool(non_null_mask.any()):
        return False
    if converted[non_null_mask].isna().any():
        return False

    gdf[column] = converted
    return True


def iter_polygons(geom):
    if geom is None or geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        yield geom
    elif geom.geom_type == "MultiPolygon":
        yield from geom.geoms
    elif geom.geom_type == "GeometryCollection":
        for sub in geom.geoms:
            yield from iter_polygons(sub)


def ensure_polygon_gdf(gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf["geometry"] = gdf.geometry.apply(shp.make_valid)
    gdf["geometry"] = [shp.unary_union(list(iter_polygons(g))) or None for g in gdf.geometry]
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    if gdf.empty:
        raise ValueError("No polygon geometry found in the vector input.")
    return gdf


def _normalize_boundary_label(value: object) -> str | None:
    if value is None:
        return None
    token = str(value).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    return token or None


def split_embedded_boundary(
    gdf: "gpd.GeoDataFrame",
    *,
    requested_value_field: str | None = None,
) -> tuple["gpd.GeoDataFrame", "gpd.GeoDataFrame"]:
    """Split a single vector layer into application polygons and a boundary polygon."""
    for col in gdf.columns:
        if col == "geometry":
            continue
        if gdf[col].dtype != object:
            continue
        labels = gdf[col].map(_normalize_boundary_label)
        mask = labels.isin(_BOUNDARY_LABELS)
        if int(mask.sum()) == 1:
            app_gdf = gdf.loc[~mask].copy()
            boundary_gdf = gdf.loc[mask].copy()
            if app_gdf.empty:
                raise ValueError("Embedded boundary detection left no application-map features.")
            return app_gdf, boundary_gdf

    if requested_value_field and requested_value_field in gdf.columns:
        mask = gdf[requested_value_field].isna()
        if int(mask.sum()) == 1:
            app_gdf = gdf.loc[~mask].copy()
            boundary_gdf = gdf.loc[mask].copy()
            if app_gdf.empty:
                raise ValueError("Embedded boundary detection left no application-map features.")
            return app_gdf, boundary_gdf

    raise ValueError(
        "boundary_path is required unless the input vector contains exactly one "
        "boundary feature labelled 'border' or 'boundary'."
    )


def auto_value_field(gdf: "gpd.GeoDataFrame") -> str:
    numeric_cols = list(gdf.select_dtypes(include=["number"]).columns)
    for col in gdf.columns:
        if col == "geometry" or col in numeric_cols:
            continue
        if _coerce_numeric_column(gdf, col):
            numeric_cols.append(col)
    if not numeric_cols:
        raise ValueError("No numeric field found. Pass value_field explicitly.")
    priority = ["rate", "dose", "value", "amount", "kg", "fert", "app"]
    for kw in priority:
        for col in numeric_cols:
            if kw in col.lower():
                return col
    return numeric_cols[0]


def resolve_value_field(gdf: "gpd.GeoDataFrame", requested: str | None) -> str:
    if requested is None:
        return auto_value_field(gdf)
    if requested not in gdf.columns:
        raise ValueError(f"Field '{requested}' does not exist in the vector input.")
    if not _coerce_numeric_column(gdf, requested):
        raise ValueError(f"Field '{requested}' is not numeric.")
    return requested


def rasterize(
    gdf_grid: "gpd.GeoDataFrame",
    boundary_geom: shp.Geometry,
    value_field: str,
    rows: int,
    cols: int,
    grid_bounds: tuple[float, float, float, float],
    boundary_mask: str,
) -> tuple[np.ndarray, np.ndarray, float, float, int, int]:
    """Rasterize application-map polygons onto a regular grid."""
    if rows <= 0 or cols <= 0:
        raise ValueError("Grid rows/cols must be > 0.")
    if boundary_mask not in {"center", "strict", "touch"}:
        raise ValueError(f"Unsupported boundary_mask: {boundary_mask!r}")

    minx, miny, maxx, maxy = [float(v) for v in grid_bounds]
    cell_e = (maxx - minx) / cols
    cell_n = (maxy - miny) / rows
    if cell_e <= 0 or cell_n <= 0:
        raise ValueError("Invalid grid bounds: non-positive cell size.")

    grid_data = np.zeros((rows, cols), dtype=np.float32)
    coverage = np.zeros((rows, cols), dtype=bool)

    for feature in gdf_grid[[value_field, "geometry"]].itertuples(index=False):
        value = float(feature[0])
        if not np.isfinite(value):
            continue
        geom = feature[1]
        for polygon in iter_polygons(geom):
            if polygon.is_empty:
                continue
            px0, py0, px1, py1 = polygon.bounds
            c0 = max(0, int(math.floor((px0 - minx) / cell_e)))
            c1 = min(cols - 1, int(math.ceil((px1 - minx) / cell_e)) - 1)
            r0 = max(0, int(math.floor((py0 - miny) / cell_n)))
            r1 = min(rows - 1, int(math.ceil((py1 - miny) / cell_n)) - 1)
            if c0 > c1 or r0 > r1:
                continue

            lc = c1 - c0 + 1
            lr = r1 - r0 + 1

            if boundary_mask == "touch":
                col_off = np.arange(lc, dtype=np.int32)
                row_off = np.arange(lr, dtype=np.int32)
                cg, rg = np.meshgrid(col_off, row_off)
                west = minx + (c0 + cg.ravel()) * cell_e
                south = miny + (r0 + rg.ravel()) * cell_n
                boxes = shp.box(west, south, west + cell_e, south + cell_n)
                keep = np.logical_and(
                    shp.intersects(polygon, boxes),
                    shp.intersects(boundary_geom, boxes),
                )
                if not np.any(keep):
                    continue
                local_r = rg.ravel()[keep]
                local_c = cg.ravel()[keep]
            else:
                xs = minx + (np.arange(c0, c1 + 1, dtype=np.float64) + 0.5) * cell_e
                ys = miny + (np.arange(r0, r1 + 1, dtype=np.float64) + 0.5) * cell_n
                xg, yg = np.meshgrid(xs, ys)
                pts = shp.points(xg.ravel(), yg.ravel())
                keep = shp.covers(polygon, pts)
                if boundary_mask == "center":
                    keep &= shp.covers(boundary_geom, pts)
                if not np.any(keep):
                    continue
                hit = np.flatnonzero(keep)
                local_r = hit // lc
                local_c = hit % lc
                if boundary_mask == "strict":
                    west = minx + (c0 + local_c) * cell_e
                    south = miny + (r0 + local_r) * cell_n
                    boxes = shp.box(west, south, west + cell_e, south + cell_n)
                    bkeep = shp.covers(boundary_geom, boxes)
                    if not np.any(bkeep):
                        continue
                    local_r = local_r[bkeep]
                    local_c = local_c[bkeep]

            grid_data[local_r + r0, local_c + c0] = value
            coverage[local_r + r0, local_c + c0] = True

    return grid_data, coverage, minx, miny, rows, cols


def infer_partfield_name(
    gdf: "gpd.GeoDataFrame", source_path: Path, explicit: str | None
) -> str:
    if explicit:
        return trim(explicit, 32)
    for col in gdf.columns:
        if col == "geometry":
            continue
        if gdf[col].dtype == object:
            first = gdf[col].dropna()
            if not first.empty:
                return trim(str(first.iloc[0]), 32)
    return trim(source_path.stem, 32)
