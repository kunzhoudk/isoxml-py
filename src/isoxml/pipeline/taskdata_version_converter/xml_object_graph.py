"""Version-to-version XML object-graph conversion for task data."""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any

from isoxml.models.base import get_version_module
from isoxml.pipeline.taskdata_version_converter.field_mappings import get_field_mapping


def resolve_target_module(target_xml_version: int | str):
    try:
        return get_version_module(target_xml_version)
    except ValueError as exc:
        raise ValueError(
            f"Unsupported target XML version: {target_xml_version!r}"
        ) from exc


def convert_tree(value: Any, target_iso) -> Any:
    classes, enums = _module_indexes(target_iso)
    return _convert_value(value, target_iso, classes, enums)


def convert_reference(ref_data: Any, target_iso) -> Any:
    if isinstance(ref_data, bytes):
        return ref_data
    if dataclasses.is_dataclass(ref_data) and not isinstance(ref_data, type):
        return convert_tree(ref_data, target_iso)
    return ref_data


def _module_indexes(target_iso) -> tuple[dict[str, type], dict[str, type[Enum]]]:
    classes = {
        name: obj
        for name, obj in vars(target_iso).items()
        if isinstance(obj, type) and dataclasses.is_dataclass(obj)
    }
    enums = {
        name: obj
        for name, obj in vars(target_iso).items()
        if isinstance(obj, type) and issubclass(obj, Enum) and obj is not Enum
    }
    return classes, enums


def _convert_value(
    value: Any,
    target_iso,
    classes: dict[str, type],
    enums: dict[str, type[Enum]],
) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        converted_items = [
            _convert_value(item, target_iso, classes, enums) for item in value
        ]
        return [item for item in converted_items if item is not None]
    if isinstance(value, Enum):
        return _convert_enum(value, target_iso, enums)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _convert_dataclass(value, target_iso, classes, enums)
    return value


def _convert_enum(
    value: Enum,
    target_iso,
    enums: dict[str, type[Enum]],
) -> Enum | None:
    target_enum = enums.get(type(value).__name__)
    if target_enum is None:
        if type(value).__module__.startswith(target_iso.__name__):
            return value
        return None
    try:
        return target_enum(value.value)
    except ValueError:
        return None


def _convert_dataclass(
    source_obj: Any,
    target_iso,
    classes: dict[str, type],
    enums: dict[str, type[Enum]],
) -> Any:
    cls_name = type(source_obj).__name__
    target_cls = classes.get(cls_name)
    if target_cls is None:
        if type(source_obj).__module__.startswith(target_iso.__name__):
            target_cls = type(source_obj)
        else:
            return None

    source_fields = {field.name for field in dataclasses.fields(source_obj)}
    kwargs: dict[str, Any] = {}

    for target_field in dataclasses.fields(target_cls):
        if not target_field.init:
            continue

        mapping = get_field_mapping(cls_name, target_field.name, target_iso)
        source_field_name = target_field.name
        apply_transform = False
        if mapping is not None:
            mapped_source_name = mapping.source_field_for_target(target_iso)
            if mapped_source_name in source_fields:
                source_field_name = mapped_source_name
                apply_transform = True

        if source_field_name not in source_fields:
            continue

        converted = _convert_value(
            getattr(source_obj, source_field_name),
            target_iso,
            classes,
            enums,
        )

        if apply_transform and mapping is not None:
            converted = mapping.transform_for_target(converted, target_iso)

        kwargs[target_field.name] = converted

    return target_cls(**kwargs)
