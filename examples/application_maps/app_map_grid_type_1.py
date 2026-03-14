"""
Grid Type 1 application map example.

Grid Type 1 works as a lookup table: each cell stores a treatment zone code
(uint8) and the actual dose values live in the XML TreatmentZone elements.
"""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import numpy as np
import shapely as shp

import isoxml.models.base.v3 as iso
from isoxml.geometry import ShapelyConverterV3
from isoxml.grid import encode_type1
from isoxml.io import write_to_zip
from isoxml.models import DDEntity

EXAMPLES_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = EXAMPLES_DIR / "output" / "example_grid_1.zip"

ROWS, COLS = 2, 2
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
        id="PFD101",
        designator="jr_field",
        area=123456,
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
        polygons=[iso_boundary],
    )

    grid = iso.Grid(
        minimum_north_position=Decimal("48.12674"),
        minimum_east_position=Decimal("15.14615"),
        cell_north_size=0.0001,
        cell_east_size=0.0001,
        maximum_column=COLS,
        maximum_row=ROWS,
        filename="GRD00000",
        type=iso.GridType.GridType1,
    )

    grid_data = np.arange(ROWS * COLS, dtype=np.uint8).reshape(ROWS, COLS)
    grid_bin = encode_type1(grid_data, grid)

    base_pdv = iso.ProcessDataVariable(
        process_data_ddi=bytes(DD_ENTITY),
        process_data_value=0,
    )
    treatment_zones = [
        iso.TreatmentZone(code=0, designator="zone_0", process_data_variables=[replace(base_pdv, process_data_value=0)]),
        iso.TreatmentZone(code=1, designator="zone_1", process_data_variables=[replace(base_pdv, process_data_value=1000)]),
        iso.TreatmentZone(code=2, designator="zone_2", process_data_variables=[replace(base_pdv, process_data_value=2000)]),
        iso.TreatmentZone(code=3, designator="zone_3", process_data_variables=[replace(base_pdv, process_data_value=3000)]),
    ]

    task = iso.Task(
        id="TSK101",
        designator="task_grid_type_1",
        status=iso.TaskStatus.Initial,
        grids=[grid],
        treatment_zones=treatment_zones,
        customer_id_ref=customer.id,
        farm_id_ref=farm.id,
        partfield_id_ref=partfield.id,
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

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "wb") as file_handle:
        write_to_zip(file_handle, task_data, {grid.filename: grid_bin})
    print(f"Written: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
