from __future__ import annotations

import argparse
import json
from typing import Any

from .config import ObsidianSettings
from .obsidian import ObsidianClient, ObsidianError


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


def _print(value: Any) -> None:
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        print(value)


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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        client, settings = _client()

        if args.area == "obsidian" and args.command == "bootstrap-ca":
            path = client.bootstrap_ca(settings.ca_cert)
            print(f"Saved local Obsidian CA certificate to: {path}")
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

        parser.error("Unsupported command.")
    except ObsidianError as exc:
        print(f"Atlas error: {exc}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
