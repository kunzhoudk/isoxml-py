"""Convert polygon prescription shapefiles into ISOXML grid task data."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import numpy as np
import shapely as shp

import isoxml.models.base.v3 as iso
import isoxml.models.base.v4 as iso4
from isoxml.geometry.shapely import ShapelyConverterV3, ShapelyConverterV4
from isoxml.grids.binary import from_numpy_array_to_type_1, from_numpy_array_to_type_2
from isoxml.models.ddi_entities import DDEntity
from isoxml.validation import validate_taskdata_xsd

if TYPE_CHECKING:
    import geopandas as gpd


@dataclass(frozen=True)
class GridFromShpOptions:
    """Conversion options for polygon shapefile -> ISOXML grid."""

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
class GridFromShpResult:
    """Result bundle produced by `convert_grid_from_shp`."""

    task_data: iso.Iso11783TaskData | iso4.Iso11783TaskData
    refs: dict[str, bytes]
    value_field: str
    effective_unit: str
    unit_source: str


def _load_geopandas():
    try:
        import geopandas as gpd
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        raise ModuleNotFoundError(
            "geopandas is required for shapefile conversion. Install optional dependencies "
            "with `pip install .[dev]`."
        ) from exc
    return gpd


def _trim(text: str, max_len: int) -> str:
    return text[:max_len]


def _unit_factor_to_ddi(input_unit: str, ddi: DDEntity) -> float:
    if input_unit == "ddi":
        return 1.0
    if input_unit == "kg/ha":
        if ddi.ddi == 6 or ddi.unit == "mg/m²":
            return 100.0
        raise ValueError(
            f"--value-unit kg/ha is only supported for DDI=6 (mg/m² base unit), got DDI={ddi.ddi}."
        )
    raise ValueError(f"Unsupported input unit: {input_unit}")


def _normalize_unit_text(raw_unit: str | None) -> str | None:
    if raw_unit is None:
        return None
    token = str(raw_unit).strip().lower()
    if not token:
        return None
    compact = token.replace(" ", "").replace("_", "").replace("-", "")
    compact = compact.replace("²", "2")

    if compact in {"kg/ha", "kg/ha1", "kgha", "kg/hm2", "kg/hm^2", "kg/公顷"}:
        return "kg/ha"
    if compact in {"mg/m2", "mg/m^2", "mgm2"}:
        return "ddi"
    return None


def _detect_unit_from_shp(
    gdf: "gpd.GeoDataFrame",
    value_field: str,
) -> tuple[str | None, str | None]:
    candidate_cols: list[str] = []
    paired_col = f"{value_field}_unit"
    if paired_col in gdf.columns:
        candidate_cols.append(paired_col)

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
        col_lower = col.lower()
        if col_lower in preferred or col_lower.endswith("_unit"):
            if col not in candidate_cols:
                candidate_cols.append(col)

    for col in candidate_cols:
        series = gdf[col].dropna()
        if series.empty:
            continue
        normalized = {
            unit for unit in (_normalize_unit_text(v) for v in series.unique()) if unit is not None
        }
        if len(normalized) == 1:
            return next(iter(normalized)), col
    return None, None


def _resolve_value_unit(
    gdf: "gpd.GeoDataFrame",
    requested_unit: str,
    value_field: str,
) -> tuple[str, str]:
    if requested_unit != "auto":
        return requested_unit, "cli"

    detected, column = _detect_unit_from_shp(gdf, value_field)
    if detected is not None:
        return detected, f"shp:{column}"
    return "ddi", "default"


def _iter_polygons(geom):
    if geom is None or geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        yield geom
        return
    if geom.geom_type == "MultiPolygon":
        for polygon in geom.geoms:
            yield polygon
        return
    if geom.geom_type == "GeometryCollection":
        for sub_geom in geom.geoms:
            yield from _iter_polygons(sub_geom)


def _ensure_polygon_geometries(gdf: "gpd.GeoDataFrame") -> "gpd.GeoDataFrame":
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf["geometry"] = gdf.geometry.apply(shp.make_valid)

    polygonal = []
    for geom in gdf.geometry:
        polygons = list(_iter_polygons(geom))
        polygonal.append(shp.unary_union(polygons) if polygons else None)

    gdf["geometry"] = polygonal
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    if gdf.empty:
        raise ValueError("No polygon geometry found in shapefile.")
    return gdf


def _auto_value_field(gdf: "gpd.GeoDataFrame") -> str:
    numeric_cols = list(gdf.select_dtypes(include=["number"]).columns)
    if not numeric_cols:
        raise ValueError("No numeric field found. Please pass --value-field.")

    priority_keywords = ["rate", "dose", "value", "amount", "kg", "fert", "app"]
    for keyword in priority_keywords:
        for col in numeric_cols:
            if keyword in col.lower():
                return col
    return numeric_cols[0]


def _resolve_value_field(gdf: "gpd.GeoDataFrame", requested: str | None) -> str:
    if requested is None:
        return _auto_value_field(gdf)
    if requested not in gdf.columns:
        raise ValueError(f"Field '{requested}' does not exist in shapefile.")
    if not np.issubdtype(gdf[requested].dtype, np.number):
        raise ValueError(f"Field '{requested}' is not numeric.")
    return requested


def _rasterize_to_grid(
    gdf_grid: "gpd.GeoDataFrame",
    boundary_geom_grid: shp.Geometry,
    value_field: str,
    rows: int,
    cols: int,
    grid_bounds: tuple[float, float, float, float],
    boundary_mask_mode: str,
) -> tuple[np.ndarray, np.ndarray, float, float, int, int]:
    if rows <= 0 or cols <= 0:
        raise ValueError("Grid rows/cols must be > 0")
    if boundary_mask_mode not in {"center", "strict", "touch"}:
        raise ValueError(f"Unsupported boundary mask mode: {boundary_mask_mode}")

    minx, miny, maxx, maxy = [float(v) for v in grid_bounds]
    cell_east_size = (maxx - minx) / cols
    cell_north_size = (maxy - miny) / rows
    if cell_east_size <= 0 or cell_north_size <= 0:
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
            p_minx, p_miny, p_maxx, p_maxy = polygon.bounds
            c0 = max(0, int(math.floor((p_minx - minx) / cell_east_size)))
            c1 = min(cols - 1, int(math.ceil((p_maxx - minx) / cell_east_size)) - 1)
            r0 = max(0, int(math.floor((p_miny - miny) / cell_north_size)))
            r1 = min(rows - 1, int(math.ceil((p_maxy - miny) / cell_north_size)) - 1)
            if c0 > c1 or r0 > r1:
                continue

            local_cols = c1 - c0 + 1
            local_rows_count = r1 - r0 + 1

            if boundary_mask_mode == "touch":
                col_offsets = np.arange(local_cols, dtype=np.int32)
                row_offsets = np.arange(local_rows_count, dtype=np.int32)
                col_grid, row_grid = np.meshgrid(col_offsets, row_offsets)

                west = minx + (c0 + col_grid.ravel()) * cell_east_size
                south = miny + (r0 + row_grid.ravel()) * cell_north_size
                cell_boxes = shp.box(west, south, west + cell_east_size, south + cell_north_size)

                poly_mask = shp.intersects(polygon, cell_boxes)
                boundary_mask = shp.intersects(boundary_geom_grid, cell_boxes)
                keep_mask = np.logical_and(poly_mask, boundary_mask)
                if not np.any(keep_mask):
                    continue
                local_rows = row_grid.ravel()[keep_mask]
                local_cols_idx = col_grid.ravel()[keep_mask]
            else:
                xs = minx + (np.arange(c0, c1 + 1, dtype=np.float64) + 0.5) * cell_east_size
                ys = miny + (np.arange(r0, r1 + 1, dtype=np.float64) + 0.5) * cell_north_size
                x_grid, y_grid = np.meshgrid(xs, ys)
                points = shp.points(x_grid.ravel(), y_grid.ravel())
                keep_mask = shp.covers(polygon, points)
                if boundary_mask_mode == "center":
                    keep_mask = np.logical_and(keep_mask, shp.covers(boundary_geom_grid, points))
                if not np.any(keep_mask):
                    continue

                hit_idx = np.flatnonzero(keep_mask)
                local_rows = hit_idx // local_cols
                local_cols_idx = hit_idx % local_cols

                if boundary_mask_mode == "strict":
                    west = minx + (c0 + local_cols_idx) * cell_east_size
                    south = miny + (r0 + local_rows) * cell_north_size
                    cell_boxes = shp.box(west, south, west + cell_east_size, south + cell_north_size)
                    boundary_keep_mask = shp.covers(boundary_geom_grid, cell_boxes)
                    if not np.any(boundary_keep_mask):
                        continue
                    local_rows = local_rows[boundary_keep_mask]
                    local_cols_idx = local_cols_idx[boundary_keep_mask]

            hit_rows = local_rows + r0
            hit_cols = local_cols_idx + c0
            grid_data[hit_rows, hit_cols] = value
            coverage[hit_rows, hit_cols] = True

    return grid_data, coverage, minx, miny, rows, cols


def _infer_partfield_name(
    gdf: "gpd.GeoDataFrame",
    shp_path: Path,
    explicit_name: str | None,
) -> str:
    if explicit_name:
        return _trim(explicit_name, 32)

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


def _to_decimal_9(value: float) -> Decimal:
    return Decimal(f"{value:.9f}")


def _count_decimals(value: float, max_decimals: int = 7) -> int:
    text = f"{value:.12f}".rstrip("0").rstrip(".")
    if "." not in text:
        return 0
    return min(max_decimals, len(text.split(".")[1]))


def build_grid_taskdata_from_shapefile(options: GridFromShpOptions) -> GridFromShpResult:
    """Build ISOXML task data and binary refs from a prescription shapefile."""

    gpd = _load_geopandas()
    shp_path = options.shp_path
    if not shp_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shp_path}")

    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        if options.input_crs:
            gdf = gdf.set_crs(options.input_crs)
        else:
            raise ValueError("Input shapefile has no CRS. Pass --input-crs.")

    gdf = _ensure_polygon_geometries(gdf)
    value_field = _resolve_value_field(gdf, options.value_field)
    effective_unit, unit_source = _resolve_value_unit(gdf, options.value_unit, value_field)

    if options.boundary_shp is None:
        raise ValueError("Missing --boundary-shp. Boundary shapefile is required for PFD.")
    if not options.boundary_shp.exists():
        raise FileNotFoundError(f"Boundary shapefile not found: {options.boundary_shp}")

    gdf_boundary = gpd.read_file(options.boundary_shp)
    if gdf_boundary.crs is None:
        if options.input_crs:
            gdf_boundary = gdf_boundary.set_crs(options.input_crs)
        else:
            raise ValueError("Boundary shapefile has no CRS. Pass --input-crs.")
    gdf_boundary = _ensure_polygon_geometries(gdf_boundary)

    gdf_wgs84 = gdf.to_crs("EPSG:4326")
    gdf_boundary_wgs84 = gdf_boundary.to_crs("EPSG:4326")
    metric_crs = gdf_wgs84.estimate_utm_crs()
    if metric_crs is None:
        raise ValueError("Could not estimate a projected CRS from input geometry.")

    gdf_metric = gdf_wgs84.to_crs(metric_crs)
    gdf_boundary_metric = gdf_boundary_wgs84.to_crs(metric_crs)
    rx_metric_union = shp.unary_union(gdf_metric.geometry.values)
    rx_wgs84_union = shp.unary_union(gdf_wgs84.geometry.values)
    boundary_metric_union = shp.unary_union(gdf_boundary_metric.geometry.values)
    boundary_wgs84_union = shp.unary_union(gdf_boundary_wgs84.geometry.values)
    if boundary_metric_union.is_empty:
        raise ValueError("Boundary geometry is empty after projection.")
    if rx_metric_union.is_empty or rx_wgs84_union.is_empty:
        raise ValueError("Prescription geometry is empty after projection.")

    if options.grid_extent == "boundary":
        extent_metric_geom = boundary_metric_union
        extent_wgs84_geom = boundary_wgs84_union
    elif options.grid_extent == "union":
        extent_metric_geom = shp.unary_union([rx_metric_union, boundary_metric_union])
        extent_wgs84_geom = shp.unary_union([rx_wgs84_union, boundary_wgs84_union])
    else:
        extent_metric_geom = rx_metric_union
        extent_wgs84_geom = rx_wgs84_union

    if extent_metric_geom.is_empty or extent_wgs84_geom.is_empty:
        raise ValueError(f"Grid extent geometry is empty (mode: {options.grid_extent}).")

    extent_metric_bounds = extent_metric_geom.bounds
    metric_width = float(extent_metric_bounds[2]) - float(extent_metric_bounds[0])
    metric_height = float(extent_metric_bounds[3]) - float(extent_metric_bounds[1])
    cols = max(1, math.ceil(metric_width / options.cell_size_m))
    rows = max(1, math.ceil(metric_height / options.cell_size_m))

    grid_values, coverage, _origin_x, _origin_y, rows, cols = _rasterize_to_grid(
        gdf_grid=gdf_wgs84,
        boundary_geom_grid=boundary_wgs84_union,
        value_field=value_field,
        rows=rows,
        cols=cols,
        grid_bounds=extent_wgs84_geom.bounds,
        boundary_mask_mode=options.boundary_mask,
    )

    if options.xml_version == "4":
        iso_module = iso4
        shp_converter = ShapelyConverterV4()
        task_status = iso4.TaskStatus.Planned
        transfer_origin = iso4.Iso11783TaskDataDataTransferOrigin.FMIS
    else:
        iso_module = iso
        shp_converter = ShapelyConverterV3()
        task_status = iso.TaskStatus.Initial
        transfer_origin = iso.Iso11783TaskDataDataTransferOrigin.FMIS

    dd_entity = DDEntity.from_id(options.ddi)
    factor_to_ddi = _unit_factor_to_ddi(effective_unit, dd_entity)
    grid_values = grid_values * factor_to_ddi

    vpn_scale = dd_entity.bit_resolution / factor_to_ddi
    vpn_decimals = _count_decimals(vpn_scale)
    vpn_unit = effective_unit if effective_unit != "ddi" else (dd_entity.unit or "ddi")
    value_presentation = iso_module.ValuePresentation(
        id="VPN100",
        offset=0,
        scale=Decimal(str(vpn_scale)),
        number_of_decimals=vpn_decimals,
        unit_designator=_trim(vpn_unit, 32),
    )

    if boundary_wgs84_union.geom_type == "Polygon":
        partfield_polygons = [
            shp_converter.to_iso_polygon(boundary_wgs84_union, iso_module.PolygonType.PartfieldBoundary)
        ]
    elif boundary_wgs84_union.geom_type == "MultiPolygon":
        partfield_polygons = shp_converter.to_iso_polygon_list(
            boundary_wgs84_union,
            iso_module.PolygonType.PartfieldBoundary,
        )
    else:
        raise ValueError("Union geometry is not polygonal.")

    partfield_area_m2 = int(round(boundary_metric_union.area))
    min_lon, min_lat, max_lon, max_lat = extent_wgs84_geom.bounds
    cell_east_deg = (float(max_lon) - float(min_lon)) / cols
    cell_north_deg = (float(max_lat) - float(min_lat)) / rows

    customer = _build_customer(options.xml_version)
    farm = iso_module.Farm(id="FRM100", designator="farm", customer_id_ref=customer.id)
    partfield = iso_module.Partfield(
        id="PFD100",
        designator=_infer_partfield_name(gdf_boundary_wgs84, options.boundary_shp, options.partfield_name),
        area=partfield_area_m2,
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
        polygons=partfield_polygons,
    )

    default_tz = iso_module.TreatmentZone(
        code=0,
        designator="zone_0",
        process_data_variables=[
            iso_module.ProcessDataVariable(
                process_data_ddi=bytes(dd_entity),
                process_data_value=0,
                value_presentation_id_ref=value_presentation.id,
            )
        ],
    )

    grid_type = iso_module.GridType.GridType1 if options.grid_type == "1" else iso_module.GridType.GridType2
    treatment_zones = [default_tz]
    grid_kwargs: dict[str, object] = {}

    if grid_type == iso_module.GridType.GridType1:
        covered_values = grid_values[coverage]
        unique_values = np.unique(covered_values)
        unique_values = unique_values[unique_values != 0]
        if unique_values.size > 254:
            raise ValueError(
                f"Grid type 1 supports at most 254 treatment values, got {unique_values.size}. "
                "Use --grid-type 2."
            )

        grid_codes = np.zeros((rows, cols), dtype=np.uint8)
        for code, raw_value in enumerate(unique_values, start=1):
            code_int = int(code)
            value_float = float(raw_value)
            grid_codes[np.logical_and(coverage, grid_values == raw_value)] = code_int

            pdv = iso_module.ProcessDataVariable(
                process_data_ddi=bytes(dd_entity),
                process_data_value=int(round(value_float / dd_entity.bit_resolution)),
                value_presentation_id_ref=value_presentation.id,
            )
            treatment_zones.append(
                iso_module.TreatmentZone(
                    code=code_int,
                    designator=_trim(f"zone_{code_int}_{value_float:g}", 32),
                    process_data_variables=[pdv],
                )
            )
    else:
        grid_kwargs["treatment_zone_code"] = default_tz.code

    grid = iso_module.Grid(
        minimum_north_position=_to_decimal_9(float(min_lat)),
        minimum_east_position=_to_decimal_9(float(min_lon)),
        cell_north_size=float(cell_north_deg),
        cell_east_size=float(cell_east_deg),
        maximum_column=cols,
        maximum_row=rows,
        filename="GRD00000",
        type=grid_type,
        **grid_kwargs,
    )
    if grid_type == iso_module.GridType.GridType1:
        grid_bin = from_numpy_array_to_type_1(grid_codes, grid)
    else:
        grid_bin = from_numpy_array_to_type_2(grid_values, grid, ddi_list=[dd_entity], scale=True)

    task = iso_module.Task(
        id="TSK100",
        designator=_trim(f"grid{options.grid_type}_{shp_path.stem}", 32),
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

    task_data = iso_module.Iso11783TaskData(
        management_software_manufacturer=_trim(options.software_manufacturer, 32),
        management_software_version=_trim(options.software_version, 32),
        data_transfer_origin=transfer_origin,
        tasks=[task],
        customers=[customer],
        farms=[farm],
        partfields=[partfield],
        value_presentations=[value_presentation],
    )

    return GridFromShpResult(
        task_data=task_data,
        refs={grid.filename: grid_bin},
        value_field=value_field,
        effective_unit=effective_unit,
        unit_source=unit_source,
    )


convert_grid_from_shp = build_grid_taskdata_from_shapefile

__all__ = [
    "GridFromShpOptions",
    "GridFromShpResult",
    "build_grid_taskdata_from_shapefile",
    "convert_grid_from_shp",
    "validate_taskdata_xsd",
]
