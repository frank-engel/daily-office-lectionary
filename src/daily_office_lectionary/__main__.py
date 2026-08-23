"""Command-line interface: `python -m daily_office_lectionary` or the
`daily-office-lectionary` console script."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import asdict
from datetime import date

from . import BibleNotInstalledError, get_readings, get_readings_with_text
from .bible.fetch import fetch_bible


def _cmd_fetch_bible(args: argparse.Namespace) -> int:
    path = fetch_bible(translation=args.translation, force=args.force)
    print(f"Bible database ready at {path}")
    return 0


def _cmd_readings(args: argparse.Namespace) -> int:
    when = args.date or date.today().isoformat()
    try:
        readings = get_readings_with_text(when) if args.full else get_readings(when)
    except BibleNotInstalledError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if readings is None:
        print(f"No Daily Office entry found for {when}", file=sys.stderr)
        return 1
    if args.json:
        import json

        print(json.dumps(asdict(readings), indent=2, ensure_ascii=False))
    else:
        print(readings)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    # Reference strings and BCP text contain en-dashes and other non-ASCII
    # characters; a default Windows console (cp1252) would otherwise crash
    # with UnicodeEncodeError as soon as one is printed.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(prog="daily-office-lectionary")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch_p = sub.add_parser(
        "fetch-bible", help="Download the public-domain KJVA Bible database for full mode"
    )
    fetch_p.add_argument("--translation", default="kjva")
    fetch_p.add_argument("--force", action="store_true", help="Re-download even if already cached")
    fetch_p.set_defaults(func=_cmd_fetch_bible)

    readings_p = sub.add_parser("readings", help="Print the Daily Office readings for a date")
    readings_p.add_argument("date", nargs="?", default=None, help="YYYY-MM-DD (default: today)")
    readings_p.add_argument("--full", action="store_true", help="Include full scripture verse text")
    readings_p.add_argument("--json", action="store_true", help="Print as JSON")
    readings_p.set_defaults(func=_cmd_readings)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
