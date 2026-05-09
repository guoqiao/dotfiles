#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "furl>=2.1.4",
# ]
# ///
"""Simple CLI to inspect parts of a URL using the furl library.

Prints:
- Scheme
- Domain (host)
- Port (explicit or default for scheme)
- Args (query parameters) as key/value list

Example:
    url-spliter.py "https://foo.bar.com:8443/path?a=1&a=2&b=x"
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Optional

from furl import furl


DEFAULT_PORTS: Dict[str, int] = {
    "http": 80,
    "https": 443,
    "ftp": 21,
}


def _effective_port(url_scheme: Optional[str], explicit_port: Optional[int]) -> Optional[int]:
    if explicit_port is not None:
        return explicit_port
    if not url_scheme:
        return None
    return DEFAULT_PORTS.get(url_scheme.lower())


def _collect_query_args(parsed: "furl") -> Dict[str, List[str]]:
    # Preserve duplicate keys by aggregating values into lists
    aggregated: Dict[str, List[str]] = {}
    for key, value in parsed.query.params.allitems():
        aggregated.setdefault(key, []).append(value)
    return aggregated


def _print_human_output(url: str) -> None:
    parsed = furl(url)

    scheme = parsed.scheme or ""
    host = parsed.host or ""
    port = _effective_port(scheme, parsed.port)
    args_map = _collect_query_args(parsed)

    print(f"Scheme: {scheme or '-'}")
    print(f"Domain: {host or '-'}")
    print(f"Port: {port if port is not None else '-'}")
    print("Args:")
    if not args_map:
        print("  (none)")
    else:
        for key in sorted(args_map.keys()):
            values = args_map[key]
            if len(values) == 1:
                print(f"  {key}: {json.dumps(values[0], ensure_ascii=False)}")
            else:
                print(f"  {key}: {json.dumps(values, ensure_ascii=False)}")


def _read_url_from_stdin_if_piped() -> Optional[str]:
    if sys.stdin and not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            # Use first non-empty line
            for line in data.splitlines():
                candidate = line.strip()
                if candidate:
                    return candidate
    return None


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect parts of a URL (scheme, domain, port, args) using furl",
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="The URL to parse (if omitted and input is piped, read from stdin)",
    )
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    url: Optional[str] = args.url
    if not url:
        url = _read_url_from_stdin_if_piped()

    if not url:
        parser.error("a URL is required (provide as an argument or via stdin)")
        return

    _print_human_output(url)


if __name__ == "__main__":
    main()

