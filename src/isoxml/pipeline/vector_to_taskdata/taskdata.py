"""ISOXML object-graph building for vector-to-taskdata conversion."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import shapely as shp

import isoxml.models.base.v3 as iso
import isoxml.models.base.v4 as iso4
from isoxml.geometry.shapely import ShapelyConverterV3, ShapelyConverterV4
from isoxml.grid.codec import encode_type1, encode_type2
from isoxml.models.ddi import DDEntity
from isoxml.pipeline.vector_to_taskdata.geometry import infer_partfield_name
from isoxml.pipeline.vector_to_taskdata.inputs import trim, unit_factor_to_ddi
from isoxml.pipeline.vector_to_taskdata.types import (
    VectorToTaskDataOptions,
    VectorToTaskDataResult,
)


@dataclass(frozen=True)
class VersionContext:
    iso_mod: object
    shp_conv: object
    task_status: object
    transfer_origin: object


def select_version_context(xml_version: str) -> VersionContext:
    if xml_version == "4":
        return VersionContext(
            iso_mod=iso4,
            shp_conv=ShapelyConverterV4(),
            task_status=iso4.TaskStatus.Planned,
            transfer_origin=iso4.Iso11783TaskDataDataTransferOrigin.FMIS,
        )
    return VersionContext(
        iso_mod=iso,
        shp_conv=ShapelyConverterV3(),
        task_status=iso.TaskStatus.Initial,
        transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS,
    )


def build_customer(xml_version: str):
    if xml_version == "4":
        return iso4.Customer(id="CTR100", last_name="customer")
    return iso.Customer(id="CTR100", designator="customer")


def to_decimal9(value: float) -> Decimal:
    return Decimal(f"{value:.9f}")


def count_decimals(value: float, max_decimals: int = 7) -> int:
    text = f"{value:.12f}".rstrip("0").rstrip(".")
    if "." not in text:
        return 0
    return min(max_decimals, len(text.split(".")[1]))


def build_result(
    options: VectorToTaskDataOptions,
    gdf_boundary_wgs84,
    boundary_metric: shp.Geometry,
    boundary_wgs84: shp.Geometry,
    extent_wgs84: shp.Geometry,
    rows: int,
    cols: int,
    coverage: np.ndarray,
    grid_values: np.ndarray,
    value_field: str,
    effective_unit: str,
    unit_source: str,
) -> VectorToTaskDataResult:
    version_ctx = select_version_context(options.xml_version)
    iso_mod = version_ctx.iso_mod
    dd_entity = DDEntity.from_id(options.ddi)
    factor = unit_factor_to_ddi(effective_unit, dd_entity)
    scaled_grid_values = grid_values * factor

    vpn_scale = dd_entity.bit_resolution / factor
    vpn_unit = effective_unit if effective_unit != "ddi" else (dd_entity.unit or "ddi")
    value_presentation = iso_mod.ValuePresentation(
        id="VPN100",
        offset=0,
        scale=Decimal(str(vpn_scale)),
        number_of_decimals=count_decimals(vpn_scale),
        unit_designator=trim(vpn_unit, 32),
    )

    if boundary_wgs84.geom_type == "Polygon":
        partfield_polygons = [
            version_ctx.shp_conv.to_iso_polygon(
                boundary_wgs84, iso_mod.PolygonType.PartfieldBoundary
            )
        ]
    elif boundary_wgs84.geom_type == "MultiPolygon":
        partfield_polygons = version_ctx.shp_conv.to_iso_polygon_list(
            boundary_wgs84, iso_mod.PolygonType.PartfieldBoundary
        )
    else:
        raise ValueError("Boundary union is not polygonal.")

    min_lon, min_lat, max_lon, max_lat = extent_wgs84.bounds
    cell_east_deg = (float(max_lon) - float(min_lon)) / cols
    cell_north_deg = (float(max_lat) - float(min_lat)) / rows

    customer = build_customer(options.xml_version)
    farm = iso_mod.Farm(id="FRM100", designator="farm", customer_id_ref=customer.id)
    partfield = iso_mod.Partfield(
        id="PFD100",
        designator=infer_partfield_name(
            gdf_boundary_wgs84,
            options.boundary_path or options.source_path,
            options.partfield_name,
        ),
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
        iso_mod.GridType.GridType1
        if options.grid_type == "1"
        else iso_mod.GridType.GridType2
    )
    treatment_zones = [default_tz]
    grid_kwargs: dict = {}

    if grid_type == iso_mod.GridType.GridType1:
        covered_vals = np.unique(scaled_grid_values[coverage])
        covered_vals = covered_vals[covered_vals != 0]
        if covered_vals.size > 254:
            raise ValueError(
                f"Grid Type 1 supports at most 254 treatment values; "
                f"found {covered_vals.size}. Use grid_type='2'."
            )
        grid_codes = np.zeros((rows, cols), dtype=np.uint8)
        for code, raw in enumerate(covered_vals, start=1):
            mask = np.logical_and(coverage, scaled_grid_values == raw)
            grid_codes[mask] = int(code)
            treatment_zones.append(
                iso_mod.TreatmentZone(
                    code=int(code),
                    designator=trim(f"zone_{code}_{float(raw):g}", 32),
                    process_data_variables=[
                        iso_mod.ProcessDataVariable(
                            process_data_ddi=bytes(dd_entity),
                            process_data_value=int(
                                round(float(raw) / dd_entity.bit_resolution)
                            ),
                            value_presentation_id_ref=value_presentation.id,
                        )
                    ],
                )
            )
    else:
        grid_kwargs["treatment_zone_code"] = default_tz.code

    grid = iso_mod.Grid(
        minimum_north_position=to_decimal9(float(min_lat)),
        minimum_east_position=to_decimal9(float(min_lon)),
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
        grid_bin = encode_type2(
            scaled_grid_values, grid, ddi_list=[dd_entity], scale=True
        )

    task = iso_mod.Task(
        id="TSK100",
        designator=trim(f"grid{options.grid_type}_{options.source_path.stem}", 32),
        status=version_ctx.task_status,
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
        management_software_manufacturer=trim(options.software_manufacturer, 32),
        management_software_version=trim(options.software_version, 32),
        data_transfer_origin=version_ctx.transfer_origin,
        tasks=[task],
        customers=[customer],
        farms=[farm],
        partfields=[partfield],
        value_presentations=[value_presentation],
    )

    return VectorToTaskDataResult(
        task_data=task_data,
        refs={grid.filename: grid_bin},
        value_field=value_field,
        effective_unit=effective_unit,
        unit_source=unit_source,
    )
