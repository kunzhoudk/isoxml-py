from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.pdv import Pdv
from isoxml.models.base.v2.pln import Pln


@dataclass(kw_only=True)
class Tzn:
    """
    TreatmentZone.

    :ivar pdv: ProcessDataVariable
    :ivar pln: Polygon, TreatmentZone only
    :ivar a: TreatmentZoneCode
    :ivar b: TreatmentZoneDesignator
    :ivar c: TreatmentZoneColour
    """

    class Meta:
        name = "TZN"

    pdv: list[Pdv] = field(
        default_factory=list,
        metadata={
            "name": "PDV",
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
    a: int = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 254,
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
            "max_inclusive": 254,
        },
    )
