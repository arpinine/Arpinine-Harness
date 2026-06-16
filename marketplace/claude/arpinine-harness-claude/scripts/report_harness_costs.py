#!/usr/bin/env python3
"""Aggregate Arpinine Harness delivery-cost telemetry into a governed report."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from measurement_artifacts import harness_usage_paths


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


def read_jsonl(path: pathlib.Path) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    records: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def load_usage_runs(repo: pathlib.Path) -> list[dict]:
    paths = harness_usage_paths(repo)
    index = paths["index"]
    if not index.exists():
        return []
    return read_jsonl(index)


def _num(value: object) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _add_bucket(buckets: dict[str, dict], label: str, record: dict) -> None:
    bucket = buckets.setdefault(
        label,
        {
            "label": label,
            "runs": 0,
            "token_count_input": 0,
            "token_count_output": 0,
            "cost_usd": 0.0,
        },
    )
    bucket["runs"] += 1
    bucket["token_count_input"] += int(_num(record.get("token_count_input")))
    bucket["token_count_output"] += int(_num(record.get("token_count_output")))
    bucket["cost_usd"] += _num(record.get("cost_usd"))


def aggregate_harness_costs(repo: pathlib.Path, slug: str | None = None) -> dict:
    by_model: dict[str, dict] = {}
    by_command: dict[str, dict] = {}
    by_host: dict[str, dict] = {}
    incomplete_runs = 0
    total_runs = 0
    scope_labels: set[str] = set()

    for record in load_usage_runs(repo):
        spec_slug = str(record.get("spec_slug") or "")
        if slug and spec_slug != slug:
            continue
        total_runs += 1
        if spec_slug:
            scope_labels.add(spec_slug)
        has_cost = record.get("cost_usd") is not None
        has_tokens = record.get("token_count_input") is not None or record.get("token_count_output") is not None
        if not (has_cost and has_tokens):
            incomplete_runs += 1
            continue

        model_name = str(record.get("model_name") or "unknown-model")
        model_version = record.get("model_version")
        model_label = f"{model_name}@{model_version}" if model_version else model_name
        command_label = str(record.get("command") or "unknown-command")
        host_label = str(record.get("host") or "unknown-host")

        _add_bucket(by_model, model_label, record)
        _add_bucket(by_command, command_label, record)
        _add_bucket(by_host, host_label, record)

    def ordered(values: dict[str, dict]) -> list[dict]:
        return sorted(values.values(), key=lambda item: (item["cost_usd"], item["runs"]), reverse=True)

    models = ordered(by_model)
    commands = ordered(by_command)
    hosts = ordered(by_host)
    total_cost = sum(item["cost_usd"] for item in models)
    total_in = sum(item["token_count_input"] for item in models)
    total_out = sum(item["token_count_output"] for item in models)

    if slug:
        scopes = [slug]
    else:
        scopes = sorted(scope_labels)
    if not scopes and not slug and total_runs == 0:
        scopes = []

    return {
        "scope": scopes,
        "models": models,
        "commands": commands,
        "hosts": hosts,
        "total_runs": total_runs,
        "measured_runs": total_runs - incomplete_runs,
        "incomplete_runs": incomplete_runs,
        "total_cost_usd": round(total_cost, 6),
        "total_token_input": total_in,
        "total_token_output": total_out,
        "total_tokens": total_in + total_out,
    }


def _summary_line(items: list[dict]) -> str:
    if not items:
        return "(none)"
    return ", ".join(f"{item['label']} (${item['cost_usd']:.4f})" for item in items[:3])


def render_report(report: dict) -> str:
    width = 72
    bar = "━" * width
    lines = [bar, "HARNESS DELIVERY COST REPORT", bar]
    scope = ", ".join(report["scope"]) if report["scope"] else "(no harness usage data found)"
    lines.append(f"Scope: {scope}")
    lines.append(f"Runs measured: {report['measured_runs']}/{report['total_runs']}")
    if report["incomplete_runs"]:
        lines.append(f"⚠ {report['incomplete_runs']} run(s) lack token/cost telemetry — excluded from totals")
    lines.append(f"Top commands: {_summary_line(report['commands'])}")
    lines.append(f"Top hosts: {_summary_line(report['hosts'])}")
    lines.append(bar)
    lines.append(f"{'Model':<34}{'Runs':>6}{'Tokens in':>14}{'Tokens out':>14}{'Cost USD':>14}".rstrip())
    lines.append("-" * width)
    for item in report["models"]:
        lines.append(
            f"{item['label'][:33]:<34}{item['runs']:>6}{item['token_count_input']:>14,}"
            f"{item['token_count_output']:>14,}{('$' + format(item['cost_usd'], '.4f')):>14}"
        )
    if not report["models"]:
        lines.append("(no harness runs with token and cost telemetry recorded yet)")
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
    parser = argparse.ArgumentParser(description="Report Arpinine Harness delivery cost from governed usage telemetry")
    parser.add_argument("--slug", help="Limit the report to one governed spec slug")
    parser.add_argument("--json", action="store_true", help="Emit aggregate JSON instead of a rendered table")
    args = parser.parse_args(argv)

    repo = find_project_root(pathlib.Path.cwd())
    if repo is None:
        print("Run report_harness_costs.py from the project root directory", file=sys.stderr)
        return 1

    report = aggregate_harness_costs(repo, args.slug)
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(render_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
