import pytest

from isoxml.models.ddi import DDEntity


def test__from_id__when_known__expect_ddi_entry():
    entry = DDEntity.from_id(1)
    assert isinstance(entry, DDEntity)
    assert entry.ddi == 1
    assert entry.unit == "mm³/m²"
    assert entry.bit_resolution == 0.01
    assert entry.name


def test__from_id__when_unknown__expect_key_error():
    with pytest.raises(KeyError):
        DDEntity.from_id(9999999)


def test__to_bytes__when_valid__expect_big_endian():
    entry = DDEntity.from_id(60)
    assert bytes(entry) == b'\x00\x3c'


def test__from_bytes__when_valid__expect_correct_ddi():
    entry = DDEntity.from_bytes(b'\x00\x3c')
    assert entry.ddi == 60


def test__from_id__when_missing_optional_keys__expect_ddi_entry():
    # DDI 160 may have missing optional fields – should not raise
    entry = DDEntity.from_id(160)
    assert isinstance(entry, DDEntity)


def test__from_bytes__when_bytes_too_long__expect_key_error():
    with pytest.raises(KeyError):
        DDEntity.from_bytes(b"\xff\xff\xff")
