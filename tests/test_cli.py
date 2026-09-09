"""Tests for CLI input expansion and output naming."""

import tempfile
from pathlib import Path

from pdf_color_inverter.cli import _build_jobs, _collect_input_files
from pdf_color_inverter.models import ConversionSettings, TransformMode


def test_collects_pdfs_from_directory() -> None:
    """Collect PDF files from a directory and ignore unrelated files."""
    with tempfile.TemporaryDirectory() as temp_directory:
        root = Path(temp_directory)
        first = root / "a.pdf"
        second = root / "b.PDF"
        ignored = root / "notes.txt"
        first.touch()
        second.touch()
        ignored.touch()

        files = _collect_input_files([root], recursive=False)

        assert files == [first, second]


def test_batch_uses_default_output_directory() -> None:
    """Use the converted directory when multiple inputs have no output path."""
    inputs = [Path("a.pdf"), Path("b.pdf")]
    settings = ConversionSettings(mode=TransformMode.INVERT)

    jobs = _build_jobs(inputs, None, settings, overwrite=False)

    assert jobs[0].output_path == Path("converted/a-inverted.pdf")
    assert jobs[1].output_path == Path("converted/b-inverted.pdf")
