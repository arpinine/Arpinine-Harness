#!/usr/bin/env python3
"""Helpers for governed observation and evaluation measurement artifacts."""

from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone


def utc_now_run_id(prefix: str = "run") -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{prefix}"


def _write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: pathlib.Path, payload: dict) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _append_jsonl(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def observation_paths(repo: pathlib.Path, slug: str) -> dict[str, pathlib.Path]:
    root = repo / ".specify" / "observations" / slug
    return {
        "root": root,
        "latest_markdown": root / "latest-observation.md",
        "latest_trace": root / "trace.json",
        "history": root / "history",
        "index": root / "index.jsonl",
    }


def eval_paths(repo: pathlib.Path, slug: str) -> dict[str, pathlib.Path]:
    root = repo / ".specify" / "evals" / slug
    return {
        "root": root,
        "latest_markdown": root / "latest-results.md",
        "history": root / "history",
        "baseline": root / "baseline.json",
        "dataset_manifest": root / "dataset-manifest.json",
    }


def default_observation_markdown(observation: dict) -> str:
    return "\n".join(
        [
            "# Observation Report",
            "",
            f"- Run id: {observation.get('run_id', 'unknown')}",
            f"- Scenario: {observation.get('scenario_id', 'unknown')}",
            f"- Runtime class: {observation.get('runtime_class', 'unknown')}",
            f"- Runtime implementation: {observation.get('runtime_implementation', 'unknown')}",
            f"- Latency ms: {observation.get('latency_ms', 'n/a')}",
            f"- Token input: {observation.get('token_count_input', 'n/a')}",
            f"- Token output: {observation.get('token_count_output', 'n/a')}",
            f"- Cost USD: {observation.get('cost_usd', 'n/a')}",
            f"- Final outcome: {observation.get('final_outcome', 'unknown')}",
            "",
        ]
    )


def write_observation_run(
    repo: pathlib.Path,
    slug: str,
    observation: dict,
    markdown: str | None = None,
) -> dict[str, pathlib.Path]:
    paths = observation_paths(repo, slug)
    run_id = observation.get("run_id") or utc_now_run_id(observation.get("scenario_id", "scenario"))
    observation = {**observation, "run_id": run_id}
    md = markdown or default_observation_markdown(observation)

    history_json = paths["history"] / f"{run_id}.json"
    history_md = paths["history"] / f"{run_id}.md"

    _write_json(paths["latest_trace"], observation)
    _write_text(paths["latest_markdown"], md)
    _write_json(history_json, observation)
    _write_text(history_md, md)
    _append_jsonl(
        paths["index"],
        {
            "run_id": run_id,
            "scenario_id": observation.get("scenario_id"),
            "variant_id": observation.get("variant_id"),
            "dataset_version": observation.get("dataset_version"),
            "latency_ms": observation.get("latency_ms"),
            "token_count_input": observation.get("token_count_input"),
            "token_count_output": observation.get("token_count_output"),
            "cost_usd": observation.get("cost_usd"),
            "final_outcome": observation.get("final_outcome"),
        },
    )
    return {
        "latest_markdown": paths["latest_markdown"],
        "latest_trace": paths["latest_trace"],
        "history_json": history_json,
        "history_markdown": history_md,
        "index": paths["index"],
    }


def default_eval_markdown(result: dict) -> str:
    lines = [
        "# Evaluation Results",
        "",
        f"Result: {result.get('result', 'RECORDED')}",
        f"Run ID: {result.get('run_id', 'unknown')}",
        f"Dataset Version: {result.get('dataset_version', 'unknown')}",
        f"Variant ID: {result.get('variant_id', 'unknown')}",
        f"Scenario Set: {result.get('scenario_set', 'unknown')}",
        f"Passed: {result.get('passed', 0)}",
        f"Failed: {result.get('failed', 0)}",
    ]
    metrics = result.get("metrics", {})
    if metrics:
        lines.extend(
            [
                f"Latency P50 ms: {metrics.get('latency_p50_ms', 'n/a')}",
                f"Latency P95 ms: {metrics.get('latency_p95_ms', 'n/a')}",
                f"Token Input Total: {metrics.get('token_input_total', 'n/a')}",
                f"Token Output Total: {metrics.get('token_output_total', 'n/a')}",
                f"Cost USD Total: {metrics.get('cost_total_usd', 'n/a')}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def write_eval_run(
    repo: pathlib.Path,
    slug: str,
    result: dict,
    markdown: str | None = None,
    archive: bool = True,
) -> dict[str, pathlib.Path]:
    paths = eval_paths(repo, slug)
    run_id = result.get("run_id") or utc_now_run_id("results")
    result = {**result, "run_id": run_id}
    md = markdown or default_eval_markdown(result)

    _write_text(paths["latest_markdown"], md)
    history_json = paths["history"] / f"{run_id}-results.json"
    history_md = paths["history"] / f"{run_id}-results.md"
    if archive:
        _write_json(history_json, result)
        _write_text(history_md, md)
    return {
        "latest_markdown": paths["latest_markdown"],
        "history_json": history_json,
        "history_markdown": history_md,
    }


def compare_baseline_dimensions(baseline: dict, result: dict) -> tuple[bool, list[str]]:
    mismatches: list[str] = []
    comparable_fields = (
        "dataset_version",
        "variant_id",
        "model_name",
        "model_version",
        "scenario_set",
    )
    for field in comparable_fields:
        baseline_value = baseline.get(field)
        result_value = result.get(field)
        if baseline_value is not None and result_value is not None and baseline_value != result_value:
            mismatches.append(field)
    return not mismatches, mismatches
