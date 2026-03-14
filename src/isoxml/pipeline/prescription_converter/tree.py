"""Version-to-version object tree conversion for prescription task data."""

from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4

_FIELD_RENAMES_TO_V4: dict[str, dict[str, str]] = {
    "Customer": {"designator": "last_name"},
    "Worker": {"designator": "last_name"},
    "Device": {"working_set_master_name": "client_name"},
    "DeviceAllocation": {
        "working_set_master_name_value": "client_name_value",
        "working_set_master_name_mask": "client_name_mask",
    },
    "ProductAllocation": {
        "amount_ddi": "quantity_ddi",
        "amount_value": "quantity_value",
    },
}

_FIELD_RENAMES_TO_V3: dict[str, dict[str, str]] = {
    "Customer": {"last_name": "designator"},
    "Worker": {"last_name": "designator"},
    "Device": {"client_name": "working_set_master_name"},
    "DeviceAllocation": {
        "client_name_value": "working_set_master_name_value",
        "client_name_mask": "working_set_master_name_mask",
    },
    "ProductAllocation": {
        "quantity_ddi": "amount_ddi",
        "quantity_value": "amount_value",
    },
}


def resolve_target_module(target_xml_version: int | str):
    version = str(target_xml_version)
    if version == "3":
        return iso3
    if version == "4":
        return iso4
    raise ValueError(f"Unsupported target XML version: {target_xml_version!r}")


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
            _convert_value(item, target_iso, classes, enums)
            for item in value
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

        source_field_name = _source_field_name(cls_name, target_field.name, target_iso)
        if source_field_name not in source_fields:
            continue

        converted = _convert_value(
            getattr(source_obj, source_field_name),
            target_iso,
            classes,
            enums,
        )

        if cls_name == "Point" and target_field.name == "colour":
            if target_iso is iso4 and isinstance(converted, int):
                converted = str(converted)
            elif target_iso is iso3 and isinstance(converted, str):
                try:
                    converted = int(converted)
                except (TypeError, ValueError):
                    converted = None

        kwargs[target_field.name] = converted

    _patch_special_field_mappings(source_obj, kwargs, target_iso, classes, enums)
    return target_cls(**kwargs)


def _source_field_name(cls_name: str, target_field_name: str, target_iso) -> str:
    rename_map = _FIELD_RENAMES_TO_V4 if target_iso is iso4 else _FIELD_RENAMES_TO_V3
    reverse_map = {
        target_name: source_name
        for source_name, target_name in rename_map.get(cls_name, {}).items()
    }
    return reverse_map.get(target_field_name, target_field_name)


def _patch_special_field_mappings(
    source_obj: Any,
    kwargs: dict[str, Any],
    target_iso,
    classes: dict[str, type],
    enums: dict[str, type[Enum]],
) -> None:
    cls_name = type(source_obj).__name__

    if cls_name == "AllocationStamp":
        if target_iso is iso4 and getattr(source_obj, "position", None) is not None:
            kwargs["positions"] = [
                _convert_value(source_obj.position, target_iso, classes, enums)
            ]
        elif target_iso is iso3 and getattr(source_obj, "positions", None):
            kwargs["position"] = _convert_value(
                source_obj.positions[0],
                target_iso,
                classes,
                enums,
            )
