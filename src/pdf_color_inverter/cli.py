"""Command-line interface for PDF Color Inverter."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ValidationError

from pdf_color_inverter import __version__
from pdf_color_inverter.converter import convert_pdf
from pdf_color_inverter.models import (
    DEFAULT_DPI,
    ConversionJob,
    ConversionSettings,
    ThresholdSide,
    TransformMode,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

LOGGER = logging.getLogger(__name__)
_DEFAULT_BATCH_DIRECTORY = Path("converted")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="pdf-color-inverter",
        description="Rasterize PDFs, invert their colors, and optionally threshold one or both luminance sides.",
    )
    _add_input_arguments(parser)
    _add_transform_arguments(parser)
    _add_runtime_arguments(parser)
    return parser


def _add_input_arguments(parser: argparse.ArgumentParser) -> None:
    """Add input and output path arguments."""
    parser.add_argument("inputs", nargs="+", type=Path, help="PDF file(s) or directories containing PDF files.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output PDF for one input, or output directory for batch input.",
    )
    parser.add_argument("--recursive", action="store_true", help="Search input directories recursively for PDFs.")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files.")


def _add_transform_arguments(parser: argparse.ArgumentParser) -> None:
    """Add image transformation arguments."""
    parser.add_argument(
        "-m",
        "--mode",
        choices=[mode.value for mode in TransformMode],
        default=TransformMode.INVERT.value,
    )
    parser.add_argument("-t", "--threshold", type=int, help="Required for threshold mode; valid range is 0-255.")
    parser.add_argument(
        "-s",
        "--side",
        choices=[side.value for side in ThresholdSide],
        help="Threshold side to flatten; defaults to both.",
    )
    parser.add_argument("-d", "--dpi", type=int, default=DEFAULT_DPI, help="Render resolution in DPI. Default: 600.")


def _add_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    """Add application metadata arguments."""
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line application."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        _execute(args)
    except (FileExistsError, FileNotFoundError) as error:
        parser.error(str(error))
    except ValidationError as error:
        parser.error(str(error))
    except ValueError as error:
        parser.error(str(error))
    return 0


def _execute(args: argparse.Namespace) -> None:
    """Build conversion jobs and execute them."""
    settings = ConversionSettings(
        dpi=args.dpi,
        mode=TransformMode(args.mode),
        threshold=args.threshold,
        side=ThresholdSide(args.side) if args.side else None,
    )
    input_files = _collect_input_files(args.inputs, recursive=args.recursive)
    jobs = _build_jobs(input_files, args.output, settings, overwrite=args.overwrite)
    for job in jobs:
        convert_pdf(job)
        LOGGER.info("Wrote %s", job.output_path)


def _collect_input_files(inputs: Sequence[Path], *, recursive: bool) -> list[Path]:
    """Expand input files and directories into a unique ordered PDF list."""
    files: list[Path] = []
    seen: set[Path] = set()

    for input_path in inputs:
        for candidate in _expand_input(input_path, recursive=recursive):
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                files.append(candidate)

    if not files:
        msg = "No PDF files found in the supplied input paths"
        raise FileNotFoundError(msg)
    return files


def _expand_input(input_path: Path, *, recursive: bool) -> list[Path]:
    """Expand one input path into PDF files."""
    if input_path.is_file():
        if not _is_pdf_file(input_path):
            msg = f"Input file is not a PDF: {input_path}"
            raise ValueError(msg)
        return [input_path]
    if input_path.is_dir():
        candidates = input_path.rglob("*") if recursive else input_path.iterdir()
        return sorted(filter(_is_pdf_file, candidates))
    msg = f"Input path does not exist: {input_path}"
    raise FileNotFoundError(msg)


def _is_pdf_file(path: Path) -> bool:
    """Return whether a path points to a PDF file."""
    return path.is_file() and path.suffix.lower() == ".pdf"


def _build_jobs(
    input_files: Sequence[Path],
    output: Path | None,
    settings: ConversionSettings,
    *,
    overwrite: bool,
) -> list[ConversionJob]:
    """Create conversion jobs and resolve output paths."""
    if len(input_files) == 1:
        return [_single_job(input_files[0], output, settings, overwrite=overwrite)]

    output_directory = output or _DEFAULT_BATCH_DIRECTORY
    if output_directory.suffix.lower() == ".pdf":
        msg = "Batch conversion requires --output to be a directory"
        raise ValueError(msg)
    return _batch_jobs(input_files, output_directory, settings, overwrite=overwrite)


def _batch_jobs(
    input_files: Iterable[Path],
    output_directory: Path,
    settings: ConversionSettings,
    *,
    overwrite: bool,
) -> list[ConversionJob]:
    """Build jobs for a batch of input files."""
    return [
        ConversionJob(
            input_path=input_path,
            output_path=output_directory / _output_filename(input_path, settings),
            settings=settings,
            overwrite=overwrite,
        )
        for input_path in input_files
    ]


def _single_job(
    input_path: Path,
    output: Path | None,
    settings: ConversionSettings,
    *,
    overwrite: bool,
) -> ConversionJob:
    """Build a conversion job for one PDF."""
    if output is None:
        output_path = input_path.with_name(_output_filename(input_path, settings))
    elif output.suffix.lower() == ".pdf":
        output_path = output
    else:
        output_path = output / _output_filename(input_path, settings)
    return ConversionJob(
        input_path=input_path,
        output_path=output_path,
        settings=settings,
        overwrite=overwrite,
    )


def _output_filename(input_path: Path, settings: ConversionSettings) -> str:
    """Return the default output filename for a conversion mode."""
    suffix = "inverted" if settings.mode is TransformMode.INVERT else "threshold"
    return f"{input_path.stem}-{suffix}.pdf"


if __name__ == "__main__":
    sys.exit(main())
