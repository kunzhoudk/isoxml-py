"""Rasterization services for grid-from-shapefile workflows."""

from __future__ import annotations

import math

import numpy as np
import shapely as shp

from isoxml.prescriptions._grid.shapefile import iter_polygons
from isoxml.prescriptions._grid.types import PreparedGridInputs, RasterizedGrid


def resolve_grid_extent(
    prepared: PreparedGridInputs,
    grid_extent: str,
):
    """Resolve the geometry used to define the output grid extent."""

    if grid_extent == "boundary":
        return prepared.boundary_metric_union, prepared.boundary_wgs84_union
    if grid_extent == "union":
        return (
            shp.unary_union([prepared.rx_metric_union, prepared.boundary_metric_union]),
            shp.unary_union([prepared.rx_wgs84_union, prepared.boundary_wgs84_union]),
        )
    return prepared.rx_metric_union, prepared.rx_wgs84_union


def rasterize_grid(
    prepared: PreparedGridInputs,
    *,
    grid_extent: str,
    boundary_mask_mode: str,
    cell_size_m: float,
) -> RasterizedGrid:
    """Rasterize prescription polygons into an output grid."""

    extent_metric_geom, extent_wgs84_geom = resolve_grid_extent(prepared, grid_extent)
    if extent_metric_geom.is_empty or extent_wgs84_geom.is_empty:
        raise ValueError(f"Grid extent geometry is empty (mode: {grid_extent}).")

    extent_metric_bounds = extent_metric_geom.bounds
    metric_width = float(extent_metric_bounds[2]) - float(extent_metric_bounds[0])
    metric_height = float(extent_metric_bounds[3]) - float(extent_metric_bounds[1])
    cols = max(1, math.ceil(metric_width / cell_size_m))
    rows = max(1, math.ceil(metric_height / cell_size_m))

    grid_values, coverage, _minx, _miny, rows, cols = _rasterize_to_grid(
        gdf_grid=prepared.gdf_wgs84,
        boundary_geom_grid=prepared.boundary_wgs84_union,
        value_field=prepared.value_field,
        rows=rows,
        cols=cols,
        grid_bounds=extent_wgs84_geom.bounds,
        boundary_mask_mode=boundary_mask_mode,
    )
    return RasterizedGrid(
        values=grid_values,
        coverage=coverage,
        rows=rows,
        cols=cols,
        extent_wgs84_bounds=tuple(float(v) for v in extent_wgs84_geom.bounds),
    )


def _rasterize_to_grid(
    gdf_grid,
    boundary_geom_grid: shp.Geometry,
    value_field: str,
    rows: int,
    cols: int,
    grid_bounds: tuple[float, float, float, float],
    boundary_mask_mode: str,
) -> tuple[np.ndarray, np.ndarray, float, float, int, int]:
    if rows <= 0 or cols <= 0:
        raise ValueError("Grid rows/cols must be > 0")
    if boundary_mask_mode not in {"center", "strict", "touch"}:
        raise ValueError(f"Unsupported boundary mask mode: {boundary_mask_mode}")

    minx, miny, maxx, maxy = [float(v) for v in grid_bounds]
    cell_east_size = (maxx - minx) / cols
    cell_north_size = (maxy - miny) / rows
    if cell_east_size <= 0 or cell_north_size <= 0:
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
            p_minx, p_miny, p_maxx, p_maxy = polygon.bounds
            c0 = max(0, int(math.floor((p_minx - minx) / cell_east_size)))
            c1 = min(cols - 1, int(math.ceil((p_maxx - minx) / cell_east_size)) - 1)
            r0 = max(0, int(math.floor((p_miny - miny) / cell_north_size)))
            r1 = min(rows - 1, int(math.ceil((p_maxy - miny) / cell_north_size)) - 1)
            if c0 > c1 or r0 > r1:
                continue

            local_cols = c1 - c0 + 1
            local_rows_count = r1 - r0 + 1

            if boundary_mask_mode == "touch":
                col_offsets = np.arange(local_cols, dtype=np.int32)
                row_offsets = np.arange(local_rows_count, dtype=np.int32)
                col_grid, row_grid = np.meshgrid(col_offsets, row_offsets)

                west = minx + (c0 + col_grid.ravel()) * cell_east_size
                south = miny + (r0 + row_grid.ravel()) * cell_north_size
                cell_boxes = shp.box(
                    west,
                    south,
                    west + cell_east_size,
                    south + cell_north_size,
                )

                poly_mask = shp.intersects(polygon, cell_boxes)
                boundary_mask = shp.intersects(boundary_geom_grid, cell_boxes)
                keep_mask = np.logical_and(poly_mask, boundary_mask)
                if not np.any(keep_mask):
                    continue
                local_rows = row_grid.ravel()[keep_mask]
                local_cols_idx = col_grid.ravel()[keep_mask]
            else:
                xs = minx + (np.arange(c0, c1 + 1, dtype=np.float64) + 0.5) * cell_east_size
                ys = miny + (np.arange(r0, r1 + 1, dtype=np.float64) + 0.5) * cell_north_size
                x_grid, y_grid = np.meshgrid(xs, ys)
                points = shp.points(x_grid.ravel(), y_grid.ravel())
                keep_mask = shp.covers(polygon, points)
                if boundary_mask_mode == "center":
                    keep_mask = np.logical_and(
                        keep_mask,
                        shp.covers(boundary_geom_grid, points),
                    )
                if not np.any(keep_mask):
                    continue

                hit_idx = np.flatnonzero(keep_mask)
                local_rows = hit_idx // local_cols
                local_cols_idx = hit_idx % local_cols

                if boundary_mask_mode == "strict":
                    west = minx + (c0 + local_cols_idx) * cell_east_size
                    south = miny + (r0 + local_rows) * cell_north_size
                    cell_boxes = shp.box(
                        west,
                        south,
                        west + cell_east_size,
                        south + cell_north_size,
                    )
                    boundary_keep_mask = shp.covers(boundary_geom_grid, cell_boxes)
                    if not np.any(boundary_keep_mask):
                        continue
                    local_rows = local_rows[boundary_keep_mask]
                    local_cols_idx = local_cols_idx[boundary_keep_mask]

            hit_rows = local_rows + r0
            hit_cols = local_cols_idx + c0
            grid_data[hit_rows, hit_cols] = value
            coverage[hit_rows, hit_cols] = True

    return grid_data, coverage, minx, miny, rows, cols
