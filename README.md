# PDF Color Inverter

`pdf-color-inverter` rasterizes PDF pages at high resolution, inverts their colors, and can optionally flatten the dark side, light side, or both sides of a luminance threshold.

The default render resolution is **600 DPI**. Output PDFs are rasterized and are therefore not intended to preserve selectable/searchable text.

## Features

- Plain RGB color inversion by default.
- 600 DPI default rendering.
- Optional threshold mode with a required `0-255` threshold.
- Flatten only the dark side, only the light side, or both sides.
- Preserve inverted anti-aliased detail on the side that is not flattened.
- Convert one PDF, multiple PDFs, or every PDF in a directory.
- Optional recursive directory scanning.
- Standalone executables built by GitHub Actions for Windows x64, Linux x64, macOS Intel, and macOS Apple Silicon.

## How the modes work

### Default: invert

Without `--mode`, every RGB channel is inverted independently:

```text
output = 255 - input
```

Example:

```bash
pdf-color-inverter document.pdf
```

### Threshold mode

Threshold mode classifies pixels by their original luminance, performs the normal RGB inversion, then replaces pixels on the selected side of the threshold with pure white or pure black. Pixels on the other side keep their inverted RGB values.

`--threshold` is mandatory when `--mode threshold` is selected. There is deliberately no default threshold. A value of **127** is a useful general starting point, but the best value depends on the source PDF.

If `--side` is omitted in threshold mode, it defaults to `both`.

#### Flatten the dark side

Original pixels at or below the threshold become pure white. Pixels above the threshold keep their normal inverted values.

This is useful for dark-background PDFs where you want a clean white background but want to preserve anti-aliased text edges.

```bash
pdf-color-inverter document.pdf --mode threshold --threshold 105 --side dark
```

For a grayscale source with threshold `105`, this behaves like:

```text
original 0..105   -> 255 (pure white)
original 106..255 -> 149..0 (normal inversion)
```

#### Flatten the light side

Original pixels above the threshold become pure black. Pixels at or below the threshold keep their normal inverted values.

```bash
pdf-color-inverter document.pdf --mode threshold --threshold 127 --side light
```

#### Flatten both sides

This produces a true black-and-white threshold result:

```bash
pdf-color-inverter document.pdf --mode threshold --threshold 127 --side both
```

Equivalent behavior:

```text
original <= threshold -> white
original > threshold  -> black
```

## CLI usage

```text
pdf-color-inverter INPUT [INPUT ...] [options]
```

Common examples:

```bash
# Plain inversion at the default 600 DPI
pdf-color-inverter input.pdf

# Explicit output path
pdf-color-inverter input.pdf --output result.pdf

# Dark background -> pure white, while preserving inverted text anti-aliasing
pdf-color-inverter input.pdf --mode threshold --threshold 105 --side dark

# Full black-and-white threshold conversion
pdf-color-inverter input.pdf --mode threshold --threshold 127 --side both

# Use a different render resolution
pdf-color-inverter input.pdf --dpi 300

# Convert every PDF in a directory
pdf-color-inverter ./input --output ./converted

# Convert multiple files
pdf-color-inverter a.pdf b.pdf c.pdf --output ./converted

# Include PDFs in nested directories
pdf-color-inverter ./input --recursive --output ./converted

# Replace existing outputs
pdf-color-inverter input.pdf --overwrite
```

Run `pdf-color-inverter --help` for the full option list.

## Output naming

For a single input without `--output`:

- invert mode: `document-inverted.pdf`
- threshold mode: `document-threshold.pdf`

For multiple inputs, the default output directory is `./converted`.

Existing files are not replaced unless `--overwrite` is specified. The tool never permits an output path to be the same as its input path.

## Installation from source

Python 3.12 or newer is required.

Using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e .
```

Using `uv`:

```bash
uv sync
uv run pdf-color-inverter --help
```

## Development

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run all checks:

```bash
ruff check .
ruff format --check .
flake8 src tests
mypy src tests
pytest
```

The lint setup intentionally uses both Ruff and Flake8. Flake8 includes wemake-python-styleguide, bugbear, annotations, comprehensions, eradicate, builtins, print, assertive, spellcheck, Pydantic checks, and PEP 8 naming checks.

## Release executables

Pushing a semantic version tag such as `v0.1.0` triggers the release workflow. The tag version must match the version declared by the project.

The workflow builds and smoke-tests these standalone executables:

- `pdf-color-inverter-windows-x64.exe`
- `pdf-color-inverter-linux-x64`
- `pdf-color-inverter-macos-x64`
- `pdf-color-inverter-macos-arm64`

The resulting binaries are attached to a GitHub Release for that tag.

## Notes and trade-offs

- The converter intentionally rasterizes every page. Text selection/searchability is not preserved.
- 600 DPI produces high-quality text but can use substantial memory and disk space for large documents.
- Threshold mode uses luminance only for threshold classification. Pixels on an unflattened side keep their normal inverted RGB values.
- Password-protected PDFs are not currently supported.

## License

See [LICENSE](LICENSE).
