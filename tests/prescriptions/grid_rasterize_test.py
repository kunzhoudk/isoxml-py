from pathlib import Path

import numpy as np
import pytest
import shapely as shp

from isoxml.prescriptions._grid.rasterize import (
    _rasterize_to_grid,
    rasterize_grid,
    resolve_grid_extent,
)
from isoxml.prescriptions._grid.shapefile import prepare_grid_inputs
from isoxml.prescriptions._grid.types import GridFromShpOptions

gpd = pytest.importorskip("geopandas")

REPO_ROOT = Path(__file__).resolve().parents[2]


def _prepared_small():
    options = GridFromShpOptions(
        shp_path=REPO_ROOT / "examples" / "input" / "small" / "shp" / "Rx.shp",
        boundary_shp=REPO_ROOT / "examples" / "input" / "small" / "boundary" / "Boundary.shp",
        value_field="rate",
        value_unit="kg/ha",
        grid_type="1",
        xml_version="3",
        cell_size_m=3.0,
        boundary_mask="touch",
        grid_extent="boundary",
    )
    return prepare_grid_inputs(options)


def test_resolve_grid_extent__when_switching_modes__expect_expected_geometries_returned():
    prepared = _prepared_small()

    boundary_metric, boundary_wgs84 = resolve_grid_extent(prepared, "boundary")
    union_metric, union_wgs84 = resolve_grid_extent(prepared, "union")
    rx_metric, rx_wgs84 = resolve_grid_extent(prepared, "rx")

    assert boundary_metric.equals(prepared.boundary_metric_union)
    assert boundary_wgs84.equals(prepared.boundary_wgs84_union)
    assert rx_metric.equals(prepared.rx_metric_union)
    assert rx_wgs84.equals(prepared.rx_wgs84_union)
    assert union_metric.area >= boundary_metric.area
    assert union_wgs84.area >= rx_wgs84.area


def test_rasterize_grid__when_touch_vs_strict__expect_touch_covers_at_least_as_many_cells():
    prepared = _prepared_small()

    touch = rasterize_grid(
        prepared,
        grid_extent="boundary",
        boundary_mask_mode="touch",
        cell_size_m=3.0,
    )
    strict = rasterize_grid(
        prepared,
        grid_extent="boundary",
        boundary_mask_mode="strict",
        cell_size_m=3.0,
    )

    assert touch.values.shape == (touch.rows, touch.cols)
    assert strict.values.shape == (strict.rows, strict.cols)
    assert int(np.count_nonzero(touch.coverage)) >= int(np.count_nonzero(strict.coverage))


def test_rasterize_grid__when_union_extent__expect_grid_not_smaller_than_boundary_extent():
    prepared = _prepared_small()

    boundary_grid = rasterize_grid(
        prepared,
        grid_extent="boundary",
        boundary_mask_mode="touch",
        cell_size_m=3.0,
    )
    union_grid = rasterize_grid(
        prepared,
        grid_extent="union",
        boundary_mask_mode="touch",
        cell_size_m=3.0,
    )

    assert union_grid.rows >= boundary_grid.rows
    assert union_grid.cols >= boundary_grid.cols


def test__rasterize_to_grid__when_invalid_boundary_mask__expect_error():
    gdf = gpd.GeoDataFrame(
        {"rate": [1.0], "geometry": [shp.Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    boundary = shp.Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])

    with pytest.raises(ValueError, match="Unsupported boundary mask mode"):
        _rasterize_to_grid(
            gdf_grid=gdf,
            boundary_geom_grid=boundary,
            value_field="rate",
            rows=1,
            cols=1,
            grid_bounds=(0.0, 0.0, 1.0, 1.0),
            boundary_mask_mode="invalid",
        )
