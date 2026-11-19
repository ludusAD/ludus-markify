# Ludus Markify

A local-first app to convert documents to Markdown. Drop in files, preview the result, and save `.md` files to any folder on your machine.

**Runs entirely locally. No cloud upload. No accounts.**

---

## What it converts

PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), plain text, HTML, images (with Tesseract OCR fallback), and anything else supported by Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

---

## Quick start

```bash
uvx ludus-markify          # or: pipx run ludus-markify
```

Opens **http://127.0.0.1:8000** in your browser. Needs Python 3.10+ and [uv](https://docs.astral.sh/uv/) (or pipx). No Node.js needed. Options: `--port 9000`, `--no-browser`.

Optional: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for image files (`sudo apt install tesseract-ocr` / `brew install tesseract` / [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki)).

---

## Development

Needs Python 3.10+ and Node.js 20.19+ or 22.12+.

```bash
git clone https://github.com/ludusAD/ludus-markify.git
cd ludus-markify
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e . pytest httpx
(cd frontend && npm install)
./start.sh                                            # backend :8000 + Vite dev server :3333
```

Dev UI opens at **http://localhost:3333**. `start.sh` uses `.venv` automatically and stops if a port is taken.

Build the package (bundles the frontend into the wheel):

```bash
./scripts/build.sh --wheel      # output in dist/
twine upload dist/*             # publish to PyPI
```

---

## How to use

1. Drag and drop files onto the drop zone (or click to browse)
2. Click **Convert**
3. Preview the Markdown output on the right
4. Enter an output folder path and click **Save** to write `.md` files locally. Saving never overwrites: if `report.md` exists, the new file becomes `report (1).md`.

---

## Use with AI tools

Markdown costs far fewer tokens than a PDF or Word file, so converting first saves tokens and money. No AI is involved: everything runs on this computer.

- **Token count:** every file shows `≈ N tokens` (an estimate, about 4 characters per token). Real counts vary by AI tool.
- **Trim for AI:** a checkbox in the results. Removes embedded base64 images, `Page 3 of 9` lines, headers and footers that repeat on 3+ pages, table padding and extra blank lines. Preview, copy and save all use the trimmed text. The saving is shown per file.
- **Save as one file:** joins all converted files into one `combined.md`, each under a `# File: name` heading.
- **Command line:** no browser needed.

```bash
ludus-markify convert report.pdf                     # Markdown to stdout
ludus-markify convert a.pdf b.docx --trim --tokens   # several files: one text, with # File: headings
ludus-markify convert *.pdf -o ~/notes               # save one .md per file
ludus-markify convert *.pdf -o ~/notes --bundle      # save one combined.md
```

- **MCP server** (Claude Code, Claude Desktop, any MCP client): the AI tool calls the converter locally and receives Markdown instead of a binary file.

```bash
claude mcp add ludus-markify -- uvx --from "ludus-markify[mcp]" ludus-markify mcp
```

For Claude Desktop add the same command to `claude_desktop_config.json` under `mcpServers`. The tool is `convert_to_markdown(paths, trim=true)`. It reads files on this computer from the paths the AI tool gives it, so only add it to tools you trust.

---

## What it cannot convert

Old `.doc` / `.ppt`, RTF, Apple Pages/Numbers/Keynote, OpenDocument, audio and video get a clear error. Scanned PDFs have no text to read (OCR works for `.jpg`/`.png` only, with Tesseract installed). The same list is shown in the app.

---

## Project structure

```
ludus_markify/
  cli.py           `ludus-markify` command: serve (default), convert
  aiprep.py        token estimate, trim for AI, bundle (pure text functions)
  mcp_server.py    MCP server: `ludus-markify mcp`
  server.py        FastAPI app — /convert and /save endpoints
  conversion.py    MarkItDown adapter
  filesystem.py    local file save logic
  models.py        data types (InputFile, ConversionResult, UserError)
frontend/
  src/
    App.jsx        main UI
    components/    DropZone, FileRow, Preview
    api.js         fetch calls to backend
pyproject.toml     package metadata and dependencies
scripts/build.sh   build frontend into package (+ wheel with --wheel)
start.sh           starts backend + frontend together
tests/             backend unit and HTTP tests
```

---

## Self-hosting (server deployment)

Set `HOSTED=true` before starting the backend, and build the frontend with `VITE_HOSTED=true`:

```bash
# Build frontend for hosting
VITE_HOSTED=true ./scripts/build.sh

# Run backend (serves the built frontend + API)
HOSTED=true uvicorn ludus_markify.server:app --host 0.0.0.0 --port 8000
```

In hosted mode:
- The `/save` endpoint is disabled — files cannot be written to the server's disk.
- Uploads are limited to 500 MB per file; set `MAX_UPLOAD_MB=50` (for example) to lower it.
- The frontend shows a download button instead of the save-to-folder UI.
- A privacy notice is shown to users: "Files are converted in memory and discarded immediately. Nothing is stored or visible — not to us, not to anyone."
- The built React app is served directly by FastAPI (no separate frontend process needed).

Set `SITE_DOMAIN` to your public domain if you need CORS support from that origin:

```bash
HOSTED=true SITE_DOMAIN=https://your-domain.com uvicorn ludus_markify.server:app --host 0.0.0.0 --port 8000
```

---

## Run tests

```bash
source .venv/bin/activate
pip install -e . pytest httpx     # test-only: pytest httpx
pytest tests/
```

---

## License

MIT
