"""Input loading and value-unit helpers for vector-to-taskdata conversion."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
from isoxml.models.ddi import DDEntity

if TYPE_CHECKING:
    import geopandas as _gpd


def trim(text: str, max_len: int) -> str:
    return text[:max_len]


def load_vector_gdf(
    source_path: Path,
    *,
    input_crs: str | None = None,
    label: str = "Input",
) -> "gpd.GeoDataFrame":
    """Load a vector file supported by GeoPandas and ensure a CRS is present."""
    if not source_path.exists():
        raise FileNotFoundError(f"{label} file not found: {source_path}")

    gdf = gpd.read_file(source_path)
    if gdf.crs is None:
        if input_crs:
            gdf = gdf.set_crs(input_crs)
        else:
            raise ValueError(f"{label} file has no CRS. Provide input_crs.")
    return gdf


def unit_factor_to_ddi(input_unit: str, ddi: DDEntity) -> float:
    if input_unit == "ddi":
        return 1.0
    if input_unit == "kg/ha":
        if ddi.ddi == 6 or ddi.unit == "mg/m²":
            return 100.0
        raise ValueError(
            f"value_unit='kg/ha' is only supported for DDI=6 (mg/m² base unit); "
            f"got DDI={ddi.ddi}."
        )
    raise ValueError(f"Unsupported value_unit: {input_unit!r}")


def normalize_unit_text(raw: str | None) -> str | None:
    if not raw:
        return None
    token = str(raw).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    token = token.replace("²", "2")
    if token in {"kg/ha", "kg/ha1", "kgha", "kg/hm2", "kg/hm^2", "kg/公顷"}:
        return "kg/ha"
    if token in {"mg/m2", "mg/m^2", "mgm2"}:
        return "ddi"
    return None


def detect_unit_from_gdf(
    gdf: "_gpd.GeoDataFrame", value_field: str
) -> tuple[str | None, str | None]:
    """Scan vector-file columns for a recognisable unit annotation."""
    candidates: list[str] = []
    paired = f"{value_field}_unit"
    if paired in gdf.columns:
        candidates.append(paired)
    preferred = {
        "unit",
        "units",
        "uom",
        "value_unit",
        "rate_unit",
        "dose_unit",
        "app_unit",
        "application_unit",
    }
    for col in gdf.columns:
        if col == "geometry":
            continue
        col_l = col.lower()
        if (col_l in preferred or col_l.endswith("_unit")) and col not in candidates:
            candidates.append(col)
    for col in candidates:
        series = gdf[col].dropna()
        if series.empty:
            continue
        normalised = {u for u in (normalize_unit_text(v) for v in series.unique()) if u}
        if len(normalised) == 1:
            return next(iter(normalised)), col
    return None, None


def resolve_value_unit(
    gdf: "_gpd.GeoDataFrame", requested: str, value_field: str
) -> tuple[str, str]:
    if requested != "auto":
        return requested, "cli"
    detected, col = detect_unit_from_gdf(gdf, value_field)
    if detected is not None:
        return detected, f"vector:{col}"
    return "ddi", "default"
