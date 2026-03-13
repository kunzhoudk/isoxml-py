from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from isoxml.models.base.v2.pnt_a import PntA


@dataclass(kw_only=True)
class Pnt:
    """
    Point.

    :ivar a: PointType
    :ivar b: PointDesignator
    :ivar c: PointNorth
    :ivar d: PointEast
    :ivar e: PointUp
    :ivar f: PointColour
    """

    class Meta:
        name = "PNT"

    a: PntA = field(
        metadata={
            "name": "A",
            "type": "Attribute",
        }
    )
    b: None | str = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        },
    )
    c: Decimal = field(
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": Decimal("-90.0"),
            "max_inclusive": Decimal("90.0"),
        }
    )
    d: Decimal = field(
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_inclusive": Decimal("-180.0"),
            "max_inclusive": Decimal("180.0"),
        }
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
            "min_inclusive": 0,
            "max_inclusive": 254,
        },
    )
