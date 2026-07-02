from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_APP = "main:app"


def _default_app_dir() -> str:
    backend_root = Path(__file__).resolve().parents[2]
    source_dir = backend_root / "src"
    return str(source_dir if source_dir.exists() else Path("src"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the WoSB FastAPI backend for local development.")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host to bind to. Default: {DEFAULT_HOST}")
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        type=int,
        help=f"Port to bind to. Default: {DEFAULT_PORT}",
    )
    parser.add_argument(
        "--app",
        default=DEFAULT_APP,
        help=f"ASGI app import string. Default: {DEFAULT_APP}",
    )
    parser.add_argument(
        "--app-dir",
        default=_default_app_dir(),
        help="Directory containing the ASGI app module. Defaults to the backend src directory.",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload. Reload is enabled by default for development.",
    )
    args = parser.parse_args()

    uvicorn.run(
        args.app,
        app_dir=args.app_dir,
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
    )


if __name__ == "__main__":
    main()
