"""Command line entry point: `ludus-markify` starts the local app and opens the browser."""
import argparse
import os
import socket
import sys
import threading
import webbrowser


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) != 0


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "convert":
        raise SystemExit(convert_command(argv[1:]))
    if argv and argv[0] == "mcp":
        from .mcp_server import run
        run()
        return
    serve(argv)


def convert_command(argv: list[str]) -> int:
    """`ludus-markify convert FILE...`: print Markdown to stdout, or save with -o. Returns an exit code."""
    from pathlib import Path

    from .aiprep import bundle_markdown, estimate_tokens, trim_for_ai
    from .conversion import convert_file
    from .filesystem import resolve_output_dir, save_markdown
    from .models import InputFile, Status, UserError

    parser = argparse.ArgumentParser(prog="ludus-markify convert", description="Convert files to Markdown.")
    parser.add_argument("files", nargs="+", help="files to convert")
    parser.add_argument("-o", "--output", metavar="FOLDER", help="save .md files here instead of printing")
    parser.add_argument("--trim", action="store_true", help="remove repeated headers, page numbers and embedded images")
    parser.add_argument("--bundle", action="store_true", help="with -o: save one combined file")
    parser.add_argument("--tokens", action="store_true", help="print an estimated token count to stderr")
    args = parser.parse_args(argv)

    out_dir = None
    if args.output:
        try:
            out_dir = resolve_output_dir(args.output)
        except UserError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    done: list[tuple[str, str]] = []
    failed = 0
    for raw in args.files:
        p = Path(raw).expanduser()
        if not p.is_file():
            print(f"{raw}: file not found", file=sys.stderr)
            failed += 1
            continue
        result = convert_file(InputFile(name=p.name, content=p.read_bytes()))
        if result.status != Status.ok:
            print(f"{p.name}: could not convert. {result.error}", file=sys.stderr)
            failed += 1
            continue
        done.append((p.name, trim_for_ai(result.markdown) if args.trim else result.markdown))

    if out_dir is not None and not args.bundle:
        for name, md in done:
            print(save_markdown(md, name, out_dir))
    else:
        text = done[0][1] if len(done) == 1 else bundle_markdown(done) if done else ""
        if out_dir is not None and text:
            print(save_markdown(text, "combined.md", out_dir))
        else:
            sys.stdout.write(text)
        if args.tokens:
            print(f"≈ {estimate_tokens(text):,} tokens", file=sys.stderr)
    return 1 if failed else 0


def serve(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="ludus-markify", description="Convert documents to Markdown locally. Other commands: convert, mcp.")
    parser.add_argument("--port", type=int, default=8000, help="port to listen on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser")
    args = parser.parse_args(argv)

    host = "127.0.0.1"  # local only: never expose the app to the network
    if not _port_free(host, args.port):
        raise SystemExit(f"Port {args.port} is already in use. Try: ludus-markify --port {args.port + 1}")

    # Must be set before the server module is imported.
    os.environ["LUDUS_MARKIFY_PORT"] = str(args.port)

    import uvicorn

    from .server import app, _find_frontend

    if _find_frontend() is None:
        raise SystemExit("Frontend not found. Build it first: ./scripts/build.sh")

    url = f"http://{host}:{args.port}"
    print(f"Ludus Markify running at {url}\nPress Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    uvicorn.run(app, host=host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
