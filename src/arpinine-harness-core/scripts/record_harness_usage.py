#!/usr/bin/env python3
"""Append a governed Arpinine Harness usage-cost record."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from measurement_artifacts import resolve_host, write_harness_usage_run


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


def read_json(path: pathlib.Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Harness usage payload must be a JSON object")
    return payload


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Record a harness usage telemetry event")
    parser.add_argument("--input", required=True, help="Path to a JSON file containing one usage record")
    parser.add_argument("--session-id", help="Optional session id used to partition history")
    args = parser.parse_args(argv)

    repo = find_project_root(pathlib.Path.cwd())
    if repo is None:
        print("Run record_harness_usage.py from the project root directory", file=sys.stderr)
        return 1

    payload = read_json(pathlib.Path(args.input))
    # Default host attribution to the canonical team id when the caller omits it,
    # keeping manual records consistent with hook-recorded ones.
    if not payload.get("host"):
        payload["host"] = resolve_host()
    write_harness_usage_run(repo, payload, session_id=args.session_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
