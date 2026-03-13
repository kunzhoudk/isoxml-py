"""
Convert a polygon prescription shapefile to ISOXML v3 grid map (TASKDATA.XML + GRDxxxx.bin).

Example:
    .venv/bin/python examples/app_map_grid_type_2_from_shp.py \
        examples/input/Rx/Rx.shp \
        --grid-type 1 \
        --value-field rate \
        --cell-size-m 10 \
        --output-dir examples/output/app_map_grid_type_2_from_shp
"""

from __future__ import annotations

import argparse
import math
from decimal import Decimal
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely as shp
import xmlschema
from pyproj import CRS, Transformer

import isoxml.models.base.v3 as iso
import isoxml.models.base.v4 as iso4
from isoxml.converter.np_grid import from_numpy_array_to_type_1, from_numpy_array_to_type_2
from isoxml.converter.shapely_geom import ShapelyConverterV3, ShapelyConverterV4
from isoxml.models.ddi_entities import DDEntity
from isoxml.util.isoxml_io import isoxml_to_dir, isoxml_to_text, isoxml_to_zip


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).parent
    parser = argparse.ArgumentParser(
        description="Convert polygon .shp prescription map to ISOXML v3 grid type 1 or 2.",
    )
    parser.add_argument(
        "shp_path",
        nargs="?",
        type=Path,
        default=base_dir / "input" / "Rx" / "Rx.shp",
        help="Input shapefile (.shp).",
    )
    parser.add_argument(
        "--value-field",
        type=str,
        default=None,
        help="Numeric field used as prescription value (auto-detected if omitted).",
    )
    parser.add_argument(
        "--ddi",
        type=int,
        default=6,
        help="DDI used for grid values (default: 6, Setpoint Mass Per Area Application Rate).",
    )
    parser.add_argument(
        "--value-unit",
        choices=["auto", "ddi", "kg/ha"],
        default="auto",
        help=(
            "Unit of input value field. 'auto' tries to read from shapefile fields, "
            "'ddi' means already in DDI base unit, 'kg/ha' will be converted."
        ),
    )
    parser.add_argument(
        "--grid-type",
        choices=["1", "2"],
        default="2",
        help="ISOXML grid type (1=lookup table in XML, 2=values in BIN). Default: 2.",
    )
    parser.add_argument(
        "--xml-version",
        choices=["3", "4"],
        default="3",
        help="ISOXML task data version to generate (default: 3).",
    )
    parser.add_argument(
        "--cell-size-m",
        type=float,
        default=10.0,
        help="Grid cell size in meters in projected CRS (default: 10).",
    )
    parser.add_argument(
        "--input-crs",
        type=str,
        default=None,
        help="CRS to apply when input file has no CRS metadata, e.g. EPSG:4326.",
    )
    parser.add_argument(
        "--partfield-name",
        type=str,
        default=None,
        help="Partfield designator (default: auto from data/file name).",
    )
    parser.add_argument(
        "--boundary-shp",
        type=Path,
        default=None,
        help="Boundary shapefile (.shp) used to build PFD geometry (required).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=base_dir / "output" / "app_map_grid_type_2_from_shp",
        help="Directory to write TASKDATA.XML and GRD00000.bin.",
    )
    parser.add_argument(
        "--output-zip",
        type=Path,
        default=None,
        help="Optional zip output path (e.g. examples/output/app_map_grid_type_2_from_shp.zip).",
    )
    parser.add_argument(
        "--software-manufacturer",
        type=str,
        default="isoxml-py",
        help="ISOXML ManagementSoftwareManufacturer field.",
    )
    parser.add_argument(
        "--software-version",
        type=str,
        default="0.1.0",
        help="ISOXML ManagementSoftwareVersion field.",
    )
    parser.add_argument(
        "--no-xsd-validate",
        action="store_true",
        help="Skip XSD validation after generating TASKDATA.",
    )
    return parser.parse_args()


def _trim(text: str, max_len: int) -> str:
    return text[:max_len]


def _unit_factor_to_ddi(input_unit: str, ddi: DDEntity) -> float:
    if input_unit == "ddi":
        return 1.0
    if input_unit == "kg/ha":
        # 1 kg/ha = 100 mg/m²
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


def _detect_unit_from_shp(gdf: gpd.GeoDataFrame, value_field: str) -> tuple[str | None, str | None]:
    candidate_cols: list[str] = []
    paired_col = f"{value_field}_unit"
    if paired_col in gdf.columns:
        candidate_cols.append(paired_col)

    preferred = {"unit", "units", "uom", "value_unit", "rate_unit", "dose_unit", "app_unit", "application_unit"}
    for col in gdf.columns:
        if col == "geometry":
            continue
        col_l = col.lower()
        if col_l in preferred or col_l.endswith("_unit"):
            if col not in candidate_cols:
                candidate_cols.append(col)

    for col in candidate_cols:
        series = gdf[col].dropna()
        if series.empty:
            continue
        normalized = {u for u in (_normalize_unit_text(v) for v in series.unique()) if u is not None}
        if len(normalized) == 1:
            detected = next(iter(normalized))
            return detected, col
    return None, None


def _resolve_value_unit(gdf: gpd.GeoDataFrame, requested_unit: str, value_field: str) -> tuple[str, str]:
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


def _ensure_polygon_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf["geometry"] = gdf.geometry.apply(shp.make_valid)

    polygonal = []
    for geom in gdf.geometry:
        polygons = list(_iter_polygons(geom))
        if polygons:
            polygonal.append(shp.unary_union(polygons))
        else:
            polygonal.append(None)
    gdf["geometry"] = polygonal
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    if gdf.empty:
        raise ValueError("No polygon geometry found in shapefile.")
    return gdf


def _auto_value_field(gdf: gpd.GeoDataFrame) -> str:
    numeric_cols = list(gdf.select_dtypes(include=["number"]).columns)
    if not numeric_cols:
        raise ValueError("No numeric field found. Please pass --value-field.")

    priority_keywords = ["rate", "dose", "value", "amount", "kg", "fert", "app"]
    for keyword in priority_keywords:
        for col in numeric_cols:
            if keyword in col.lower():
                return col
    return numeric_cols[0]


def _resolve_value_field(gdf: gpd.GeoDataFrame, requested: str | None) -> str:
    if requested is None:
        return _auto_value_field(gdf)
    if requested not in gdf.columns:
        raise ValueError(f"Field '{requested}' does not exist in shapefile.")
    if not np.issubdtype(gdf[requested].dtype, np.number):
        raise ValueError(f"Field '{requested}' is not numeric.")
    return requested


def _rasterize_to_grid(
    gdf_metric: gpd.GeoDataFrame,
    value_field: str,
    cell_size_m: float,
) -> tuple[np.ndarray, np.ndarray, float, float, int, int]:
    if cell_size_m <= 0:
        raise ValueError("--cell-size-m must be > 0")

    minx, miny, maxx, maxy = gdf_metric.total_bounds
    cols = max(1, math.ceil((maxx - minx) / cell_size_m))
    rows = max(1, math.ceil((maxy - miny) / cell_size_m))

    # row 0 starts at the minimum northing (south). This matches ISOXML's bottom-up grid axis.
    grid_data = np.zeros((rows, cols), dtype=np.float32)
    coverage = np.zeros((rows, cols), dtype=bool)

    for feature in gdf_metric[[value_field, "geometry"]].itertuples(index=False):
        value = float(feature[0])
        if not np.isfinite(value):
            continue
        geom = feature[1]
        for polygon in _iter_polygons(geom):
            if polygon.is_empty:
                continue
            p_minx, p_miny, p_maxx, p_maxy = polygon.bounds
            c0 = max(0, int(math.floor((p_minx - minx) / cell_size_m)))
            c1 = min(cols - 1, int(math.ceil((p_maxx - minx) / cell_size_m)) - 1)
            r0 = max(0, int(math.floor((p_miny - miny) / cell_size_m)))
            r1 = min(rows - 1, int(math.ceil((p_maxy - miny) / cell_size_m)) - 1)
            if c0 > c1 or r0 > r1:
                continue

            xs = minx + (np.arange(c0, c1 + 1, dtype=np.float64) + 0.5) * cell_size_m
            ys = miny + (np.arange(r0, r1 + 1, dtype=np.float64) + 0.5) * cell_size_m
            x_grid, y_grid = np.meshgrid(xs, ys)
            points = shp.points(x_grid.ravel(), y_grid.ravel())
            mask = shp.covers(polygon, points)
            if not np.any(mask):
                continue

            hit_idx = np.flatnonzero(mask)
            local_cols = c1 - c0 + 1
            hit_rows = (hit_idx // local_cols) + r0
            hit_cols = (hit_idx % local_cols) + c0
            grid_data[hit_rows, hit_cols] = value
            coverage[hit_rows, hit_cols] = True

    origin_x = minx
    origin_y = miny
    return grid_data, coverage, origin_x, origin_y, rows, cols


def _infer_partfield_name(
    gdf: gpd.GeoDataFrame, shp_path: Path, explicit_name: str | None
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


def _validate_taskdata_xsd(task_data: iso.Iso11783TaskData | iso4.Iso11783TaskData, xml_version: str) -> Path:
    xsd_filename = "ISO11783_TaskFile_V4-3.xsd" if xml_version == "4" else "ISO11783_TaskFile_V3-3.xsd"
    xsd_path = Path(__file__).resolve().parent.parent / "resources" / "xsd" / xsd_filename
    xmlschema.validate(isoxml_to_text(task_data), xsd_path)
    return xsd_path


def build_isoxml_from_shp(
    args: argparse.Namespace,
) -> tuple[iso.Iso11783TaskData | iso4.Iso11783TaskData, dict[str, bytes], str, str, str]:
    shp_path = args.shp_path
    if not shp_path.exists():
        raise FileNotFoundError(f"Shapefile not found: {shp_path}")

    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        if args.input_crs:
            gdf = gdf.set_crs(args.input_crs)
        else:
            raise ValueError("Input shapefile has no CRS. Pass --input-crs.")

    gdf = _ensure_polygon_geometries(gdf)
    value_field = _resolve_value_field(gdf, args.value_field)
    effective_unit, unit_source = _resolve_value_unit(gdf, args.value_unit, value_field)

    if args.boundary_shp is None:
        raise ValueError("Missing --boundary-shp. Boundary shapefile is required for PFD.")
    if not args.boundary_shp.exists():
        raise FileNotFoundError(f"Boundary shapefile not found: {args.boundary_shp}")

    gdf_boundary = gpd.read_file(args.boundary_shp)
    if gdf_boundary.crs is None:
        if args.input_crs:
            gdf_boundary = gdf_boundary.set_crs(args.input_crs)
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

    grid_values, coverage, origin_x, origin_y, rows, cols = _rasterize_to_grid(
        gdf_metric=gdf_metric,
        value_field=value_field,
        cell_size_m=args.cell_size_m,
    )

    if args.xml_version == "4":
        iso_module = iso4
        shp_converter = ShapelyConverterV4()
        task_status = iso4.TaskStatus.Planned
        transfer_origin = iso4.Iso11783TaskDataDataTransferOrigin.FMIS
    else:
        iso_module = iso
        shp_converter = ShapelyConverterV3()
        task_status = iso.TaskStatus.Initial
        transfer_origin = iso.Iso11783TaskDataDataTransferOrigin.FMIS

    dd_entity = DDEntity.from_id(args.ddi)
    factor_to_ddi = _unit_factor_to_ddi(effective_unit, dd_entity)
    grid_values = grid_values * factor_to_ddi

    # Raw integer in PDV/bin is converted to display value by VPN scale:
    # display = raw * (ddi.bit_resolution / factor_to_ddi)
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

    boundary_wgs84 = shp.unary_union(gdf_boundary_wgs84.geometry.values)
    if boundary_wgs84.geom_type == "Polygon":
        partfield_polygons = [
            shp_converter.to_iso_polygon(boundary_wgs84, iso_module.PolygonType.PartfieldBoundary)
        ]
    elif boundary_wgs84.geom_type == "MultiPolygon":
        partfield_polygons = shp_converter.to_iso_polygon_list(
            boundary_wgs84, iso_module.PolygonType.PartfieldBoundary
        )
    else:
        raise ValueError("Union geometry is not polygonal.")

    boundary_metric = shp.unary_union(gdf_boundary_metric.geometry.values)
    partfield_area_m2 = int(round(boundary_metric.area))

    min_lon, min_lat, max_lon, max_lat = gdf_wgs84.total_bounds
    origin_lon = float(min_lon)
    origin_lat = float(min_lat)
    cell_east_deg = (float(max_lon) - float(min_lon)) / cols
    cell_north_deg = (float(max_lat) - float(min_lat)) / rows

    customer = _build_customer(args.xml_version)
    farm = iso_module.Farm(id="FRM100", designator="farm", customer_id_ref=customer.id)

    partfield = iso_module.Partfield(
        id="PFD100",
        designator=_infer_partfield_name(gdf_boundary_wgs84, args.boundary_shp, args.partfield_name),
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

    grid_type = (
        iso_module.GridType.GridType1
        if args.grid_type == "1"
        else iso_module.GridType.GridType2
    )
    treatment_zones = [default_tz]
    grid_kwargs: dict[str, object] = {}

    if grid_type == iso_module.GridType.GridType1:
        covered_values = grid_values[coverage]
        unique_values = np.unique(covered_values)
        # code=0 is reserved for the default zone; avoid creating a duplicate zone for value 0.
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
        minimum_north_position=_to_decimal_9(origin_lat),
        minimum_east_position=_to_decimal_9(origin_lon),
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
        grid_bin = from_numpy_array_to_type_2(
            grid_values, grid, ddi_list=[dd_entity], scale=True
        )

    task = iso_module.Task(
        id="TSK100",
        designator=_trim(f"grid{args.grid_type}_{shp_path.stem}", 32),
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
        management_software_manufacturer=_trim(args.software_manufacturer, 32),
        management_software_version=_trim(args.software_version, 32),
        data_transfer_origin=transfer_origin,
        tasks=[task],
        customers=[customer],
        farms=[farm],
        partfields=[partfield],
        value_presentations=[value_presentation],
    )

    refs = {grid.filename: grid_bin}
    return task_data, refs, value_field, effective_unit, unit_source


def main() -> None:
    args = parse_args()
    task_data, refs, value_field, effective_unit, unit_source = build_isoxml_from_shp(args)

    validated_xsd_path = None
    if not args.no_xsd_validate:
        validated_xsd_path = _validate_taskdata_xsd(task_data, args.xml_version)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    isoxml_to_dir(output_dir, task_data, refs)

    if args.output_zip is not None:
        args.output_zip.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_zip, "wb") as zip_file:
            isoxml_to_zip(zip_file, task_data, refs)

    grid = task_data.tasks[0].grids[0]
    print("ISOXML conversion complete:")
    print(f"  xml version:{args.xml_version}")
    print(f"  input:      {args.shp_path}")
    print(f"  boundary:   {args.boundary_shp}")
    print(f"  grid type:  {args.grid_type}")
    print(f"  value field:{value_field}")
    print(f"  value unit: {effective_unit} (source: {unit_source})")
    print(f"  grid:       {grid.maximum_row} x {grid.maximum_column}")
    print(f"  zones:      {len(task_data.tasks[0].treatment_zones)}")
    if validated_xsd_path is not None:
        print(f"  xsd:        OK ({validated_xsd_path.name})")
    print(f"  output dir: {output_dir}")
    if args.output_zip is not None:
        print(f"  output zip: {args.output_zip}")


if __name__ == "__main__":
    main()
