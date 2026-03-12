from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.ccl import Ccl
from isoxml.models.base.v2.cct_c import CctC


@dataclass(kw_only=True)
class Cct:
    """
    CodedComment.

    :ivar ccl: CodedCommentListValue
    :ivar a: CodedCommentId
    :ivar b: CodedCommentDesignator
    :ivar c: CodedCommentScope
    :ivar d: CodedCommentGroupIdRef
    """

    class Meta:
        name = "CCT"

    ccl: list[Ccl] = field(
        default_factory=list,
        metadata={
            "name": "CCL",
            "type": "Element",
        },
    )
    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CCT|CCT-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        }
    )
    c: CctC = field(
        metadata={
            "name": "C",
            "type": "Attribute",
        }
    )
    d: None | str = field(
        default=None,
        metadata={
            "name": "D",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CCG|CCG-)([0-9])+",
        },
    )
