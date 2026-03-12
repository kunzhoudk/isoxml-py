from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Dlv:
    """
    DataLogValue.

    :ivar a: ProcessDataDDI
    :ivar b: ProcessDataValue
    :ivar c: DeviceElementIdRef
    :ivar d: DataLogPGN
    :ivar e: DataLogPGNStartBit
    :ivar f: DataLogPGNStopBit
    """

    class Meta:
        name = "DLV"

    a: bytes = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "length": 2,
            "format": "base16",
        }
    )
    b: int = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_inclusive": -2147483648,
            "max_inclusive": 2147483647,
        }
    )
    c: str = field(
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DET|DET-)([0-9])+",
        }
    )
    d: None | int = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 262143,
        },
    )
    e: None | int = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 63,
        },
    )
    f: None | int = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 63,
        },
    )
