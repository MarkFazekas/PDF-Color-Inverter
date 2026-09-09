"""Tests for CLI input expansion and output naming."""

import tempfile
import unittest
from pathlib import Path

from pdf_color_inverter.cli import _build_jobs, _collect_input_files
from pdf_color_inverter.models import ConversionSettings, TransformMode


class CliHelpersTestCase(unittest.TestCase):
    """Verify batch input and output path behavior."""

    def test_collect_input_files_reads_pdf_files_from_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            first = root / "a.pdf"
            second = root / "b.PDF"
            ignored = root / "notes.txt"
            first.touch()
            second.touch()
            ignored.touch()

            result = _collect_input_files([root], recursive=False)

            self.assertEqual(result, [first, second])

    def test_multiple_inputs_use_converted_directory_by_default(self) -> None:
        inputs = [Path("a.pdf"), Path("b.pdf")]
        settings = ConversionSettings(mode=TransformMode.INVERT)

        jobs = _build_jobs(inputs, None, settings, overwrite=False)

        self.assertEqual(jobs[0].output_path, Path("converted/a-inverted.pdf"))
        self.assertEqual(jobs[1].output_path, Path("converted/b-inverted.pdf"))
