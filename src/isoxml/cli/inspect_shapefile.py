"""CLI for inspecting shapefiles used in task-data generation."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import geopandas as gpd


def inspect(shp_path: Path) -> None:
    gdf = gpd.read_file(shp_path)
    print(f"Inspecting: {shp_path}\n")

    print("--- Basic information ---")
    print(f"Features:       {len(gdf)}")
    print(f"Geometry types: {gdf.geometry.geom_type.unique().tolist()}")
    print(f"CRS:            {gdf.crs}")
    if "MultiPolygon" in gdf.geometry.geom_type.unique():
        count = int((gdf.geometry.geom_type == "MultiPolygon").sum())
        print(f"  MultiPolygons: {count}")
    print()

    print("--- Fields ---")
    for col in gdf.columns:
        if col != "geometry":
            print(f"  {col:20s}  {gdf[col].dtype}")
    print()

    print("--- Spatial bounds ---")
    west, south, east, north = gdf.total_bounds
    print(f"  West / East:   {west:.8f}  /  {east:.8f}")
    print(f"  South / North: {south:.8f}  /  {north:.8f}")
    print()

    print("--- Sample data (first 5 rows) ---")
    print(gdf.drop(columns=["geometry"]).head().to_string())
    print()

    numeric_cols = gdf.select_dtypes(include=["number"]).columns.tolist()
    text_cols = gdf.select_dtypes(include=["object"]).columns.tolist()

    print("--- Numeric field statistics ---")
    if numeric_cols:
        for col in numeric_cols:
            series = gdf[col]
            unique = series.nunique()
            print(
                f"  {col}: min={series.min()}, max={series.max()}, "
                f"mean={series.mean():.2f}, unique={unique}"
            )
            if unique <= 20:
                print(f"    values: {sorted(series.unique().tolist())}")
    else:
        print("  No numeric fields found.")
    print()

    print("--- Candidate fields for application map ---")
    dose_candidates = [
        col
        for col in numeric_cols
        if any(key in col.lower() for key in ("dose", "rate", "amount", "value", "kg", "fertilizer"))
    ]
    print(f"  Dose/value field: {dose_candidates or numeric_cols}")

    zone_candidates = [
        col
        for col in text_cols
        if any(key in col.lower() for key in ("name", "id", "type", "zone", "class"))
    ]
    print(f"  Zone/ID field:    {zone_candidates or text_cols}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    default_path = Path(__file__).resolve().parents[3] / "examples" / "input" / "small" / "shp" / "Rx.shp"
    parser = argparse.ArgumentParser(description="Inspect a shapefile for application-map generation.")
    parser.add_argument(
        "shp_path",
        nargs="?",
        type=Path,
        default=default_path,
        help="Path to shapefile (.shp).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    if not args.shp_path.exists():
        raise SystemExit(f"File not found: {args.shp_path}")
    inspect(args.shp_path)


if __name__ == "__main__":
    main()
