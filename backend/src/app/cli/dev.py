import argparse

import uvicorn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the Blackwater Mercenaries Hub backend in development mode.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-reload", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    uvicorn.run(
        "main:app",
        app_dir="src",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
    )
