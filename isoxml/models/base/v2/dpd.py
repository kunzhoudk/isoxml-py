from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Dpd:
    """
    DeviceProcessData.

    :ivar a: DeviceProcessDataObjectId
    :ivar b: DeviceProcessDataDDI
    :ivar c: DeviceProcessDataProperty
    :ivar d: DeviceProcessDataTriggerMethods
    :ivar e: DeviceProcessDataDesignator
    :ivar f: DeviceValuePresentationObjectId
    """

    class Meta:
        name = "DPD"

    a: int = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_inclusive": 1,
            "max_inclusive": 65534,
        }
    )
    b: bytes = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "length": 2,
            "format": "base16",
        }
    )
    c: int = field(
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 3,
        }
    )
    d: int = field(
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 31,
        }
    )
    e: None | str = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    f: None | int = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_inclusive": 1,
            "max_inclusive": 65534,
        },
    )
