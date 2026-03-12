from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.crg import Crg


@dataclass(kw_only=True)
class Cld:
    """
    ColourLegend.

    :ivar crg: ColourRange
    :ivar a: ColourLegendId
    :ivar b: DefaultColor
    """

    class Meta:
        name = "CLD"

    crg: list[Crg] = field(
        default_factory=list,
        metadata={
            "name": "CRG",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CLD|CLD-)([0-9])+",
        }
    )
    b: None | int = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
        },
    )
