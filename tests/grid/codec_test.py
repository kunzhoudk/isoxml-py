from decimal import Decimal

import numpy as np
import pytest

from isoxml.grid.codec import decode, encode_type1, encode_type2
from isoxml.models.base.v3 import Grid, GridType
from isoxml.models.ddi import DDEntity


def test__encode_type1__when_wrong_dtype__expect_error():
    arr = np.array([[-1, 2], [3, 4]], dtype=np.int8)
    grid = Grid(maximum_column=2, maximum_row=2, type=GridType.GridType1)
    with pytest.raises(ValueError):
        encode_type1(arr, grid)


def test__encode_type1__when_wrong_shape__expect_error():
    arr = np.array([1, 2, 3], dtype=np.uint8)
    grid = Grid(maximum_column=3, maximum_row=1, type=GridType.GridType1)
    with pytest.raises(ValueError):
        encode_type1(arr, grid)


def test__encode_type1__when_valid__expect_correct_bytes():
    arr = np.array([[1, 2], [254, 255]], dtype=np.uint8)
    grid = Grid(maximum_column=2, maximum_row=2, type=GridType.GridType1)
    assert encode_type1(arr, grid) == b"\x01\x02\xfe\xff"


def test__decode__when_grid_type_1__expect_correct_array():
    grid_bin = b"\x01\x02\xfe\xff\x03\x04"
    grid = Grid(
        minimum_north_position=Decimal("48.143304983"),
        minimum_east_position=Decimal("15.141245418"),
        cell_north_size=0.0001,
        cell_east_size=0.0001,
        maximum_column=2,
        maximum_row=3,
        filename="GRD00000",
        type=GridType.GridType1,
    )
    expected = np.array([[1, 2], [254, 255], [3, 4]], dtype=np.uint8)
    assert np.array_equal(decode(grid_bin, grid), expected)


def test__encode_type2__when_int32_values__expect_correct_bytes():
    arr = np.array(
        [
            [-2147483648, 1],
            [2, 3],
            [4, 2147483647],
        ],
        dtype=np.int32,
    )
    grid = Grid(maximum_column=2, maximum_row=3, type=GridType.GridType2)
    expected = (
        b"\x00\x00\x00\x80"
        + b"\x01\x00\x00\x00"
        + b"\x02\x00\x00\x00"
        + b"\x03\x00\x00\x00"
        + b"\x04\x00\x00\x00"
        + b"\xff\xff\xff\x7f"
    )
    assert encode_type2(arr, grid) == expected


def test__encode_type2__when_multi_pdv__expect_correct_bytes():
    arr = np.array(
        [
            [[0, 0], [1, -1]],
            [[2, -2], [3, -3]],
        ],
        dtype=np.int16,
    )
    grid = Grid(maximum_column=2, maximum_row=2, type=GridType.GridType2)
    ddi6 = DDEntity.from_id(6)
    expected = (
        b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x01\x00\x00\x00"
        + b"\xff\xff\xff\xff"
        + b"\x02\x00\x00\x00"
        + b"\xfe\xff\xff\xff"
        + b"\x03\x00\x00\x00"
        + b"\xfd\xff\xff\xff"
    )
    assert encode_type2(arr, grid, ddi_list=[ddi6, ddi6], scale=False) == expected


def test__encode_type2__when_ddi_scaling__expect_correct_bytes():
    arr = np.array(
        [
            [[0.0, 0.0], [1.0, -0.01]],
            [[2.0, -0.02], [3.0, -0.03]],
        ]
    )
    grid = Grid(maximum_column=2, maximum_row=2, type=GridType.GridType2)
    ddi1 = DDEntity.from_id(1)  # scale 0.01
    ddi6 = DDEntity.from_id(6)  # scale 1
    expected = (
        b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x01\x00\x00\x00"
        + b"\xff\xff\xff\xff"
        + b"\x02\x00\x00\x00"
        + b"\xfe\xff\xff\xff"
        + b"\x03\x00\x00\x00"
        + b"\xfd\xff\xff\xff"
    )
    assert encode_type2(arr, grid, ddi_list=[ddi6, ddi1]) == expected


def test__decode__when_type_2_simple__expect_correct_array():
    grid_bin = (
        b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x01\x00\x00\x00"
        + b"\xff\xff\xff\xff"
    )
    grid = Grid(maximum_column=2, maximum_row=2, type=GridType.GridType2)
    expected = np.array([[0, 0], [1, -1]], dtype=np.int32)
    assert np.array_equal(decode(grid_bin, grid), expected)


def test__decode__when_type_2_multi_ddi__expect_correct_arrays():
    grid_bin = (
        b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x01\x00\x00\x00"
        + b"\xff\xff\xff\xff"
        + b"\x02\x00\x00\x00"
        + b"\xfe\xff\xff\xff"
        + b"\x03\x00\x00\x00"
        + b"\xfd\xff\xff\xff"
    )
    grid = Grid(maximum_column=2, maximum_row=2, type=GridType.GridType2)
    ddi1 = DDEntity.from_id(1)  # scale 0.01
    ddi6 = DDEntity.from_id(6)  # scale 1

    scaled = decode(grid_bin, grid, ddi_list=[ddi6, ddi1])
    expected_scaled = np.array(
        [
            [[0.0, 0.0], [1.0, -0.01]],
            [[2.0, -0.02], [3.0, -0.03]],
        ],
        dtype=np.float32,
    )
    assert np.allclose(scaled, expected_scaled)

    unscaled = decode(grid_bin, grid, ddi_list=[ddi6, ddi1], scale=False)
    expected_unscaled = np.array(
        [
            [[0, 0], [1, -1]],
            [[2, -2], [3, -3]],
        ],
        dtype=np.int32,
    )
    assert np.array_equal(unscaled, expected_unscaled)
