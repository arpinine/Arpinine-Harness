#!/usr/bin/env python3
"""
compression_config.py — read/write the governed context-compression toggle.

The toggle lives in `.specify/CONSTITUTION.md` (ADR-0016: the constitution is the
single, auditable, governed home for the decision). It is stored in a marked,
machine-readable block so check scripts and the composition root can read it
deterministically:

    ## Context Compression
    <!-- arpinine:compression -->
    Enabled: false
    NetworkRestrictionAck: false
    <!-- /arpinine:compression -->

Invariants (ADR-0016):
  - Absent block (or absent constitution) reads as DISABLED.
  - The block records only flags (enabled, residual-risk ack), never a provider class.
  - Writing is idempotent: a single block is maintained.

Governs: specs/011-context-compression-governance (TASK-004).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

OPEN_MARKER = "<!-- arpinine:compression -->"
CLOSE_MARKER = "<!-- /arpinine:compression -->"
SECTION_HEADING = "## Context Compression"

_BLOCK_RE = re.compile(
    re.escape(OPEN_MARKER) + r"(.*?)" + re.escape(CLOSE_MARKER),
    re.DOTALL,
)


def _constitution_path(repo_root: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(repo_root) / ".specify" / "CONSTITUTION.md"


def _read_block(repo_root: pathlib.Path) -> str | None:
    path = _constitution_path(repo_root)
    if not path.exists():
        return None
    match = _BLOCK_RE.search(path.read_text())
    return match.group(1) if match else None


def _flag(block: str | None, key: str) -> bool:
    if block is None:
        return False
    m = re.search(rf"^{re.escape(key)}:\s*(true|false)\s*$", block, re.MULTILINE | re.IGNORECASE)
    return bool(m) and m.group(1).lower() == "true"


def read_compression_enabled(repo_root: pathlib.Path | str) -> bool:
    """True only if the constitution block explicitly enables compression."""
    return _flag(_read_block(pathlib.Path(repo_root)), "Enabled")


def read_network_restriction_ack(repo_root: pathlib.Path | str) -> bool:
    """True if the operator acknowledged the network-restriction residual risk."""
    return _flag(_read_block(pathlib.Path(repo_root)), "NetworkRestrictionAck")


def _render_block(enabled: bool, network_restriction_ack: bool) -> str:
    return (
        f"{SECTION_HEADING}\n"
        f"{OPEN_MARKER}\n"
        f"Enabled: {'true' if enabled else 'false'}\n"
        f"NetworkRestrictionAck: {'true' if network_restriction_ack else 'false'}\n"
        f"{CLOSE_MARKER}\n"
    )


def set_compression_enabled(
    repo_root: pathlib.Path | str,
    enabled: bool,
    network_restriction_ack: bool = False,
) -> None:
    """
    Record the compression toggle in the constitution. Idempotent: replaces the
    existing marked block, or appends a new section if none exists. Preserves all
    other constitution content.
    """
    path = _constitution_path(pathlib.Path(repo_root))
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text() if path.exists() else "# Project Constitution\n"
    block_body = (
        f"{OPEN_MARKER}\n"
        f"Enabled: {'true' if enabled else 'false'}\n"
        f"NetworkRestrictionAck: {'true' if network_restriction_ack else 'false'}\n"
        f"{CLOSE_MARKER}"
    )
    if _BLOCK_RE.search(existing):
        new_text = _BLOCK_RE.sub(lambda _m: block_body, existing)
    else:
        sep = "" if existing.endswith("\n") else "\n"
        new_text = f"{existing}{sep}\n{_render_block(enabled, network_restriction_ack)}"
    path.write_text(new_text)


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Read/write the compression toggle.")
    parser.add_argument("--repo", default=".", help="project root")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("get", help="print the toggle state as JSON")
    set_p = sub.add_parser("set", help="set the toggle")
    set_p.add_argument("--enabled", choices=["true", "false"], required=True)
    set_p.add_argument("--network-restriction-ack", choices=["true", "false"], default="false")
    args = parser.parse_args(argv)

    repo = pathlib.Path(args.repo)
    if args.cmd == "get":
        print(
            json.dumps(
                {
                    "enabled": read_compression_enabled(repo),
                    "network_restriction_ack": read_network_restriction_ack(repo),
                }
            )
        )
        return 0
    set_compression_enabled(
        repo,
        args.enabled == "true",
        network_restriction_ack=args.network_restriction_ack == "true",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
