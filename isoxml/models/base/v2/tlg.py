from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.tlg_c import TlgC


@dataclass(kw_only=True)
class Tlg:
    """
    TimeLog.

    :ivar a: Filename
    :ivar b: Filelength
    :ivar c: TimeLogType
    """

    class Meta:
        name = "TLG"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "length": 8,
            "pattern": r"TLG[0-9][0-9][0-9][0-9][0-9]",
        }
    )
    b: None | int = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_inclusive": 0,
            "max_inclusive": 4294967294,
        },
    )
    c: TlgC = field(
        metadata={
            "name": "C",
            "type": "Attribute",
        }
    )
