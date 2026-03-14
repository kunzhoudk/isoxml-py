"""Convert polygon prescription shapefiles into ISOXML grid task data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from importlib import resources as _pkg_resources
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import numpy as np
import shapely as shp

import isoxml.models.base.v3 as iso
import isoxml.models.base.v4 as iso4
from isoxml.grid.codec import encode_type1, encode_type2
from isoxml.geometry.shapely import ShapelyConverterV3, ShapelyConverterV4
from isoxml.models.ddi import DDEntity
from isoxml.io.writer import to_xml

if TYPE_CHECKING:
    import geopandas as gpd


# ---------------------------------------------------------------------------
# Public option / result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShpToGridOptions:
    """Conversion options for polygon shapefile → ISOXML grid task data."""

    shp_path: Path
    value_field: str | None = None
    ddi: int = 6
    value_unit: Literal["auto", "ddi", "kg/ha"] = "auto"
    grid_type: Literal["1", "2"] = "2"
    xml_version: Literal["3", "4"] = "3"
    cell_size_m: float = 10.0
    boundary_mask: Literal["center", "strict", "touch"] = "touch"
    grid_extent: Literal["rx", "boundary", "union"] = "rx"
    input_crs: str | None = None
    partfield_name: str | None = None
    boundary_shp: Path | None = None
    software_manufacturer: str = "kz_isoxml"
    software_version: str = "0.1.0"


@dataclass(frozen=True)
class ShpToGridResult:
    """Result bundle produced by :func:`convert`."""

    task_data: iso.Iso11783TaskData | iso4.Iso11783TaskData
    refs: dict[str, bytes]
    value_field: str
    effective_unit: str
    unit_source: str


# ---------------------------------------------------------------------------
# Optional dependency loaders
# ---------------------------------------------------------------------------

def _require_geopandas():
    try:
        import geopandas as gpd
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "geopandas is required for shapefile conversion. "
            "Install optional dependencies with `pip install .[dev]`."
        ) from exc
    return gpd


def _require_xmlschema():
    try:
        import xmlschema
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "xmlschema is required for XSD validation. "
            "Install optional dependencies with `pip install .[dev]`."
        ) from exc
    return xmlschema


# ---------------------------------------------------------------------------
# Unit resolution helpers
# ---------------------------------------------------------------------------

def _trim(text: str, max_len: int) -> str:
    return text[:max_len]


def _unit_factor_to_ddi(input_unit: str, ddi: DDEntity) -> float:
    if input_unit == "ddi":
        return 1.0
    if input_unit == "kg/ha":
        if ddi.ddi == 6 or ddi.unit == "mg/m²":
            return 100.0  # 1 kg/ha = 100 mg/m²
        raise ValueError(
            f"value_unit='kg/ha' is only supported for DDI=6 (mg/m² base unit); "
            f"got DDI={ddi.ddi}."
        )
    raise ValueError(f"Unsupported value_unit: {input_unit!r}")


def _normalize_unit_text(raw: str | None) -> str | None:
    if not raw:
        return None
    token = str(raw).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    token = token.replace("²", "2")
    if token in {"kg/ha", "kg/ha1", "kgha", "kg/hm2", "kg/hm^2", "kg/公顷"}:
        return "kg/ha"
    if token in {"mg/m2", "mg/m^2", "mgm2"}:
        return "ddi"
    return None


def _detect_unit_from_gdf(
        gdf: "gpd.GeoDataFrame", value_field: str
) -> tuple[str | None, str | None]:
    """Scan shapefile columns for a recognisable unit annotation."""
    candidates: list[str] = []
    paired = f"{value_field}_unit"
    if paired in gdf.columns:
        candidates.append(paired)
    preferred = {"unit", "units", "uom", "value_unit", "rate_unit",
                 "dose_unit", "app_unit", "application_unit"}
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
        normalised = {u for u in (_normalize_unit_text(v) for v in series.unique()) if u}
        if len(normalised) == 1:
            return next(iter(normalised)), col
    return None, None


def _resolve_value_unit(
        gdf: "gpd.GeoDataFrame", requested: str, value_field: str
) -> tuple[str, str]:
    if requested != "auto":
        return requested, "cli"
    detected, col = _detect_unit_from_gdf(gdf, value_field)
    if detected is not None:
        return detected, f"shp:{col}"
    return "ddi", "default"


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _iter_polygons(geom):
    if geom is None or geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        yield geom
    elif geom.geom_type == "MultiPolygon":
        yield from geom.geoms
    elif geom.geom_type == "GeometryCollection":
        for sub in geom.geoms:
            yield from _iter_polygons(sub)


def _ensure_polygon_gdf(gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf["geometry"] = gdf.geometry.apply(shp.make_valid)
    gdf["geometry"] = [
        shp.unary_union(list(_iter_polygons(g))) or None for g in gdf.geometry
    ]
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    if gdf.empty:
        raise ValueError("No polygon geometry found in the shapefile.")
    return gdf


def _auto_value_field(gdf: "gpd.GeoDataFrame") -> str:
    numeric_cols = list(gdf.select_dtypes(include=["number"]).columns)
    if not numeric_cols:
        raise ValueError("No numeric field found. Pass value_field explicitly.")
    priority = ["rate", "dose", "value", "amount", "kg", "fert", "app"]
    for kw in priority:
        for col in numeric_cols:
            if kw in col.lower():
                return col
    return numeric_cols[0]


def _resolve_value_field(gdf: "gpd.GeoDataFrame", requested: str | None) -> str:
    if requested is None:
        return _auto_value_field(gdf)
    if requested not in gdf.columns:
        raise ValueError(f"Field '{requested}' does not exist in the shapefile.")
    if not np.issubdtype(gdf[requested].dtype, np.number):
        raise ValueError(f"Field '{requested}' is not numeric.")
    return requested


# ---------------------------------------------------------------------------
# Rasterisation
# ---------------------------------------------------------------------------

def _rasterize(
        gdf_grid: "gpd.GeoDataFrame",
        boundary_geom: shp.Geometry,
        value_field: str,
        rows: int,
        cols: int,
        grid_bounds: tuple[float, float, float, float],
        boundary_mask: str,
) -> tuple[np.ndarray, np.ndarray, float, float, int, int]:
    """Rasterize prescription polygons onto a regular grid."""
    if rows <= 0 or cols <= 0:
        raise ValueError("Grid rows/cols must be > 0.")
    if boundary_mask not in {"center", "strict", "touch"}:
        raise ValueError(f"Unsupported boundary_mask: {boundary_mask!r}")

    minx, miny, maxx, maxy = [float(v) for v in grid_bounds]
    cell_e = (maxx - minx) / cols
    cell_n = (maxy - miny) / rows
    if cell_e <= 0 or cell_n <= 0:
        raise ValueError("Invalid grid bounds: non-positive cell size.")

    grid_data = np.zeros((rows, cols), dtype=np.float32)
    coverage = np.zeros((rows, cols), dtype=bool)

    for feature in gdf_grid[[value_field, "geometry"]].itertuples(index=False):
        value = float(feature[0])
        if not np.isfinite(value):
            continue
        geom = feature[1]
        for polygon in _iter_polygons(geom):
            if polygon.is_empty:
                continue
            px0, py0, px1, py1 = polygon.bounds
            c0 = max(0, int(math.floor((px0 - minx) / cell_e)))
            c1 = min(cols - 1, int(math.ceil((px1 - minx) / cell_e)) - 1)
            r0 = max(0, int(math.floor((py0 - miny) / cell_n)))
            r1 = min(rows - 1, int(math.ceil((py1 - miny) / cell_n)) - 1)
            if c0 > c1 or r0 > r1:
                continue

            lc = c1 - c0 + 1
            lr = r1 - r0 + 1

            if boundary_mask == "touch":
                col_off = np.arange(lc, dtype=np.int32)
                row_off = np.arange(lr, dtype=np.int32)
                cg, rg = np.meshgrid(col_off, row_off)
                west = minx + (c0 + cg.ravel()) * cell_e
                south = miny + (r0 + rg.ravel()) * cell_n
                boxes = shp.box(west, south, west + cell_e, south + cell_n)
                keep = np.logical_and(
                    shp.intersects(polygon, boxes),
                    shp.intersects(boundary_geom, boxes),
                )
                if not np.any(keep):
                    continue
                local_r = rg.ravel()[keep]
                local_c = cg.ravel()[keep]
            else:
                xs = minx + (np.arange(c0, c1 + 1, dtype=np.float64) + 0.5) * cell_e
                ys = miny + (np.arange(r0, r1 + 1, dtype=np.float64) + 0.5) * cell_n
                xg, yg = np.meshgrid(xs, ys)
                pts = shp.points(xg.ravel(), yg.ravel())
                keep = shp.covers(polygon, pts)
                if boundary_mask == "center":
                    keep &= shp.covers(boundary_geom, pts)
                if not np.any(keep):
                    continue
                hit = np.flatnonzero(keep)
                local_r = hit // lc
                local_c = hit % lc
                if boundary_mask == "strict":
                    west = minx + (c0 + local_c) * cell_e
                    south = miny + (r0 + local_r) * cell_n
                    boxes = shp.box(west, south, west + cell_e, south + cell_n)
                    bkeep = shp.covers(boundary_geom, boxes)
                    if not np.any(bkeep):
                        continue
                    local_r = local_r[bkeep]
                    local_c = local_c[bkeep]

            grid_data[local_r + r0, local_c + c0] = value
            coverage[local_r + r0, local_c + c0] = True

    return grid_data, coverage, minx, miny, rows, cols


# ---------------------------------------------------------------------------
# ISOXML object builders
# ---------------------------------------------------------------------------

def _infer_partfield_name(
        gdf: "gpd.GeoDataFrame", shp_path: Path, explicit: str | None
) -> str:
    if explicit:
        return _trim(explicit, 32)
    for col in gdf.columns:
        if col == "geometry":
            continue
        if gdf[col].dtype == object:
            first = gdf[col].dropna()
            if not first.empty:
                return _trim(str(first.iloc[0]), 32)
    return _trim(shp_path.stem, 32)


def _build_customer(xml_version: str):
    if xml_version == "4":
        return iso4.Customer(id="CTR100", last_name="customer")
    return iso.Customer(id="CTR100", designator="customer")


def _to_decimal9(value: float) -> Decimal:
    return Decimal(f"{value:.9f}")


def _count_decimals(value: float, max_decimals: int = 7) -> int:
    text = f"{value:.12f}".rstrip("0").rstrip(".")
    if "." not in text:
        return 0
    return min(max_decimals, len(text.split(".")[1]))


# ---------------------------------------------------------------------------
# XSD validation helper
# ---------------------------------------------------------------------------

def validate_xsd(
        task_data: iso.Iso11783TaskData | iso4.Iso11783TaskData,
        xml_version: str,
) -> Path:
    """Validate generated task data XML against the bundled ISOXML XSD schema."""
    xmlschema = _require_xmlschema()
    xsd_name = (
        "ISO11783_TaskFile_V4-3.xsd" if xml_version == "4"
        else "ISO11783_TaskFile_V3-3.xsd"
    )
    xsd_ref = _pkg_resources.files("isoxml.data.xsd").joinpath(xsd_name)
    with _pkg_resources.as_file(xsd_ref) as xsd_path:
        if not xsd_path.exists():
            raise FileNotFoundError(f"Bundled XSD not found: {xsd_name}")
        xmlschema.validate(to_xml(task_data), xsd_path)
    return Path(str(xsd_ref))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def convert(options: ShpToGridOptions) -> ShpToGridResult:
    """Build ISOXML task data and binary grid from a prescription shapefile.

    Args:
        options: Conversion parameters (see :class:`ShpToGridOptions`).

    Returns:
        A :class:`ShpToGridResult` containing the ready-to-write task data,
        binary grid reference, and metadata about the value field and unit.
    """
    gpd = _require_geopandas()

    if not options.shp_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {options.shp_path}")
    if options.boundary_shp is None:
        raise ValueError("boundary_shp is required.")
    if not options.boundary_shp.exists():
        raise FileNotFoundError(f"Boundary shapefile not found: {options.boundary_shp}")

    # ------------------------------------------------------------------
    # Load & validate input data
    # ------------------------------------------------------------------
    gdf = gpd.read_file(options.shp_path)
    if gdf.crs is None:
        if options.input_crs:
            gdf = gdf.set_crs(options.input_crs)
        else:
            raise ValueError("Input shapefile has no CRS. Provide input_crs.")

    gdf = _ensure_polygon_gdf(gdf)
    value_field = _resolve_value_field(gdf, options.value_field)
    effective_unit, unit_source = _resolve_value_unit(gdf, options.value_unit, value_field)

    gdf_boundary = gpd.read_file(options.boundary_shp)
    if gdf_boundary.crs is None:
        if options.input_crs:
            gdf_boundary = gdf_boundary.set_crs(options.input_crs)
        else:
            raise ValueError("Boundary shapefile has no CRS. Provide input_crs.")
    gdf_boundary = _ensure_polygon_gdf(gdf_boundary)

    # ------------------------------------------------------------------
    # CRS projection
    # ------------------------------------------------------------------
    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    gdf_boundary_wgs84 = gdf_boundary.to_crs("EPSG:4326")
    metric_crs = gdf_wgs84.estimate_utm_crs()
    if metric_crs is None:
        raise ValueError("Could not estimate a UTM CRS from the input geometry.")

    gdf_metric = gdf_wgs84.to_crs(metric_crs)
    gdf_boundary_metric = gdf_boundary_wgs84.to_crs(metric_crs)
    rx_metric = shp.unary_union(gdf_metric.geometry.values)
    rx_wgs84 = shp.unary_union(gdf_wgs84.geometry.values)
    boundary_metric = shp.unary_union(gdf_boundary_metric.geometry.values)
    boundary_wgs84 = shp.unary_union(gdf_boundary_wgs84.geometry.values)

    if boundary_metric.is_empty:
        raise ValueError("Boundary geometry is empty after projection.")
    if rx_metric.is_empty:
        raise ValueError("Prescription geometry is empty after projection.")

    # ------------------------------------------------------------------
    # Grid extent
    # ------------------------------------------------------------------
    if options.grid_extent == "boundary":
        extent_metric = boundary_metric
        extent_wgs84 = boundary_wgs84
    elif options.grid_extent == "union":
        extent_metric = shp.unary_union([rx_metric, boundary_metric])
        extent_wgs84 = shp.unary_union([rx_wgs84, boundary_wgs84])
    else:
        extent_metric = rx_metric
        extent_wgs84 = rx_wgs84

    if extent_metric.is_empty or extent_wgs84.is_empty:
        raise ValueError(f"Grid extent is empty (grid_extent={options.grid_extent!r}).")

    bounds_m = extent_metric.bounds
    cols = max(1, math.ceil((bounds_m[2] - bounds_m[0]) / options.cell_size_m))
    rows = max(1, math.ceil((bounds_m[3] - bounds_m[1]) / options.cell_size_m))

    # ------------------------------------------------------------------
    # Rasterise
    # ------------------------------------------------------------------
    grid_values, coverage, _ox, _oy, rows, cols = _rasterize(
        gdf_grid=gdf_wgs84,
        boundary_geom=boundary_wgs84,
        value_field=value_field,
        rows=rows,
        cols=cols,
        grid_bounds=extent_wgs84.bounds,
        boundary_mask=options.boundary_mask,
    )

    # ------------------------------------------------------------------
    # Select version-specific objects
    # ------------------------------------------------------------------
    if options.xml_version == "4":
        iso_mod = iso4
        shp_conv = ShapelyConverterV4()
        task_status = iso4.TaskStatus.Planned
        transfer_origin = iso4.Iso11783TaskDataDataTransferOrigin.FMIS
    else:
        iso_mod = iso
        shp_conv = ShapelyConverterV3()
        task_status = iso.TaskStatus.Initial
        transfer_origin = iso.Iso11783TaskDataDataTransferOrigin.FMIS

    # ------------------------------------------------------------------
    # Unit scaling
    # ------------------------------------------------------------------
    dd_entity = DDEntity.from_id(options.ddi)
    factor = _unit_factor_to_ddi(effective_unit, dd_entity)
    grid_values = grid_values * factor

    vpn_scale = dd_entity.bit_resolution / factor
    vpn_unit = effective_unit if effective_unit != "ddi" else (dd_entity.unit or "ddi")
    value_presentation = iso_mod.ValuePresentation(
        id="VPN100",
        offset=0,
        scale=Decimal(str(vpn_scale)),
        number_of_decimals=_count_decimals(vpn_scale),
        unit_designator=_trim(vpn_unit, 32),
    )

    # ------------------------------------------------------------------
    # Partfield boundary polygon
    # ------------------------------------------------------------------
    if boundary_wgs84.geom_type == "Polygon":
        partfield_polygons = [
            shp_conv.to_iso_polygon(boundary_wgs84, iso_mod.PolygonType.PartfieldBoundary)
        ]
    elif boundary_wgs84.geom_type == "MultiPolygon":
        partfield_polygons = shp_conv.to_iso_polygon_list(
            boundary_wgs84, iso_mod.PolygonType.PartfieldBoundary
        )
    else:
        raise ValueError("Boundary union is not polygonal.")

    # ------------------------------------------------------------------
    # Grid dimensions
    # ------------------------------------------------------------------
    min_lon, min_lat, max_lon, max_lat = extent_wgs84.bounds
    cell_east_deg = (float(max_lon) - float(min_lon)) / cols
    cell_north_deg = (float(max_lat) - float(min_lat)) / rows

    # ------------------------------------------------------------------
    # ISOXML object graph
    # ------------------------------------------------------------------
    customer = _build_customer(options.xml_version)
    farm = iso_mod.Farm(id="FRM100", designator="farm", customer_id_ref=customer.id)
    partfield = iso_mod.Partfield(
        id="PFD100",
        designator=_infer_partfield_name(gdf_boundary_wgs84, options.boundary_shp, options.partfield_name),
        area=int(round(boundary_metric.area)),
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
        polygons=partfield_polygons,
    )

    default_tz = iso_mod.TreatmentZone(
        code=0,
        designator="zone_0",
        process_data_variables=[
            iso_mod.ProcessDataVariable(
                process_data_ddi=bytes(dd_entity),
                process_data_value=0,
                value_presentation_id_ref=value_presentation.id,
            )
        ],
    )

    grid_type = (
        iso_mod.GridType.GridType1 if options.grid_type == "1"
        else iso_mod.GridType.GridType2
    )
    treatment_zones = [default_tz]
    grid_kwargs: dict = {}

    if grid_type == iso_mod.GridType.GridType1:
        covered_vals = np.unique(grid_values[coverage])
        covered_vals = covered_vals[covered_vals != 0]
        if covered_vals.size > 254:
            raise ValueError(
                f"Grid Type 1 supports at most 254 treatment values; "
                f"found {covered_vals.size}. Use grid_type='2'."
            )
        grid_codes = np.zeros((rows, cols), dtype=np.uint8)
        for code, raw in enumerate(covered_vals, start=1):
            mask = np.logical_and(coverage, grid_values == raw)
            grid_codes[mask] = int(code)
            treatment_zones.append(
                iso_mod.TreatmentZone(
                    code=int(code),
                    designator=_trim(f"zone_{code}_{float(raw):g}", 32),
                    process_data_variables=[
                        iso_mod.ProcessDataVariable(
                            process_data_ddi=bytes(dd_entity),
                            process_data_value=int(round(float(raw) / dd_entity.bit_resolution)),
                            value_presentation_id_ref=value_presentation.id,
                        )
                    ],
                )
            )
    else:
        grid_kwargs["treatment_zone_code"] = default_tz.code

    grid = iso_mod.Grid(
        minimum_north_position=_to_decimal9(float(min_lat)),
        minimum_east_position=_to_decimal9(float(min_lon)),
        cell_north_size=cell_north_deg,
        cell_east_size=cell_east_deg,
        maximum_column=cols,
        maximum_row=rows,
        filename="GRD00000",
        type=grid_type,
        **grid_kwargs,
    )

    if grid_type == iso_mod.GridType.GridType1:
        grid_bin = encode_type1(grid_codes, grid)
    else:
        grid_bin = encode_type2(grid_values, grid, ddi_list=[dd_entity], scale=True)

    task = iso_mod.Task(
        id="TSK100",
        designator=_trim(f"grid{options.grid_type}_{options.shp_path.stem}", 32),
        status=task_status,
        grids=[grid],
        treatment_zones=treatment_zones,
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
        partfield_id_ref=partfield.id,
        default_treatment_zone_code=default_tz.code,
        position_lost_treatment_zone_code=default_tz.code,
        out_of_field_treatment_zone_code=default_tz.code,
    )

    task_data = iso_mod.Iso11783TaskData(
        management_software_manufacturer=_trim(options.software_manufacturer, 32),
        management_software_version=_trim(options.software_version, 32),
        data_transfer_origin=transfer_origin,
        tasks=[task],
        customers=[customer],
        farms=[farm],
        partfields=[partfield],
        value_presentations=[value_presentation],
    )

    return ShpToGridResult(
        task_data=task_data,
        refs={grid.filename: grid_bin},
        value_field=value_field,
        effective_unit=effective_unit,
        unit_source=unit_source,
    )
