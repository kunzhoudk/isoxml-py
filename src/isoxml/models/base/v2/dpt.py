from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Dpt:
    """
    DeviceProperty.

    :ivar a: DevicePropertyObjectId
    :ivar b: DevicePropertyDDI
    :ivar c: DevicePropertyValue
    :ivar d: DevicePropertyDesignator
    :ivar e: DeviceValuePresentationObjectId
    """

    class Meta:
        name = "DPT"

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
            "min_inclusive": -2147483648,
            "max_inclusive": 2147483647,
        }
    )
    d: None | str = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    e: None | int = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_inclusive": 1,
            "max_inclusive": 65534,
        },
    )
