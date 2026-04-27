#!/usr/bin/env python3
"""Validate Arpinine Harness runtime dependencies."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


def command_status(label: str, cmd: str, required: bool) -> dict[str, object]:
    return {
        "label": label,
        "command": cmd,
        "required": required,
        "available": shutil.which(cmd) is not None,
    }


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def parse_framework(eval_plan: pathlib.Path) -> str:
    text = read_text(eval_plan)
    if not text:
        return ""

    match = re.search(r"^- Framework:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    table_match = re.search(
        r"^\|\s*\[[^\]]+\]\s*\|\s*\[[^\]]+\]\s*\|\s*\[[^\]]+\]\s*\|\s*([^\|]+?)\s*\|",
        text,
        re.MULTILINE,
    )
    return table_match.group(1).strip() if table_match else ""


def spec_checks(repo: pathlib.Path, spec_root: pathlib.Path, eval_root: pathlib.Path) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    if not spec_root.exists():
        return results

    for plan in sorted(spec_root.glob("*/plan.md")):
        slug = plan.parent.name
        plan_text = read_text(plan)
        checks: list[dict[str, object]] = []

        if "## Harness Strategy" in plan_text and re.search(r"openharness", plan_text, re.IGNORECASE):
            checks.append(command_status("Node.js for OpenHarness workflows", "node", False))
            checks.append(command_status("npm for OpenHarness workflows", "npm", False))

        eval_plan = eval_root / slug / "eval-plan.md"
        framework = parse_framework(eval_plan) if eval_plan.exists() else ""
        if framework:
            checks.append(
                {
                    "label": "Declared evaluation framework",
                    "command": framework,
                    "required": False,
                    "available": True,
                }
            )

        eval_text = read_text(eval_plan)
        if re.search(r"deepeval", eval_text, re.IGNORECASE):
            checks.append(command_status("DeepEval CLI/runtime", "deepeval", False))
        if re.search(r"pytest", eval_text, re.IGNORECASE):
            checks.append(command_status("pytest", "pytest", False))

        if checks:
            results.append({"spec": slug, "checks": checks})

    return results


def build_report() -> dict[str, object]:
    repo = find_project_root(pathlib.Path.cwd())
    global_checks = [
        command_status("spec-kit CLI", "specify", True),
        command_status("Python", "python3", True),
        command_status("uv/uvx", "uvx", False),
        command_status("Node.js", "node", False),
        command_status("npm", "npm", False),
        command_status("OpenHarness-ready JS toolchain", "npx", False),
    ]
    report = {
        "summary": {
            "blocking": [
                item["label"] for item in global_checks if item["required"] and not item["available"]
            ],
            "root_found": bool(repo),
        },
        "global": global_checks,
        "specs": [],
        "guidance": [
            "spec-kit is required for automated /at-* generation flows.",
            "Harness and eval dependencies are required only if selected in plan/eval artifacts.",
            "Arpinine Harness validates dependencies; it does not install them during plugin installation.",
        ],
    }
    if repo:
        spec_root = repo / ".specify" / "specs"
        eval_root = repo / ".specify" / "evals"
        report["specs"] = spec_checks(repo, spec_root, eval_root)
    else:
        report["summary"]["warning"] = "Run this command from the project root directory."
    return report


def render_text(report: dict[str, object]) -> str:
    lines = [
        "AGENTALIGN DEPENDENCY CHECK",
        "---------------------------",
    ]

    for item in report["global"]:
        status = "OK" if item["available"] else "MISSING"
        requirement = "required" if item["required"] else "optional"
        lines.append(f"{status:<7} {item['label']} ({item['command']} found={str(item['available']).lower()}) [{requirement}]")

    spec_entries = report.get("specs", [])
    if spec_entries:
        lines.extend(["", "SPEC-SCOPED CHECKS", "------------------"])
        for entry in spec_entries:
            lines.append(f"Spec: {entry['spec']}")
            for item in entry["checks"]:
                status = "OK" if item["available"] else "MISSING"
                requirement = "required" if item["required"] else "optional"
                lines.append(
                    f"  {status:<7} {item['label']} ({item['command']}) [{requirement}]"
                )

    if report["summary"]["blocking"]:
        lines.extend(["", "Blocking issues:"])
        for item in report["summary"]["blocking"]:
            lines.append(f"- {item}")

    lines.extend(["", "Guidance:"])
    lines.extend(f"- {line}" for line in report["guidance"])
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    report = build_report()
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
