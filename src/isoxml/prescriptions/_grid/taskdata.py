"""Task-data assembly services for grid-from-shapefile workflows."""

from __future__ import annotations

from decimal import Decimal

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.geometry.shapely import ShapelyConverterV3, ShapelyConverterV4
from isoxml.grids.binary import encode_grid_type_1_binary, encode_grid_type_2_binary
from isoxml.models.ddi_entities import DDEntity
from isoxml.prescriptions._grid.types import (
    GridFromShpOptions,
    GridFromShpResult,
    IsoWorkflowContext,
    PreparedGridInputs,
    RasterizedGrid,
)


def truncate_text(text: str, max_len: int) -> str:
    return text[:max_len]


def conversion_factor_to_ddi(input_unit: str, ddi: DDEntity) -> float:
    if input_unit == "ddi":
        return 1.0
    if input_unit == "kg/ha":
        if ddi.ddi == 6 or ddi.unit == "mg/m²":
            return 100.0
        raise ValueError(
            f"--value-unit kg/ha is only supported for DDI=6 (mg/m² base unit), got DDI={ddi.ddi}."
        )
    raise ValueError(f"Unsupported input unit: {input_unit}")


def build_iso_workflow_context(xml_version: str) -> IsoWorkflowContext:
    if xml_version == "4":
        return IsoWorkflowContext(
            iso_module=iso4,
            shapely_converter=ShapelyConverterV4(),
            task_status=iso4.TaskStatus.Planned,
            transfer_origin=iso4.Iso11783TaskDataDataTransferOrigin.FMIS,
        )
    return IsoWorkflowContext(
        iso_module=iso3,
        shapely_converter=ShapelyConverterV3(),
        task_status=iso3.TaskStatus.Initial,
        transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
    )


def build_default_customer(xml_version: str):
    if xml_version == "4":
        return iso4.Customer(id="CTR100", last_name="customer")
    return iso3.Customer(id="CTR100", designator="customer")


def to_decimal_9_places(value: float) -> Decimal:
    return Decimal(f"{value:.9f}")


def count_decimal_places(value: float, max_decimals: int = 7) -> int:
    text = f"{value:.12f}".rstrip("0").rstrip(".")
    if "." not in text:
        return 0
    return min(max_decimals, len(text.split(".")[1]))


def _first_nonempty_string(series) -> str | None:
    try:
        from pandas.api.types import is_object_dtype, is_string_dtype
    except ModuleNotFoundError:  # pragma: no cover - pandas comes with geopandas
        is_string_like = series.dtype == object
    else:
        is_string_like = is_string_dtype(series.dtype) or is_object_dtype(series.dtype)

    if not is_string_like:
        return None

    for value in series.dropna():
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def infer_partfield_name(gdf_boundary_wgs84, shp_path, explicit_name: str | None) -> str:
    if explicit_name:
        return truncate_text(explicit_name, 32)

    columns_by_lower_name = {
        col.lower(): col for col in gdf_boundary_wgs84.columns if col != "geometry"
    }
    preferred_columns = [
        "name",
        "designator",
        "field_name",
        "partfield",
        "partfield_name",
        "label",
        "description",
    ]
    for col in preferred_columns:
        actual_col = columns_by_lower_name.get(col)
        if actual_col is not None:
            value = _first_nonempty_string(gdf_boundary_wgs84[actual_col])
            if value is not None:
                return truncate_text(value, 32)

    for col in gdf_boundary_wgs84.columns:
        if col == "geometry":
            continue
        value = _first_nonempty_string(gdf_boundary_wgs84[col])
        if value is not None:
            return truncate_text(value, 32)
    return truncate_text(shp_path.stem, 32)


def assemble_grid_taskdata_result(
    options: GridFromShpOptions,
    prepared: PreparedGridInputs,
    rasterized: RasterizedGrid,
) -> GridFromShpResult:
    """Build ISOXML task data and binary refs from prepared inputs."""

    context = build_iso_workflow_context(options.xml_version)
    iso_module = context.iso_module
    shp_converter = context.shapely_converter

    dd_entity = DDEntity.from_id(options.ddi)
    factor_to_ddi = conversion_factor_to_ddi(prepared.effective_unit, dd_entity)
    grid_values = rasterized.values * factor_to_ddi

    vpn_scale = dd_entity.bit_resolution / factor_to_ddi
    vpn_decimals = count_decimal_places(vpn_scale)
    vpn_unit = (
        prepared.effective_unit
        if prepared.effective_unit != "ddi"
        else (dd_entity.unit or "ddi")
    )
    value_presentation = iso_module.ValuePresentation(
        id="VPN100",
        offset=0,
        scale=Decimal(str(vpn_scale)),
        number_of_decimals=vpn_decimals,
        unit_designator=truncate_text(vpn_unit, 32),
    )

    if prepared.boundary_wgs84_union.geom_type == "Polygon":
        partfield_polygons = [
            shp_converter.to_iso_polygon(
                prepared.boundary_wgs84_union,
                iso_module.PolygonType.PartfieldBoundary,
            )
        ]
    elif prepared.boundary_wgs84_union.geom_type == "MultiPolygon":
        partfield_polygons = shp_converter.to_iso_polygon_list(
            prepared.boundary_wgs84_union,
            iso_module.PolygonType.PartfieldBoundary,
        )
    else:
        raise ValueError("Union geometry is not polygonal.")

    partfield_area_m2 = int(round(prepared.boundary_metric_union.area))
    min_lon, min_lat, max_lon, max_lat = rasterized.extent_wgs84_bounds
    cell_east_deg = (float(max_lon) - float(min_lon)) / rasterized.cols
    cell_north_deg = (float(max_lat) - float(min_lat)) / rasterized.rows

    customer = build_default_customer(options.xml_version)
    farm = iso_module.Farm(id="FRM100", designator="farm", customer_id_ref=customer.id)
    partfield = iso_module.Partfield(
        id="PFD100",
        designator=infer_partfield_name(
            prepared.gdf_boundary_wgs84,
            options.boundary_shp,
            options.partfield_name,
        ),
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
        if options.grid_type == "1"
        else iso_module.GridType.GridType2
    )
    treatment_zones = [default_tz]
    grid_kwargs: dict[str, object] = {}

    if grid_type == iso_module.GridType.GridType1:
        covered_values = grid_values[rasterized.coverage]
        unique_values = np.unique(covered_values)
        unique_values = unique_values[unique_values != 0]
        if unique_values.size > 254:
            raise ValueError(
                f"Grid type 1 supports at most 254 treatment values, got {unique_values.size}. "
                "Use --grid-type 2."
            )

        grid_codes = np.zeros((rasterized.rows, rasterized.cols), dtype=np.uint8)
        for code, raw_value in enumerate(unique_values, start=1):
            code_int = int(code)
            value_float = float(raw_value)
            grid_codes[
                np.logical_and(rasterized.coverage, grid_values == raw_value)
            ] = code_int

            pdv = iso_module.ProcessDataVariable(
                process_data_ddi=bytes(dd_entity),
                process_data_value=int(round(value_float / dd_entity.bit_resolution)),
                value_presentation_id_ref=value_presentation.id,
            )
            treatment_zones.append(
                iso_module.TreatmentZone(
                    code=code_int,
                    designator=truncate_text(f"zone_{code_int}_{value_float:g}", 32),
                    process_data_variables=[pdv],
                )
            )
    else:
        grid_kwargs["treatment_zone_code"] = default_tz.code

    grid = iso_module.Grid(
        minimum_north_position=to_decimal_9_places(float(min_lat)),
        minimum_east_position=to_decimal_9_places(float(min_lon)),
        cell_north_size=float(cell_north_deg),
        cell_east_size=float(cell_east_deg),
        maximum_column=rasterized.cols,
        maximum_row=rasterized.rows,
        filename="GRD00000",
        type=grid_type,
        **grid_kwargs,
    )
    if grid_type == iso_module.GridType.GridType1:
        grid_bin = encode_grid_type_1_binary(grid_codes, grid)
    else:
        grid_bin = encode_grid_type_2_binary(
            grid_values,
            grid,
            ddi_list=[dd_entity],
            scale=True,
        )

    task = iso_module.Task(
        id="TSK100",
        designator=truncate_text(f"grid{options.grid_type}_{options.shp_path.stem}", 32),
        status=context.task_status,
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
        management_software_manufacturer=truncate_text(options.software_manufacturer, 32),
        management_software_version=truncate_text(options.software_version, 32),
        data_transfer_origin=context.transfer_origin,
        tasks=[task],
        customers=[customer],
        farms=[farm],
        partfields=[partfield],
        value_presentations=[value_presentation],
    )

    return GridFromShpResult(
        task_data=task_data,
        refs={grid.filename: grid_bin},
        value_field=prepared.value_field,
        effective_unit=prepared.effective_unit,
        unit_source=prepared.unit_source,
    )
