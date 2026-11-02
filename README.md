# MarkItDown

A local-first app to convert documents to Markdown. Drop in files, preview the result, and save `.md` files to any folder on your machine.

**Runs entirely locally. No cloud upload. No accounts.**

---

## What it converts

PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), plain text, HTML, images (with Tesseract OCR fallback), and anything else supported by Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) library.

---

## Requirements

- Python 3.10+
- Node.js 18+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — optional, only needed for image files

---

## Installation

```bash
git clone https://github.com/ludusAD/markitdown.git
cd markitdown

# Backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
cd ..
```

Install Tesseract (optional, for image OCR):

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr

# macOS
brew install tesseract

# Windows — download from https://github.com/UB-Mannheim/tesseract/wiki
```

---

## Run

```bash
./start.sh
```

Or manually:

```bash
# Terminal 1 — backend
uvicorn backend.server:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Opens at **http://localhost:3333**

---

## How to use

1. Drag and drop files onto the drop zone (or click to browse)
2. Click **Convert**
3. Preview the Markdown output on the right
4. Enter an output folder path and click **Save** to write `.md` files locally

---

## Project structure

```
backend/
  server.py        FastAPI app — /convert and /save endpoints
  conversion.py    MarkItDown adapter
  filesystem.py    local file save logic
  models.py        data types (InputFile, ConversionResult, UserError)
frontend/
  src/
    App.jsx        main UI
    components/    DropZone, FileRow, Preview
    api.js         fetch calls to backend
requirements.txt   Python dependencies
start.sh           starts backend + frontend together
tests/             backend unit and HTTP tests
```

---

## Self-hosting (server deployment)

Set `HOSTED=true` before starting the backend, and build the frontend with `VITE_HOSTED=true`:

```bash
# Build frontend for hosting
cd frontend
VITE_HOSTED=true npm run build
cd ..

# Run backend (serves the built frontend + API)
HOSTED=true uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

In hosted mode:
- The `/save` endpoint is disabled — files cannot be written to the server's disk.
- The frontend shows a download button instead of the save-to-folder UI.
- A privacy notice is shown to users: "Files are converted in memory and discarded immediately. Nothing is stored or visible — not to us, not to anyone."
- The built React app is served directly by FastAPI (no separate frontend process needed).

Set `SITE_DOMAIN` to your public domain if you need CORS support from that origin:

```bash
HOSTED=true SITE_DOMAIN=https://your-domain.com uvicorn backend.server:app --host 0.0.0.0 --port 8000
```

---

## Run tests

```bash
source .venv/bin/activate
pytest tests/
```

---

## License

MIT
