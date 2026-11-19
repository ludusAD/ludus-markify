"""Make Markdown cheaper and easier to hand to an AI tool. Pure text in, text out. No LLM, no network."""
import math
import re

# A pipe that is not escaped as \| separates table cells.
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_DATA_IMAGE = re.compile(r"!\[([^\]]*)\]\(\s*data:[^)]*\)")
_PAGE_MARKER = re.compile(r"^\s*(page\s+\d+(\s+of\s+\d+)?|-\s*\d+\s*-)\s*$", re.IGNORECASE)
_LIST_START = re.compile(r"^(\s*([-*+]|\d+[.)])\s)")
_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
_FENCE = re.compile(r"^\s*(```|~~~)")


def estimate_tokens(text: str) -> int:
    """Rough token count. Roughly 4 ASCII characters per token, 1 token per other character.

    Real counts depend on the AI tool's tokenizer, so show this as an estimate (≈).
    An exact tokenizer would need a vocabulary download, which local-first forbids.
    """
    if not text:
        return 0
    non_ascii = sum(1 for ch in text if ord(ch) > 127)
    return math.ceil((len(text) - non_ascii) / 4) + non_ascii


def trim_for_ai(markdown: str) -> str:
    """Remove text that costs tokens but carries no meaning for a reader.

    - embedded base64 images (can be thousands of tokens each)
    - "Page 3 of 10" lines and headers/footers repeated on every page
    - table padding, long separator dashes, trailing spaces, runs of blank lines
    Text inside code fences is left alone.
    """
    text = _DATA_IMAGE.sub(lambda m: f"[image: {m.group(1).strip()}]" if m.group(1).strip() else "[image]", markdown)
    lines = text.split("\n")

    in_fence = [False] * len(lines)
    fenced = False
    for i, line in enumerate(lines):
        if _FENCE.match(line):
            fenced = not fenced
            in_fence[i] = True
        else:
            in_fence[i] = fenced

    # Headers and footers: a short plain line that returns on 3+ pages (digits ignored).
    def repeat_key(line: str) -> str | None:
        s = line.strip()
        if not 8 <= len(s) <= 80:
            return None
        if s[0] in "|#>" or s.startswith("![") or _LIST_START.match(line):
            return None
        return re.sub(r"\d+", "#", s).lower()

    counts: dict[str, int] = {}
    for i, line in enumerate(lines):
        if not in_fence[i]:
            key = repeat_key(line)
            if key:
                counts[key] = counts.get(key, 0) + 1

    seen: set[str] = set()
    out: list[str] = []
    for i, line in enumerate(lines):
        if in_fence[i]:
            out.append(line)
            continue
        if _PAGE_MARKER.match(line):
            continue
        key = repeat_key(line)
        if key and counts.get(key, 0) >= 3:
            if key in seen:
                continue  # keep the first copy, drop the repeats
            seen.add(key)
        out.append(_compact_table_line(line.rstrip()) if line.lstrip().startswith("|") else line.rstrip())

    # in_fence no longer lines up after drops, so collapse blank runs by a fresh pass.
    result: list[str] = []
    fenced = False
    blank = 0
    for line in out:
        if _FENCE.match(line):
            fenced = not fenced
        if not fenced and not line.strip():
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        result.append(line)

    trimmed = "\n".join(result).strip()
    return trimmed + "\n" if trimmed else ""


def _compact_table_line(line: str) -> str:
    cells = _CELL_SPLIT.split(line)
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    compact = []
    for cell in cells:
        c = re.sub(r"\s+", " ", cell).strip()
        if _SEPARATOR_CELL.match(c):
            c = (":" if c.startswith(":") else "") + "---" + (":" if c.endswith(":") else "")
        compact.append(c)
    return "| " + " | ".join(compact) + " |"


def bundle_markdown(items: list[tuple[str, str]]) -> str:
    """Join several documents into one Markdown text, each under a '# File: name' heading."""
    parts = [f"# File: {name}\n\n{md.strip()}" for name, md in items]
    return "\n\n---\n\n".join(parts) + "\n"
