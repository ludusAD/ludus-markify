from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .conversion import convert_file
from .filesystem import resolve_output_dir, save_markdown
from .models import ConversionResult, InputFile, Status, UserError

# Allow uploads up to 500 MB per file
_MAX_UPLOAD_SIZE = 500 * 1024 * 1024

app = FastAPI(title="MarkItDown", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3333", "http://127.0.0.1:3333"],
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


def _to_out(r: ConversionResult) -> ResultOut:
    return ResultOut(
        input_name=r.input_name,
        status=r.status,
        markdown=r.markdown,
        error=r.error,
    )
