import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile

import pytest

import isoxml.models.base.v4 as iso4
from isoxml.util.isoxml_io import isoxml_from_path, isoxml_from_text, isoxml_to_dir, isoxml_to_zip
from tests.resources.test_resources import TEST_RES_DIR


def _task_data_minimal_v4() -> iso4.Iso11783TaskData:
    return iso4.Iso11783TaskData(
        management_software_manufacturer="pytest",
        management_software_version="0.0.1",
        data_transfer_origin=iso4.Iso11783TaskDataDataTransferOrigin.FMIS,
    )


def test__isoxml_from_text__when_version_missing__expect_error():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?><ISO11783_TaskData></ISO11783_TaskData>"""
    with pytest.raises(ValueError):
        isoxml_from_text(xml_content)


def test__isoxml_from_path__when_taskdata_xml_path__expect_parsed():
    path = TEST_RES_DIR / "isoxml/v3/grid_type_2/TASKDATA.XML"
    task_data, refs = isoxml_from_path(path)
    assert str(getattr(task_data.version_major, "value", task_data.version_major)) == "3"
    assert "GRD00001" in refs


def test__isoxml_from_path__when_read_bin_files_false__expect_no_bin_refs():
    path = TEST_RES_DIR / "isoxml/v3/grid_type_2"
    task_data, refs = isoxml_from_path(path, read_bin_files=False)
    assert str(getattr(task_data.version_major, "value", task_data.version_major)) == "3"
    assert refs == {}


def test__isoxml_from_path__when_external_files_ignore__expect_no_external_content_loaded():
    path = TEST_RES_DIR / "isoxml/v4/deutz_export"
    task_data, refs = isoxml_from_path(path, external_files="ignore", read_bin_files=False)
    assert len(task_data.external_file_references) > 0
    assert refs == {}


def test__isoxml_from_path__when_external_ref_matches_multiple_files__expect_assertion():
    src = TEST_RES_DIR / "isoxml/v4/deutz_export"
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "taskdata"
        shutil.copytree(src, tmp_path)
        original = tmp_path / "TSK00000.XML"
        duplicate = tmp_path / "TSK00000_DUP.XML"
        duplicate.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")

        with pytest.raises(AssertionError):
            isoxml_from_path(tmp_path, external_files="separate", read_bin_files=False)


def test__isoxml_to_dir__when_ref_type_unknown__expect_error():
    task_data = _task_data_minimal_v4()
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(ValueError):
            isoxml_to_dir(Path(tmp_dir), task_data, {"BADREF": 123})


def test__isoxml_to_zip__when_ref_type_unknown__expect_error():
    task_data = _task_data_minimal_v4()
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / "bad.zip"
        with pytest.raises(ValueError):
            with ZipFile(zip_path, "w") as _:
                pass
            isoxml_to_zip(zip_path, task_data, {"BADREF": object()})
