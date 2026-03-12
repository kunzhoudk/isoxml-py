from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.lsg import Lsg
from isoxml.models.base.v2.pln import Pln
from isoxml.models.base.v2.pnt import Pnt


@dataclass(kw_only=True)
class Pfd:
    """
    Partfield.

    :ivar lsg: Linestring
    :ivar pln: Polygon, non Treatment Zone only
    :ivar pnt: Point
    :ivar a: PartfieldId
    :ivar b: PartfieldCode
    :ivar c: PartfieldDesignator
    :ivar d: PartfieldArea
    :ivar e: CustomerIdRef
    :ivar f: FarmIdRef
    :ivar g: CropTypeIdRef
    :ivar h: CropVarietyIdRef
    :ivar i: FieldIdRef
    """

    class Meta:
        name = "PFD"

    lsg: list[Lsg] = field(
        default_factory=list,
        metadata={
            "name": "LSG",
            "type": "Element",
        },
    )
    pln: list[Pln] = field(
        default_factory=list,
        metadata={
            "name": "PLN",
            "type": "Element",
        },
    )
    pnt: list[Pnt] = field(
        default_factory=list,
        metadata={
            "name": "PNT",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(PFD|PFD-)([0-9])+",
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
    c: str = field(
        metadata={
            "name": "C",
            "type": "Attribute",
            "max_length": 32,
        }
    )
    d: int = field(
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 4294967294,
        }
    )
    e: None | str = field(
        default=None,
        metadata={
            "name": "E",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CTR|CTR-)([0-9])+",
        },
    )
    f: None | str = field(
        default=None,
        metadata={
            "name": "F",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(FRM|FRM-)([0-9])+",
        },
    )
    g: None | str = field(
        default=None,
        metadata={
            "name": "G",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CTP|CTP-)([0-9])+",
        },
    )
    h: None | str = field(
        default=None,
        metadata={
            "name": "H",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CVT|CVT-)([0-9])+",
        },
    )
    i: None | str = field(
        default=None,
        metadata={
            "name": "I",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(PFD|PFD-)([0-9])+",
        },
    )
