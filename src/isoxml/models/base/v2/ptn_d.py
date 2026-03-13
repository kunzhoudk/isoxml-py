from __future__ import annotations

from enum import Enum


class PtnD(Enum):
    """
    :cvar VALUE_0: no GPS fix
    :cvar VALUE_1: GNSS fix
    :cvar VALUE_2: DGNSS fix
    :cvar VALUE_3: Precise GNSS
    :cvar VALUE_4: RTK fixed integer
    :cvar VALUE_5: RTK float
    :cvar VALUE_6: Est (DR) mode
    :cvar VALUE_7: Manual input
    :cvar VALUE_8: Simulate mode
    :cvar VALUE_9: Reserved
    :cvar VALUE_10: Reserved
    :cvar VALUE_11: Reserved
    :cvar VALUE_12: Reserved
    :cvar VALUE_13: Reserved
    :cvar VALUE_14: Error
    :cvar VALUE_15: PositionStatus value is not available
    """

    VALUE_0 = "0"
    VALUE_1 = "1"
    VALUE_2 = "2"
    VALUE_3 = "3"
    VALUE_4 = "4"
    VALUE_5 = "5"
    VALUE_6 = "6"
    VALUE_7 = "7"
    VALUE_8 = "8"
    VALUE_9 = "9"
    VALUE_10 = "10"
    VALUE_11 = "11"
    VALUE_12 = "12"
    VALUE_13 = "13"
    VALUE_14 = "14"
    VALUE_15 = "15"
