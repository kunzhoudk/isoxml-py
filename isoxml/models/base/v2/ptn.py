from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from isoxml.models.base.v2.ptn_d import PtnD


@dataclass(kw_only=True)
class Ptn:
    """
    Position.

    :ivar a: PositionNorth
    :ivar b: PositionEast
    :ivar c: PositionUp
    :ivar d: PositionStatus
    :ivar e: PDOP
    :ivar f: HDOP
    :ivar g: NumberOfSatellites
    :ivar h: GpsUtcTime
    :ivar i: GpsUtcDate
    """

    class Meta:
        name = "PTN"

    a: Decimal = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_inclusive": Decimal("-90.0"),
            "max_inclusive": Decimal("90.0"),
        }
    )
    b: Decimal = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_inclusive": Decimal("-180.0"),
            "max_inclusive": Decimal("180.0"),
        }
    )
    c: None | int = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": -2147483648,
            "max_inclusive": 2147483647,
        },
    )
    d: PtnD = field(
        metadata={
            "name": "D",
            "type": "Attribute",
        }
    )
    e: None | Decimal = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_inclusive": Decimal("0.0"),
            "max_inclusive": Decimal("99.9"),
        },
    )
    f: None | Decimal = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_inclusive": Decimal("0.0"),
            "max_inclusive": Decimal("99.9"),
        },
    )
    g: None | int = field(
        default=None,
        metadata={
            "name": "G",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
        },
    )
    h: None | int = field(
        default=None,
        metadata={
            "name": "H",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 4294967294,
        },
    )
    i: None | int = field(
        default=None,
        metadata={
            "name": "I",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 65534,
        },
    )
