import os
import tempfile
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
import xmlschema

import isoxml.models.base.v4 as iso4
from isoxml.io.writer import to_xml, write_to_dir, write_to_zip
from isoxml.models.ddi import DDEntity
from resources.resources import RES_DIR
from tests.resources.test_resources import TEST_RES_DIR


@pytest.fixture()
def task_with_grid():
    task_data = iso4.Iso11783TaskData(
        management_software_manufacturer="josephinum research",
        management_software_version="0.0.1",
        data_transfer_origin=iso4.Iso11783TaskDataDataTransferOrigin.FMIS,
    )
    pdv_0 = iso4.ProcessDataVariable(
        process_data_ddi=bytes(DDEntity.from_id(6)),
        process_data_value=0,
    )
    treatment_0 = iso4.TreatmentZone(
        code=0, designator="zone_0", process_data_variables=[pdv_0]
    )
    grid = iso4.Grid(
        minimum_north_position=round(Decimal(48.143304983), 9),
        minimum_east_position=round(Decimal(15.141245418), 9),
        cell_north_size=0.0001,
        cell_east_size=0.0001,
        maximum_column=2,
        maximum_row=2,
        filename="GRD00000",
        type=iso4.GridType.GridType2,
        treatment_zone_code=treatment_0.code,
    )
    grid_bin = (
        b'\x00\x00\x00\x80' + b'\x01\x00\x00\x00'
        + b'\x02\x00\x00\x00' + b'\x03\x00\x00\x00'
    )
    task = iso4.Task(
        id="TSK-01",
        status=iso4.TaskStatus.Planned,
        grids=[grid],
        treatment_zones=[treatment_0],
    )
    task_data.tasks = [task]
    return task_data, {'GRD00000': grid_bin}


def test__to_xml__when_valid_task_data__expect_valid_xml(task_with_grid):
    task_data, _ = task_with_grid
    xml = to_xml(task_data)
    xmlschema.validate(xml, RES_DIR / "xsd/ISO11783_TaskFile_V4-3.xsd")


def test__write_to_dir__when_valid__expect_files_created(task_with_grid):
    task_data, ext_refs = task_with_grid
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        write_to_dir(tmp_path, task_data, ext_refs)
        assert os.path.isfile(tmp_path / 'TASKDATA.XML')
        assert os.path.isfile(tmp_path / 'GRD00000.bin')


def test__write_to_dir__when_ext_file_contents__expect_xml_written(task_with_grid):
    task_data, ext_refs = task_with_grid
    ext_ref = iso4.ExternalFileReference('TSK00000', iso4.ExternalFileReferenceType.XML)
    ext_file = iso4.ExternalFileContents(tasks=task_data.tasks)
    task_data.tasks = []
    task_data.external_file_references = [ext_ref]
    ext_refs[ext_ref.filename] = ext_file
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        write_to_dir(tmp_path, task_data, ext_refs)
        assert os.path.isfile(tmp_path / 'GRD00000.bin')
        assert os.path.isfile(tmp_path / 'TSK00000.XML')


def test__write_to_dir__when_unknown_ref_type__expect_error(task_with_grid):
    task_data, _ = task_with_grid
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(ValueError):
            write_to_dir(Path(tmp_dir), task_data, {"BADREF": 123})


def test__write_to_zip__when_buffer_target__expect_archive_contents(task_with_grid):
    task_data, ext_refs = task_with_grid
    with BytesIO() as buf:
        write_to_zip(buf, task_data, ext_refs)
        with ZipFile(buf, 'r') as zf:
            assert 'TASKDATA/TASKDATA.XML' in zf.namelist()
            assert 'TASKDATA/GRD00000.bin' in zf.namelist()


def test__write_to_zip__when_no_folder__expect_flat_archive(task_with_grid):
    task_data, ext_refs = task_with_grid
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / 'TASKDATA.zip'
        with open(zip_path, 'wb') as fh:
            write_to_zip(fh, task_data, ext_refs, include_folder=False)
        with ZipFile(zip_path, 'r') as zf:
            assert 'TASKDATA.XML' in zf.namelist()
            assert 'GRD00000.bin' in zf.namelist()


def test__write_to_zip__when_ext_file_contents__expect_xml_in_archive(task_with_grid):
    task_data, ext_refs = task_with_grid
    ext_ref = iso4.ExternalFileReference('TSK00000', iso4.ExternalFileReferenceType.XML)
    ext_file = iso4.ExternalFileContents(tasks=task_data.tasks)
    task_data.tasks = []
    task_data.external_file_references = [ext_ref]
    ext_refs[ext_ref.filename] = ext_file
    with BytesIO() as buf:
        write_to_zip(buf, task_data, ext_refs)
        with ZipFile(buf, 'r') as zf:
            names = zf.namelist()
            assert 'TASKDATA/TASKDATA.XML' in names
            assert 'TASKDATA/GRD00000.bin' in names
            assert 'TASKDATA/TSK00000.XML' in names


def test__write_to_zip__when_unknown_ref_type__expect_error(task_with_grid):
    task_data, _ = task_with_grid
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / 'bad.zip'
        with pytest.raises(ValueError):
            write_to_zip(zip_path, task_data, {"BADREF": object()})
