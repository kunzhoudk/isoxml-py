from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import shapely as shp

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.grids import to_numpy_array
from isoxml.models.ddi_entities import DDEntity
from isoxml.prescriptions._grid.taskdata import (
    build_iso_context,
    build_taskdata_result,
    infer_partfield_name,
    unit_factor_to_ddi,
)
from isoxml.prescriptions._grid.types import (
    GridFromShpOptions,
    PreparedGridInputs,
    RasterizedGrid,
)

gpd = pytest.importorskip("geopandas")


def _prepared_inputs():
    boundary = shp.Polygon([(10.0, 50.0), (10.01, 50.0), (10.01, 50.01), (10.0, 50.0)])
    rx = shp.Polygon([(10.0, 50.0), (10.005, 50.0), (10.005, 50.005), (10.0, 50.0)])

    gdf_boundary = gpd.GeoDataFrame(
        {"name": ["demo_field"], "geometry": [boundary]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    gdf_rx = gpd.GeoDataFrame(
        {"rate": [150.0], "geometry": [rx]},
        geometry="geometry",
        crs="EPSG:4326",
    )
    metric_crs = gdf_boundary.estimate_utm_crs()

    return PreparedGridInputs(
        gdf_wgs84=gdf_rx,
        gdf_boundary_wgs84=gdf_boundary,
        rx_metric_union=gdf_rx.to_crs(metric_crs).geometry.union_all(),
        rx_wgs84_union=gdf_rx.geometry.union_all(),
        boundary_metric_union=gdf_boundary.to_crs(metric_crs).geometry.union_all(),
        boundary_wgs84_union=gdf_boundary.geometry.union_all(),
        value_field="rate",
        effective_unit="kg/ha",
        unit_source="shp:unit",
    )


def _options(grid_type: str, xml_version: str = "3") -> GridFromShpOptions:
    return GridFromShpOptions(
        shp_path=Path("rx.shp"),
        boundary_shp=Path("boundary.shp"),
        value_field="rate",
        value_unit="kg/ha",
        grid_type=grid_type,
        xml_version=xml_version,
        cell_size_m=10.0,
        boundary_mask="touch",
        grid_extent="boundary",
        partfield_name=None,
    )


def test_build_iso_context__when_version_changes__expect_matching_model_modules():
    context_v3 = build_iso_context("3")
    context_v4 = build_iso_context("4")

    assert context_v3.iso_module is iso3
    assert context_v4.iso_module is iso4


def test_unit_factor_to_ddi__when_supported_and_unsupported_units__expect_expected_behavior():
    ddi = DDEntity.from_id(6)
    assert unit_factor_to_ddi("ddi", ddi=ddi) == 1.0
    assert unit_factor_to_ddi("kg/ha", ddi=ddi) == 100.0

    with pytest.raises(ValueError, match="Unsupported input unit"):
        unit_factor_to_ddi("lb/ac", ddi=ddi)


def test_infer_partfield_name__when_explicit_and_fallback_values__expect_expected_name_resolution():
    gdf = gpd.GeoDataFrame(
        {
            "Name": pd.Series(["demo_field"], dtype="string"),
            "geometry": [shp.Point(10, 50)],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

    assert infer_partfield_name(gdf, Path("boundary.shp"), "manual") == "manual"
    assert infer_partfield_name(gdf, Path("boundary.shp"), None) == "demo_field"


def test_build_taskdata_result__when_grid_type_1__expect_lookup_grid_and_multiple_treatment_zones():
    prepared = _prepared_inputs()
    rasterized = RasterizedGrid(
        values=np.array([[0.0, 10.0], [10.0, 20.0]], dtype=np.float32),
        coverage=np.array([[False, True], [True, True]]),
        rows=2,
        cols=2,
        extent_wgs84_bounds=(10.0, 50.0, 10.02, 50.02),
    )

    result = build_taskdata_result(_options("1"), prepared, rasterized)
    grid = result.task_data.tasks[0].grids[0]
    grid_arr = to_numpy_array(result.refs[grid.filename], grid, scale=False)

    assert grid.type == iso3.GridType.GridType1
    assert len(result.task_data.tasks[0].treatment_zones) == 3
    assert set(np.unique(grid_arr)) == {0, 1, 2}


def test_build_taskdata_result__when_grid_type_2_v4__expect_binary_grid_and_default_zone_reference():
    prepared = _prepared_inputs()
    rasterized = RasterizedGrid(
        values=np.array([[0.0, 10.0], [20.0, 30.0]], dtype=np.float32),
        coverage=np.array([[False, True], [True, True]]),
        rows=2,
        cols=2,
        extent_wgs84_bounds=(10.0, 50.0, 10.02, 50.02),
    )

    result = build_taskdata_result(_options("2", xml_version="4"), prepared, rasterized)
    grid = result.task_data.tasks[0].grids[0]
    raw = to_numpy_array(result.refs[grid.filename], grid, scale=False)
    raw_3d = to_numpy_array(
        result.refs[grid.filename],
        grid,
        ddi_list=[DDEntity.from_id(6)],
        scale=False,
    )

    assert isinstance(result.task_data, iso4.Iso11783TaskData)
    assert grid.type == iso4.GridType.GridType2
    assert grid.treatment_zone_code == 0
    assert raw.shape == (2, 2)
    assert raw_3d.shape == (2, 2, 1)
