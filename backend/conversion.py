import io
import tempfile
from pathlib import Path

from markitdown import MarkItDown

from .models import ConversionResult, InputFile, Status, UserError

_converter = MarkItDown()
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def convert_file(f: InputFile) -> ConversionResult:
    suffix = Path(f.name).suffix.lower() or ".bin"
    try:
        markdown = None

        # Use specialised extractors for formats where MarkItDown loses table structure
        if suffix == ".pdf":
            markdown = _convert_pdf(f.content)
        elif suffix == ".xlsx":
            markdown = _convert_xlsx(f.content)

        # Fall back to MarkItDown for everything else, or if the specialised
        # extractor produced nothing (e.g. a PDF with no detectable tables)
        if not markdown or not markdown.strip():
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
                tmp.write(f.content)
                tmp.flush()
                result = _converter.convert(tmp.name)
            markdown = result.text_content
            if not markdown.strip() and suffix in _IMAGE_EXTENSIONS:
                markdown = _ocr_image(f.content)

        # Fix any pipe tables whose rows have inconsistent column counts
        markdown = _normalize_md_tables(markdown)

        return ConversionResult(
            input_name=f.name,
            status=Status.ok,
            markdown=markdown,
        )
    except Exception as exc:
        return ConversionResult(
            input_name=f.name,
            status=Status.error,
            error=_friendly(exc),
        )


# ── PDF ───────────────────────────────────────────────────────────────────────

def _convert_pdf(content: bytes) -> str:
    """Extract PDF content using pdfplumber, preserving table structure.

    pdfplumber uses spatial heuristics to reconstruct table rows/columns from
    character coordinates — far more reliable than pdfminer's flat stream.
    Falls back to plain text when no tables are found on a page.
    Returns empty string on any failure so the caller falls back to MarkItDown.
    """
    try:
        import pdfplumber
    except ImportError:
        return ""

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(content)
            tmp.flush()
            with pdfplumber.open(tmp.name) as pdf:
                parts = []
                for page in pdf.pages:
                    tables = page.find_tables()
                    if not tables:
                        text = page.extract_text()
                        if text and text.strip():
                            parts.append(text.strip())
                        continue

                    # Sort tables top-to-bottom so we emit content in reading order
                    regions = sorted(
                        [(t.bbox[1], t.bbox[3], t) for t in tables],
                        key=lambda x: x[0],
                    )

                    prev_y = 0
                    for top_y, bottom_y, table in regions:
                        if top_y > prev_y:
                            crop = page.crop((0, prev_y, page.width, top_y))
                            text = crop.extract_text()
                            if text and text.strip():
                                parts.append(text.strip())

                        md = _table_to_md(table.extract())
                        if md:
                            parts.append(md)

                        prev_y = bottom_y

                    # Text after the last table on the page
                    if prev_y < page.height:
                        crop = page.crop((0, prev_y, page.width, page.height))
                        text = crop.extract_text()
                        if text and text.strip():
                            parts.append(text.strip())

                return "\n\n".join(parts)
    except Exception:
        return ""


# ── XLSX ──────────────────────────────────────────────────────────────────────

def _convert_xlsx(content: bytes) -> str:
    """Convert an Excel workbook to Markdown, correctly expanding merged cells.

    openpyxl exposes merged cell ranges directly; we fill every cell in each
    range with the top-left value so Markdown columns stay aligned.
    Returns empty string on any failure so the caller falls back to MarkItDown.
    """
    try:
        from openpyxl import load_workbook
    except ImportError:
        return ""

    try:
        wb = load_workbook(io.BytesIO(content), data_only=True)
        parts = []

        for sheet in wb.worksheets:
            # Build (row, col) → value map for every merged cell range
            merge_fill: dict = {}
            for merged_range in sheet.merged_cells.ranges:
                value = sheet.cell(merged_range.min_row, merged_range.min_col).value
                for r in range(merged_range.min_row, merged_range.max_row + 1):
                    for c in range(merged_range.min_col, merged_range.max_col + 1):
                        merge_fill[(r, c)] = value

            rows = []
            for row in sheet.iter_rows():
                cells = []
                for cell in row:
                    val = merge_fill.get((cell.row, cell.column), cell.value)
                    cells.append(str(val) if val is not None else "")
                if any(cells):
                    rows.append(cells)

            if not rows:
                continue

            # Trim trailing empty columns
            max_used = 0
            for row in rows:
                for j in range(len(row) - 1, -1, -1):
                    if row[j]:
                        max_used = max(max_used, j + 1)
                        break
            if max_used == 0:
                continue
            rows = [r[:max_used] for r in rows]

            md = _table_to_md(rows)
            if not md:
                continue

            if len(wb.worksheets) > 1:
                parts.append(f"## {sheet.title}\n\n{md}")
            else:
                parts.append(md)

        return "\n\n".join(parts)
    except Exception:
        return ""


# ── Shared table renderer ─────────────────────────────────────────────────────

def _table_to_md(rows: list) -> str:
    """Render a list-of-lists as a Markdown pipe table."""
    if not rows:
        return ""

    norm = []
    for row in rows:
        if row is None:
            continue
        norm.append([str(c).strip() if c is not None else "" for c in row])

    if not norm:
        return ""

    col_count = max(len(r) for r in norm)
    if col_count == 0:
        return ""

    norm = [r + [""] * (col_count - len(r)) for r in norm]

    def fmt(r: list) -> str:
        return "| " + " | ".join(r) + " |"

    header, *body = norm
    sep = ["---"] * col_count
    return "\n".join([fmt(header), fmt(sep)] + [fmt(r) for r in body])


# ── Post-processing normaliser ────────────────────────────────────────────────

def _normalize_md_tables(md: str) -> str:
    """Pad pipe-table rows that are shorter than the widest row in the block.

    Inconsistent column counts (a symptom of collapsed merged cells) cause
    Markdown renderers to produce garbled output. This pass detects each table
    block and pads every short row with empty cells (or --- for separator rows).
    """
    if "|" not in md:
        return md

    lines = md.split("\n")
    result = []
    i = 0

    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            result.append(lines[i])
            i += 1
            continue

        # Collect the whole table block
        block = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            block.append(lines[i])
            i += 1

        def ncols(line: str) -> int:
            segs = line.split("|")
            if segs and not segs[0].strip():
                segs = segs[1:]
            if segs and not segs[-1].strip():
                segs = segs[:-1]
            return len(segs)

        def is_sep(line: str) -> bool:
            inner = [s.strip() for s in line.split("|") if s.strip()]
            return bool(inner) and all(
                s.replace("-", "").replace(":", "").replace(" ", "") == "" for s in inner
            )

        max_c = max(ncols(l) for l in block) if block else 0

        for line in block:
            n = ncols(line)
            if n < max_c:
                s = line.rstrip()
                pad = max_c - n
                pad_cell = " --- |" if is_sep(line) else " |"
                if s.endswith("|"):
                    s = s + pad_cell * pad
                else:
                    # close the open last cell, then add more
                    s = s + " |" + pad_cell * pad
                result.append(s)
            else:
                result.append(line)

    return "\n".join(result)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ocr_image(content: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception:
        return ""


def _friendly(exc: Exception) -> str:
    msg = str(exc)
    if not msg:
        return type(exc).__name__
    return msg
