"""Tests for conversion configuration models."""

import unittest

from pydantic import ValidationError

from pdf_color_inverter.models import ConversionSettings, ThresholdSide, TransformMode


class ConversionSettingsTestCase(unittest.TestCase):
    """Validate settings defaults and mode constraints."""

    def test_default_settings_use_600_dpi_invert_mode(self) -> None:
        settings = ConversionSettings()

        self.assertEqual(settings.dpi, 600)
        self.assertEqual(settings.mode, TransformMode.INVERT)
        self.assertIsNone(settings.threshold)
        self.assertIsNone(settings.side)

    def test_threshold_mode_requires_threshold(self) -> None:
        with self.assertRaises(ValidationError):
            ConversionSettings(mode=TransformMode.THRESHOLD)

    def test_threshold_mode_defaults_effective_side_to_both(self) -> None:
        settings = ConversionSettings(mode=TransformMode.THRESHOLD, threshold=127)

        self.assertEqual(settings.effective_side, ThresholdSide.BOTH)

    def test_invert_mode_rejects_threshold(self) -> None:
        with self.assertRaises(ValidationError):
            ConversionSettings(threshold=127)
