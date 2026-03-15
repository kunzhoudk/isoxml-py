"""
Vector-based application map example.

Creates an ISOXML v4 task where each treatment zone is a polygon with its own
dose value. Suitable for a small number of clearly defined zones (< ~20).
"""

from importlib import resources
from pathlib import Path

import geopandas as gpd
import xmlschema

import isoxml.models.base.v4 as iso
from isoxml.geometry import ShapelyConverterV4
from isoxml.io import write_to_dir
from isoxml.models import DDEntity

EXAMPLES_DIR = Path(__file__).resolve().parents[1]
INPUT_PATH = EXAMPLES_DIR / "input" / "app_map_vector.geojson"
OUTPUT_DIR = EXAMPLES_DIR / "output" / "app_map_vector"

DD_ENTITY = DDEntity.from_id(1)
converter = ShapelyConverterV4()


def load_zones(path: Path) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    gdf = gpd.read_file(path).to_crs("EPSG:4326")
    border = gdf[gdf["name"] == "border"]
    zones = gdf[gdf["dose"] >= 0]
    if len(border) != 1:
        raise ValueError(f"Expected exactly one 'border' feature, found {len(border)}.")
    return border, zones


def build_partfield(
    border: gpd.GeoDataFrame,
    customer: iso.Customer,
    farm: iso.Farm,
) -> iso.Partfield:
    geom = border.geometry.values[0]
    area_m2 = int(border.to_crs(border.estimate_utm_crs()).area.values[0])
    return iso.Partfield(
        id="PFD100",
        designator=str(border["name"].values[0]),
        area=area_m2,
        polygons=[converter.to_iso_polygon(geom, iso.PolygonType.PartfieldBoundary)],
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
    )


def build_treatment_zones(zones: gpd.GeoDataFrame) -> list[iso.TreatmentZone]:
    default = iso.TreatmentZone(
        code=0,
        designator="no_zone",
        process_data_variables=[
            iso.ProcessDataVariable(
                process_data_ddi=bytes(DD_ENTITY),
                process_data_value=0,
            )
        ],
    )
    result = [default]
    for code, row in enumerate(zones.itertuples(), start=1):
        pdv = iso.ProcessDataVariable(
            process_data_ddi=bytes(DD_ENTITY),
            process_data_value=int(row.dose / DD_ENTITY.bit_resolution),
        )
        result.append(
            iso.TreatmentZone(
                code=code,
                designator=str(row.name),
                process_data_variables=[pdv],
                polygons=[converter.to_iso_polygon(row.geometry, iso.PolygonType.TreatmentZone)],
            )
        )
    return result


def main() -> None:
    border, zones = load_zones(INPUT_PATH)

    customer = iso.Customer(id="CTR100", last_name="jr_customer")
    farm = iso.Farm(id="FRM100", designator="jr_farm", customer_id_ref=customer.id)
    partfield = build_partfield(border, customer, farm)
    treatment_zones = build_treatment_zones(zones)
    default_tz = treatment_zones[0]

    task = iso.Task(
        id="TSK100",
        designator="vector application map",
        status=iso.TaskStatus.Planned,
        partfield_id_ref=partfield.id,
        treatment_zones=treatment_zones,
        default_treatment_zone_code=default_tz.code,
        position_lost_treatment_zone_code=default_tz.code,
        out_of_field_treatment_zone_code=default_tz.code,
    )

    task_data = iso.Iso11783TaskData(
        management_software_manufacturer="josephinum research",
        management_software_version="0.0.1",
        data_transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS,
        customers=[customer],
        farms=[farm],
        partfields=[partfield],
        tasks=[task],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_to_dir(OUTPUT_DIR, task_data)

    xsd_ref = resources.files("isoxml.reference.xsd").joinpath("ISO11783_TaskFile_V4-3.xsd")
    with resources.as_file(xsd_ref) as xsd_path:
        xmlschema.validate(OUTPUT_DIR / "TASKDATA.XML", xsd_path)
    print(f"Written and validated: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
