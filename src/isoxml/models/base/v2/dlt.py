from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Dlt:
    """
    DataLogTrigger.

    :ivar a: DataLogDDI
    :ivar b: DataLogMethod
    :ivar c: DataLogDistanceInterval
    :ivar d: DataLogTimeInterval
    :ivar e: DataLogThresholdMinimum
    :ivar f: DataLogThresholdMaximum
    :ivar g: DataLogThresholdChange
    :ivar h: DeviceElementIdRef
    :ivar i: ValuePresentationIdRef
    :ivar j: DataLogPGN
    :ivar k: DataLogPGNStartBit
    :ivar l: DataLogPGNStopBit
    """

    class Meta:
        name = "DLT"

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
            "min_inclusive": 1,
            "max_inclusive": 31,
        }
    )
    c: None | int = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 1000000,
        },
    )
    d: None | int = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 60000,
        },
    )
    e: None | int = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_inclusive": -2147483647,
            "max_inclusive": 2147483647,
        },
    )
    f: None | int = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_inclusive": -2147483647,
            "max_inclusive": 2147483647,
        },
    )
    g: None | int = field(
        default=None,
        metadata={
            "name": "G",
            "type": "Attribute",
            "min_inclusive": -2147483647,
            "max_inclusive": 2147483647,
        },
    )
    h: None | str = field(
        default=None,
        metadata={
            "name": "H",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(DET|DET-)([0-9])+",
        },
    )
    i: None | str = field(
        default=None,
        metadata={
            "name": "I",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(VPN|VPN-)([0-9])+",
        },
    )
    j: None | int = field(
        default=None,
        metadata={
            "name": "J",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 262143,
        },
    )
    k: None | int = field(
        default=None,
        metadata={
            "name": "K",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 63,
        },
    )
    l: None | int = field(
        default=None,
        metadata={
            "name": "L",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 63,
        },
    )
