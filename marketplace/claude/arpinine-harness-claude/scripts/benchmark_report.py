#!/usr/bin/env python3
"""Aggregate benchmark result history into a governed latest-results report."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import statistics
import sys

from measurement_artifacts import compare_baseline_dimensions, eval_paths, write_eval_run


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(values)
    index = (len(ordered) - 1) * p
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return float(ordered[lower])
    fraction = index - lower
    return float(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction)


def latest_session_id(paths: dict[str, pathlib.Path]) -> str | None:
    session_file = paths.get("latest_session")
    if not session_file or not session_file.exists():
        return None
    try:
        payload = read_json(session_file)
    except Exception:
        return None
    value = payload.get("session_id")
    return str(value) if value else None


def load_eval_history(history_dir: pathlib.Path, session_id: str | None = None) -> list[dict]:
    entries: list[dict] = []
    target_dir = history_dir / session_id if session_id else history_dir
    if not target_dir.exists():
        return entries
    for path in sorted(target_dir.glob("*-results.json")):
        try:
            entries.append(read_json(path))
        except Exception:
            continue
    return entries


def section_body(text: str, title: str) -> str:
    pattern = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for idx, match in enumerate(matches):
        if match.group(1).strip().lower() == title.lower():
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""


def parse_markdown_table(section_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        rows.append([cell.strip().strip("`") for cell in stripped.strip("|").split("|")])
    return rows[1:] if len(rows) > 1 else []


def parse_thresholds(eval_plan_text: str) -> tuple[list[dict[str, object]], int | None]:
    thresholds: list[dict[str, object]] = []
    benchmark_section = section_body(eval_plan_text, "Benchmark Policy")
    min_match = re.search(r"Minimum scenario count.*?:\s*\[?(?:e\.g\.\s*)?(\d+)\]?", benchmark_section, re.IGNORECASE)
    minimum_runs = int(min_match.group(1)) if min_match else None

    metrics_section = section_body(eval_plan_text, "Metrics And Thresholds")
    for row in parse_markdown_table(metrics_section):
        if len(row) < 4:
            continue
        dimension, metric, threshold, failure_action = row[:4]
        threshold_match = re.search(r"(<=|>=|<|>)\s*([0-9]+(?:\.[0-9]+)?)", threshold)
        if not threshold_match:
            continue
        op, value = threshold_match.groups()
        thresholds.append(
            {
                "dimension": dimension,
                "metric": metric,
                "threshold": threshold,
                "operator": op,
                "value": float(value),
                "failure_action": failure_action,
            }
        )
    return thresholds, minimum_runs


def metric_value(metric_name: str, aggregate: dict) -> float | None:
    name = metric_name.lower()
    if "task success" in name or "pass rate" in name:
        return float(aggregate.get("pass_rate", 0.0))
    if "approval check" in name:
        return aggregate.get("metrics", {}).get("approval_check_rate")
    if "memory scope" in name or "session-scoped memory" in name:
        return aggregate.get("metrics", {}).get("memory_scope_rate")
    if "latency p50" in name:
        return aggregate.get("metrics", {}).get("latency_p50_ms")
    if "latency p95" in name:
        return aggregate.get("metrics", {}).get("latency_p95_ms")
    if "latency avg" in name or "latency mean" in name:
        return aggregate.get("metrics", {}).get("latency_avg_ms")
    if "token input" in name:
        return aggregate.get("metrics", {}).get("token_input_total")
    if "token output" in name:
        return aggregate.get("metrics", {}).get("token_output_total")
    if "cost" in name:
        return aggregate.get("metrics", {}).get("cost_total_usd")
    return None


def passes_threshold(actual: float, operator: str, expected: float) -> bool:
    if operator == "<=":
        return actual <= expected
    if operator == ">=":
        return actual >= expected
    if operator == "<":
        return actual < expected
    if operator == ">":
        return actual > expected
    return False


def evaluate_thresholds(aggregate: dict, thresholds: list[dict[str, object]], minimum_runs: int | None) -> tuple[str, list[str]]:
    notes: list[str] = []
    verdict = "PASS"

    if minimum_runs is not None and aggregate["run_count"] < minimum_runs:
        verdict = "FAIL"
        notes.append(f"run_count {aggregate['run_count']} < minimum benchmark scenario count {minimum_runs}")

    for threshold in thresholds:
        actual = metric_value(str(threshold["metric"]), aggregate)
        if actual is None:
            # Fail closed: a release-blocking threshold cannot be proven met when
            # its required telemetry is absent. Non-blocking thresholds warn only.
            if "block" in str(threshold.get("failure_action", "")).lower():
                verdict = "FAIL"
                notes.append(
                    f"required telemetry missing for release-blocking threshold: {threshold['metric']} "
                    f"({threshold['failure_action']})"
                )
            else:
                if verdict != "FAIL":
                    verdict = "WARN"
                notes.append(f"metric unavailable for threshold: {threshold['metric']}")
            continue
        actual_float = float(actual)
        operator = str(threshold["operator"])
        expected = float(threshold["value"])
        if not passes_threshold(actual_float, operator, expected):
            verdict = "FAIL"
            notes.append(
                f"{threshold['metric']} {actual_float:.3f} does not satisfy {operator} {expected:g}"
            )

    if not notes:
        notes.append("all configured thresholds satisfied")
    return verdict, notes


def combine_verdicts(threshold_verdict: str, baseline_verdict: str) -> str:
    if threshold_verdict == "FAIL" or baseline_verdict == "FAIL":
        return "FAIL"
    if baseline_verdict == "REGRESSION":
        return "REGRESSION"
    if threshold_verdict == "WARN" or baseline_verdict == "WARN":
        return "WARN"
    return "PASS"


def consistent_value(results: list[dict], field: str) -> object | None:
    values = {item.get(field) for item in results if item.get(field) is not None}
    if len(values) == 1:
        return next(iter(values))
    return None


def aggregate_results(results: list[dict]) -> dict:
    latencies = [float(item["latency_ms"]) for item in results if item.get("latency_ms") is not None]
    token_in = [int(item["token_count_input"]) for item in results if item.get("token_count_input") is not None]
    token_out = [int(item["token_count_output"]) for item in results if item.get("token_count_output") is not None]
    costs = [float(item["cost_usd"]) for item in results if item.get("cost_usd") is not None]
    approval_checks = [bool(item["approval_check_present"]) for item in results if item.get("approval_check_present") is not None]
    memory_checks = [bool(item["memory_scope_ok"]) for item in results if item.get("memory_scope_ok") is not None]
    passed = sum(1 for item in results if item.get("result") == "PASS")
    failed = len(results) - passed
    mixed_dimensions = [
        field
        for field in ("dataset_version", "variant_id", "model_name", "model_version", "scenario_set")
        if consistent_value(results, field) is None
    ]
    return {
        "run_count": len(results),
        "dataset_version": consistent_value(results, "dataset_version"),
        "variant_id": consistent_value(results, "variant_id"),
        "model_name": consistent_value(results, "model_name"),
        "model_version": consistent_value(results, "model_version"),
        "scenario_set": consistent_value(results, "scenario_set"),
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / len(results) if results else 0.0,
        "mixed_dimensions": mixed_dimensions,
        "metrics": {
            "latency_p50_ms": percentile(latencies, 0.50),
            "latency_p95_ms": percentile(latencies, 0.95),
            "latency_avg_ms": statistics.mean(latencies) if latencies else None,
            "approval_check_rate": (sum(1 for item in approval_checks if item) / len(approval_checks)) if approval_checks else None,
            "memory_scope_rate": (sum(1 for item in memory_checks if item) / len(memory_checks)) if memory_checks else None,
            "token_input_total": sum(token_in) if token_in else None,
            "token_output_total": sum(token_out) if token_out else None,
            "cost_total_usd": sum(costs) if costs else None,
        },
    }


def compare_to_baseline(aggregate: dict, baseline: dict, baseline_results: dict | None) -> tuple[str, list[str]]:
    compatible, mismatches = compare_baseline_dimensions(baseline, aggregate)
    if not compatible:
        return "FAIL", [f"incompatible baseline dimensions: {', '.join(mismatches)}"]
    if not baseline_results:
        return "WARN", ["baseline source results not found"]

    signals: list[str] = []
    result = "PASS"
    current_pass_rate = aggregate.get("pass_rate", 0.0)
    baseline_pass_rate = baseline_results.get("pass_rate", 0.0)
    if current_pass_rate < baseline_pass_rate:
        result = "REGRESSION"
        signals.append(f"pass_rate {current_pass_rate:.3f} < baseline {baseline_pass_rate:.3f}")

    current_p95 = aggregate.get("metrics", {}).get("latency_p95_ms")
    baseline_p95 = baseline_results.get("metrics", {}).get("latency_p95_ms")
    if current_p95 is not None and baseline_p95 is not None and current_p95 > baseline_p95:
        result = "REGRESSION"
        signals.append(f"latency_p95_ms {current_p95:.2f} > baseline {baseline_p95:.2f}")

    current_cost = aggregate.get("metrics", {}).get("cost_total_usd")
    baseline_cost = baseline_results.get("metrics", {}).get("cost_total_usd")
    if current_cost is not None and baseline_cost is not None and current_cost > baseline_cost:
        if result != "REGRESSION":
            result = "WARN"
        signals.append(f"cost_total_usd {current_cost:.4f} > baseline {baseline_cost:.4f}")

    if not signals:
        signals.append("no baseline regressions detected")
    return result, signals


def build_report(repo: pathlib.Path, slug: str, session_id: str | None = None) -> dict:
    paths = eval_paths(repo, slug)
    dataset_manifest = paths["dataset_manifest"]
    if not dataset_manifest.exists():
        raise FileNotFoundError("dataset-manifest.json is required for benchmark reporting")
    eval_plan = paths["root"] / "eval-plan.md"
    if not eval_plan.exists():
        raise FileNotFoundError("eval-plan.md is required for benchmark reporting")

    effective_session_id = session_id or latest_session_id(paths)
    results = load_eval_history(paths["history"], effective_session_id)
    if not results:
        raise FileNotFoundError("no benchmark history results were found")

    thresholds, minimum_runs = parse_thresholds(read_text(eval_plan))
    aggregate = aggregate_results(results)
    aggregate["run_id"] = results[-1].get("run_id", "aggregate")
    if effective_session_id:
        aggregate["benchmark_session_id"] = effective_session_id
    threshold_verdict, threshold_notes = evaluate_thresholds(aggregate, thresholds, minimum_runs)
    if aggregate["mixed_dimensions"] and threshold_verdict != "FAIL":
        threshold_verdict = "FAIL"
        threshold_notes.append(
            f"benchmark history mixes incompatible dimensions: {', '.join(aggregate['mixed_dimensions'])}"
        )
    if aggregate["failed"] > 0 and threshold_verdict != "FAIL":
        threshold_verdict = "FAIL"
        threshold_notes.append(f"failed benchmark runs present: {aggregate['failed']}")
    verdict = threshold_verdict
    baseline_notes: list[str] = ["baseline not configured"]
    baseline_verdict = "PASS"

    if paths["baseline"].exists():
        baseline = read_json(paths["baseline"])
        baseline_source = baseline.get("source_results_path")
        baseline_results = read_json(repo / baseline_source) if baseline_source and (repo / baseline_source).exists() else None
        baseline_verdict, baseline_notes = compare_to_baseline(aggregate, baseline, baseline_results)

    verdict = combine_verdicts(threshold_verdict, baseline_verdict)

    aggregate["result"] = verdict
    aggregate["threshold_notes"] = threshold_notes
    aggregate["baseline_notes"] = baseline_notes
    return aggregate


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True, help="Spec slug under .specify/evals/")
    parser.add_argument("--json", action="store_true", help="Emit aggregate JSON instead of writing markdown")
    parser.add_argument("--session-id", help="Limit aggregation to one benchmark session")
    args = parser.parse_args(argv)

    repo = find_project_root(pathlib.Path.cwd())
    if repo is None:
        print("Run benchmark_report.py from the project root directory", file=sys.stderr)
        return 1

    try:
        aggregate = build_report(repo, args.slug, args.session_id)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        json.dump(aggregate, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    write_eval_run(repo, args.slug, aggregate, archive=False, session_id=args.session_id or aggregate.get("benchmark_session_id"))
    print(f"Wrote benchmark summary for {args.slug} with result {aggregate['result']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
