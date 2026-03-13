"""Public helpers for reading and writing ISOXML task data."""

from __future__ import annotations

import os.path
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Literal
from zipfile import ZipFile

from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.io.external_files import merge_external_file_contents

_PARSER = XmlParser(
    ParserConfig(
        fail_on_unknown_properties=False,
        fail_on_unknown_attributes=False,
    )
)
_SERIALIZER = XmlSerializer(
    config=SerializerConfig(
        xml_version="1.0",
        encoding="UTF-8",
        indent="    ",
    )
)


def _select_base_module(xml_content: str) -> ModuleType:
    """Select the ISOXML model module (`v3` or `v4`) from the XML header."""

    xml_head = xml_content[:1024]
    if 'VersionMajor="4"' in xml_head:
        return iso4
    if 'VersionMajor="3"' in xml_head:
        return iso3
    raise ValueError("the provided xml file is neither version 3 or 4")


def load_taskdata_from_path(
    task_data_path: Path,
    external_files: Literal["merge", "ignore", "separate"] = "merge",
    read_bin_files: bool = True,
) -> tuple[
    iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    dict[str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents],
]:
    """Load `TASKDATA.XML` plus optional external references from a directory."""

    if task_data_path.is_file():
        task_data_path = task_data_path.parent

    with open(task_data_path / "TASKDATA.XML", "r", encoding="utf-8") as file:
        xml_content = file.read()

    iso_module = _select_base_module(xml_content)
    task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData = _PARSER.from_string(
        xml_content,
        iso_module.Iso11783TaskData,
    )

    refs: dict[
        str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents
    ] = {}
    file_names = os.listdir(task_data_path)

    if external_files in ("merge", "separate"):
        for ext_ref in task_data.external_file_references:
            assert ext_ref.filetype == iso_module.ExternalFileReferenceType.XML
            matching_files = [
                file_name
                for file_name in file_names
                if file_name.startswith(ext_ref.filename)
            ]
            assert len(matching_files) == 1
            full_ref_filename = matching_files[0]
            refs[ext_ref.filename] = _PARSER.from_path(
                task_data_path / full_ref_filename,
                iso_module.ExternalFileContents,
            )

    if external_files == "merge":
        task_data, refs = merge_external_file_contents(task_data, refs, inplace=True)

    if read_bin_files:
        for file_name in file_names:
            if file_name.lower().endswith(".bin") and file_name.startswith(
                ("GRD", "TLG", "PNT")
            ):
                iso_id_ref = file_name.rsplit(".")[0]
                with open(task_data_path / file_name, "rb") as bin_file:
                    refs[iso_id_ref] = bin_file.read()

    return task_data, refs


def load_taskdata_from_zip(
    zip_path: Path,
    external_files: Literal["merge", "ignore", "separate"] = "merge",
    read_bin_files: bool = True,
) -> tuple[
    iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    dict[str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents],
]:
    """Load ISOXML task data from a zip archive by extracting it to a temp folder."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with ZipFile(zip_path, "r") as zip_archive:
            zip_archive.extractall(tmp_path)
        return load_taskdata_from_path(tmp_path, external_files, read_bin_files)


def load_taskdata_from_text(
    xml_content: str,
) -> iso3.Iso11783TaskData | iso4.Iso11783TaskData:
    """Parse task data XML text into the matching v3/v4 dataclass model."""

    iso_module = _select_base_module(xml_content)
    return _PARSER.from_string(xml_content, iso_module.Iso11783TaskData)


def dump_taskdata_to_text(
    task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData,
) -> str:
    """Serialize task data dataclass objects to XML text."""

    return _SERIALIZER.render(task_data)


def write_taskdata_to_dir(
    dir_path: Path,
    task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    ext_refs: dict[str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents]
    | None = None,
) -> None:
    """Write `TASKDATA.XML` and optional external references into a directory."""

    refs = {} if ext_refs is None else ext_refs
    xml_path = dir_path / "TASKDATA.XML"
    with open(xml_path, "w", encoding="utf-8") as xml_file:
        _SERIALIZER.write(xml_file, task_data)

    for ref_name, ref_data in refs.items():
        if isinstance(ref_data, bytes):
            bin_path = dir_path / f"{ref_name}.bin"
            with open(bin_path, "wb") as bin_file:
                bin_file.write(ref_data)
        elif isinstance(ref_data, (iso3.ExternalFileContents, iso4.ExternalFileContents)):
            ext_path = dir_path / f"{ref_name}.XML"
            with open(ext_path, "w", encoding="utf-8") as xml_file:
                _SERIALIZER.write(xml_file, ref_data)
        else:
            raise ValueError(f"unknown type {type(ref_data)} of external ref {ref_name}")


def write_taskdata_to_zip(
    target,
    task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    ext_refs: dict[str, bytes | iso3.ExternalFileContents | iso4.ExternalFileContents]
    | None = None,
    include_folder: bool = True,
) -> None:
    """Write task data and references into a zip archive."""

    refs = {} if ext_refs is None else ext_refs
    path_in_archive = "TASKDATA/" if include_folder else ""
    with ZipFile(target, "w") as zip_archive:
        with zip_archive.open(path_in_archive + "TASKDATA.XML", "w") as xml_file:
            xml_content = dump_taskdata_to_text(task_data)
            xml_file.write(xml_content.encode("utf-8"))

        for ref_name, ref_data in refs.items():
            if isinstance(ref_data, bytes):
                with zip_archive.open(path_in_archive + f"{ref_name}.bin", "w") as bin_file:
                    bin_file.write(ref_data)
            elif isinstance(ref_data, (iso3.ExternalFileContents, iso4.ExternalFileContents)):
                with zip_archive.open(path_in_archive + f"{ref_name}.XML", "w") as xml_file:
                    xml_content = _SERIALIZER.render(ref_data)
                    xml_file.write(xml_content.encode("utf-8"))
            else:
                raise ValueError(f"unknown type {type(ref_data)} of external ref {ref_name}")

__all__ = [
    "dump_taskdata_to_text",
    "load_taskdata_from_path",
    "load_taskdata_from_text",
    "load_taskdata_from_zip",
    "write_taskdata_to_dir",
    "write_taskdata_to_zip",
]
