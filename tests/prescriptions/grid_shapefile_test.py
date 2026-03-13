from pathlib import Path

import pytest
import shapely as shp

from isoxml.prescriptions._grid.shapefile import (
    detect_unit_from_shp,
    ensure_polygon_geometries,
    normalize_unit_text,
    prepare_grid_inputs,
    resolve_value_field,
    resolve_value_unit,
)
from isoxml.prescriptions._grid.types import GridFromShpOptions

gpd = pytest.importorskip("geopandas")

REPO_ROOT = Path(__file__).resolve().parents[2]


def _sample_options() -> GridFromShpOptions:
    return GridFromShpOptions(
        shp_path=REPO_ROOT / "examples" / "input" / "small" / "shp" / "Rx.shp",
        boundary_shp=REPO_ROOT / "examples" / "input" / "small" / "boundary" / "Boundary.shp",
        value_field=None,
        value_unit="auto",
        grid_type="1",
        xml_version="3",
        cell_size_m=3.0,
        boundary_mask="touch",
        grid_extent="boundary",
    )


def test_normalize_unit_text__when_common_variants__expect_normalized_tokens():
    assert normalize_unit_text("kg/ha") == "kg/ha"
    assert normalize_unit_text("KG_HA") == "kg/ha"
    assert normalize_unit_text("mg/m²") == "ddi"
    assert normalize_unit_text("mg/m^2") == "ddi"
    assert normalize_unit_text("unknown") is None


def test_resolve_value_field__when_auto__expect_rate_like_column_preferred():
    gdf = gpd.GeoDataFrame(
        {"dose": [1], "rate_value": [2], "geometry": [shp.Point(0, 0)]},
        geometry="geometry",
        crs="EPSG:4326",
    )

    assert resolve_value_field(gdf, None) == "rate_value"


def test_detect_unit_from_shp__when_unit_column_present__expect_detected_from_shapefile():
    gdf = gpd.GeoDataFrame(
        {"rate": [100.0, 200.0], "unit": ["kg/ha", "kg/ha"], "geometry": [shp.Point(0, 0), shp.Point(1, 1)]},
        geometry="geometry",
        crs="EPSG:4326",
    )

    detected, column = detect_unit_from_shp(gdf, "rate")
    effective_unit, source = resolve_value_unit(gdf, "auto", "rate")

    assert detected == "kg/ha"
    assert column == "unit"
    assert effective_unit == "kg/ha"
    assert source == "shp:unit"


def test_ensure_polygon_geometries__when_non_polygon_rows_present__expect_only_polygonal_geometries_kept():
    gdf = gpd.GeoDataFrame(
        {
            "value": [1, 2],
            "geometry": [
                shp.GeometryCollection(
                    [
                        shp.Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
                        shp.Point(5, 5),
                    ]
                ),
                shp.LineString([(0, 0), (1, 1)]),
            ],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

    cleaned = ensure_polygon_geometries(gdf)

    assert len(cleaned) == 1
    assert cleaned.geometry.iloc[0].geom_type == "Polygon"


def test_prepare_grid_inputs__when_sample_files__expect_expected_metadata_and_non_empty_unions():
    prepared = prepare_grid_inputs(_sample_options())

    assert prepared.value_field == "rate"
    assert prepared.effective_unit == "kg/ha"
    assert prepared.unit_source == "shp:unit"
    assert not prepared.rx_wgs84_union.is_empty
    assert not prepared.boundary_wgs84_union.is_empty
