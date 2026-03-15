"""
Grid Type 2 application map example.

Grid Type 2 encodes application values directly in a binary file as int32.
The XML only holds scale/offset metadata. Best for many continuous values.
"""

from decimal import Decimal
from pathlib import Path

import numpy as np
import shapely as shp

import isoxml.models.base.v3 as iso
from isoxml.geometry import ShapelyConverterV3
from isoxml.grid import encode_type2
from isoxml.io import write_to_zip
from isoxml.models import DDEntity

EXAMPLES_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = EXAMPLES_DIR / "output" / "example_grid_2.zip"

FIELD_WKT = (
    "POLYGON ((15.1461618 48.1269217, 15.1461618 48.1267442, "
    "15.1463363 48.1267442, 15.1463363 48.1269217, 15.1461618 48.1269217))"
)

DD_ENTITY = DDEntity.from_id(6)
converter = ShapelyConverterV3()


def main() -> None:
    iso_boundary = converter.to_iso_polygon(
        shp.from_wkt(FIELD_WKT), iso.PolygonType.PartfieldBoundary
    )

    customer = iso.Customer(id="CTR100", designator="jr_customer")
    farm = iso.Farm(id="FRM100", designator="jr_farm", customer_id_ref=customer.id)
    partfield = iso.Partfield(
        id="PFD100",
        designator="test_field",
        area=123456,
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
        polygons=[iso_boundary],
    )

    grid_data = np.array([[0, 1111], [2222, 3333]])
    rows, cols = grid_data.shape

    default_tz = iso.TreatmentZone(
        code=0,
        designator="zone_0",
        process_data_variables=[
            iso.ProcessDataVariable(
                process_data_ddi=bytes(DD_ENTITY),
                process_data_value=0,
            )
        ],
    )

    grid = iso.Grid(
        minimum_north_position=Decimal("48.12674"),
        minimum_east_position=Decimal("15.14615"),
        cell_north_size=0.0001,
        cell_east_size=0.0001,
        maximum_column=cols,
        maximum_row=rows,
        filename="GRD00000",
        type=iso.GridType.GridType2,
        treatment_zone_code=default_tz.code,
    )
    grid_bin = encode_type2(grid_data, grid, ddi_list=[DD_ENTITY])

    task = iso.Task(
        id="TSK100",
        designator="task_grid_type_2",
        status=iso.TaskStatus.Initial,
        grids=[grid],
        treatment_zones=[default_tz],
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
        partfield_id_ref=partfield.id,
        default_treatment_zone_code=default_tz.code,
        position_lost_treatment_zone_code=default_tz.code,
        out_of_field_treatment_zone_code=default_tz.code,
    )

    task_data = iso.Iso11783TaskData(
        management_software_manufacturer="test_manufacturer",
        management_software_version="0.0.1",
        data_transfer_origin=iso.Iso11783TaskDataDataTransferOrigin.FMIS,
        customers=[customer],
        farms=[farm],
        partfields=[partfield],
        tasks=[task],
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "wb") as file_handle:
        write_to_zip(file_handle, task_data, {grid.filename: grid_bin})
    print(f"Written: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
