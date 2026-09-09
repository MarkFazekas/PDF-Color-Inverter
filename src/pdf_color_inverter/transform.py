"""Pixel transformations used by the PDF converter."""

import numpy as np
from numpy.typing import NDArray

from pdf_color_inverter.models import ConversionSettings, ThresholdSide, TransformMode


_CHANNEL_COUNT = 3
_CHUNK_ROWS = 256
_RED_WEIGHT = 77
_GREEN_WEIGHT = 150
_BLUE_WEIGHT = 29
_LUMINANCE_SHIFT = 8
_WHITE = 255
_BLACK = 0


def apply_threshold_in_place(
    samples: memoryview,
    width: int,
    height: int,
    settings: ConversionSettings,
) -> None:
    """Invert RGB pixels and flatten the configured threshold side in place.

    Threshold classification uses the original RGB luminance. Processing is
    chunked by rows so 600 DPI pages do not require full-page temporary arrays.
    Pixels on an unselected side keep their channel-wise inverted RGB values.
    """
    if settings.mode is not TransformMode.THRESHOLD:
        msg = "apply_threshold_in_place requires threshold mode"
        raise ValueError(msg)
    threshold = settings.threshold
    if threshold is None:
        msg = "threshold mode requires a threshold"
        raise ValueError(msg)

    pixels = np.frombuffer(samples, dtype=np.uint8).reshape(height, width, _CHANNEL_COUNT)
    for start_row in range(0, height, _CHUNK_ROWS):
        end_row = min(start_row + _CHUNK_ROWS, height)
        _transform_chunk(pixels[start_row:end_row], threshold, settings.effective_side)


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
    red = pixels[:, :, 0].astype(np.uint16)
    green = pixels[:, :, 1].astype(np.uint16)
    blue = pixels[:, :, 2].astype(np.uint16)
    weighted = (_RED_WEIGHT * red) + (_GREEN_WEIGHT * green) + (_BLUE_WEIGHT * blue)
    return weighted >> _LUMINANCE_SHIFT
