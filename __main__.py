"""Entry point: python3 -m webgen --serve [--port 8770]."""

import argparse

from .server import serve


def main() -> None:
    ap = argparse.ArgumentParser(prog="webgen", description="Website generator")
    ap.add_argument("--serve", action="store_true", help="run the local web UI")
    ap.add_argument("--port", type=int, default=8770)
    args = ap.parse_args()

    if args.serve:
        serve(args.port)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
