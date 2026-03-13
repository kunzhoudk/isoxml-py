from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from isoxml.models.base.v2.asp_d import AspD
from isoxml.models.base.v2.ptn import Ptn


@dataclass(kw_only=True)
class Asp:
    """
    AllocationStamp.

    :ivar ptn: Position
    :ivar a: Start
    :ivar b: Stop
    :ivar c: Duration
    :ivar d: Type
    """

    class Meta:
        name = "ASP"

    ptn: None | Ptn = field(
        default=None,
        metadata={
            "name": "PTN",
            "type": "Element",
        },
    )
    a: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "A",
            "type": "Attribute",
        },
    )
    b: None | XmlDateTime = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
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
    d: AspD = field(
        metadata={
            "name": "D",
            "type": "Attribute",
        }
    )
