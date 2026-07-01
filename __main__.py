"""Entry point: python3 -m webgen --serve [--port 8770]."""

import argparse

from .server import serve


def main() -> None:
    ap = argparse.ArgumentParser(prog="webgen", description="Website generator")
    ap.add_argument("--serve", action="store_true", help="run the local web UI")
    ap.add_argument("--port", type=int, default=8770)
    ap.add_argument("--worker", action="store_true",
                    help="run the generation worker (consumes captured leads)")
    ap.add_argument("--once", action="store_true",
                    help="worker: do a single pass then exit")
    ap.add_argument("--interval", type=float, default=10.0,
                    help="worker: seconds between polls (default 10)")
    args = ap.parse_args()

    if args.serve:
        serve(args.port)
    elif args.worker:
        from .worker import run
        run(interval=args.interval, once=args.once)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
