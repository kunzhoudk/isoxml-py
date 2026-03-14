from decimal import Decimal

import numpy as np
import pytest
from xsdata.models.datatype import XmlDateTime

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.pipeline.prescription_converter.grid import (
    convert_task_grids,
    normalize_grid_type,
)
from isoxml.pipeline.prescription_converter.tree import (
    convert_reference,
    convert_tree,
    resolve_target_module,
)

DDI_6 = b"\x00\x06"


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


def test_resolve_target_module_rejects_unsupported_version():
    with pytest.raises(ValueError, match="Unsupported target XML version"):
        resolve_target_module(5)


def test_normalize_grid_type_rejects_unsupported_grid_type():
    with pytest.raises(ValueError, match="Unsupported target grid type"):
        normalize_grid_type(3)


def test_convert_reference_keeps_bytes_unchanged():
    payload = b"grid-bin"
    assert convert_reference(payload, iso4) is payload


def test_convert_tree_maps_point_colour_between_versions():
    v3_point = iso3.Point(
        type=iso3.PointType.Flag,
        north=Decimal("55.1"),
        east=Decimal("12.1"),
        colour=7,
    )
    v4_point = convert_tree(v3_point, iso4)
    assert isinstance(v4_point, iso4.Point)
    assert v4_point.colour == "7"

    roundtrip = convert_tree(v4_point, iso3)
    assert isinstance(roundtrip, iso3.Point)
    assert roundtrip.colour == 7


def test_convert_tree_maps_allocation_stamp_position_between_versions():
    stamp = iso3.AllocationStamp(
        start=XmlDateTime.from_string("2024-01-01T00:00:00"),
        type=iso3.AllocationStampType.Planned,
        position=iso3.Position(north=Decimal("55.1"), east=Decimal("12.1")),
    )

    converted = convert_tree(stamp, iso4)
    assert isinstance(converted, iso4.AllocationStamp)
    assert len(converted.positions) == 1
    assert converted.positions[0].north == Decimal("55.1")

    roundtrip = convert_tree(converted, iso3)
    assert isinstance(roundtrip, iso3.AllocationStamp)
    assert roundtrip.position is not None
    assert roundtrip.position.east == Decimal("12.1")


def test_convert_task_grids_rejects_missing_binary_reference():
    grid = iso3.Grid(**_grid_kwargs("GRD00001"), type=iso3.GridType.GridType1)
    task = iso3.Task(
        id="TSK0001",
        status=iso3.TaskStatus.Initial,
        treatment_zones=[],
        grids=[grid],
    )
    task_data = iso3.Iso11783TaskData(
        management_software_manufacturer="acme",
        management_software_version="1.0",
        data_transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
        tasks=[task],
    )

    with pytest.raises(KeyError, match="Missing binary payload"):
        convert_task_grids(task_data, {}, iso3, 1)


def test_convert_task_grids_rejects_non_binary_reference():
    grid = iso3.Grid(**_grid_kwargs("GRD00001"), type=iso3.GridType.GridType1)
    task = iso3.Task(
        id="TSK0001",
        status=iso3.TaskStatus.Initial,
        treatment_zones=[],
        grids=[grid],
    )
    task_data = iso3.Iso11783TaskData(
        management_software_manufacturer="acme",
        management_software_version="1.0",
        data_transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
        tasks=[task],
    )

    with pytest.raises(ValueError, match="is not binary data"):
        convert_task_grids(task_data, {"GRD00001": "not-bytes"}, iso3, 1)


def test_convert_task_grids_rejects_type1_with_unknown_zone_code():
    grid = iso3.Grid(**_grid_kwargs("GRD00001"), type=iso3.GridType.GridType1)
    task = iso3.Task(
        id="TSK0001",
        status=iso3.TaskStatus.Initial,
        treatment_zones=[
            iso3.TreatmentZone(
                code=1,
                process_data_variables=[
                    iso3.ProcessDataVariable(process_data_ddi=DDI_6, process_data_value=100)
                ],
            )
        ],
        grids=[grid],
    )
    task_data = iso3.Iso11783TaskData(
        management_software_manufacturer="acme",
        management_software_version="1.0",
        data_transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
        tasks=[task],
    )
    refs = {"GRD00001": np.array([[1, 2], [1, 1]], dtype=np.uint8).tobytes()}

    with pytest.raises(ValueError, match="unknown TreatmentZone code"):
        convert_task_grids(task_data, refs, iso3, 2)


def test_convert_task_grids_rejects_type1_with_inconsistent_pdv_counts():
    grid = iso3.Grid(**_grid_kwargs("GRD00001"), type=iso3.GridType.GridType1)
    task = iso3.Task(
        id="TSK0001",
        status=iso3.TaskStatus.Initial,
        treatment_zones=[
            iso3.TreatmentZone(
                code=1,
                process_data_variables=[
                    iso3.ProcessDataVariable(process_data_ddi=DDI_6, process_data_value=100)
                ],
            ),
            iso3.TreatmentZone(
                code=2,
                process_data_variables=[
                    iso3.ProcessDataVariable(process_data_ddi=DDI_6, process_data_value=200),
                    iso3.ProcessDataVariable(process_data_ddi=DDI_6, process_data_value=300),
                ],
            ),
        ],
        grids=[grid],
    )
    task_data = iso3.Iso11783TaskData(
        management_software_manufacturer="acme",
        management_software_version="1.0",
        data_transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
        tasks=[task],
    )
    refs = {"GRD00001": np.array([[1, 2], [1, 2]], dtype=np.uint8).tobytes()}

    with pytest.raises(ValueError, match="inconsistent PDV counts"):
        convert_task_grids(task_data, refs, iso3, 2)


def test_convert_task_grids_type2_to_type1_uses_null_templates_when_no_zone_matches():
    grid = iso4.Grid(
        **_grid_kwargs("GRD00002"),
        type=iso4.GridType.GridType2,
        treatment_zone_code=99,
    )
    task = iso4.Task(
        id="TSK0002",
        status=iso4.TaskStatus.Planned,
        treatment_zones=[],
        grids=[grid],
    )
    task_data = iso4.Iso11783TaskData(
        management_software_manufacturer="acme",
        management_software_version="2.0",
        data_transfer_origin=iso4.Iso11783TaskDataDataTransferOrigin.FMIS,
        lang="en",
        tasks=[task],
    )
    refs = {"GRD00002": np.array([[100, 200], [100, 200]], dtype=np.int32).tobytes()}

    convert_task_grids(task_data, refs, iso4, 1)

    zone_codes = np.frombuffer(refs["GRD00002"], dtype=np.uint8).reshape(2, 2)
    produced_codes = set(np.unique(zone_codes).tolist())
    produced_zones = [tzn for tzn in task.treatment_zones if tzn.code in produced_codes]

    assert task.grids[0].type == iso4.GridType.GridType1
    assert produced_codes == {0, 1}
    assert all(tzn.process_data_variables[0].process_data_ddi is None for tzn in produced_zones)
    assert all(tzn.process_data_variables[0].value_presentation_id_ref is None for tzn in produced_zones)
