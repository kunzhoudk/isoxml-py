"""CLI for normalizing polygon vectors into a GeoJSON application map with boundary."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import geopandas as gpd
import pandas as pd
import shapely as shp

from isoxml.pipeline.vector_to_taskdata.geometry import (
    ensure_polygon_gdf,
    resolve_value_field,
)
from isoxml.pipeline.vector_to_taskdata.inputs import load_vector_gdf


def build_application_map_geojson(
    source_path: Path,
    *,
    output_path: Path,
    value_field: str | None,
    name_field: str | None,
    input_crs: str | None,
    boundary_name: str,
) -> None:
    gdf = ensure_polygon_gdf(load_vector_gdf(source_path, input_crs=input_crs))
    value_field = resolve_value_field(gdf, value_field)

    gdf = gdf.to_crs("EPSG:4326").copy()
    gdf["dose"] = gdf[value_field]

    if name_field is not None:
        if name_field not in gdf.columns:
            raise ValueError(
                f"Field '{name_field}' does not exist in the vector input."
            )
        gdf["name"] = gdf[name_field].astype(str)
    else:
        gdf["name"] = [f"zone{i}" for i in range(1, len(gdf) + 1)]

    gdf = gdf[
        [
            *(
                [
                    c
                    for c in gdf.columns
                    if c != "geometry" and c not in {"name", "dose"}
                ]
            ),
            "name",
            "dose",
            "geometry",
        ]
    ]

    boundary_row = {col: None for col in gdf.columns if col != "geometry"}
    boundary_row["name"] = boundary_name
    boundary_row["dose"] = None
    boundary_geom = shp.unary_union(gdf.geometry.values)
    boundary_gdf = gpd.GeoDataFrame(
        [boundary_row], geometry=[boundary_geom], crs=gdf.crs
    )

    output_gdf = pd.concat([gdf, boundary_gdf], ignore_index=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(output_gdf, geometry="geometry", crs=gdf.crs).to_file(
        output_path,
        driver="GeoJSON",
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parents[3] / "examples"
    parser = argparse.ArgumentParser(
        description="Normalize a polygon vector into a GeoJSON application map with an embedded boundary feature.",
    )
    parser.add_argument(
        "source_path",
        nargs="?",
        type=Path,
        default=base_dir / "input" / "test_shp" / "20250415_211530.shp",
        help="Source polygon vector file (.shp, .geojson, .gpkg, ...).",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=base_dir / "input" / "test_shp_application_map_with_boundary.geojson",
        help="GeoJSON output path.",
    )
    parser.add_argument(
        "--value-field",
        type=str,
        default=None,
        help="Numeric attribute to copy into the standardised 'dose' field.",
    )
    parser.add_argument(
        "--name-field",
        type=str,
        default=None,
        help="Optional source attribute to copy into the standardised 'name' field.",
    )
    parser.add_argument(
        "--input-crs",
        type=str,
        default=None,
        help="CRS to apply when input has no CRS metadata, e.g. EPSG:4326.",
    )
    parser.add_argument(
        "--boundary-name",
        type=str,
        default="border",
        help="Name assigned to the generated boundary feature.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    build_application_map_geojson(
        args.source_path,
        output_path=args.output_path,
        value_field=args.value_field,
        name_field=args.name_field,
        input_crs=args.input_crs,
        boundary_name=args.boundary_name,
    )
    print("GeoJSON application map complete")
    print(f"  input:       {args.source_path}")
    print(f"  output:      {args.output_path}")
    print(f"  value field: {args.value_field or 'auto'}")
    print(f"  name field:  {args.name_field or 'auto: zone1..N'}")
    print(f"  boundary:    {args.boundary_name}")


if __name__ == "__main__":
    main()
