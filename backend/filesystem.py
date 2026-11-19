from pathlib import Path

from .models import UserError


def resolve_output_dir(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise UserError(message=f"Output directory does not exist: {p}")
    if not p.is_dir():
        raise UserError(message=f"Not a directory: {p}")
    return p


def _safe_stem(input_name: str) -> str:
    # The name comes from the browser: keep only the last path part (either separator).
    leaf = input_name.replace("\\", "/").rsplit("/", 1)[-1]
    stem = Path(leaf).stem.strip().strip(".")
    return stem or "document"


def save_markdown(markdown: str, input_name: str, output_dir: Path) -> Path:
    """Write <name>.md into output_dir without ever replacing an existing file.

    If the name is taken (for example report.pdf and report.docx), the next
    free "name (1).md", "name (2).md" is used.
    """
    stem = _safe_stem(input_name)
    n = 0
    while True:
        name = f"{stem}.md" if n == 0 else f"{stem} ({n}).md"
        dest = output_dir / name
        try:
            # "x" fails if the file exists, so two saves cannot race onto one name.
            with open(dest, "x", encoding="utf-8") as fh:
                fh.write(markdown)
            return dest
        except FileExistsError:
            n += 1
