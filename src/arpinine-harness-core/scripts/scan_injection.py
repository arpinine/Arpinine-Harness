#!/usr/bin/env python3
"""Scan .specify/ files for prompt injection patterns."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


INJECTION_PATTERNS = [
    # Direct instruction override attempts
    (re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE), "instruction override"),
    (re.compile(r"ignore\s+(all\s+)?prior\s+instructions", re.IGNORECASE), "instruction override"),
    (re.compile(r"disregard\s+(all\s+)?(previous|prior|above)", re.IGNORECASE), "instruction override"),
    (re.compile(r"forget\s+(all\s+)?(previous|prior|everything)", re.IGNORECASE), "instruction override"),
    (re.compile(r"your\s+new\s+(instruction|task|role|objective)", re.IGNORECASE), "instruction override"),
    (re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE), "role switching"),
    (re.compile(r"act\s+as\s+(if\s+you\s+are|a)\b", re.IGNORECASE), "role switching"),
    (re.compile(r"pretend\s+(you\s+are|to\s+be)", re.IGNORECASE), "role switching"),
    # System prompt manipulation
    (re.compile(r"<\s*system\s*>", re.IGNORECASE), "system tag injection"),
    (re.compile(r"\bsystem\s*:\s*you\s+are\b", re.IGNORECASE), "system prompt injection"),
    (re.compile(r"\[SYSTEM\]"), "system tag injection"),
    (re.compile(r"<\s*\|im_start\|>"), "chat template injection"),
    (re.compile(r"<\s*\|im_end\|>"), "chat template injection"),
    # Data exfiltration attempts
    (re.compile(r"output\s+(the\s+)?(contents?|text|data)\s+of\s+", re.IGNORECASE), "data exfiltration"),
    (re.compile(r"(read|cat|print|show|display)\s+.*(\.env|\.ssh|id_rsa|credentials|secrets)", re.IGNORECASE), "data exfiltration"),
    (re.compile(r"send\s+(this|the|all)\s+.*(to|via)\s+(http|url|webhook|endpoint)", re.IGNORECASE), "data exfiltration"),
    # Instruction boundary breaks
    (re.compile(r"---+\s*END\s+(OF\s+)?(SYSTEM|INSTRUCTIONS?)", re.IGNORECASE), "boundary break"),
    (re.compile(r"###\s*(HUMAN|USER|ASSISTANT)\s*:"), "boundary break"),
]

SCANNABLE_EXTENSIONS = {".md", ".json", ".yaml", ".yml"}

MAX_MATCH_DISPLAY = 80


def find_project_root(start: pathlib.Path) -> pathlib.Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists():
            return candidate
    return pathlib.Path(".").resolve()


def truncate(text: str, length: int = MAX_MATCH_DISPLAY) -> str:
    text = text.strip()
    if len(text) <= length:
        return text
    return text[:length] + "..."


def scan_file(path: pathlib.Path) -> list[dict]:
    """Scan a single file for injection patterns. Return findings."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    findings: list[dict] = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        for pattern, label in INJECTION_PATTERNS:
            match = pattern.search(line)
            if match:
                findings.append({
                    "file": str(path),
                    "line": line_num,
                    "pattern": label,
                    "match": truncate(match.group(0)),
                })
    return findings


def scan_directory(directory: pathlib.Path) -> list[dict]:
    """Scan all scannable files in a directory recursively."""
    findings: list[dict] = []
    if not directory.is_dir():
        return findings
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix in SCANNABLE_EXTENSIONS:
            findings.extend(scan_file(path))
    return findings


def read_stdin_payload() -> str:
    """Read hook payload from stdin, extract file_path."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return ""
    tool_input = payload.get("tool_input", {})
    return str(tool_input.get("file_path", ""))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Scan .specify/ files for prompt injection patterns.",
    )
    parser.add_argument("--path", help="Directory to scan")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args, _ = parser.parse_known_args(argv)

    if args.path:
        findings = scan_directory(pathlib.Path(args.path))
    else:
        file_path = read_stdin_payload()
        repo = find_project_root(pathlib.Path.cwd())
        specify_dir = repo / ".specify"
        if not specify_dir.exists():
            return 0

        findings = scan_directory(specify_dir)

        # Also scan the specific file if it lives inside .specify/
        if file_path:
            target = pathlib.Path(file_path)
            if target.is_file() and target.suffix in SCANNABLE_EXTENSIONS:
                try:
                    if specify_dir.resolve() in target.resolve().parents:
                        # Already covered by the directory scan above
                        pass
                    else:
                        findings.extend(scan_file(target))
                except Exception:
                    pass

    if not findings:
        return 0

    if args.json:
        json.dump(findings, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print("SECURITY WARNING: Potential prompt injection detected in .specify/ files:")
        for f in findings:
            print(f"  {f['file']}:{f['line']} — {f['pattern']}: ...{truncate(f['match'])}...")
        print("Review these files before proceeding. Possible embedded AI directives found.")

    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
