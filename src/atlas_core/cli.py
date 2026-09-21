from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .config import ObsidianSettings
from .obsidian import ObsidianClient, ObsidianError
from .organizer import ShadowOrganizer, render_summary, write_local_report


def _client() -> tuple[ObsidianClient, ObsidianSettings]:
    settings = ObsidianSettings.from_env()
    return (
        ObsidianClient(
            base_url=settings.base_url,
            api_key=settings.api_key,
            ca_cert=settings.ca_cert,
        ),
        settings,
    )


def _console_safe_text(text: str, encoding: str | None = None) -> str:
    encoding = encoding or getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return text
    except (LookupError, UnicodeEncodeError):
        pass

    safe: list[str] = []
    for char in text:
        try:
            char.encode(encoding)
            safe.append(char)
        except UnicodeEncodeError:
            # JSON-style escaping stays ASCII-safe and keeps structured output valid.
            safe.append(json.dumps(char, ensure_ascii=True)[1:-1])
    return "".join(safe)


def _print(value: Any) -> None:
    if isinstance(value, (dict, list)):
        rendered = json.dumps(value, ensure_ascii=False, indent=2)
    else:
        rendered = str(value)
    sys.stdout.write(_console_safe_text(rendered) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas")
    top = parser.add_subparsers(dest="area", required=True)

    obsidian = top.add_parser("obsidian", help="Read-only Obsidian integration")
    commands = obsidian.add_subparsers(dest="command", required=True)

    commands.add_parser("bootstrap-ca", help="Trust the local Obsidian CA for Atlas")
    commands.add_parser("status", help="Check whether the local API is running")

    list_parser = commands.add_parser("list", help="List a vault directory")
    list_parser.add_argument("path", nargs="?", default="")

    search_parser = commands.add_parser("search", help="Search existing notes")
    search_parser.add_argument("query")

    read_parser = commands.add_parser("read", help="Read an existing note")
    read_parser.add_argument("path")

    organize = top.add_parser(
        "organize",
        help="Analyze the vault and propose knowledge organization without editing it",
    )
    organize.add_argument(
        "--shadow",
        action="store_true",
        required=True,
        help="Required safety flag: analyze only; never change Obsidian",
    )
    organize.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of notes to scan",
    )
    organize.add_argument(
        "--output",
        default=".local/atlas-shadow-report.json",
        help="Local gitignored JSON report path",
    )
    organize.add_argument(
        "--json",
        action="store_true",
        help="Print the full JSON report instead of the concise summary",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        client, settings = _client()

        if args.area == "obsidian" and args.command == "bootstrap-ca":
            path = client.bootstrap_ca(settings.ca_cert)
            _print(f"Saved local Obsidian CA certificate to: {path}")
            return 0
        if args.area == "obsidian" and args.command == "status":
            _print(client.status())
            return 0
        if args.area == "obsidian" and args.command == "list":
            _print(client.list_files(args.path))
            return 0
        if args.area == "obsidian" and args.command == "search":
            _print(client.search(args.query))
            return 0
        if args.area == "obsidian" and args.command == "read":
            _print(client.read_note(args.path))
            return 0
        if args.area == "organize":
            report = ShadowOrganizer(client).scan(limit=args.limit)
            write_local_report(report, args.output)
            if args.json:
                _print(report)
            else:
                _print(render_summary(report))
                _print(f"Local report: {args.output}")
            return 0

        parser.error("Unsupported command.")
    except ObsidianError as exc:
        _print(f"Atlas error: {exc}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
