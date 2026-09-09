"""Configuration models for PDF conversion."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

DEFAULT_DPI = 600
MIN_DPI = 72
MAX_DPI = 2400
MAX_CHANNEL_VALUE = 255


class TransformMode(StrEnum):
    """Available image transformation modes."""

    INVERT = "invert"
    THRESHOLD = "threshold"


class ThresholdSide(StrEnum):
    """Threshold side to flatten to a one-bit value."""

    DARK = "dark"
    LIGHT = "light"
    BOTH = "both"


class ConversionSettings(BaseModel):
    """Validated image conversion settings."""

    dpi: int = Field(default=DEFAULT_DPI, ge=MIN_DPI, le=MAX_DPI)
    mode: TransformMode = TransformMode.INVERT
    threshold: int | None = Field(default=None, ge=0, le=MAX_CHANNEL_VALUE)
    side: ThresholdSide | None = None

    @model_validator(mode="after")
    def validate_threshold_settings(self) -> ConversionSettings:
        """Ensure threshold arguments are used only in threshold mode."""
        if self.mode is TransformMode.THRESHOLD and self.threshold is None:
            msg = "threshold is required when mode is 'threshold'"
            raise ValueError(msg)
        if self.mode is TransformMode.INVERT and self.threshold is not None:
            msg = "threshold can only be used when mode is 'threshold'"
            raise ValueError(msg)
        if self.mode is TransformMode.INVERT and self.side is not None:
            msg = "side can only be used when mode is 'threshold'"
            raise ValueError(msg)
        return self

    @property
    def effective_side(self) -> ThresholdSide:
        """Return the threshold side, defaulting to both in threshold mode."""
        return self.side or ThresholdSide.BOTH


class ConversionJob(BaseModel):
    """One PDF conversion job."""

    input_path: Path
    output_path: Path
    settings: ConversionSettings
    overwrite: bool = False
