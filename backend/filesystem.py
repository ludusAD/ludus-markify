from pathlib import Path

from .models import UserError


def resolve_output_dir(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise UserError(message=f"Output directory does not exist: {p}")
    if not p.is_dir():
        raise UserError(message=f"Not a directory: {p}")
    return p


def save_markdown(markdown: str, input_name: str, output_dir: Path) -> Path:
    stem = Path(input_name).stem
    dest = output_dir / f"{stem}.md"
    dest.write_text(markdown, encoding="utf-8")
    return dest
