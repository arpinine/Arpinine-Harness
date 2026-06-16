#!/usr/bin/env python3
"""Aggregate governed observation telemetry into a token and cost report.

Reads immutable observation history under
`.specify/observations/<slug>/history/**/*.json`, groups token consumption by
model, and summarizes total cost at the moment of invocation. Arpinine Harness
governs the presence of this telemetry but never synthesizes missing runtime
numbers: runs without `cost_usd`/token fields are reported as incomplete.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from measurement_artifacts import observation_paths


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


def read_json(path: pathlib.Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def discover_slugs(repo: pathlib.Path) -> list[str]:
    root = repo / ".specify" / "observations"
    if not root.exists():
        return []
    return sorted(child.name for child in root.iterdir() if child.is_dir())


def load_observation_runs(repo: pathlib.Path, slug: str) -> list[dict]:
    """Read full observation records (history snapshots, falling back to the latest trace)."""
    paths = observation_paths(repo, slug)
    runs: list[dict] = []
    history = paths["history"]
    if history.exists():
        for path in sorted(history.rglob("*.json")):
            record = read_json(path)
            if record is not None:
                runs.append(record)
    if not runs:
        # Lightweight projects may only keep the latest trace, no history.
        record = read_json(paths["latest_trace"])
        if record is not None:
            runs.append(record)
    return runs


def model_label(record: dict) -> str:
    name = record.get("model_name") or "unknown-model"
    version = record.get("model_version")
    return f"{name}@{version}" if version else str(name)


def _num(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def aggregate_costs(repo: pathlib.Path, slugs: list[str]) -> dict:
    by_model: dict[str, dict] = {}
    incomplete_runs = 0
    total_runs = 0

    for slug in slugs:
        for record in load_observation_runs(repo, slug):
            total_runs += 1
            has_cost = record.get("cost_usd") is not None
            has_tokens = record.get("token_count_input") is not None or record.get("token_count_output") is not None
            # A run is measured only when BOTH token and cost telemetry are present.
            # Counting a tokens-only run would silently roll a 0.0 cost into totals and
            # under-report real spend, so partial runs are excluded, not synthesized.
            if not (has_cost and has_tokens):
                incomplete_runs += 1
                continue
            label = model_label(record)
            bucket = by_model.setdefault(
                label,
                {
                    "model_name": record.get("model_name") or "unknown-model",
                    "model_version": record.get("model_version"),
                    "runs": 0,
                    "token_count_input": 0,
                    "token_count_output": 0,
                    "cost_usd": 0.0,
                    "cost_known": has_cost,
                },
            )
            bucket["runs"] += 1
            bucket["token_count_input"] += int(_num(record.get("token_count_input")))
            bucket["token_count_output"] += int(_num(record.get("token_count_output")))
            bucket["cost_usd"] += _num(record.get("cost_usd"))
            bucket["cost_known"] = bucket["cost_known"] or has_cost

    models = sorted(by_model.values(), key=lambda item: item["cost_usd"], reverse=True)
    total_cost = sum(item["cost_usd"] for item in models)
    total_in = sum(item["token_count_input"] for item in models)
    total_out = sum(item["token_count_output"] for item in models)
    return {
        "slugs": slugs,
        "models": models,
        "total_runs": total_runs,
        "measured_runs": total_runs - incomplete_runs,
        "incomplete_runs": incomplete_runs,
        "total_cost_usd": round(total_cost, 6),
        "total_token_input": total_in,
        "total_token_output": total_out,
        "total_tokens": total_in + total_out,
    }


def render_report(report: dict) -> str:
    width = 72
    bar = "━" * width
    lines = [bar, "TOKEN & COST REPORT", bar]
    scope = ", ".join(report["slugs"]) if report["slugs"] else "(no observation data found)"
    lines.append(f"Scope: {scope}")
    lines.append(f"Runs measured: {report['measured_runs']}/{report['total_runs']}")
    if report["incomplete_runs"]:
        lines.append(f"⚠ {report['incomplete_runs']} run(s) lack token/cost telemetry — excluded from totals")
    lines.append(bar)
    lines.append(f"{'Model':<34}{'Runs':>6}{'Tokens in':>14}{'Tokens out':>14}{'Cost USD':>14}".rstrip())
    lines.append("-" * width)
    for item in report["models"]:
        cost = f"${item['cost_usd']:.4f}" if item["cost_known"] else "n/a"
        label = model_label(item)
        lines.append(
            f"{label[:33]:<34}{item['runs']:>6}{item['token_count_input']:>14,}{item['token_count_output']:>14,}{cost:>14}"
        )
    if not report["models"]:
        lines.append("(no runs with token or cost telemetry recorded yet)")
    lines.append("-" * width)
    lines.append(
        f"{'TOTAL':<34}{report['measured_runs']:>6}{report['total_token_input']:>14,}"
        f"{report['total_token_output']:>14,}{('$' + format(report['total_cost_usd'], '.4f')):>14}"
    )
    lines.append(bar)
    lines.append(f"Total tokens: {report['total_tokens']:,}    Total cost: ${report['total_cost_usd']:.4f}")
    lines.append(bar)
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Report token consumption and cost from observation telemetry")
    parser.add_argument("--slug", help="Limit the report to one spec slug under .specify/observations/")
    parser.add_argument("--json", action="store_true", help="Emit aggregate JSON instead of a rendered table")
    args = parser.parse_args(argv)

    repo = find_project_root(pathlib.Path.cwd())
    if repo is None:
        print("Run report_costs.py from the project root directory", file=sys.stderr)
        return 1

    slugs = [args.slug] if args.slug else discover_slugs(repo)
    report = aggregate_costs(repo, slugs)

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(render_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
