from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(kw_only=True)
class Ccl:
    """
    CodedCommentListValue.

    :ivar a: CodedCommentListValueId
    :ivar b: CodedCommentListValueDesignator
    """

    class Meta:
        name = "CCL"

    a: str = field(
        metadata={
            "name": "A",
            "type": "Attribute",
            "min_length": 4,
            "max_length": 14,
            "pattern": r"(CCL|CCL-)([0-9])+",
        }
    )
    b: str = field(
        metadata={
            "name": "B",
            "type": "Attribute",
            "max_length": 32,
        }
    )
