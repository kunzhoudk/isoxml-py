import pytest

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.io.external import merge_ext_content


def _minimal_v3() -> iso3.Iso11783TaskData:
    return iso3.Iso11783TaskData(
        management_software_manufacturer="pytest",
        management_software_version="0.0.1",
        data_transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
    )


def test__merge_ext_content__when_not_inplace__expect_originals_unchanged():
    task_data = _minimal_v3()
    customer = iso3.Customer(id='CTR1234', designator='test_ctr')
    ext_ref = iso3.ExternalFileReference(filename='CTR1234', filetype=iso3.ExternalFileReferenceType.XML)
    ext_file = iso3.ExternalFileContents(customers=[customer])
    task_data.external_file_references = [ext_ref]
    ext_map = {'CTR1234': ext_file}

    merged, remaining = merge_ext_content(task_data, ext_map, inplace=False)

    assert customer in merged.customers
    assert customer not in task_data.customers
    assert remaining == {}
    assert 'CTR1234' in ext_map  # original dict untouched


def test__merge_ext_content__when_inplace__expect_task_data_altered():
    task_data = iso4.Iso11783TaskData(
        management_software_manufacturer="pytest",
        management_software_version="0.0.1",
        data_transfer_origin=iso4.Iso11783TaskDataDataTransferOrigin.FMIS,
    )
    customer = iso4.Customer(id='CTR1234', last_name='test_ctr')
    ext_ref = iso4.ExternalFileReference(filename='CTR1234', filetype=iso4.ExternalFileReferenceType.XML)
    ext_file = iso4.ExternalFileContents(customers=[customer])
    task_data.external_file_references = [ext_ref]
    ext_map = {'CTR1234': ext_file}

    merge_ext_content(task_data, ext_map, inplace=True)

    assert customer in task_data.customers
    assert ext_map == {}


def test__merge_ext_content__when_unreferenced_entry__expect_entry_retained():
    task_data = _minimal_v3()
    customer = iso3.Customer(id='CTR1234', designator='test_ctr')
    ext_file = iso3.ExternalFileContents(customers=[customer])
    ext_map = {'CTR1234': ext_file}

    merge_ext_content(task_data, ext_map, inplace=True)

    assert 'CTR1234' in ext_map


def test__merge_ext_content__when_reference_missing_from_map__expect_key_error():
    task_data = _minimal_v3()
    task_data.external_file_references = [
        iso3.ExternalFileReference(filename='CTR1234', filetype=iso3.ExternalFileReferenceType.XML)
    ]
    with pytest.raises(KeyError):
        merge_ext_content(task_data, {}, inplace=True)


def test__merge_ext_content__when_not_inplace_source_list_kept():
    task_data = _minimal_v3()
    task_data.external_file_references = [
        iso3.ExternalFileReference(filename='CTR1234', filetype=iso3.ExternalFileReferenceType.XML)
    ]
    ext_map = {
        'CTR1234': iso3.ExternalFileContents(
            customers=[iso3.Customer(id='CTR1234', designator='cust')]
        )
    }
    merged, remaining = merge_ext_content(task_data, ext_map, inplace=False)

    assert len(task_data.customers) == 0
    assert len(task_data.external_file_references) == 1
    assert len(merged.customers) == 1
    assert len(merged.external_file_references) == 0
    assert remaining == {}
    assert 'CTR1234' in ext_map
