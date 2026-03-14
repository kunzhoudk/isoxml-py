"""
Plot ISOXML grid overlay against PFD boundary and print alignment metrics.

Examples:
    .venv/bin/python examples/check_grid_overlay.py examples/output/big_xml_v3_auto
    .venv/bin/python examples/check_grid_overlay.py examples/output/big_xml_v3_auto \
        --shp examples/input/big/shp/Rx.shp --out examples/output/big_xml_v3_auto/overlay.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import shapely as shp
from pyproj import Transformer

from isoxml.grid import decode
from isoxml.geometry import ShapelyConverterV3, ShapelyConverterV4
from isoxml.models import DDEntity
from isoxml.io import read_from_path, read_from_zip


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check overlay between ISOXML grid and PFD boundary.",
    )
    parser.add_argument("source", type=Path, help="TASKDATA directory or zip.")
    parser.add_argument(
        "--task-index",
        type=int,
        default=0,
        help="Which task to read from TASKDATA (0-based; default: 0 = first task).",
    )
    parser.add_argument(
        "--grid-index",
        type=int,
        default=0,
        help="Which grid to read inside the selected task (0-based; default: 0 = first grid).",
    )
    parser.add_argument("--ddi", type=int, default=6, help="DDI for GridType2 decode (default: 6).")
    parser.add_argument("--show-zero", action="store_true", help="Include zero-valued cells in plot.")
    parser.add_argument("--shp", type=Path, default=None, help="Optional shapefile to overlay.")
    parser.add_argument("--out", type=Path, default=None, help="Output PNG path.")
    parser.add_argument(
        "--cells-out",
        type=Path,
        default=None,
        help="Optional GeoJSON output for grid cells (properties: row, col, value).",
    )
    return parser.parse_args()


def load_isoxml(source: Path):
    if source.is_dir():
        return read_from_path(source)
    if source.suffix.lower() == ".zip":
        return read_from_zip(source)
    raise ValueError(f"Unsupported source: {source}")


def get_converter(task_data):
    if getattr(task_data.version_major, "value", None) == "4":
        return ShapelyConverterV4()
    return ShapelyConverterV3()


def get_partfield(task_data, task):
    if not task_data.partfields:
        return None
    if task.partfield_id_ref:
        for partfield in task_data.partfields:
            if partfield.id == task.partfield_id_ref:
                return partfield
    return task_data.partfields[0]


def partfield_union_geometry(task_data, task):
    converter = get_converter(task_data)
    partfield = get_partfield(task_data, task)
    if partfield is None or not partfield.polygons:
        return None
    polys = [converter.to_shapely_polygon(poly) for poly in partfield.polygons]
    return shp.unary_union(polys)


def type1_code_to_value(task_data, task) -> dict[int, float]:
    vpn_by_id = {vpn.id: vpn for vpn in getattr(task_data, "value_presentations", []) if vpn.id}
    mapping: dict[int, float] = {}
    for tz in task.treatment_zones:
        if tz.code is None:
            continue
        code = int(tz.code)
        if not tz.process_data_variables:
            mapping[code] = 0.0
            continue
        pdv = tz.process_data_variables[0]
        raw = float(pdv.process_data_value or 0)
        vpn_ref = pdv.value_presentation_id_ref
        if vpn_ref and vpn_ref in vpn_by_id:
            vpn = vpn_by_id[vpn_ref]
            scale = float(vpn.scale)
            offset = float(vpn.offset)
            mapping[code] = raw * scale + offset
        else:
            mapping[code] = raw
    return mapping


def decode_grid_values(task_data, task, grid, grid_bin: bytes, ddi: DDEntity) -> np.ndarray:
    grid_type = str(getattr(grid.type, "value", grid.type))
    if grid_type == "1":
        arr_code = decode(grid_bin, grid, scale=False)
        code_to_val = type1_code_to_value(task_data, task)
        return np.vectorize(lambda code: code_to_val.get(int(code), 0.0))(arr_code).astype(np.float32)
    arr = decode(grid_bin, grid, ddi_list=[ddi], scale=True)
    if arr.ndim == 3 and arr.shape[-1] == 1:
        arr = arr[:, :, 0]
    return arr.astype(np.float32)


def grid_to_geodataframe(grid, values: np.ndarray, show_zero: bool) -> gpd.GeoDataFrame:
    min_north = float(grid.minimum_north_position)
    min_east = float(grid.minimum_east_position)
    cell_north = float(grid.cell_north_size)
    cell_east = float(grid.cell_east_size)
    rows = int(grid.maximum_row)
    cols = int(grid.maximum_column)

    geoms = []
    rows_idx = []
    cols_idx = []
    vals = []
    for r in range(rows):
        south = min_north + r * cell_north
        north = south + cell_north
        for c in range(cols):
            value = float(values[r, c])
            if not show_zero and value == 0.0:
                continue
            west = min_east + c * cell_east
            east = west + cell_east
            geoms.append(shp.box(west, south, east, north))
            rows_idx.append(r)
            cols_idx.append(c)
            vals.append(value)

    return gpd.GeoDataFrame(
        {"row": rows_idx, "col": cols_idx, "value": vals},
        geometry=geoms,
        crs="EPSG:4326",
    )


def estimate_metrics(grid_bbox: shp.Polygon, pfd_geom: shp.Geometry | None) -> dict[str, float] | None:
    if pfd_geom is None or pfd_geom.is_empty:
        return None
    center_grid = shp.Point((grid_bbox.bounds[0] + grid_bbox.bounds[2]) / 2, (grid_bbox.bounds[1] + grid_bbox.bounds[3]) / 2)
    center_pfd = shp.Point((pfd_geom.bounds[0] + pfd_geom.bounds[2]) / 2, (pfd_geom.bounds[1] + pfd_geom.bounds[3]) / 2)

    utm_crs = gpd.GeoSeries([pfd_geom], crs="EPSG:4326").estimate_utm_crs()
    if utm_crs is None:
        return None
    tr = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True)

    gx, gy = tr.transform(center_grid.x, center_grid.y)
    px, py = tr.transform(center_pfd.x, center_pfd.y)
    dx = gx - px
    dy = gy - py

    gdf_metric = gpd.GeoSeries([grid_bbox, pfd_geom], crs="EPSG:4326").to_crs(utm_crs)
    grid_m = gdf_metric.iloc[0]
    pfd_m = gdf_metric.iloc[1]
    inter = grid_m.intersection(pfd_m).area
    union = grid_m.union(pfd_m).area
    overlap = inter / union if union > 0 else 0.0

    return {"dx_m": dx, "dy_m": dy, "overlap_ratio": overlap}


def main() -> None:
    args = parse_args()
    task_data, refs = load_isoxml(args.source)

    # task_index selects task_data.tasks[*], and grid_index selects task.grids[*] inside that task.
    if len(task_data.tasks) <= args.task_index:
        raise IndexError(f"Task index {args.task_index} out of range.")
    task = task_data.tasks[args.task_index]
    if len(task.grids) <= args.grid_index:
        raise IndexError(f"Grid index {args.grid_index} out of range.")
    grid = task.grids[args.grid_index]

    grid_bin = refs.get(grid.filename)
    if not isinstance(grid_bin, bytes):
        raise ValueError(f"Missing binary data for {grid.filename}.bin")

    ddi = DDEntity.from_id(args.ddi)
    values = decode_grid_values(task_data, task, grid, grid_bin, ddi)
    grid_gdf = grid_to_geodataframe(grid, values, args.show_zero)

    pfd_geom = partfield_union_geometry(task_data, task)
    pfd_gdf = (
        gpd.GeoDataFrame(geometry=[pfd_geom], crs="EPSG:4326")
        if pfd_geom is not None and not pfd_geom.is_empty
        else None
    )

    shp_gdf = None
    if args.shp is not None:
        shp_gdf = gpd.read_file(args.shp).to_crs("EPSG:4326")

    fig, ax = plt.subplots(figsize=(10, 10))
    if not grid_gdf.empty:
        grid_gdf.plot(column="value", ax=ax, cmap="YlOrRd", legend=True, linewidth=0)
    if pfd_gdf is not None:
        pfd_gdf.boundary.plot(ax=ax, color="magenta", linewidth=2)
    if shp_gdf is not None:
        shp_gdf.boundary.plot(ax=ax, color="cyan", linewidth=1)

    ax.set_title("ISOXML Grid Overlay Check")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="datalim")

    out_path = args.out
    if out_path is None:
        if args.source.is_dir():
            out_path = args.source / "overlay_check.png"
        else:
            out_path = args.source.with_name("overlay_check.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)

    cells_out_path = args.cells_out
    if cells_out_path is None:
        if args.source.is_dir():
            cells_out_path = args.source / "grid_cells.geojson"
        else:
            cells_out_path = args.source.with_name("grid_cells.geojson")
    cells_out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cells_out_path, "w", encoding="utf-8") as geojson_file:
        geojson_file.write(grid_gdf.to_json(drop_id=True))

    grid_bbox = shp.box(
        float(grid.minimum_east_position),
        float(grid.minimum_north_position),
        float(grid.minimum_east_position) + float(grid.cell_east_size) * int(grid.maximum_column),
        float(grid.minimum_north_position) + float(grid.cell_north_size) * int(grid.maximum_row),
    )
    metrics = estimate_metrics(grid_bbox, pfd_geom)

    print("Overlay check")
    print(f"  source: {args.source}")
    print(f"  output png: {out_path}")
    print(f"  cells geojson: {cells_out_path}")
    print(f"  grid rows x cols: {grid.maximum_row} x {grid.maximum_column}")
    print(f"  grid bbox (lon/lat): {grid_bbox.bounds}")
    if pfd_geom is not None and not pfd_geom.is_empty:
        print(f"  pfd bbox (lon/lat):  {pfd_geom.bounds}")
    if metrics:
        print(f"  center offset dx/dy (m): {metrics['dx_m']:.3f}, {metrics['dy_m']:.3f}")
        print(f"  bbox overlap ratio: {metrics['overlap_ratio']:.6f}")


if __name__ == "__main__":
    main()
