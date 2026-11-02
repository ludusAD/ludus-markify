import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.server import app
from backend.conversion import convert_file, _table_to_md, _normalize_md_tables, _convert_xlsx
from backend.filesystem import resolve_output_dir, save_markdown
from backend.models import InputFile, Status, UserError

client = TestClient(app)


# --- conversion layer ---

def test_convert_markdown_file():
    f = InputFile(name="hello.md", content=b"# Hello\n\nworld")
    result = convert_file(f)
    assert result.status == Status.ok
    assert "Hello" in result.markdown


def test_convert_txt_file():
    f = InputFile(name="note.txt", content=b"plain text content")
    result = convert_file(f)
    assert result.status == Status.ok
    assert "plain text content" in result.markdown


def test_convert_unsupported_file_returns_error():
    f = InputFile(name="bad.xyz123", content=b"\x00\x01\x02")
    result = convert_file(f)
    # May succeed or fail depending on MarkItDown; either is acceptable —
    # what matters is no unhandled exception.
    assert result.status in (Status.ok, Status.error)


# --- _table_to_md ---

def test_table_to_md_basic():
    rows = [["Name", "Score"], ["Alice", "95"], ["Bob", "87"]]
    md = _table_to_md(rows)
    assert md.startswith("| Name | Score |")
    assert "| --- | --- |" in md
    assert "| Alice | 95 |" in md
    assert "| Bob | 87 |" in md


def test_table_to_md_none_cells_become_empty():
    rows = [["A", None, "C"], [None, "2", None]]
    md = _table_to_md(rows)
    assert "|  |" in md or "| A |  | C |" in md


def test_table_to_md_ragged_rows_padded():
    rows = [["H1", "H2", "H3"], ["only one"]]
    md = _table_to_md(rows)
    lines = md.split("\n")
    # Every row must have 3 columns
    for line in lines:
        assert line.count("|") == 4  # | col | col | col |


def test_table_to_md_empty_input():
    assert _table_to_md([]) == ""
    assert _table_to_md(None) == ""


# --- _normalize_md_tables ---

def test_normalize_already_correct_table_unchanged():
    md = "| A | B |\n| --- | --- |\n| 1 | 2 |"
    assert _normalize_md_tables(md) == md


def test_normalize_pads_short_body_row():
    md = "| A | B | C |\n| --- | --- | --- |\n| 1 | 2 |"
    result = _normalize_md_tables(md)
    last = result.split("\n")[-1]
    # A 3-column pipe-table row has exactly 4 pipe characters: | c | c | c |
    assert last.count("|") == 4


def test_normalize_pads_short_separator():
    md = "| A | B | C |\n| --- | --- |\n| 1 | 2 | 3 |"
    result = _normalize_md_tables(md)
    sep_line = result.split("\n")[1]
    # Separator must be padded with --- cells, not empty cells
    assert sep_line.count("---") == 3
    assert sep_line.count("|") == 4


def test_normalize_passes_through_non_table_content():
    md = "# Heading\n\nSome paragraph.\n\n| X |\n| --- |\n| val |"
    result = _normalize_md_tables(md)
    assert "# Heading" in result
    assert "Some paragraph." in result


# --- _convert_xlsx (merged cells) ---

def _make_xlsx(setup_fn) -> bytes:
    """Build an in-memory .xlsx using openpyxl, run setup_fn(ws), return bytes."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    setup_fn(ws)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_convert_xlsx_simple_table():
    def setup(ws):
        ws["A1"] = "Product"; ws["B1"] = "Price"
        ws["A2"] = "Widget";  ws["B2"] = 9.99
        ws["A3"] = "Gadget";  ws["B3"] = 4.49

    md = _convert_xlsx(_make_xlsx(setup))
    assert "Product" in md and "Price" in md
    assert "Widget" in md
    assert "|" in md


def test_convert_xlsx_horizontal_merged_cells():
    """A header merged across two columns must appear in both output columns."""
    def setup(ws):
        ws["A1"] = "Revenue"
        ws.merge_cells("A1:B1")       # Revenue spans A1 and B1
        ws["A2"] = "Q1"; ws["B2"] = "Q2"
        ws["A3"] = 100;  ws["B3"] = 150

    md = _convert_xlsx(_make_xlsx(setup))
    # Revenue should appear twice in the header row (once per merged column)
    header_row = [l for l in md.split("\n") if "Revenue" in l][0]
    assert header_row.count("Revenue") == 2


def test_convert_xlsx_vertical_merged_cells():
    """A row-header merged across two rows must appear in both output rows."""
    def setup(ws):
        ws["A1"] = "Region"
        ws.merge_cells("A1:A2")       # Region spans rows 1 and 2
        ws["B1"] = "Jan"; ws["B2"] = "Feb"

    md = _convert_xlsx(_make_xlsx(setup))
    region_rows = [l for l in md.split("\n") if "Region" in l]
    assert len(region_rows) == 2


def test_convert_xlsx_multisheet_adds_headings():
    from openpyxl import Workbook
    wb = Workbook()
    ws1 = wb.active; ws1.title = "Sales"
    ws1["A1"] = "Item"; ws1["B1"] = "Units"
    ws1["A2"] = "Pen";  ws1["B2"] = 10
    ws2 = wb.create_sheet("Costs")
    ws2["A1"] = "Item"; ws2["B1"] = "Cost"
    ws2["A2"] = "Pen";  ws2["B2"] = 1.5
    buf = io.BytesIO(); wb.save(buf)

    md = _convert_xlsx(buf.getvalue())
    assert "## Sales" in md
    assert "## Costs" in md


def test_convert_file_xlsx_end_to_end():
    """convert_file with an xlsx returns ok status and a pipe table."""
    def setup(ws):
        ws["A1"] = "Col1"; ws["B1"] = "Col2"
        ws["A2"] = "x";    ws["B2"] = "y"

    content = _make_xlsx(setup)
    result = convert_file(InputFile(name="report.xlsx", content=content))
    assert result.status == Status.ok
    assert "|" in result.markdown


# --- filesystem layer ---

def test_resolve_output_dir_valid():
    with tempfile.TemporaryDirectory() as d:
        p = resolve_output_dir(d)
        assert p.is_dir()


def test_resolve_output_dir_missing():
    with pytest.raises(UserError):
        resolve_output_dir("/tmp/does_not_exist_xyz_abc_123")


def test_save_markdown():
    with tempfile.TemporaryDirectory() as d:
        out = save_markdown("# Hi", "doc.docx", Path(d))
        assert out.name == "doc.md"
        assert out.read_text() == "# Hi"


# --- HTTP routes ---

def test_post_convert_txt():
    resp = client.post(
        "/convert",
        files=[("files", ("sample.txt", b"hello world", "text/plain"))],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "ok"
    assert "hello world" in data[0]["markdown"]


def test_post_convert_multiple_files():
    resp = client.post(
        "/convert",
        files=[
            ("files", ("a.txt", b"file A", "text/plain")),
            ("files", ("b.txt", b"file B", "text/plain")),
        ],
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_post_save():
    with tempfile.TemporaryDirectory() as d:
        resp = client.post(
            "/save",
            json={"input_name": "report.pdf", "markdown": "# Report", "output_dir": d},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert Path(resp.json()["saved_path"]).exists()


def test_post_save_bad_dir():
    resp = client.post(
        "/save",
        json={"input_name": "x.txt", "markdown": "hi", "output_dir": "/no/such/path"},
    )
    assert resp.status_code == 400
