from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from isoxml.io import read_from_path
from isoxml.xsd_validation import validate_xsd

FIXTURE_DIR = Path(__file__).resolve().parent / "resources" / "isoxml" / "prescription_converter"


def test_validate_xsd_infers_version_from_task_data():
    with TemporaryDirectory() as tmp_dir:
        with ZipFile(FIXTURE_DIR / "small_xml_v4_type_2_auto.zip") as zf:
            zf.extractall(tmp_dir)
        task_data, _ = read_from_path(Path(tmp_dir) / "TASKDATA")

    xsd_path = validate_xsd(task_data)
    assert xsd_path.name == "ISO11783_TaskFile_V4-3.xsd"


def test_validate_xsd_accepts_explicit_version():
    with TemporaryDirectory() as tmp_dir:
        with ZipFile(FIXTURE_DIR / "small_xml_v3_type_1_auto.zip") as zf:
            zf.extractall(tmp_dir)
        task_data, _ = read_from_path(Path(tmp_dir) / "TASKDATA")

    xsd_path = validate_xsd(task_data, xml_version=3)
    assert xsd_path.name == "ISO11783_TaskFile_V3-3.xsd"
