"""Tests for pixel transformations."""

import unittest

import numpy as np

from pdf_color_inverter.models import ConversionSettings, ThresholdSide, TransformMode
from pdf_color_inverter.transform import apply_threshold_in_place


class ApplyThresholdInPlaceTestCase(unittest.TestCase):
    """Verify one-sided and full threshold behavior."""

    def test_dark_side_threshold_whitens_dark_pixels_and_keeps_inverted_light_values(self) -> None:
        pixels = _grayscale_rgb_pixels([0, 105, 255])
        settings = ConversionSettings(
            mode=TransformMode.THRESHOLD,
            threshold=105,
            side=ThresholdSide.DARK,
        )

        _apply(pixels, settings)

        self.assertEqual(_first_channel(pixels), [255, 255, 0])

    def test_dark_side_threshold_preserves_antialiasing_above_threshold(self) -> None:
        pixels = _grayscale_rgb_pixels([106, 180, 254])
        settings = ConversionSettings(
            mode=TransformMode.THRESHOLD,
            threshold=105,
            side=ThresholdSide.DARK,
        )

        _apply(pixels, settings)

        self.assertEqual(_first_channel(pixels), [149, 75, 1])

    def test_light_side_threshold_blackens_light_pixels(self) -> None:
        pixels = _grayscale_rgb_pixels([0, 105, 106])
        settings = ConversionSettings(
            mode=TransformMode.THRESHOLD,
            threshold=105,
            side=ThresholdSide.LIGHT,
        )

        _apply(pixels, settings)

        self.assertEqual(_first_channel(pixels), [255, 150, 0])

    def test_both_sides_produce_binary_output(self) -> None:
        pixels = _grayscale_rgb_pixels([0, 105, 106, 255])
        settings = ConversionSettings(
            mode=TransformMode.THRESHOLD,
            threshold=105,
            side=ThresholdSide.BOTH,
        )

        _apply(pixels, settings)

        self.assertEqual(_first_channel(pixels), [255, 255, 0, 0])

    def test_unflattened_side_preserves_inverted_rgb_color(self) -> None:
        pixels = np.array([[[200, 180, 160]]], dtype=np.uint8)
        settings = ConversionSettings(
            mode=TransformMode.THRESHOLD,
            threshold=105,
            side=ThresholdSide.DARK,
        )

        _apply(pixels, settings)

        self.assertEqual(pixels[0, 0].tolist(), [55, 75, 95])


def _grayscale_rgb_pixels(values: list[int]) -> np.ndarray:
    """Build a one-row RGB array from grayscale values."""
    return np.array([[[value, value, value] for value in values]], dtype=np.uint8)


def _apply(pixels: np.ndarray, settings: ConversionSettings) -> None:
    """Apply the in-place transform to a test pixel array."""
    height, width, _channels = pixels.shape
    apply_threshold_in_place(memoryview(pixels), width, height, settings)


def _first_channel(pixels: np.ndarray) -> list[int]:
    """Return the first channel as plain integers for assertions."""
    return pixels[0, :, 0].tolist()
