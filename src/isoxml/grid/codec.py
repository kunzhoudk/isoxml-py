"""Encode and decode ISOXML binary grid files (GRD????.bin) using NumPy arrays."""

import numpy as np

import isoxml.models.base.v3 as iso3
import isoxml.models.base.v4 as iso4
from isoxml.models.ddi import DDEntity


def _grid_shape(grid: iso3.Grid | iso4.Grid) -> tuple[int, int]:
    return (grid.maximum_row, grid.maximum_column)


# ---------------------------------------------------------------------------
# Encoding: NumPy → binary bytes
# ---------------------------------------------------------------------------


def encode(
    arr: np.ndarray,
    grid: iso3.Grid | iso4.Grid,
    ddi_list: list[DDEntity] | None = None,
    scale: bool = True,
) -> bytes:
    """Convert a NumPy array to the binary format required by the given *grid*.

    Dispatches to :func:`encode_type1` or :func:`encode_type2` based on
    ``grid.type``.
    """
    match grid.type:
        case iso3.GridType.GridType1 | iso4.GridType.GridType1:
            return encode_type1(arr, grid)
        case iso3.GridType.GridType2 | iso4.GridType.GridType2:
            return encode_type2(arr, grid, ddi_list=ddi_list, scale=scale)
        case _:
            raise NotImplementedError(f"Unsupported grid type: {grid.type!r}")


def encode_type1(arr: np.ndarray, grid: iso3.Grid | iso4.Grid) -> bytes:
    """Encode a uint8 array as a Grid Type 1 binary payload.

    Grid Type 1 stores one unsigned byte per cell (0–255), each value
    referencing a ``TreatmentZone`` code.

    Args:
        arr: 2-D array with dtype ``uint8`` and shape ``(rows, columns)``.
        grid: Matching ISOXML ``Grid`` element supplying the expected shape.

    Returns:
        Row-major (C-order) byte sequence.
    """
    if arr.dtype != np.uint8:
        raise ValueError(f"Grid Type 1 requires dtype uint8; got {arr.dtype!r}.")
    expected = _grid_shape(grid)
    if arr.shape != expected:
        raise ValueError(
            f"Array shape {arr.shape} does not match grid shape {expected}."
        )
    return arr.tobytes(order="C")


def encode_type2(
    arr: np.ndarray,
    grid: iso3.Grid | iso4.Grid,
    ddi_list: list[DDEntity] | None = None,
    scale: bool = True,
) -> bytes:
    """Encode an int32-compatible array as a Grid Type 2 binary payload.

    Grid Type 2 stores one signed 32-bit integer per cell per
    ``ProcessDataVariable``. Optionally applies DDI bit-resolution scaling
    before quantisation.

    Args:
        arr: Array with shape ``(rows, columns)`` for a single PDV, or
            ``(rows, columns, pdv_count)`` for multiple PDVs.
        grid: Matching ISOXML ``Grid`` element.
        ddi_list: DDI metadata used for scaling. Required when *scale* is
            ``True`` and the array contains physical-unit values.
        scale: When ``True`` and *ddi_list* is provided, multiply by
            ``1 / bit_resolution`` before casting to int32.

    Returns:
        Row-major (C-order) byte sequence of int32 values.
    """
    expected = _grid_shape(grid)
    if ddi_list and len(ddi_list) > 1:
        expected = expected + (len(ddi_list),)
    if arr.shape != expected:
        raise ValueError(
            f"Array shape {arr.shape} does not match expected shape {expected}."
        )
    if scale and ddi_list:
        factors = [int(1 / ddi.bit_resolution) for ddi in ddi_list]
        arr = np.round(arr * factors, decimals=0)
        arr_int32 = arr.astype(dtype=np.int32, order="C", casting="unsafe", copy=True)
    else:
        try:
            arr_int32 = arr.astype(dtype=np.int32, order="C", casting="safe", copy=True)
        except (TypeError, ValueError) as exc:
            raise ValueError("Cannot safely cast array to int32.") from exc
    return arr_int32.tobytes(order="C")


# ---------------------------------------------------------------------------
# Decoding: binary bytes → NumPy
# ---------------------------------------------------------------------------


def decode(
    grid_bin: bytes,
    grid: iso3.Grid | iso4.Grid,
    ddi_list: list[DDEntity] | None = None,
    scale: bool = True,
) -> np.ndarray:
    """Convert a binary grid payload back to a NumPy array.

    Dispatches to the appropriate decoder based on ``grid.type``.

    Args:
        grid_bin: Raw bytes from the ``.bin`` file.
        grid: Matching ISOXML ``Grid`` element.
        ddi_list: (Type 2 only) DDI metadata for interpreting multi-PDV grids
            and optionally scaling raw integer values to physical units.
        scale: (Type 2 only) When ``True``, multiply raw int32 values by
            ``bit_resolution`` to obtain physical-unit floats.

    Returns:
        - Type 1: uint8 array of shape ``(rows, cols)``.
        - Type 2: int32 array of shape ``(rows, cols)`` or float32 array
          of shape ``(rows, cols, pdv_count)`` when *ddi_list* is provided
          and *scale* is ``True``.
    """
    shape = _grid_shape(grid)
    match grid.type:
        case iso3.GridType.GridType1 | iso4.GridType.GridType1:
            return np.frombuffer(grid_bin, dtype=np.uint8).reshape(shape)
        case iso3.GridType.GridType2 | iso4.GridType.GridType2:
            scale_factors = None
            if ddi_list:
                shape = shape + (len(ddi_list),)
                scale_factors = [ddi.bit_resolution for ddi in ddi_list]
            arr = np.frombuffer(grid_bin, dtype=np.int32).reshape(shape)
            if scale and scale_factors:
                arr = arr.astype(np.float32) * scale_factors
            return arr
        case _:
            raise NotImplementedError(f"Unsupported grid type: {grid.type!r}")
