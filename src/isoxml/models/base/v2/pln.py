from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.lsg import Lsg
from isoxml.models.base.v2.pln_a import PlnA


@dataclass(kw_only=True)
class Pln:
    """
    Polygon.

    :ivar lsg: Linestring
    :ivar a: PolygonType
    :ivar b: PolygonDesignator
    :ivar c: PolygonArea
    :ivar d: PolygonColour
    """

    class Meta:
        name = "PLN"

    lsg: list[Lsg] = field(
        default_factory=list,
        metadata={
            "name": "LSG",
            "type": "Element",
        },
    )
    a: PlnA = field(
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
            "max_inclusive": 254,
        },
    )
