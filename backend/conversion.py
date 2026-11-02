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
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(f.content)
            tmp.flush()
            result = _converter.convert(tmp.name)
        markdown = result.text_content
        # MarkItDown needs an LLM to describe images; fall back to OCR instead
        if not markdown.strip() and suffix in _IMAGE_EXTENSIONS:
            markdown = _ocr_image(f.content)
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
