import os
import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile

import pytest

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.io.reader import read_from_path, read_from_xml, read_from_zip
from tests.resources.test_resources import TEST_RES_DIR


def test__read_from_xml__when_v4_str__expect_parsed():
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ISO11783_TaskData VersionMajor="4" VersionMinor="3"'
        ' ManagementSoftwareManufacturer="pytest"'
        ' ManagementSoftwareVersion="0.0.1"'
        ' DataTransferOrigin="1"></ISO11783_TaskData>'
    )
    task_data = read_from_xml(xml)
    assert isinstance(task_data, iso4.Iso11783TaskData)


def test__read_from_xml__when_version_missing__expect_error():
    xml = '<?xml version="1.0" encoding="UTF-8"?><ISO11783_TaskData></ISO11783_TaskData>'
    with pytest.raises(ValueError):
        read_from_xml(xml)


def test__read_from_path__when_xml_path__expect_parsed_v3():
    path = TEST_RES_DIR / 'isoxml/v3/grid_type_2/TASKDATA.XML'
    task_data, refs = read_from_path(path)
    assert isinstance(task_data, iso3.Iso11783TaskData)
    assert 'GRD00001' in refs


def test__read_from_path__when_dir_path__expect_parsed_v3():
    path = TEST_RES_DIR / 'isoxml/v3/grid_type_2'
    task_data, refs = read_from_path(path)
    assert isinstance(task_data, iso3.Iso11783TaskData)
    assert 'GRD00001' in refs


def test__read_from_path__when_read_bin_files_false__expect_no_bin_refs():
    path = TEST_RES_DIR / 'isoxml/v3/grid_type_2'
    task_data, refs = read_from_path(path, read_bin_files=False)
    assert isinstance(task_data, iso3.Iso11783TaskData)
    assert refs == {}


def test__read_from_path__when_external_files_separate__expect_separate_objects():
    path = TEST_RES_DIR / 'isoxml/v4/deutz_export/'
    task_data, refs = read_from_path(path, external_files='separate')
    assert len(task_data.tasks) == 0
    ext = refs['TSK00000']
    assert isinstance(ext, iso4.ExternalFileContents)
    assert len(ext.tasks) == 2


def test__read_from_path__when_external_files_merge__expect_merged():
    path = TEST_RES_DIR / 'isoxml/v4/deutz_export/'
    task_data, refs = read_from_path(path, external_files='merge')
    assert len(task_data.tasks) == 2
    assert 'TSK00000' not in refs
    assert isinstance(task_data.tasks[0], iso4.Task)


def test__read_from_path__when_external_files_ignore__expect_empty_refs():
    path = TEST_RES_DIR / 'isoxml/v4/deutz_export'
    task_data, refs = read_from_path(path, external_files='ignore', read_bin_files=False)
    assert len(task_data.external_file_references) > 0
    assert refs == {}


def test__read_from_path__when_duplicate_ext_ref_files__expect_assertion_error():
    src = TEST_RES_DIR / 'isoxml/v4/deutz_export'
    with tempfile.TemporaryDirectory() as tmp_dir:
        dst = Path(tmp_dir) / 'taskdata'
        shutil.copytree(src, dst)
        orig = dst / 'TSK00000.XML'
        dup = dst / 'TSK00000_DUP.XML'
        dup.write_text(orig.read_text(encoding='utf-8'), encoding='utf-8')
        with pytest.raises(AssertionError):
            read_from_path(dst, external_files='separate', read_bin_files=False)


def test__read_from_zip__when_valid_archive__expect_parsed_v3():
    path = TEST_RES_DIR / 'isoxml/v3/grid_type_2/grid_type_2.zip'
    task_data, refs = read_from_zip(path)
    assert isinstance(task_data, iso3.Iso11783TaskData)
    assert 'GRD00001' in refs
