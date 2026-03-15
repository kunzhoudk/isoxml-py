from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import geopandas as gpd

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "isoxml.cli.prepare_application_map_geojson", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_cli_run__when_test_shp_input__expect_geojson_with_embedded_boundary(tmp_path: Path):
    output_path = tmp_path / "application_map.geojson"

    proc = _run_cli(
        "examples/input/test_shp/20250415_211530.shp",
        "--output-path",
        str(output_path),
        "--value-field",
        "value",
    )

    assert "GeoJSON application map complete" in proc.stdout
    assert output_path.exists()

    gdf = gpd.read_file(output_path)
    assert len(gdf) == 9
    assert (gdf["name"] == "border").sum() == 1
    assert gdf.loc[gdf["name"] != "border", "dose"].notna().all()
    assert gdf.loc[gdf["name"] == "border", "dose"].isna().all()
