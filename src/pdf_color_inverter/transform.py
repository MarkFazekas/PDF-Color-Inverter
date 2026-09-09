"""Pixel transformations used by the PDF converter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pdf_color_inverter.models import ConversionSettings, ThresholdSide, TransformMode

if TYPE_CHECKING:
    from numpy.typing import NDArray

_CHANNEL_COUNT = 3
_CHUNK_ROWS = 256
_RED_WEIGHT = 77
_GREEN_WEIGHT = 150
_BLUE_WEIGHT = 29
_LUMINANCE_SHIFT = 8
_WHITE = 255
_BLACK = 0


def apply_threshold_in_place(samples: memoryview, width: int, height: int, settings: ConversionSettings) -> None:
    """Invert RGB pixels and flatten the configured threshold side in place."""
    if settings.mode is not TransformMode.THRESHOLD:
        msg = "apply_threshold_in_place requires threshold mode"
        raise ValueError(msg)
    threshold = settings.threshold
    if threshold is None:
        msg = "threshold mode requires a threshold"
        raise ValueError(msg)

    pixels = _pixel_view(samples, width, height)
    for start_row in range(0, height, _CHUNK_ROWS):
        end_row = min(start_row + _CHUNK_ROWS, height)
        _transform_chunk(pixels[start_row:end_row], threshold, settings.effective_side)


def _pixel_view(samples: memoryview, width: int, height: int) -> NDArray[np.uint8]:
    """Expose packed RGB samples as a writable image array."""
    flat_pixels = np.frombuffer(samples, dtype=np.uint8)
    return flat_pixels.reshape(height, width, _CHANNEL_COUNT)


def _transform_chunk(pixels: NDArray[np.uint8], threshold: int, side: ThresholdSide) -> None:
    """Transform a row chunk without allocating a full-page working copy."""
    luminance = _calculate_luminance(pixels)
    np.subtract(_WHITE, pixels, out=pixels)
    if side in {ThresholdSide.DARK, ThresholdSide.BOTH}:
        pixels[luminance <= threshold] = _WHITE
    if side in {ThresholdSide.LIGHT, ThresholdSide.BOTH}:
        pixels[luminance > threshold] = _BLACK


def _calculate_luminance(pixels: NDArray[np.uint8]) -> NDArray[np.uint16]:
    """Calculate integer RGB luminance with coefficients summing to 256."""
    red = np.take(pixels, 0, axis=2).astype(np.uint16)
    green = np.take(pixels, 1, axis=2).astype(np.uint16)
    blue = np.take(pixels, 2, axis=2).astype(np.uint16)
    weighted = (_RED_WEIGHT * red) + (_GREEN_WEIGHT * green) + (_BLUE_WEIGHT * blue)
    return np.asarray(weighted >> _LUMINANCE_SHIFT, dtype=np.uint16)
