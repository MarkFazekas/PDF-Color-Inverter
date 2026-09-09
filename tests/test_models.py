"""Tests for conversion configuration models."""

import pytest
from pydantic import ValidationError

from pdf_color_inverter.models import DEFAULT_DPI, ConversionSettings, ThresholdSide, TransformMode

_TEST_THRESHOLD = 127


def test_default_settings() -> None:
    """Default to 600 DPI and plain inversion without threshold settings."""
    settings = ConversionSettings()

    assert settings.dpi == DEFAULT_DPI
    assert settings.mode is TransformMode.INVERT
    assert settings.threshold is None
    assert settings.side is None


def test_threshold_requires_value() -> None:
    """Require an explicit threshold in threshold mode."""
    with pytest.raises(ValidationError):
        ConversionSettings(mode=TransformMode.THRESHOLD)


def test_threshold_side_defaults_to_both() -> None:
    """Flatten both threshold sides when no side is supplied."""
    settings = ConversionSettings(mode=TransformMode.THRESHOLD, threshold=_TEST_THRESHOLD)

    assert settings.effective_side is ThresholdSide.BOTH


def test_invert_rejects_threshold() -> None:
    """Reject threshold values in plain inversion mode."""
    with pytest.raises(ValidationError):
        ConversionSettings(threshold=_TEST_THRESHOLD)
