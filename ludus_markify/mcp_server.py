"""MCP server: lets an AI tool (Claude Code, Claude Desktop) convert local files to Markdown.

Run: ludus-markify mcp      Needs the optional extra: pip install "ludus-markify[mcp]"
Everything runs on this computer. The AI tool receives Markdown text instead of a binary file.
"""
from pathlib import Path

from .aiprep import bundle_markdown, trim_for_ai
from .conversion import convert_file
from .models import InputFile, Status


def convert_paths(paths: list[str], trim: bool = True) -> str:
    """Convert local files to Markdown and return the text. Failed files are listed at the end."""
    done: list[tuple[str, str]] = []
    failed: list[str] = []
    for raw in paths:
        p = Path(raw).expanduser()
        if not p.is_file():
            failed.append(f"{raw}: file not found")
            continue
        result = convert_file(InputFile(name=p.name, content=p.read_bytes()))
        if result.status != Status.ok:
            failed.append(f"{p.name}: {result.error}")
            continue
        done.append((p.name, trim_for_ai(result.markdown) if trim else result.markdown))

    if len(done) == 1 and not failed:
        return done[0][1]
    text = bundle_markdown(done) if done else ""
    if failed:
        text += "\nCould not convert:\n" + "\n".join(f"- {f}" for f in failed) + "\n"
    return text


def run() -> None:
    try:
        try:
            from mcp.server.mcpserver import MCPServer as Server  # mcp 2.x
        except ImportError:
            from mcp.server.fastmcp import FastMCP as Server  # mcp 1.x
    except ImportError:
        raise SystemExit('The MCP server needs an extra package. Install it: pip install "ludus-markify[mcp]"')

    server = Server("ludus-markify")

    @server.tool()
    def convert_to_markdown(paths: list[str], trim: bool = True) -> str:
        """Convert local documents (PDF, Word, Excel, PowerPoint, HTML, images) to compact Markdown.

        Use this instead of reading a binary file directly: the text is far smaller in tokens.
        `paths` are file paths on this computer. Several files come back as one text with
        '# File: name' headings. `trim` removes repeated headers, page numbers and embedded images.
        """
        return convert_paths(paths, trim)

    server.run()
