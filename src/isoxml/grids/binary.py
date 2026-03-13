"""Convert NumPy arrays to and from ISOXML grid binary files."""

from __future__ import annotations

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.models.ddi_entities import DDEntity


def _extract_grid_shape(grid) -> tuple[int, int]:
    return (grid.maximum_row, grid.maximum_column)


def encode_grid_binary(arr: np.ndarray, grid: iso3.Grid | iso4.Grid) -> bytes:
    match grid.type:
        case iso3.GridType.GridType1 | iso4.GridType.GridType1:
            return encode_grid_type_1_binary(arr, grid)
        case iso3.GridType.GridType2 | iso4.GridType.GridType2:
            return encode_grid_type_2_binary(arr, grid)
        case _:
            raise NotImplementedError


def decode_grid_binary(
    grid_bin: bytes,
    grid: iso3.Grid | iso4.Grid,
    ddi_list: list[DDEntity] | None = None,
    scale: bool = True,
) -> np.ndarray:
    """Convert ISOXML grid binary data into a NumPy array."""

    grid_shape = _extract_grid_shape(grid)
    scale_factor = None
    match grid.type:
        case iso3.GridType.GridType1 | iso4.GridType.GridType1:
            return np.frombuffer(grid_bin, dtype=np.uint8).reshape(grid_shape)
        case iso3.GridType.GridType2 | iso4.GridType.GridType2:
            if ddi_list:
                grid_shape = grid_shape + (len(ddi_list),)
                scale_factor = [ddi.bit_resolution for ddi in ddi_list]
            np_arr = np.frombuffer(grid_bin, dtype=np.int32).reshape(grid_shape)
            if scale and scale_factor:
                np_arr = np_arr.astype(np.float32) * scale_factor
            return np_arr
        case _:
            raise NotImplementedError


def encode_grid_type_1_binary(arr: np.ndarray, grid: iso3.Grid | iso4.Grid) -> bytes:
    """Convert a NumPy array into ISOXML grid type 1 binary format."""

    if arr.dtype != np.uint8:
        raise ValueError("grid type 1 requires uint8")
    grid_shape = _extract_grid_shape(grid)
    if arr.shape != grid_shape:
        raise ValueError("numpy shape dose not match grid shape")
    return arr.tobytes(order="C")


def encode_grid_type_2_binary(
    arr: np.ndarray,
    grid: iso3.Grid | iso4.Grid,
    ddi_list: list[DDEntity] | None = None,
    scale: bool = True,
) -> bytes:
    """Convert a NumPy array into ISOXML grid type 2 binary format."""

    grid_shape = _extract_grid_shape(grid)
    if ddi_list and len(ddi_list) > 1:
        grid_shape = grid_shape + (len(ddi_list),)
    if arr.shape != grid_shape:
        raise ValueError("numpy shape dose not match grid shape")

    if scale and ddi_list:
        scale_factor = [int(1 / ddi.bit_resolution) for ddi in ddi_list]
        arr = np.round(arr * scale_factor, decimals=0)
        arr_int32 = arr.astype(dtype=np.int32, order="C", casting="unsafe", copy=True)
    else:
        try:
            arr_int32 = arr.astype(dtype=np.int32, order="C", casting="safe", copy=True)
        except (TypeError, ValueError) as exc:
            raise ValueError("cant convert given arr to type int16", exc) from exc
    return arr_int32.tobytes(order="C")


__all__ = [
    "decode_grid_binary",
    "encode_grid_binary",
    "encode_grid_type_1_binary",
    "encode_grid_type_2_binary",
]
