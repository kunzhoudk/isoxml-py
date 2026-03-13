from pathlib import Path

import numpy as np
import pytest
import shapely as shp

import isoxml.models.base.v3 as iso3
from isoxml.geometry import ShapelyConverterV3
from isoxml.grids import decode_grid_binary
from isoxml.prescriptions import GridFromShpOptions, build_grid_taskdata_from_shapefile

gpd = pytest.importorskip("geopandas")

REPO_ROOT = Path(__file__).resolve().parents[2]


def _options(
    shp_path: Path,
    boundary_shp: Path,
    *,
    boundary_mask: str = "touch",
    grid_extent: str = "boundary",
    grid_type: str = "1",
    value_unit: str = "kg/ha",
    cell_size_m: float = 3.0,
) -> GridFromShpOptions:
    return GridFromShpOptions(
        shp_path=shp_path,
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
        boundary_shp=boundary_shp,
        software_manufacturer="isoxml-py",
        software_version="0.1.0",
    )


def _grid_boxes_wgs84(grid) -> shp.Geometry:
    rows = int(grid.maximum_row)
    cols = int(grid.maximum_column)
    min_north = float(grid.minimum_north_position)
    min_east = float(grid.minimum_east_position)
    cell_north = float(grid.cell_north_size)
    cell_east = float(grid.cell_east_size)

    row_idx, col_idx = np.meshgrid(np.arange(rows), np.arange(cols), indexing="ij")
    south = min_north + row_idx.ravel() * cell_north
    west = min_east + col_idx.ravel() * cell_east
    return shp.box(west, south, west + cell_east, south + cell_north)


def _non_zero_mask_for_grid_type_1(grid_bin: bytes, grid) -> np.ndarray:
    arr = decode_grid_binary(grid_bin, grid, scale=False)
    return arr.ravel() != 0


def _partfield_boundary_union(task_data) -> shp.Geometry:
    converter = ShapelyConverterV3()
    polygons = [
        converter.to_shapely_polygon(poly) for poly in task_data.partfields[0].polygons
    ]
    return shp.unary_union(polygons)


def test_build_grid_taskdata_from_shapefile__when_touch__expect_non_zero_cells_intersect_boundary():
    result = build_grid_taskdata_from_shapefile(
        _options(
            REPO_ROOT / "examples" / "input" / "big" / "shp" / "Rx.shp",
            REPO_ROOT / "examples" / "input" / "big" / "boundary" / "Boundary.shp",
            boundary_mask="touch",
            grid_extent="boundary",
            cell_size_m=3.0,
        )
    )
    grid = result.task_data.tasks[0].grids[0]
    grid_bin = result.refs[grid.filename]
    non_zero = _non_zero_mask_for_grid_type_1(grid_bin, grid)
    boxes = _grid_boxes_wgs84(grid)
    boundary = _partfield_boundary_union(result.task_data)

    non_zero_outside = np.logical_and(non_zero, ~shp.intersects(boundary, boxes))
    assert int(np.count_nonzero(non_zero_outside)) == 0


def test_build_grid_taskdata_from_shapefile__when_strict__expect_non_zero_cells_fully_inside_boundary():
    result = build_grid_taskdata_from_shapefile(
        _options(
            REPO_ROOT / "examples" / "input" / "small" / "shp" / "Rx.shp",
            REPO_ROOT / "examples" / "input" / "small" / "boundary" / "Boundary.shp",
            boundary_mask="strict",
            grid_extent="boundary",
            cell_size_m=3.0,
        )
    )
    grid = result.task_data.tasks[0].grids[0]
    grid_bin = result.refs[grid.filename]
    non_zero = _non_zero_mask_for_grid_type_1(grid_bin, grid)
    boxes = _grid_boxes_wgs84(grid)
    boundary = _partfield_boundary_union(result.task_data)

    non_zero_not_covered = np.logical_and(non_zero, ~shp.covers(boundary, boxes))
    assert int(np.count_nonzero(non_zero_not_covered)) == 0


def test_build_grid_taskdata_from_shapefile__when_grid_extent_boundary__expect_grid_bbox_matches_boundary_bbox():
    boundary_path = REPO_ROOT / "examples" / "input" / "big" / "boundary" / "Boundary.shp"
    result = build_grid_taskdata_from_shapefile(
        _options(
            REPO_ROOT / "examples" / "input" / "big" / "shp" / "Rx.shp",
            boundary_path,
            boundary_mask="touch",
            grid_extent="boundary",
            cell_size_m=3.0,
        )
    )
    grid = result.task_data.tasks[0].grids[0]

    boundary_gdf = gpd.read_file(boundary_path).to_crs("EPSG:4326")
    b_minx, b_miny, b_maxx, b_maxy = boundary_gdf.total_bounds

    g_minx = float(grid.minimum_east_position)
    g_miny = float(grid.minimum_north_position)
    g_maxx = g_minx + float(grid.cell_east_size) * int(grid.maximum_column)
    g_maxy = g_miny + float(grid.cell_north_size) * int(grid.maximum_row)

    assert g_minx == pytest.approx(float(b_minx), abs=1e-6)
    assert g_miny == pytest.approx(float(b_miny), abs=1e-6)
    assert g_maxx == pytest.approx(float(b_maxx), abs=1e-6)
    assert g_maxy == pytest.approx(float(b_maxy), abs=1e-6)


def test_build_grid_taskdata_from_shapefile__when_auto_and_explicit_units__expect_expected_unit_resolution_and_scaling():
    shp_path = REPO_ROOT / "examples" / "input" / "small" / "shp" / "Rx.shp"
    boundary_path = REPO_ROOT / "examples" / "input" / "small" / "boundary" / "Boundary.shp"

    auto_result = build_grid_taskdata_from_shapefile(
        _options(
            shp_path,
            boundary_path,
            value_unit="auto",
            grid_type="1",
            grid_extent="boundary",
            cell_size_m=3.0,
        )
    )
    assert auto_result.effective_unit == "kg/ha"
    assert auto_result.unit_source == "shp:unit"
    assert auto_result.task_data.tasks[0].grids[0].type == iso3.GridType.GridType1
    assert "GRD00000" in auto_result.refs

    kg_result = build_grid_taskdata_from_shapefile(
        _options(
            shp_path,
            boundary_path,
            value_unit="kg/ha",
            grid_type="2",
            grid_extent="boundary",
            cell_size_m=3.0,
        )
    )
    ddi_result = build_grid_taskdata_from_shapefile(
        _options(
            shp_path,
            boundary_path,
            value_unit="ddi",
            grid_type="2",
            grid_extent="boundary",
            cell_size_m=3.0,
        )
    )

    kg_grid = kg_result.task_data.tasks[0].grids[0]
    ddi_grid = ddi_result.task_data.tasks[0].grids[0]
    assert kg_grid.type == iso3.GridType.GridType2
    assert ddi_grid.type == iso3.GridType.GridType2
    assert "GRD00000" in kg_result.refs
    assert "GRD00000" in ddi_result.refs

    kg_raw = decode_grid_binary(kg_result.refs[kg_grid.filename], kg_grid, scale=False)
    ddi_raw = decode_grid_binary(ddi_result.refs[ddi_grid.filename], ddi_grid, scale=False)
    non_zero = ddi_raw != 0
    assert np.all(kg_raw[non_zero] == ddi_raw[non_zero] * 100)
