"""PDF rendering, transformation, and output assembly."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

import pymupdf

from pdf_color_inverter.models import ConversionJob, TransformMode
from pdf_color_inverter.transform import apply_threshold_in_place

LOGGER = logging.getLogger(__name__)
_PDF_POINTS_PER_INCH = 72


def convert_pdf(job: ConversionJob) -> None:
    """Convert one PDF according to the supplied job settings."""
    _validate_paths(job)
    job.output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = _temporary_output_path(job.output_path)
    try:
        _convert_to_path(job, temp_path)
        temp_path.replace(job.output_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def _convert_to_path(job: ConversionJob, output_path: Path) -> None:
    """Render, transform, and assemble a PDF at a temporary path."""
    scale = job.settings.dpi / _PDF_POINTS_PER_INCH
    matrix = pymupdf.Matrix(scale, scale)

    with pymupdf.open(str(job.input_path)) as source, pymupdf.open() as destination:
        for page_number, page in enumerate(source, start=1):
            LOGGER.info("Processing %s page %d/%d", job.input_path.name, page_number, source.page_count)
            image_bytes = _render_and_transform_page(page, matrix, job)
            _insert_page(destination, page.rect, image_bytes)

        _copy_document_metadata(source, destination)
        destination.save(str(output_path), garbage=4, deflate=True)


def _render_and_transform_page(page: pymupdf.Page, matrix: pymupdf.Matrix, job: ConversionJob) -> bytes:
    """Render and transform one page, returning lossless PNG bytes."""
    pixmap = page.get_pixmap(matrix=matrix, colorspace=pymupdf.csRGB, alpha=False)
    if job.settings.mode is TransformMode.INVERT:
        pixmap.invert_irect(pixmap.irect)
    else:
        apply_threshold_in_place(pixmap.samples_mv, pixmap.width, pixmap.height, job.settings)
    return bytes(pixmap.tobytes("png"))


def _insert_page(destination: pymupdf.Document, page_rect: pymupdf.Rect, image_bytes: bytes) -> None:
    """Append a rasterized page while preserving the original page dimensions."""
    output_page = destination.new_page(width=page_rect.width, height=page_rect.height)
    output_page.insert_image(output_page.rect, stream=image_bytes)


def _copy_document_metadata(source: pymupdf.Document, destination: pymupdf.Document) -> None:
    """Copy metadata and table of contents when available."""
    if source.metadata:
        destination.set_metadata(source.metadata)
    table_of_contents = source.get_toc()
    if table_of_contents:
        destination.set_toc(table_of_contents)


def _temporary_output_path(output_path: Path) -> Path:
    """Reserve a temporary file path next to the requested output."""
    with NamedTemporaryFile(
        prefix=f".{output_path.stem}.",
        suffix=".tmp.pdf",
        dir=output_path.parent,
        delete=False,
    ) as temporary_file:
        return Path(temporary_file.name)


def _validate_paths(job: ConversionJob) -> None:
    """Validate input and output paths before conversion starts."""
    _validate_input_path(job.input_path)
    _validate_output_path(job)


def _validate_input_path(input_path: Path) -> None:
    """Validate the input PDF path."""
    if not input_path.is_file():
        msg = f"Input PDF does not exist: {input_path}"
        raise FileNotFoundError(msg)
    if input_path.suffix.lower() != ".pdf":
        msg = f"Input file is not a PDF: {input_path}"
        raise ValueError(msg)


def _validate_output_path(job: ConversionJob) -> None:
    """Validate the requested output path."""
    if job.input_path.resolve() == job.output_path.resolve():
        msg = "Input and output paths must be different"
        raise ValueError(msg)
    if job.output_path.exists() and not job.overwrite:
        msg = f"Output already exists: {job.output_path}. Use --overwrite to replace it."
        raise FileExistsError(msg)
