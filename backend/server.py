import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .conversion import convert_file
from .filesystem import resolve_output_dir, save_markdown
from .models import ConversionResult, InputFile, Status, UserError

# Allow uploads up to 500 MB per file
_MAX_UPLOAD_SIZE = 500 * 1024 * 1024

HOSTED = os.environ.get("HOSTED", "").lower() in ("1", "true", "yes")

app = FastAPI(title="MarkItDown", version="0.1.0")

_cors_origins = ["http://localhost:3333", "http://127.0.0.1:3333"]
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
            result = convert_file(InputFile(name=upload.filename or "upload", content=content))
            results.append(_to_out(result))
    finally:
        await form.close()
    return results


@app.post("/save", response_model=ResultOut)
async def save(req: SaveRequest) -> ResultOut:
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


# In hosted mode, serve the built React frontend from /api/* and catch-all → index.html
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if HOSTED and _frontend_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> Response:
        index = _frontend_dist / "index.html"
        return Response(content=index.read_bytes(), media_type="text/html")


def _to_out(r: ConversionResult) -> ResultOut:
    return ResultOut(
        input_name=r.input_name,
        status=r.status,
        markdown=r.markdown,
        error=r.error,
    )
