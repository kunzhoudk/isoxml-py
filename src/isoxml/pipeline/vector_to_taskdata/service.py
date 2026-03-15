"""Orchestration entry point for the vector-to-taskdata pipeline."""

from __future__ import annotations

import math

import shapely as shp

from isoxml.pipeline.vector_to_taskdata.geometry import (
    ensure_polygon_gdf,
    rasterize,
    resolve_value_field,
    split_embedded_boundary,
)
from isoxml.pipeline.vector_to_taskdata.inputs import load_vector_gdf, resolve_value_unit
from isoxml.pipeline.vector_to_taskdata.taskdata import build_result
from isoxml.pipeline.vector_to_taskdata.types import (
    VectorToTaskDataOptions,
    VectorToTaskDataResult,
)


def convert(options: VectorToTaskDataOptions) -> VectorToTaskDataResult:
    """Build ISOXML task data and binary grid from an application-map vector file."""
    gdf = ensure_polygon_gdf(
        load_vector_gdf(options.source_path, input_crs=options.input_crs, label="Input")
    )
    if options.boundary_path is None:
        gdf, gdf_boundary = split_embedded_boundary(
            gdf,
            requested_value_field=options.value_field,
        )
    else:
        gdf_boundary = ensure_polygon_gdf(
            load_vector_gdf(
                options.boundary_path,
                input_crs=options.input_crs,
                label="Boundary",
            )
        )

    value_field = resolve_value_field(gdf, options.value_field)
    effective_unit, unit_source = resolve_value_unit(gdf, options.value_unit, value_field)

    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    gdf_boundary_wgs84 = gdf_boundary.to_crs("EPSG:4326")
    metric_crs = gdf_wgs84.estimate_utm_crs()
    if metric_crs is None:
        raise ValueError("Could not estimate a UTM CRS from the input geometry.")

    gdf_metric = gdf_wgs84.to_crs(metric_crs)
    gdf_boundary_metric = gdf_boundary_wgs84.to_crs(metric_crs)
    rx_metric = shp.unary_union(gdf_metric.geometry.values)
    rx_wgs84 = shp.unary_union(gdf_wgs84.geometry.values)
    boundary_metric = shp.unary_union(gdf_boundary_metric.geometry.values)
    boundary_wgs84 = shp.unary_union(gdf_boundary_wgs84.geometry.values)

    if boundary_metric.is_empty:
        raise ValueError("Boundary geometry is empty after projection.")
    if rx_metric.is_empty:
        raise ValueError("Application-map geometry is empty after projection.")

    if options.grid_extent == "boundary":
        extent_metric = boundary_metric
        extent_wgs84 = boundary_wgs84
    elif options.grid_extent == "union":
        extent_metric = shp.unary_union([rx_metric, boundary_metric])
        extent_wgs84 = shp.unary_union([rx_wgs84, boundary_wgs84])
    else:
        extent_metric = rx_metric
        extent_wgs84 = rx_wgs84

    if extent_metric.is_empty or extent_wgs84.is_empty:
        raise ValueError(f"Grid extent is empty (grid_extent={options.grid_extent!r}).")

    bounds_m = extent_metric.bounds
    cols = max(1, math.ceil((bounds_m[2] - bounds_m[0]) / options.cell_size_m))
    rows = max(1, math.ceil((bounds_m[3] - bounds_m[1]) / options.cell_size_m))

    grid_values, coverage, _ox, _oy, rows, cols = rasterize(
        gdf_grid=gdf_wgs84,
        boundary_geom=boundary_wgs84,
        value_field=value_field,
        rows=rows,
        cols=cols,
        grid_bounds=extent_wgs84.bounds,
        boundary_mask=options.boundary_mask,
    )
    return build_result(
        options=options,
        gdf_boundary_wgs84=gdf_boundary_wgs84,
        boundary_metric=boundary_metric,
        boundary_wgs84=boundary_wgs84,
        extent_wgs84=extent_wgs84,
        rows=rows,
        cols=cols,
        coverage=coverage,
        grid_values=grid_values,
        value_field=value_field,
        effective_unit=effective_unit,
        unit_source=unit_source,
    )
