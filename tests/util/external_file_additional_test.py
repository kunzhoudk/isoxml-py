import pytest

import isoxml.models.base.v3 as iso3
from isoxml.util.external_file import merge_ext_content


def _minimal_task_data_v3() -> iso3.Iso11783TaskData:
    return iso3.Iso11783TaskData(
        management_software_manufacturer="pytest",
        management_software_version="0.0.1",
        data_transfer_origin=iso3.Iso11783TaskDataDataTransferOrigin.FMIS,
    )


def test__merge_ext_content__when_missing_reference_data__expect_key_error():
    task_data = _minimal_task_data_v3()
    task_data.external_file_references = [
        iso3.ExternalFileReference(filename="CTR1234", filetype=iso3.ExternalFileReferenceType.XML)
    ]

    with pytest.raises(KeyError):
        merge_ext_content(task_data, {}, inplace=True)


def test__merge_ext_content__when_not_inplace__expect_source_unmodified():
    task_data = _minimal_task_data_v3()
    task_data.external_file_references = [
        iso3.ExternalFileReference(filename="CTR1234", filetype=iso3.ExternalFileReferenceType.XML)
    ]
    ext_file_obj = {
        "CTR1234": iso3.ExternalFileContents(
            customers=[iso3.Customer(id="CTR1234", designator="cust")]
        )
    }

    merged, remaining = merge_ext_content(task_data, ext_file_obj, inplace=False)

    assert len(task_data.customers) == 0
    assert len(task_data.external_file_references) == 1
    assert len(merged.customers) == 1
    assert len(merged.external_file_references) == 0
    assert remaining == {}
    assert "CTR1234" in ext_file_obj
