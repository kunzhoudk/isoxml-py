"""Tests for the v3 → v4 conversion."""

from io import BytesIO

import pytest
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.convert import task_data_v3_to_v4
from tests.resources.test_resources import TEST_RES_DIR

_parser = XmlParser()
_serializer = XmlSerializer()

V3_GRID = TEST_RES_DIR / "isoxml/v3/grid_type_2/TASKDATA.XML"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_v3(path=V3_GRID) -> iso3.Iso11783TaskData:
    return _parser.parse(path, iso3.Iso11783TaskData)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_returns_v4_type():
    result = task_data_v3_to_v4(_load_v3())
    assert isinstance(result, iso4.Iso11783TaskData)


def test_version_major_is_4():
    result = task_data_v3_to_v4(_load_v3())
    assert result.version_major == iso4.Iso11783TaskDataVersionMajor.VALUE_4


def test_scalar_fields_preserved():
    v3 = _load_v3()
    v4 = task_data_v3_to_v4(v3)
    assert v4.management_software_manufacturer == v3.management_software_manufacturer
    assert v4.management_software_version == v3.management_software_version
    assert v4.data_transfer_origin.value == v3.data_transfer_origin.value


def test_task_status_enum_remapped():
    """v3 Initial(1) → v4 Planned(1), v3 Finished(4) → v4 Completed(4)."""
    v3 = _load_v3()
    assert v3.tasks[0].status == iso3.TaskStatus.Initial

    v4 = task_data_v3_to_v4(v3)
    assert v4.tasks[0].status == iso4.TaskStatus.Planned


def test_task_designator_preserved():
    v3 = _load_v3()
    v4 = task_data_v3_to_v4(v3)
    assert v4.tasks[0].designator == v3.tasks[0].designator


def test_partfield_count_preserved():
    v3 = _load_v3()
    v4 = task_data_v3_to_v4(v3)
    assert len(v4.partfields) == len(v3.partfields)
    assert v4.partfields[0].designator == v3.partfields[0].designator


def test_v4_only_lists_are_empty():
    """Fields that exist only in v4 should default to empty lists."""
    v4 = task_data_v3_to_v4(_load_v3())
    assert v4.partfields[0].guidance_groups == []
    assert v4.tasks[0].control_assignments == []
    assert v4.tasks[0].guidance_allocations == []
    assert v4.attached_files == []
    assert v4.base_stations == []


def test_point_colour_int_to_str():
    """Point.colour changed from int (v3) to str (v4)."""
    v3_point = iso3.Point(type=iso3.PointType.Flag, north=None, east=None, colour=5)
    v4_point = iso4.Point(type=iso4.PointType.Flag, north=None, east=None)

    from isoxml.convert.v3_to_v4 import _convert_dataclass
    result = _convert_dataclass(v3_point)
    assert isinstance(result, iso4.Point)
    assert result.colour == "5"


def test_xml_serialization_round_trip():
    """Converted v4 tree must survive XML serialisation and re-parsing."""
    v4 = task_data_v3_to_v4(_load_v3())
    xml = _serializer.render(v4)
    v4_rt = _parser.parse(BytesIO(xml.encode()), iso4.Iso11783TaskData)

    assert v4_rt.version_major == iso4.Iso11783TaskDataVersionMajor.VALUE_4
    assert v4_rt.tasks[0].status == iso4.TaskStatus.Planned
    assert v4_rt.tasks[0].designator == v4.tasks[0].designator


def test_type_error_on_wrong_input():
    with pytest.raises(TypeError):
        task_data_v3_to_v4("not a task data object")  # type: ignore[arg-type]
