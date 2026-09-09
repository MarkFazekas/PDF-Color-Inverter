"""Tests for pixel transformations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pdf_color_inverter.models import ConversionSettings, ThresholdSide, TransformMode
from pdf_color_inverter.transform import apply_threshold_in_place

if TYPE_CHECKING:
    from numpy.typing import NDArray

_TEST_THRESHOLD = 105


def test_dark_side_whitens_dark_pixels() -> None:
    """Flatten dark pixels to white and invert pixels above the threshold."""
    pixels = _grayscale_rgb_pixels([0, _TEST_THRESHOLD, 255])
    settings = _settings(ThresholdSide.DARK)

    _apply(pixels, settings)

    assert _first_channel(pixels) == [255, 255, 0]


def test_dark_side_preserves_antialiasing() -> None:
    """Preserve inverted grayscale detail above the dark-side threshold."""
    pixels = _grayscale_rgb_pixels([106, 180, 254])
    settings = _settings(ThresholdSide.DARK)

    _apply(pixels, settings)

    assert _first_channel(pixels) == [149, 75, 1]


def test_light_side_blackens_light_pixels() -> None:
    """Flatten pixels above the threshold to black in light-side mode."""
    pixels = _grayscale_rgb_pixels([0, _TEST_THRESHOLD, 106])
    settings = _settings(ThresholdSide.LIGHT)

    _apply(pixels, settings)

    assert _first_channel(pixels) == [255, 150, 0]


def test_both_sides_produce_binary_output() -> None:
    """Produce only white and black pixels when both sides are flattened."""
    pixels = _grayscale_rgb_pixels([0, _TEST_THRESHOLD, 106, 255])
    settings = _settings(ThresholdSide.BOTH)

    _apply(pixels, settings)

    assert _first_channel(pixels) == [255, 255, 0, 0]


def test_unflattened_side_preserves_rgb() -> None:
    """Preserve per-channel inverted RGB values on the unflattened side."""
    channels = [200, 180, 160]
    pixels = np.asarray([[channels]], dtype=np.uint8)
    settings = _settings(ThresholdSide.DARK)

    _apply(pixels, settings)

    assert pixels[0, 0].tolist() == [55, 75, 95]


def _settings(side: ThresholdSide) -> ConversionSettings:
    """Build threshold settings for a test case."""
    return ConversionSettings(mode=TransformMode.THRESHOLD, threshold=_TEST_THRESHOLD, side=side)


def _grayscale_rgb_pixels(gray_levels: list[int]) -> NDArray[np.uint8]:
    """Build a one-row RGB array from grayscale values."""
    pixel_rows = [[[level, level, level] for level in gray_levels]]
    return np.asarray(pixel_rows, dtype=np.uint8)


def _apply(pixels: NDArray[np.uint8], settings: ConversionSettings) -> None:
    """Apply the in-place transform to a test pixel array."""
    height, width, _channels = pixels.shape
    apply_threshold_in_place(memoryview(pixels), width, height, settings)


def _first_channel(pixels: NDArray[np.uint8]) -> list[int]:
    """Return the first channel as plain integers for assertions."""
    first_channel = np.take(pixels, 0, axis=2)[0]
    return [int(channel_value) for channel_value in first_channel]
