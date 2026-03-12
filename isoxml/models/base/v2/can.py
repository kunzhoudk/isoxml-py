from __future__ import annotations

from dataclasses import dataclass, field

from isoxml.models.base.v2.asp import Asp


@dataclass(kw_only=True)
class Can:
    """
    CommentAllocation.

    :ivar asp: AllocationStamp
    :ivar a: CodedCommentIdRef
    :ivar b: CodedCommentListValueIdRef
    :ivar c: FreeCommentText
    """

    class Meta:
        name = "CAN"

    asp: None | Asp = field(
        default=None,
        metadata={
            "name": "ASP",
            "type": "Element",
        },
    )
    a: None | str = field(
        default=None,
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CCT|CCT-)([0-9])+",
        },
    )
    b: None | str = field(
        default=None,
        metadata={
            "name": "B",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CCL|CCL-)([0-9])+",
        },
    )
    c: None | str = field(
        default=None,
        metadata={
            "name": "C",
            "type": "Attribute",
            "max_length": 32,
        },
    )
