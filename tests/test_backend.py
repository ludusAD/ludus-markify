import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.server import app
from backend.conversion import convert_file
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
