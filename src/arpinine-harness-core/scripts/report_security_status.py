#!/usr/bin/env python3
"""Generate security health report for /at-status."""

from __future__ import annotations

import json
import pathlib
import sys

from security_tooling import (
    find_project_root,
    format_status_report,
)


def main() -> int:
    repo = find_project_root(pathlib.Path.cwd())
    if not (repo / ".specify").exists():
        return 0

    report = format_status_report(repo)
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
