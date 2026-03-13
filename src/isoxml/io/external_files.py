"""Helpers for dealing with ISOXML external file content references."""

from copy import deepcopy
from dataclasses import fields

from isoxml.models.base import v3 as iso3
from isoxml.models.base import v4 as iso4


def merge_external_file_contents(
    task_data: iso3.Iso11783TaskData | iso4.Iso11783TaskData,
    external_content: dict[str, iso3.ExternalFileContents | iso4.ExternalFileContents],
    inplace: bool = False,
) -> tuple[iso3.Iso11783TaskData | iso4.Iso11783TaskData, dict[str, object]]:
    """Merge parsed external XML fragments back into the main task data object."""

    merged_task_data = task_data
    remaining_content = external_content
    if not inplace:
        merged_task_data = deepcopy(task_data)
        remaining_content = external_content.copy()

    iso_element_lookup: dict[str, str] = {}
    for field_meta in fields(merged_task_data):
        if "name" in field_meta.metadata:
            iso_element_lookup[field_meta.metadata["name"]] = field_meta.name

    for ext_ref in merged_task_data.external_file_references:
        ref_obj = remaining_content.pop(ext_ref.filename)
        for value in ref_obj.__dict__.values():
            if isinstance(value, list) and value:
                task_data_attr = iso_element_lookup[value[0].Meta.name]
                if hasattr(merged_task_data, task_data_attr):
                    getattr(merged_task_data, task_data_attr).extend(value)

    merged_task_data.external_file_references = []
    return merged_task_data, remaining_content


__all__ = ["merge_external_file_contents"]
