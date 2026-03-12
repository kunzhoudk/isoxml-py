from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(kw_only=True)
class Vpn:
    """
    ValuePresentation.

    :ivar a: ValuePresentationId
    :ivar b: Offset
    :ivar c: Scale
    :ivar d: NumberOfDecimals
    :ivar e: UnitDesignator
    :ivar f: ColourLegendIdRef
    """

    class Meta:
        name = "VPN"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(VPN|VPN-)([0-9])+",
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
    c: Decimal = field(
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": Decimal("1E-9"),
            "max_inclusive": Decimal("100000000.0"),
        }
    )
    d: int = field(
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 7,
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
    f: None | str = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CLD|CLD-)([0-9])+",
        },
    )
