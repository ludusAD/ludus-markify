from fastapi.testclient import TestClient

from ludus_markify.aiprep import bundle_markdown, estimate_tokens, trim_for_ai
from ludus_markify.cli import convert_command
from ludus_markify.mcp_server import convert_paths
from ludus_markify.server import app

client = TestClient(app)


# --- token estimate ---

def test_estimate_tokens_ascii_is_about_a_quarter_of_characters():
    assert estimate_tokens("a" * 400) == 100


def test_estimate_tokens_counts_non_ascii_per_character():
    assert estimate_tokens("日本語") == 3


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


# --- trim ---

def test_trim_replaces_base64_images_and_keeps_alt_text():
    md = "before\n\n![Chart](data:image/png;base64," + "A" * 5000 + ")\n\nafter"
    out = trim_for_ai(md)
    assert "base64" not in out
    assert "[image: Chart]" in out
    assert estimate_tokens(out) < 20


def test_trim_keeps_normal_image_links():
    md = "![logo](https://example.com/logo.png)"
    assert "https://example.com/logo.png" in trim_for_ai(md)


def test_trim_drops_page_markers():
    out = trim_for_ai("Intro\n\nPage 2 of 9\n\nMore text\n\n- 3 -\n\nEnd")
    assert "Page 2" not in out and "- 3 -" not in out
    assert "Intro" in out and "More text" in out and "End" in out


def test_trim_keeps_first_copy_of_repeated_header_and_drops_the_rest():
    md = "Acme Corp Confidential 1\n\nalpha\n\nAcme Corp Confidential 2\n\nbeta\n\nAcme Corp Confidential 3\n\ngamma"
    out = trim_for_ai(md)
    assert out.count("Acme Corp Confidential") == 1
    assert "alpha" in out and "beta" in out and "gamma" in out


def test_trim_keeps_a_line_that_appears_only_twice():
    md = "Totals are final here\n\nx\n\nTotals are final here"
    assert trim_for_ai(md).count("Totals are final here") == 2


def test_trim_does_not_touch_headings_lists_or_tables_that_repeat():
    md = "## Summary of results\n\n- same bullet text\n\n## Summary of results\n\n- same bullet text\n\n## Summary of results\n\n- same bullet text"
    out = trim_for_ai(md)
    assert out.count("## Summary of results") == 3
    assert out.count("- same bullet text") == 3


def test_trim_compacts_tables():
    md = "|  Name    |   Qty |\n| :------- | -----: |\n|  Pen     |    3  |"
    out = trim_for_ai(md)
    assert out == "| Name | Qty |\n| :--- | ---: |\n| Pen | 3 |\n"


def test_trim_collapses_blank_lines_and_trailing_spaces():
    assert trim_for_ai("a   \n\n\n\n\nb  \n") == "a\n\nb\n"


def test_trim_leaves_code_fences_alone():
    md = "```\nx   \n\n\n\ny\n```"
    assert trim_for_ai(md) == "```\nx   \n\n\n\ny\n```\n"


def test_trim_is_idempotent():
    md = "# T\n\n\n\nPage 1\n\n|  a | b |\n| --- | --- |\n| 1  | 2 |"
    once = trim_for_ai(md)
    assert trim_for_ai(once) == once


def test_trim_empty():
    assert trim_for_ai("") == ""


# --- bundle ---

def test_bundle_joins_files_under_headings():
    out = bundle_markdown([("a.pdf", "one"), ("b.docx", "two")])
    assert out == "# File: a.pdf\n\none\n\n---\n\n# File: b.docx\n\ntwo\n"


# --- HTTP ---

def test_convert_returns_token_counts_and_trimmed_text():
    body = "Page 1 of 3\n\n\n\n\nhello world"
    r = client.post("/convert", files=[("files", ("n.txt", body.encode(), "text/plain"))])
    item = r.json()[0]
    assert item["tokens"] > 0
    assert "Page 1" not in item["trimmed_markdown"]
    assert item["trimmed_tokens"] < item["tokens"]
    assert "hello world" in item["markdown"]


def test_bundle_endpoint():
    r = client.post("/bundle", json={"files": [{"input_name": "a.txt", "markdown": "one"}, {"input_name": "b.txt", "markdown": "two"}]})
    data = r.json()
    assert r.status_code == 200
    assert data["filename"] == "combined.md"
    assert "# File: a.txt" in data["markdown"] and "# File: b.txt" in data["markdown"]
    assert data["tokens"] > 0


def test_bundle_endpoint_rejects_empty_list():
    assert client.post("/bundle", json={"files": []}).status_code == 400


# --- CLI ---

def test_cli_convert_prints_markdown_for_one_file(tmp_path, capsys):
    f = tmp_path / "note.txt"
    f.write_text("hello cli")
    assert convert_command([str(f)]) == 0
    assert "hello cli" in capsys.readouterr().out


def test_cli_convert_bundles_several_files_on_stdout(tmp_path, capsys):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("alpha")
    b.write_text("beta")
    assert convert_command([str(a), str(b)]) == 0
    out = capsys.readouterr().out
    assert "# File: a.txt" in out and "# File: b.txt" in out


def test_cli_convert_saves_files_with_output_folder(tmp_path, capsys):
    f = tmp_path / "note.txt"
    f.write_text("saved text")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    assert convert_command([str(f), "-o", str(out_dir)]) == 0
    assert (out_dir / "note.md").read_text() == "saved text"


def test_cli_convert_bundle_saves_one_file(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("alpha")
    b.write_text("beta")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    assert convert_command([str(a), str(b), "-o", str(out_dir), "--bundle"]) == 0
    assert [p.name for p in out_dir.iterdir()] == ["combined.md"]


def test_cli_convert_missing_file_reports_and_fails_but_converts_the_rest(tmp_path, capsys):
    good = tmp_path / "ok.txt"
    good.write_text("fine")
    code = convert_command([str(tmp_path / "missing.txt"), str(good)])
    captured = capsys.readouterr()
    assert code == 1
    assert "file not found" in captured.err
    assert "fine" in captured.out


def test_cli_convert_trim_and_tokens(tmp_path, capsys):
    f = tmp_path / "n.txt"
    f.write_text("Page 4 of 9\n\n\n\n\nbody")
    assert convert_command([str(f), "--trim", "--tokens"]) == 0
    captured = capsys.readouterr()
    assert "Page 4" not in captured.out
    assert "tokens" in captured.err


# --- MCP tool logic ---

def test_mcp_convert_paths_single_file_returns_plain_markdown(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("single")
    assert convert_paths([str(f)]).strip() == "single"


def test_mcp_convert_paths_lists_failures(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("single")
    out = convert_paths([str(f), str(tmp_path / "nope.pdf")])
    assert "# File: x.txt" in out
    assert "Could not convert" in out and "nope.pdf" in out
