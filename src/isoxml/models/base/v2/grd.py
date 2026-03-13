from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from isoxml.models.base.v2.grd_i import GrdI


@dataclass(kw_only=True)
class Grd:
    """
    Grid.

    :ivar a: GridMinimumNorthPosition
    :ivar b: GridMinimumEastPosition
    :ivar c: GridCellNorthSize
    :ivar d: GridCellEastSize
    :ivar e: GridMaximumColumn
    :ivar f: GridMaximumRow
    :ivar g: Filename
    :ivar h: Filelength
    :ivar i: GridType
    :ivar j: TreatmentZoneCode
    """

    class Meta:
        name = "GRD"

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
    c: float = field(
        metadata={
            "name": "C",
            "type": "Attribute",
            "min_inclusive": 0.0,
            "max_inclusive": 1.0,
        }
    )
    d: float = field(
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_inclusive": 0.0,
            "max_inclusive": 1.0,
        }
    )
    e: int = field(
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 4294967295,
        }
    )
    f: int = field(
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 4294967295,
        }
    )
    g: str = field(
        metadata={
            "name": "G",
            "type": "Attribute",
            "length": 8,
            "pattern": r"GRD[0-9][0-9][0-9][0-9][0-9]",
        }
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
    i: GrdI = field(
        metadata={
            "name": "I",
            "type": "Attribute",
        }
    )
    j: None | int = field(
        default=None,
        metadata={
            "name": "J",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
        },
    )
