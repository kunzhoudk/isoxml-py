from pathlib import Path

import numpy as np
import pytest
import shapely as shp

import isoxml.models.base.v3 as iso3
from isoxml.grid.codec import decode
from isoxml.geometry.shapely import ShapelyConverterV3
from isoxml.pipeline.vector_to_taskdata import VectorToTaskDataOptions, convert

gpd = pytest.importorskip("geopandas")

REPO_ROOT = Path(__file__).resolve().parents[2]


def _options(
    source_path: Path,
    boundary_path: Path | None,
    *,
    boundary_mask: str = "touch",
    grid_extent: str = "boundary",
    grid_type: str = "1",
    value_unit: str = "kg/ha",
    cell_size_m: float = 3.0,
) -> VectorToTaskDataOptions:
    return VectorToTaskDataOptions(
        source_path=source_path,
        value_field="rate",
        ddi=6,
        value_unit=value_unit,
        grid_type=grid_type,
        xml_version="3",
        cell_size_m=cell_size_m,
        boundary_mask=boundary_mask,
        grid_extent=grid_extent,
        input_crs=None,
        partfield_name=None,
        boundary_path=boundary_path,
        software_manufacturer="isoxml-py",
        software_version="0.1.0",
    )


def _grid_boxes_wgs84(grid) -> shp.Geometry:
    rows = int(grid.maximum_row)
    cols = int(grid.maximum_column)
    min_n = float(grid.minimum_north_position)
    min_e = float(grid.minimum_east_position)
    cn = float(grid.cell_north_size)
    ce = float(grid.cell_east_size)
    ri, ci = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    south = min_n + ri.ravel() * cn
    west = min_e + ci.ravel() * ce
    return shp.box(west, south, west + ce, south + cn)


def _non_zero_mask(grid_bin: bytes, grid) -> np.ndarray:
    return decode(grid_bin, grid, scale=False).ravel() != 0


def _boundary_union(task_data) -> shp.Geometry:
    conv = ShapelyConverterV3()
    return shp.unary_union(
        [conv.to_shapely_polygon(p) for p in task_data.partfields[0].polygons]
    )


def test_touch__non_zero_cells_intersect_boundary():
    result = convert(
        _options(
            REPO_ROOT / "examples/input/big/shp/Rx.shp",
            REPO_ROOT / "examples/input/big/boundary/Boundary.shp",
            boundary_mask="touch",
            grid_extent="boundary",
        )
    )
    grid = result.task_data.tasks[0].grids[0]
    grid_bin = result.refs[grid.filename]
    non_zero = _non_zero_mask(grid_bin, grid)
    boxes = _grid_boxes_wgs84(grid)
    boundary = _boundary_union(result.task_data)
    outside = np.logical_and(non_zero, ~shp.intersects(boundary, boxes))
    assert int(np.count_nonzero(outside)) == 0


def test_strict__non_zero_cells_fully_inside_boundary():
    result = convert(
        _options(
            REPO_ROOT / "examples/input/small/shp/Rx.shp",
            REPO_ROOT / "examples/input/small/boundary/Boundary.shp",
            boundary_mask="strict",
            grid_extent="boundary",
        )
    )
    grid = result.task_data.tasks[0].grids[0]
    grid_bin = result.refs[grid.filename]
    non_zero = _non_zero_mask(grid_bin, grid)
    boxes = _grid_boxes_wgs84(grid)
    boundary = _boundary_union(result.task_data)
    not_covered = np.logical_and(non_zero, ~shp.covers(boundary, boxes))
    assert int(np.count_nonzero(not_covered)) == 0


def test_grid_extent_boundary__grid_bbox_matches_boundary_bbox():
    boundary_path = REPO_ROOT / "examples/input/big/boundary/Boundary.shp"
    result = convert(
        _options(
            REPO_ROOT / "examples/input/big/shp/Rx.shp",
            boundary_path,
            boundary_mask="touch",
            grid_extent="boundary",
        )
    )
    grid = result.task_data.tasks[0].grids[0]
    b_gdf = gpd.read_file(boundary_path).to_crs("EPSG:4326")
    b_minx, b_miny, b_maxx, b_maxy = b_gdf.total_bounds
    g_minx = float(grid.minimum_east_position)
    g_miny = float(grid.minimum_north_position)
    g_maxx = g_minx + float(grid.cell_east_size) * int(grid.maximum_column)
    g_maxy = g_miny + float(grid.cell_north_size) * int(grid.maximum_row)
    assert g_minx == pytest.approx(float(b_minx), abs=1e-6)
    assert g_miny == pytest.approx(float(b_miny), abs=1e-6)
    assert g_maxx == pytest.approx(float(b_maxx), abs=1e-6)
    assert g_maxy == pytest.approx(float(b_maxy), abs=1e-6)


def test_auto_and_explicit_units__expected_scaling():
    source_path = REPO_ROOT / "examples/input/small/shp/Rx.shp"
    boundary_path = REPO_ROOT / "examples/input/small/boundary/Boundary.shp"

    auto_result = convert(
        _options(source_path, boundary_path, value_unit="auto", grid_type="1")
    )
    assert auto_result.effective_unit == "kg/ha"
    assert auto_result.unit_source == "vector:unit"
    assert auto_result.task_data.tasks[0].grids[0].type == iso3.GridType.GridType1
    assert "GRD00000" in auto_result.refs

    kg_result = convert(
        _options(source_path, boundary_path, value_unit="kg/ha", grid_type="2")
    )
    ddi_result = convert(
        _options(source_path, boundary_path, value_unit="ddi", grid_type="2")
    )

    kg_grid = kg_result.task_data.tasks[0].grids[0]
    ddi_grid = ddi_result.task_data.tasks[0].grids[0]
    assert kg_grid.type == iso3.GridType.GridType2
    assert ddi_grid.type == iso3.GridType.GridType2

    kg_raw = decode(kg_result.refs[kg_grid.filename], kg_grid, scale=False)
    ddi_raw = decode(ddi_result.refs[ddi_grid.filename], ddi_grid, scale=False)
    non_zero = ddi_raw != 0
    assert np.all(kg_raw[non_zero] == ddi_raw[non_zero] * 100)


def test_geojson_embedded_boundary__string_numeric_value_field_is_accepted():
    result = convert(
        VectorToTaskDataOptions(
            source_path=REPO_ROOT
            / "examples/input/test_shp_application_map_with_boundary.geojson",
            boundary_path=None,
            value_field="dose",
            ddi=6,
            value_unit="kg/ha",
            grid_type="1",
            xml_version="4",
            cell_size_m=3.0,
            boundary_mask="touch",
            grid_extent="boundary",
            input_crs=None,
            partfield_name=None,
            software_manufacturer="isoxml-py",
            software_version="0.1.0",
        )
    )

    grid = result.task_data.tasks[0].grids[0]
    assert result.value_field == "dose"
    assert result.effective_unit == "kg/ha"
    assert int(grid.maximum_row) > 0
    assert int(grid.maximum_column) > 0
    assert grid.filename in result.refs
