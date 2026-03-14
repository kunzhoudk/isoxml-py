from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import numpy as np
import pytest
from xsdata.models.datatype import XmlDateTime

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.io import read_from_path
from isoxml.pipeline import convert_grid_prescriptions

DDI_6 = b"\x00\x06"
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "resources" / "isoxml" / "prescription_converter"
FIXTURE_NAMES = [
    "small_xml_v3_type_1_auto.zip",
    "small_xml_v3_type_2_auto.zip",
    "small_xml_v4_type_1_auto.zip",
    "small_xml_v4_type_2_auto.zip",
]


def _grid_kwargs(filename: str):
    return dict(
        minimum_north_position=Decimal("55.0"),
        minimum_east_position=Decimal("12.0"),
        cell_north_size=0.001,
        cell_east_size=0.001,
        maximum_column=2,
        maximum_row=2,
        filename=filename,
    )


def _make_v3_type1_case():
    zones = [
        iso3.TreatmentZone(
            code=1,
            process_data_variables=[
                iso3.ProcessDataVariable(process_data_ddi=DDI_6, process_data_value=100),
            ],
        ),
        iso3.TreatmentZone(
            code=2,
            process_data_variables=[
                iso3.ProcessDataVariable(process_data_ddi=DDI_6, process_data_value=200),
            ],
        ),
    ]
    grid = iso3.Grid(
        **_grid_kwargs("GRD00001"),
        type=iso3.GridType.GridType1,
    )
    task = iso3.Task(
        id="TSK0001",
        status=iso3.TaskStatus.Initial,
        treatment_zones=zones,
        grids=[grid],
    )
    task_data = iso3.Iso11783TaskData(
        management_software_manufacturer="acme",
        management_software_version="1.0",
        data_transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
        tasks=[task],
    )
    refs = {
        "GRD00001": np.array([[1, 2], [2, 1]], dtype=np.uint8).tobytes(),
    }
    return task_data, refs


def _make_v4_type2_case():
    template_zone = iso4.TreatmentZone(
        code=42,
        process_data_variables=[
            iso4.ProcessDataVariable(
                process_data_ddi=DDI_6,
                process_data_value=0,
                value_presentation_id_ref="VPN0001",
            ),
        ],
    )
    grid = iso4.Grid(
        **_grid_kwargs("GRD00002"),
        type=iso4.GridType.GridType2,
        treatment_zone_code=42,
    )
    task = iso4.Task(
        id="TSK0002",
        status=iso4.TaskStatus.Planned,
        treatment_zones=[template_zone],
        grids=[grid],
    )
    task_data = iso4.Iso11783TaskData(
        management_software_manufacturer="acme",
        management_software_version="2.0",
        data_transfer_origin=iso4.Iso11783TaskDataDataTransferOrigin.FMIS,
        lang="en",
        tasks=[task],
    )
    refs = {
        "GRD00002": np.array([[100, 100], [200, 300]], dtype=np.int32).tobytes(),
    }
    return task_data, refs


def _make_v3_metadata_case():
    device = iso3.Device(
        id="DVC100",
        working_set_master_name=b"\x01\x02\x03\x04\x05\x06\x07\x08",
        structure_label="01020304050607",
        localization_label="FF020304050607",
    )
    worker = iso3.Worker(id="WKR100", designator="worker")
    product_allocation = iso3.ProductAllocation(
        product_id_ref="PDT100",
        amount_ddi=DDI_6,
        amount_value=123,
    )
    allocation_stamp = iso3.AllocationStamp(
        start=XmlDateTime.from_string("2024-01-01T00:00:00"),
        type=iso3.AllocationStampType.Planned,
        position=iso3.Position(north=Decimal("55.1"), east=Decimal("12.1")),
    )
    device_allocation = iso3.DeviceAllocation(
        working_set_master_name_value=b"\x11\x12\x13\x14\x15\x16\x17\x18",
        working_set_master_name_mask=b"\xff\xff\xff\xff\xff\xff\xff\xff",
        allocation_stamp=allocation_stamp,
        device_id_ref=device.id,
    )
    task = iso3.Task(
        id="TSK200",
        status=iso3.TaskStatus.Initial,
        device_allocations=[device_allocation],
        product_allocations=[product_allocation],
    )
    task_data = iso3.Iso11783TaskData(
        management_software_manufacturer="acme",
        management_software_version="1.0",
        data_transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
        customers=[iso3.Customer(id="CTR200", designator="customer")],
        workers=[worker],
        devices=[device],
        tasks=[task],
    )
    return task_data


def test_convert_v3_type1_to_v4_type1():
    task_data, refs = _make_v3_type1_case()

    result = convert_grid_prescriptions(
        task_data,
        refs,
        target_xml_version=4,
        target_grid_type=1,
    )

    assert isinstance(result.task_data, iso4.Iso11783TaskData)
    assert result.task_data.version_major == iso4.Iso11783TaskDataVersionMajor.VALUE_4
    assert result.task_data.tasks[0].status == iso4.TaskStatus.Planned
    assert result.task_data.tasks[0].grids[0].type == iso4.GridType.GridType1
    assert result.refs["GRD00001"] == refs["GRD00001"]


def test_convert_v3_type1_to_v4_type2():
    task_data, refs = _make_v3_type1_case()

    result = convert_grid_prescriptions(
        task_data,
        refs,
        target_xml_version=4,
        target_grid_type=2,
    )

    grid = result.task_data.tasks[0].grids[0]
    arr = np.frombuffer(result.refs[grid.filename], dtype=np.int32).reshape(2, 2)

    assert isinstance(result.task_data, iso4.Iso11783TaskData)
    assert grid.type == iso4.GridType.GridType2
    assert grid.filelength == len(result.refs[grid.filename])
    assert np.array_equal(arr, np.array([[100, 200], [200, 100]], dtype=np.int32))


def test_convert_v4_type2_to_v3_type2():
    task_data, refs = _make_v4_type2_case()

    result = convert_grid_prescriptions(
        task_data,
        refs,
        target_xml_version="3",
        target_grid_type="2",
    )

    assert isinstance(result.task_data, iso3.Iso11783TaskData)
    assert result.task_data.version_major == iso3.Iso11783TaskDataVersionMajor.VALUE_3
    assert result.task_data.tasks[0].status == iso3.TaskStatus.Initial
    assert result.task_data.tasks[0].grids[0].type == iso3.GridType.GridType2
    assert result.refs["GRD00002"] == refs["GRD00002"]


def test_convert_v4_type2_to_v3_type1():
    task_data, refs = _make_v4_type2_case()

    result = convert_grid_prescriptions(
        task_data,
        refs,
        target_xml_version=3,
        target_grid_type=1,
    )

    task = result.task_data.tasks[0]
    grid = task.grids[0]
    zone_codes = np.frombuffer(result.refs[grid.filename], dtype=np.uint8).reshape(2, 2)
    generated_codes = set(np.unique(zone_codes).tolist())
    generated_zones = [tzn for tzn in task.treatment_zones if tzn.code in generated_codes]

    assert isinstance(result.task_data, iso3.Iso11783TaskData)
    assert grid.type == iso3.GridType.GridType1
    assert grid.filelength == len(result.refs[grid.filename])
    assert generated_codes == {0, 1, 2}
    assert {tzn.process_data_variables[0].process_data_value for tzn in generated_zones} == {
        100,
        200,
        300,
    }
    assert all(tzn.process_data_variables[0].process_data_ddi == DDI_6 for tzn in generated_zones)


def test_convert_metadata_field_renames_between_versions():
    task_data = _make_v3_metadata_case()

    v4_result = convert_grid_prescriptions(
        task_data,
        {},
        target_xml_version=4,
        target_grid_type=1,
    )
    v4_task_data = v4_result.task_data
    assert v4_task_data.customers[0].last_name == "customer"
    assert v4_task_data.workers[0].last_name == "worker"
    assert v4_task_data.devices[0].client_name == b"\x01\x02\x03\x04\x05\x06\x07\x08"
    assert v4_task_data.tasks[0].device_allocations[0].client_name_value == b"\x11\x12\x13\x14\x15\x16\x17\x18"
    assert v4_task_data.tasks[0].device_allocations[0].client_name_mask == b"\xff\xff\xff\xff\xff\xff\xff\xff"
    assert v4_task_data.tasks[0].product_allocations[0].quantity_ddi == DDI_6
    assert v4_task_data.tasks[0].product_allocations[0].quantity_value == 123
    assert len(v4_task_data.tasks[0].device_allocations[0].allocation_stamp.positions) == 1

    v3_roundtrip = convert_grid_prescriptions(
        v4_task_data,
        {},
        target_xml_version=3,
        target_grid_type=1,
    ).task_data
    assert v3_roundtrip.customers[0].designator == "customer"
    assert v3_roundtrip.workers[0].designator == "worker"
    assert v3_roundtrip.devices[0].working_set_master_name == b"\x01\x02\x03\x04\x05\x06\x07\x08"
    assert v3_roundtrip.tasks[0].device_allocations[0].working_set_master_name_value == b"\x11\x12\x13\x14\x15\x16\x17\x18"
    assert v3_roundtrip.tasks[0].product_allocations[0].amount_ddi == DDI_6
    assert v3_roundtrip.tasks[0].product_allocations[0].amount_value == 123
    assert v3_roundtrip.tasks[0].device_allocations[0].allocation_stamp.position is not None


def _load_zip_fixture(filename: str):
    with TemporaryDirectory() as tmp_dir:
        with ZipFile(FIXTURE_DIR / filename) as zf:
            zf.extractall(tmp_dir)
        task_data, refs = read_from_path(Path(tmp_dir) / "TASKDATA")
    return task_data, refs


def _materialize_pdv_values(task_data, refs) -> np.ndarray:
    task = task_data.tasks[0]
    grid = task.grids[0]
    rows = int(grid.maximum_row)
    cols = int(grid.maximum_column)
    grid_bin = refs[grid.filename]

    if int(grid.type.value) == 1:
        zone_codes = np.frombuffer(grid_bin, dtype=np.uint8).reshape(rows, cols)
        zone_map: dict[int, list[int]] = {
            int(tzn.code): [int(pdv.process_data_value) for pdv in tzn.process_data_variables]
            for tzn in task.treatment_zones
            if tzn.code is not None
        }
        pdv_count = len(next(iter(zone_map.values())))
        lookup = np.zeros((256, pdv_count), dtype=np.int32)
        for code, values in zone_map.items():
            lookup[code] = values
        values = lookup[zone_codes]
        return values[:, :, 0] if pdv_count == 1 else values

    raw = np.frombuffer(grid_bin, dtype=np.int32)
    pdv_count = raw.size // (rows * cols)
    if pdv_count == 1:
        return raw.reshape(rows, cols)
    return raw.reshape(rows, cols, pdv_count)


@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
@pytest.mark.parametrize(
    ("target_xml_version", "target_grid_type"),
    [(3, 1), (3, 2), (4, 1), (4, 2)],
)
def test_convert_real_zip_fixtures_preserves_prescription_values(
        fixture_name: str,
        target_xml_version: int,
        target_grid_type: int,
):
    task_data, refs = _load_zip_fixture(fixture_name)
    expected_values = _materialize_pdv_values(task_data, refs)

    result = convert_grid_prescriptions(
        task_data,
        refs,
        target_xml_version=target_xml_version,
        target_grid_type=target_grid_type,
    )

    actual_values = _materialize_pdv_values(result.task_data, result.refs)
    grid = result.task_data.tasks[0].grids[0]

    assert result.task_data.version_major.value == str(target_xml_version)
    assert int(grid.type.value) == target_grid_type
    assert np.array_equal(actual_values, expected_values)


def test_convert_with_xsd_validation_returns_schema_path():
    task_data, refs = _make_v3_type1_case()

    result = convert_grid_prescriptions(
        task_data,
        refs,
        target_xml_version=4,
        target_grid_type=2,
        validate_output=True,
    )

    assert result.validated_xsd_path is not None
    assert result.validated_xsd_path.name == "ISO11783_TaskFile_V4-3.xsd"


def test_convert_real_fixture_with_xsd_validation_returns_schema_path():
    task_data, refs = _load_zip_fixture("small_xml_v3_type_1_auto.zip")

    result = convert_grid_prescriptions(
        task_data,
        refs,
        target_xml_version=4,
        target_grid_type=2,
        validate_output=True,
    )

    assert result.validated_xsd_path is not None
    assert result.validated_xsd_path.name == "ISO11783_TaskFile_V4-3.xsd"
