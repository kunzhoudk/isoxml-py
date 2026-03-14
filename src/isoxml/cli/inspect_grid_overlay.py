"""CLI for checking spatial alignment between ISOXML grids and boundaries."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import shapely as shp
from pyproj import Transformer

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.geometry import ShapelyConverterV3, ShapelyConverterV4
from isoxml.grid import decode
from isoxml.io import read_from_path, read_from_zip
from isoxml.models import DDEntity


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Overlay ISOXML grid on partfield boundary.")
    parser.add_argument("source", type=Path, help="TASKDATA directory or ZIP.")
    parser.add_argument(
        "--task",
        "--task-index",
        dest="task",
        type=int,
        default=0,
        help="Task index (default: 0).",
    )
    parser.add_argument(
        "--grid",
        "--grid-index",
        dest="grid",
        type=int,
        default=0,
        help="Grid index within task (default: 0).",
    )
    parser.add_argument("--ddi", type=int, default=6, help="DDI for GridType2 decode (default: 6).")
    parser.add_argument("--show-zero", action="store_true", help="Include zero-value cells in plot.")
    parser.add_argument("--shp", type=Path, default=None, help="Optional shapefile to overlay.")
    parser.add_argument("--out", type=Path, default=None, help="Output PNG path.")
    parser.add_argument("--cells-out", type=Path, default=None, help="Output GeoJSON for grid cells.")
    return parser.parse_args(argv)


def load(source: Path):
    if source.is_dir():
        return read_from_path(source)
    if source.suffix.lower() == ".zip":
        return read_from_zip(source)
    raise ValueError(f"Expected a directory or .zip file, got: {source}")


def _converter(task_data):
    if getattr(task_data.version_major, "value", None) == "4":
        return ShapelyConverterV4()
    return ShapelyConverterV3()


def _partfield_geometry(task_data, task) -> shp.Geometry | None:
    if not task_data.partfields:
        return None
    conv = _converter(task_data)
    partfield = next(
        (partfield for partfield in task_data.partfields if partfield.id == task.partfield_id_ref),
        task_data.partfields[0],
    )
    if not partfield or not partfield.polygons:
        return None
    return shp.unary_union([conv.to_shapely_polygon(poly) for poly in partfield.polygons])


def _type1_code_to_value(task_data, task) -> dict[int, float]:
    vpn_by_id = {vpn.id: vpn for vpn in getattr(task_data, "value_presentations", []) if vpn.id}
    result: dict[int, float] = {}
    for treatment_zone in task.treatment_zones:
        if treatment_zone.code is None:
            continue
        code = int(treatment_zone.code)
        if not treatment_zone.process_data_variables:
            result[code] = 0.0
            continue
        pdv = treatment_zone.process_data_variables[0]
        raw = float(pdv.process_data_value or 0)
        vpn = vpn_by_id.get(pdv.value_presentation_id_ref)
        if vpn:
            result[code] = raw * float(vpn.scale) + float(vpn.offset)
        else:
            result[code] = raw
    return result


def _decode_values(task_data, task, grid, grid_bin: bytes, ddi: DDEntity) -> np.ndarray:
    is_type1 = grid.type in (iso3.GridType.GridType1, iso4.GridType.GridType1)
    if is_type1:
        raw = decode(grid_bin, grid, scale=False)
        code_map = _type1_code_to_value(task_data, task)
        return np.vectorize(lambda code: code_map.get(int(code), 0.0))(raw).astype(np.float32)
    arr = decode(grid_bin, grid, ddi_list=[ddi], scale=True)
    if arr.ndim == 3 and arr.shape[-1] == 1:
        arr = arr[:, :, 0]
    return arr.astype(np.float32)


def _cells_geodataframe(grid, values: np.ndarray, show_zero: bool) -> gpd.GeoDataFrame:
    min_n = float(grid.minimum_north_position)
    min_e = float(grid.minimum_east_position)
    dn = float(grid.cell_north_size)
    de = float(grid.cell_east_size)

    geometries: list[shp.Polygon] = []
    data_rows: list[int] = []
    data_cols: list[int] = []
    data_vals: list[float] = []
    for row in range(int(grid.maximum_row)):
        for col in range(int(grid.maximum_column)):
            value = float(values[row, col])
            if not show_zero and value == 0.0:
                continue
            south = min_n + row * dn
            west = min_e + col * de
            geometries.append(shp.box(west, south, west + de, south + dn))
            data_rows.append(row)
            data_cols.append(col)
            data_vals.append(value)

    return gpd.GeoDataFrame(
        {"row": data_rows, "col": data_cols, "value": data_vals},
        geometry=geometries,
        crs="EPSG:4326",
    )


def _alignment_metrics(grid_bbox: shp.Polygon, partfield: shp.Geometry) -> dict[str, float] | None:
    if partfield is None or partfield.is_empty:
        return None
    utm = gpd.GeoSeries([partfield], crs="EPSG:4326").estimate_utm_crs()
    if utm is None:
        return None
    transformer = Transformer.from_crs("EPSG:4326", utm, always_xy=True)

    def centroid_m(geom):
        cx = (geom.bounds[0] + geom.bounds[2]) / 2
        cy = (geom.bounds[1] + geom.bounds[3]) / 2
        return transformer.transform(cx, cy)

    gx, gy = centroid_m(grid_bbox)
    px, py = centroid_m(partfield)

    metric = gpd.GeoSeries([grid_bbox, partfield], crs="EPSG:4326").to_crs(utm)
    inter = metric.iloc[0].intersection(metric.iloc[1]).area
    union = metric.iloc[0].union(metric.iloc[1]).area
    return {
        "dx_m": gx - px,
        "dy_m": gy - py,
        "overlap": inter / union if union > 0 else 0.0,
    }


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    ddi = DDEntity.from_id(args.ddi)

    task_data, refs = load(args.source)

    if len(task_data.tasks) <= args.task:
        raise IndexError(f"Task index {args.task} out of range.")
    task = task_data.tasks[args.task]

    if len(task.grids) <= args.grid:
        raise IndexError(f"Grid index {args.grid} out of range.")
    grid = task.grids[args.grid]

    grid_bin = refs.get(grid.filename)
    if not isinstance(grid_bin, bytes):
        raise ValueError(f"No binary data found for {grid.filename}.bin")

    values = _decode_values(task_data, task, grid, grid_bin, ddi)
    cells_gdf = _cells_geodataframe(grid, values, args.show_zero)
    partfield_geom = _partfield_geometry(task_data, task)

    fig, ax = plt.subplots(figsize=(10, 10))
    if not cells_gdf.empty:
        cells_gdf.plot(column="value", ax=ax, cmap="YlOrRd", legend=True, linewidth=0)
    if partfield_geom and not partfield_geom.is_empty:
        gpd.GeoDataFrame(geometry=[partfield_geom], crs="EPSG:4326").boundary.plot(
            ax=ax, color="magenta", linewidth=2
        )
    if args.shp is not None:
        gpd.read_file(args.shp).to_crs("EPSG:4326").boundary.plot(
            ax=ax, color="cyan", linewidth=1
        )
    ax.set_title("ISOXML Grid Overlay Check")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_aspect("equal", adjustable="datalim")

    def _default(base: Path, name: str) -> Path:
        return (base / name) if args.source.is_dir() else args.source.with_name(name)

    out_png = args.out or _default(args.source, "overlay_check.png")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)

    out_geojson = args.cells_out or _default(args.source, "grid_cells.geojson")
    out_geojson.parent.mkdir(parents=True, exist_ok=True)
    with open(out_geojson, "w", encoding="utf-8") as file_handle:
        file_handle.write(cells_gdf.to_json(drop_id=True))

    grid_bbox = shp.box(
        float(grid.minimum_east_position),
        float(grid.minimum_north_position),
        float(grid.minimum_east_position) + float(grid.cell_east_size) * int(grid.maximum_column),
        float(grid.minimum_north_position) + float(grid.cell_north_size) * int(grid.maximum_row),
    )
    metrics = _alignment_metrics(grid_bbox, partfield_geom)

    print(f"Source:       {args.source}")
    print(f"Grid:         {grid.maximum_row} rows x {grid.maximum_column} cols")
    print(f"Grid bbox:    {grid_bbox.bounds}")
    if partfield_geom and not partfield_geom.is_empty:
        print(f"PFD bbox:     {partfield_geom.bounds}")
    if metrics:
        print(f"Centre offset: dx={metrics['dx_m']:.2f} m, dy={metrics['dy_m']:.2f} m")
        print(f"Bbox overlap:  {metrics['overlap']:.6f}")
    print(f"PNG:          {out_png}")
    print(f"GeoJSON:      {out_geojson}")


if __name__ == "__main__":
    main()
