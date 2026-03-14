"""Tests for the v4 → v3 conversion."""

from io import BytesIO

import pytest
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.convert import task_data_v3_to_v4, task_data_v4_to_v3
from tests.resources.test_resources import TEST_RES_DIR

_parser = XmlParser()
_serializer = XmlSerializer()

V3_GRID = TEST_RES_DIR / "isoxml/v3/grid_type_2/TASKDATA.XML"
V4_CNH = TEST_RES_DIR / "isoxml/v4/cnh_export/TASKDATA.XML"


def _load_v3(path=V3_GRID) -> iso3.Iso11783TaskData:
    return _parser.parse(path, iso3.Iso11783TaskData)


def _load_v4(path=V4_CNH) -> iso4.Iso11783TaskData:
    return _parser.parse(path, iso4.Iso11783TaskData)


# ---------------------------------------------------------------------------
# Basic type and version checks
# ---------------------------------------------------------------------------

def test_returns_v3_type():
    result = task_data_v4_to_v3(_load_v4())
    assert isinstance(result, iso3.Iso11783TaskData)


def test_version_major_is_3():
    result = task_data_v4_to_v3(_load_v4())
    assert result.version_major == iso3.Iso11783TaskDataVersionMajor.VALUE_3


# ---------------------------------------------------------------------------
# Scalar / metadata fields
# ---------------------------------------------------------------------------

def test_scalar_fields_preserved():
    v4 = _load_v4()
    v3 = task_data_v4_to_v3(v4)
    assert v3.management_software_manufacturer == v4.management_software_manufacturer
    assert v3.management_software_version == v4.management_software_version
    assert v3.data_transfer_origin.value == v4.data_transfer_origin.value


# ---------------------------------------------------------------------------
# TaskStatus enum remapping
# ---------------------------------------------------------------------------

def _make_v4_with_task(status: iso4.TaskStatus) -> iso4.Iso11783TaskData:
    td = iso4.Iso11783TaskData(
        management_software_manufacturer="test",
        management_software_version="1.0",
        data_transfer_origin=iso4.Iso11783TaskDataDataTransferOrigin.FMIS,
    )
    td.tasks = [iso4.Task(id="TSK00001", status=status)]
    return td


def test_task_status_planned_to_initial():
    """v4 Planned(1) → v3 Initial(1)."""
    v3 = task_data_v4_to_v3(_make_v4_with_task(iso4.TaskStatus.Planned))
    assert v3.tasks[0].status == iso3.TaskStatus.Initial


def test_task_status_completed_to_finished():
    """v4 Completed(4) → v3 Finished(4)."""
    v3 = task_data_v4_to_v3(_make_v4_with_task(iso4.TaskStatus.Completed))
    assert v3.tasks[0].status == iso3.TaskStatus.Finished


def test_task_status_v4_only_maps_to_none():
    """v4-only statuses (Template=5, Canceled=6) have no v3 equivalent → None."""
    v3 = task_data_v4_to_v3(_make_v4_with_task(iso4.TaskStatus.Template))
    assert v3.tasks[0].status is None


# ---------------------------------------------------------------------------
# Structural preservation
# ---------------------------------------------------------------------------

def test_partfield_count_preserved():
    v4 = _load_v4()
    v3 = task_data_v4_to_v3(v4)
    assert len(v3.partfields) == len(v4.partfields)


def test_partfield_designator_preserved():
    v4 = _load_v4()
    v3 = task_data_v4_to_v3(v4)
    for pf3, pf4 in zip(v3.partfields, v4.partfields):
        assert pf3.designator == pf4.designator


# ---------------------------------------------------------------------------
# v4-only fields are dropped
# ---------------------------------------------------------------------------

def test_v4_only_types_dropped():
    """v4-only collections (guidance_groups, etc.) must not appear in v3."""
    assert not hasattr(iso3.Partfield, "guidance_groups")
    assert not hasattr(iso3.Task, "control_assignments")
    assert not hasattr(iso3.Task, "guidance_allocations")
    assert not hasattr(iso3.Iso11783TaskData, "attached_files")


# ---------------------------------------------------------------------------
# Point.colour str → int
# ---------------------------------------------------------------------------

def test_point_colour_str_to_int():
    """Point.colour changed from str (v4) to int (v3)."""
    from isoxml.convert.v4_to_v3 import _convert_dataclass

    v4_point = iso4.Point(type=iso4.PointType.Flag, north=None, east=None, colour="12")
    result = _convert_dataclass(v4_point)
    assert isinstance(result, iso3.Point)
    assert result.colour == 12


def test_point_colour_non_numeric_str_becomes_none():
    from isoxml.convert.v4_to_v3 import _convert_dataclass

    v4_point = iso4.Point(type=iso4.PointType.Flag, north=None, east=None, colour="red")
    result = _convert_dataclass(v4_point)
    assert result.colour is None


# ---------------------------------------------------------------------------
# Round-trip: v3 → v4 → v3
# ---------------------------------------------------------------------------

def test_roundtrip_v3_v4_v3():
    """Converting v3→v4→v3 should reproduce the original tree."""
    v3_orig = _load_v3()
    v4 = task_data_v3_to_v4(v3_orig)
    v3_rt = task_data_v4_to_v3(v4)

    assert v3_rt.management_software_manufacturer == v3_orig.management_software_manufacturer
    assert len(v3_rt.tasks) == len(v3_orig.tasks)
    assert v3_rt.tasks[0].status == v3_orig.tasks[0].status
    assert v3_rt.tasks[0].designator == v3_orig.tasks[0].designator
    assert len(v3_rt.partfields) == len(v3_orig.partfields)


# ---------------------------------------------------------------------------
# XML serialisation
# ---------------------------------------------------------------------------

def test_xml_serialization_round_trip():
    """Converted v3 tree must survive XML serialisation and re-parsing."""
    v3 = task_data_v4_to_v3(_load_v4())
    xml = _serializer.render(v3)
    v3_rt = _parser.parse(BytesIO(xml.encode()), iso3.Iso11783TaskData)

    assert v3_rt.version_major == iso3.Iso11783TaskDataVersionMajor.VALUE_3
    assert v3_rt.management_software_manufacturer == v3.management_software_manufacturer


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_type_error_on_wrong_input():
    with pytest.raises(TypeError):
        task_data_v4_to_v3("not a task data object")  # type: ignore[arg-type]
