from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(kw_only=True)
class Dvp:
    """
    DeviceValuePresentation.

    :ivar a: DeviceValuePresentationObjectId
    :ivar b: Offset
    :ivar c: Scale
    :ivar d: NumberOfDecimals
    :ivar e: UnitDesignator
    """

    class Meta:
        name = "DVP"

    a: int = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_inclusive": 1,
            "max_inclusive": 65534,
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
