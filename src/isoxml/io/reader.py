"""Functions for reading ISOXML TaskData from disk, zip archives, and XML text."""

import os.path
import tempfile
from pathlib import Path
from typing import Literal
from zipfile import ZipFile

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.io.external import merge_ext_content
from isoxml.models.version_registry import detect_from_xml

_parser = XmlParser(
    ParserConfig(
        fail_on_unknown_properties=False,
        fail_on_unknown_attributes=False,
    )
)


def _resolve_taskdata_dir(task_data_path: Path) -> Path:
    """Resolve a directory containing ``TASKDATA.XML``.

    Supports either:
    - a direct ISOXML folder containing ``TASKDATA.XML``
    - a path to ``TASKDATA.XML`` itself
    - a parent folder containing exactly one nested ``TASKDATA/TASKDATA.XML``
    """
    if task_data_path.is_file():
        task_data_path = task_data_path.parent

    if (task_data_path / "TASKDATA.XML").exists():
        return task_data_path

    matches = sorted(task_data_path.rglob("TASKDATA.XML"))
    if len(matches) == 1:
        return matches[0].parent
    if not matches:
        raise FileNotFoundError(f"TASKDATA.XML not found under '{task_data_path}'.")
    raise ValueError(
        f"Expected exactly one TASKDATA.XML under '{task_data_path}', found {len(matches)}."
    )


def _select_version_module(xml_content: str):
    """Return the model module registered for the XML VersionMajor attribute."""
    return detect_from_xml(xml_content[:1024])


def read_from_path(
    task_data_path: Path,
    external_files: Literal["merge", "ignore", "separate"] = "merge",
    read_bin_files: bool = True,
) -> tuple[
    iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    dict[str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents],
]:
    """Load TASKDATA.XML and optional references from a directory.

    Args:
        task_data_path: Path to a folder containing ``TASKDATA.XML``, or the
            XML file itself (its parent directory is used in that case).
        external_files:
            - ``merge``    – parse external XML files and merge them into the tree.
            - ``separate`` – parse external XML files and return them separately.
            - ``ignore``   – skip external XML files entirely.
        read_bin_files: When ``True``, load ``GRD*``, ``TLG*``, and ``PNT*``
            binary files keyed by their ISOXML object ID (stem without extension).

    Returns:
        ``(task_data, references)`` where *references* maps object IDs to their
        binary payloads (``bytes``) or parsed ``ExternalFileContents`` objects.
    """
    task_data_path = _resolve_taskdata_dir(task_data_path)

    with open(task_data_path / "TASKDATA.XML", "r", encoding="utf-8") as fh:
        xml_content = fh.read()

    iso = _select_version_module(xml_content)
    task_data = _parser.from_string(xml_content, iso.Iso11783TaskData)

    ext_objects: dict = {}
    dir_entries = os.listdir(task_data_path)

    if external_files in ("merge", "separate"):
        for ext_ref in task_data.external_file_references:
            if ext_ref.filetype != iso.ExternalFileReferenceType.XML:
                raise ValueError(
                    f"ExternalFileReference '{ext_ref.filename}' has unsupported "
                    f"filetype {ext_ref.filetype!r}; only XML is supported."
                )
            matches = [f for f in dir_entries if f.startswith(ext_ref.filename)]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected exactly one file for external reference "
                    f"'{ext_ref.filename}', found {matches!r}."
                )
            ext_objects[ext_ref.filename] = _parser.from_path(
                task_data_path / matches[0],
                iso.ExternalFileContents,
            )

    if external_files == "merge":
        merge_ext_content(task_data, ext_objects, inplace=True)

    bin_refs: dict = {}
    if read_bin_files:
        for filename in dir_entries:
            if filename.lower().endswith(".bin") and filename.startswith(
                ("GRD", "TLG", "PNT")
            ):
                obj_id = filename.rsplit(".", 1)[0]
                with open(task_data_path / filename, "rb") as fh:
                    bin_refs[obj_id] = fh.read()

    return task_data, bin_refs | ext_objects


def read_from_zip(
    zip_path: Path,
    external_files: Literal["merge", "ignore", "separate"] = "merge",
    read_bin_files: bool = True,
) -> tuple[
    iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    dict[str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents],
]:
    """Load ISOXML task data from a ZIP archive by extracting to a temp folder."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_path)
        return read_from_path(tmp_path, external_files, read_bin_files)


def read_from_xml(xml_content: str) -> iso3.Iso11783TaskData | iso4.Iso11783TaskData:
    """Parse an XML string into the matching v3/v4 ``Iso11783TaskData`` dataclass."""
    iso = _select_version_module(xml_content)
    return _parser.from_string(xml_content, iso.Iso11783TaskData)
