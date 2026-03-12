from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Crg:
    """
    ColourRange.

    :ivar a: MinimumValue
    :ivar b: MaximumValue
    :ivar c: Colour
    """

    class Meta:
        name = "CRG"

    a: int = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_inclusive": -2147483647,
            "max_inclusive": 2147483647,
        }
    )
    b: int = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_inclusive": -2147483647,
            "max_inclusive": 2147483647,
        }
    )
    c: int = field(
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
        }
    )
