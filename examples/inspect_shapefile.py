"""
Inspect a shapefile to gather information needed for prescription map generation.

Prints CRS, field names/types, spatial bounds, sample records, numeric statistics,
and auto-detected candidate fields for dose and zone identification.

Usage:
    python examples/inspect_shapefile.py examples/input/small/shp/Rx.shp
"""

import argparse
from pathlib import Path

import geopandas as gpd


def inspect(shp_path: Path) -> None:
    gdf = gpd.read_file(shp_path)
    print(f"Inspecting: {shp_path}\n")

    print("--- Basic information ---")
    print(f"Features:       {len(gdf)}")
    print(f"Geometry types: {gdf.geometry.geom_type.unique().tolist()}")
    print(f"CRS:            {gdf.crs}")
    if "MultiPolygon" in gdf.geometry.geom_type.unique():
        n = int((gdf.geometry.geom_type == "MultiPolygon").sum())
        print(f"  MultiPolygons: {n}")
    print()

    print("--- Fields ---")
    for col in gdf.columns:
        if col != "geometry":
            print(f"  {col:20s}  {gdf[col].dtype}")
    print()

    print("--- Spatial bounds ---")
    w, s, e, n = gdf.total_bounds
    print(f"  West / East:   {w:.8f}  /  {e:.8f}")
    print(f"  South / North: {s:.8f}  /  {n:.8f}")
    print()

    print("--- Sample data (first 5 rows) ---")
    print(gdf.drop(columns=["geometry"]).head().to_string())
    print()

    numeric_cols = gdf.select_dtypes(include=["number"]).columns.tolist()
    text_cols = gdf.select_dtypes(include=["object"]).columns.tolist()

    print("--- Numeric field statistics ---")
    if numeric_cols:
        for col in numeric_cols:
            s = gdf[col]
            unique = s.nunique()
            print(f"  {col}: min={s.min()}, max={s.max()}, mean={s.mean():.2f}, unique={unique}")
            if unique <= 20:
                print(f"    values: {sorted(s.unique().tolist())}")
    else:
        print("  No numeric fields found.")
    print()

    print("--- Candidate fields for prescription map ---")
    dose_candidates = [
        c for c in numeric_cols
        if any(k in c.lower() for k in ("dose", "rate", "amount", "value", "kg", "fertilizer"))
    ]
    print(f"  Dose/value field: {dose_candidates or numeric_cols}")

    zone_candidates = [
        c for c in text_cols
        if any(k in c.lower() for k in ("name", "id", "type", "zone", "class"))
    ]
    print(f"  Zone/ID field:    {zone_candidates or text_cols}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Inspect a shapefile for prescription map generation.")
    p.add_argument(
        "shp_path",
        nargs="?",
        type=Path,
        default=Path(__file__).parent / "input" / "small" / "shp" / "Rx.shp",
        help="Path to shapefile (.shp).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if not args.shp_path.exists():
        print(f"File not found: {args.shp_path}")
        return
    inspect(args.shp_path)


if __name__ == "__main__":
    main()
