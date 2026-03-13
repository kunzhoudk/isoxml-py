from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import shapely as shp

from isoxml.converter.np_grid import to_numpy_array
from isoxml.converter.shapely_geom import ShapelyConverterV3

gpd = pytest.importorskip("geopandas")

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_SCRIPT = REPO_ROOT / "examples" / "app_map_grid_type_2_from_shp.py"

_SPEC = importlib.util.spec_from_file_location("app_map_grid_type_2_from_shp", EXAMPLE_SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _args(
    shp_path: Path,
    boundary_shp: Path,
    *,
    boundary_mask: str = "touch",
    grid_extent: str = "boundary",
    grid_type: str = "1",
    cell_size_m: float = 3.0,
) -> argparse.Namespace:
    return argparse.Namespace(
        shp_path=shp_path,
        value_field="rate",
        ddi=6,
        value_unit="kg/ha",
        grid_type=grid_type,
        xml_version="3",
        cell_size_m=cell_size_m,
        boundary_mask=boundary_mask,
        grid_extent=grid_extent,
        input_crs=None,
        partfield_name=None,
        boundary_shp=boundary_shp,
        output_dir=REPO_ROOT / "examples" / "output" / "pytest_tmp",
        output_zip=None,
        software_manufacturer="isoxml-py",
        software_version="0.1.0",
        no_xsd_validate=True,
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
    arr = to_numpy_array(grid_bin, grid, scale=False)
    return arr.ravel() != 0


def _partfield_boundary_union(task_data) -> shp.Geometry:
    converter = ShapelyConverterV3()
    polygons = [converter.to_shapely_polygon(poly) for poly in task_data.partfields[0].polygons]
    return shp.unary_union(polygons)


def test__build_isoxml_from_shp__when_touch__expect_non_zero_cells_intersect_boundary():
    args = _args(
        REPO_ROOT / "examples" / "input" / "big" / "shp" / "Rx.shp",
        REPO_ROOT / "examples" / "input" / "big" / "boundary" / "Boundary.shp",
        boundary_mask="touch",
        grid_extent="boundary",
        cell_size_m=3.0,
    )
    task_data, refs, *_ = _MODULE.build_isoxml_from_shp(args)
    grid = task_data.tasks[0].grids[0]
    grid_bin = refs[grid.filename]
    non_zero = _non_zero_mask_for_grid_type_1(grid_bin, grid)
    boxes = _grid_boxes_wgs84(grid)
    boundary = _partfield_boundary_union(task_data)

    non_zero_outside = np.logical_and(non_zero, ~shp.intersects(boundary, boxes))
    assert int(np.count_nonzero(non_zero_outside)) == 0


def test__build_isoxml_from_shp__when_strict__expect_non_zero_cells_fully_inside_boundary():
    args = _args(
        REPO_ROOT / "examples" / "input" / "small" / "shp" / "Rx.shp",
        REPO_ROOT / "examples" / "input" / "small" / "boundary" / "Boundary.shp",
        boundary_mask="strict",
        grid_extent="boundary",
        cell_size_m=3.0,
    )
    task_data, refs, *_ = _MODULE.build_isoxml_from_shp(args)
    grid = task_data.tasks[0].grids[0]
    grid_bin = refs[grid.filename]
    non_zero = _non_zero_mask_for_grid_type_1(grid_bin, grid)
    boxes = _grid_boxes_wgs84(grid)
    boundary = _partfield_boundary_union(task_data)

    non_zero_not_covered = np.logical_and(non_zero, ~shp.covers(boundary, boxes))
    assert int(np.count_nonzero(non_zero_not_covered)) == 0


def test__build_isoxml_from_shp__when_grid_extent_boundary__expect_grid_bbox_matches_boundary_bbox():
    shp_path = REPO_ROOT / "examples" / "input" / "big" / "shp" / "Rx.shp"
    boundary_path = REPO_ROOT / "examples" / "input" / "big" / "boundary" / "Boundary.shp"
    args = _args(
        shp_path,
        boundary_path,
        boundary_mask="touch",
        grid_extent="boundary",
        cell_size_m=3.0,
    )
    task_data, _refs, *_ = _MODULE.build_isoxml_from_shp(args)
    grid = task_data.tasks[0].grids[0]

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
