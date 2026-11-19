import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .aiprep import bundle_markdown, estimate_tokens, trim_for_ai
from .conversion import convert_file
from .filesystem import resolve_output_dir, save_markdown
from .models import ConversionResult, InputFile, Status, UserError

# Per-file upload limit (default 500 MB). Lower it on a shared server: MAX_UPLOAD_MB=50
_MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_MB", "500")) * 1024 * 1024

HOSTED = os.environ.get("HOSTED", "").lower() in ("1", "true", "yes")

app = FastAPI(title="Ludus Markify", version="0.1.0")

_cors_origins = ["http://localhost:3333", "http://127.0.0.1:3333"]
# The packaged CLI serves UI and API from one local port and exports it here.
_local_port = os.environ.get("LUDUS_MARKIFY_PORT")
if _local_port:
    _cors_origins += [f"http://127.0.0.1:{_local_port}", f"http://localhost:{_local_port}"]
if HOSTED:
    _domain = os.environ.get("SITE_DOMAIN", "https://ludus-technology.com")
    _cors_origins.append(_domain)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResultOut(BaseModel):
    input_name: str
    status: str
    markdown: str
    error: str
    saved_path: str = ""
    tokens: int = 0              # estimated tokens of `markdown`
    trimmed_markdown: str = ""   # `markdown` with token-wasting text removed
    trimmed_tokens: int = 0


class SaveRequest(BaseModel):
    input_name: str
    markdown: str
    output_dir: str


@app.post("/convert", response_model=list[ResultOut])
async def convert(request: Request) -> list[ResultOut]:
    form = await request.form(max_part_size=_MAX_UPLOAD_SIZE)
    results: list[ResultOut] = []
    try:
        uploads = form.getlist("files")
        for upload in uploads:
            content = await upload.read()
            # Conversion is CPU-heavy and synchronous; keep it off the event loop so
            # other requests (and a second user) are not frozen while it runs.
            result = await run_in_threadpool(convert_file, InputFile(name=upload.filename or "upload", content=content))
            results.append(_to_out(result))
    finally:
        await form.close()
    return results


class BundleItem(BaseModel):
    input_name: str
    markdown: str


class BundleRequest(BaseModel):
    files: list[BundleItem]


class BundleOut(BaseModel):
    filename: str
    markdown: str
    tokens: int


@app.post("/bundle", response_model=BundleOut)
async def bundle(req: BundleRequest) -> BundleOut:
    """Join converted files into one Markdown text. Nothing is written to disk."""
    if not req.files:
        raise HTTPException(status_code=400, detail="Nothing to combine. Convert files first.")
    text = bundle_markdown([(f.input_name, f.markdown) for f in req.files])
    return BundleOut(filename="combined.md", markdown=text, tokens=estimate_tokens(text))


@app.post("/save", response_model=ResultOut)
async def save(req: SaveRequest, request: Request) -> ResultOut:
    # /save writes to the local disk, so a web page on another site must not be
    # able to trigger it from the user's browser. Browsers always send Origin on
    # cross-site POSTs; command-line clients send none and stay allowed.
    origin = request.headers.get("origin")
    if origin is not None and origin not in _cors_origins:
        raise HTTPException(status_code=403, detail="Cross-site save requests are not allowed.")
    if HOSTED:
        raise HTTPException(status_code=403, detail="Save to disk is disabled in hosted mode. Use the download button.")
    try:
        out_dir = resolve_output_dir(req.output_dir)
    except UserError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    saved = save_markdown(req.markdown, req.input_name, out_dir)
    return ResultOut(
        input_name=req.input_name,
        status=Status.ok,
        markdown=req.markdown,
        error="",
        saved_path=str(saved),
    )


# Serve the built React app when it exists: bundled in the wheel (ludus_markify/static)
# or built in a source checkout (frontend/dist). API routes above take priority.
def _find_frontend() -> Path | None:
    here = Path(__file__).parent
    for candidate in (here / "static", here.parent / "frontend" / "dist"):
        if (candidate / "index.html").is_file():
            return candidate
    return None


_frontend_dir = _find_frontend()
if _frontend_dir is not None:
    if (_frontend_dir / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=str(_frontend_dir / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> Response:
        index = _frontend_dir / "index.html"
        return Response(content=index.read_bytes(), media_type="text/html")


def _to_out(r: ConversionResult) -> ResultOut:
    trimmed = trim_for_ai(r.markdown) if r.markdown else ""
    return ResultOut(
        input_name=r.input_name,
        status=r.status,
        markdown=r.markdown,
        error=r.error,
        tokens=estimate_tokens(r.markdown),
        trimmed_markdown=trimmed,
        trimmed_tokens=estimate_tokens(trimmed),
    )
