"""Prepare a GeoJSON application map from the test SHP sample."""

from __future__ import annotations

from pathlib import Path

from isoxml.cli.prepare_application_map_geojson import build_application_map_geojson

EXAMPLES_DIR = Path(__file__).resolve().parents[1]
SOURCE_PATH = EXAMPLES_DIR / "input" / "test_shp" / "20250415_211530.shp"
OUTPUT_PATH = EXAMPLES_DIR / "input" / "test_shp_application_map_with_boundary.geojson"
VALUE_FIELD = "value"


def main() -> None:
    build_application_map_geojson(
        SOURCE_PATH,
        output_path=OUTPUT_PATH,
        value_field=VALUE_FIELD,
        name_field=None,
        input_crs=None,
        boundary_name="border",
    )
    print(f"Written: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
