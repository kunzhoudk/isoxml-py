from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.lsg_a import LsgA
from isoxml.models.base.v2.pnt import Pnt


@dataclass(kw_only=True)
class Lsg:
    """
    Linestring.

    :ivar pnt: Point
    :ivar a: LinestringType
    :ivar b: LinestringDesignator
    :ivar c: LinestringWidth
    :ivar d: LinestringLength
    :ivar e: LinestringColour
    """

    class Meta:
        name = "LSG"

    pnt: list[Pnt] = field(
        default_factory=list,
        metadata={
            "name": "PNT",
            "type": "Element",
        },
    )
    a: LsgA = field(
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
    c: None | int = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 4294967294,
        },
    )
    d: None | int = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 4294967294,
        },
    )
    e: None | int = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
        },
    )
