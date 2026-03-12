from __future__ import annotations

from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

from isoxml.models.base.v2.dlv import Dlv
from isoxml.models.base.v2.ptn import Ptn
from isoxml.models.base.v2.tim_d import TimD


@dataclass(kw_only=True)
class Tim:
    """
    Time.

    :ivar dlv: DataLogValue
    :ivar ptn: Position
    :ivar a: Start
    :ivar b: Stop
    :ivar c: Duration
    :ivar d: Type
    """

    class Meta:
        name = "TIM"

    dlv: list[Dlv] = field(
        default_factory=list,
        metadata={
            "name": "DLV",
            "type": "Element",
        },
    )
    ptn: list[Ptn] = field(
        default_factory=list,
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
    d: TimD = field(
        metadata={
            "name": "D",
            "type": "Attribute",
        }
    )
