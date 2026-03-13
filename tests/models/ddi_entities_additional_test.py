import pytest

from isoxml.models.ddi_entities import DDEntity


def test__from_id__when_known__expect_unit_and_resolution_present():
    entry = DDEntity.from_id(1)
    assert entry.ddi == 1
    assert entry.unit == "mm³/m²"
    assert entry.bit_resolution == 0.01
    assert entry.name


def test__from_bytes__when_code_unknown__expect_key_error():
    with pytest.raises(KeyError):
        DDEntity.from_bytes(b"\xff\xff\xff")
