#!/usr/bin/env python3
"""Run a governed benchmark suite scenario-by-scenario and emit an aggregate result."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile

from benchmark_report import build_report
from measurement_artifacts import write_eval_run, write_observation_run


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_flag(text: str, label: str) -> bool:
    match = re.search(rf"^-\s*{re.escape(label)}:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return False
    return match.group(1).strip().lower() in {"yes", "true", "required"}


def parse_command(text: str, label: str) -> str:
    match = re.search(rf"^-\s*{re.escape(label)}:\s*`?(.+?)`?\s*$", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def has_shell_metacharacters(command: str) -> bool:
    return bool(re.search(r"[|;&><`{}]|\$\(|\$\(", command))


def required_scenarios(dataset_manifest: dict) -> list[dict]:
    scenarios = dataset_manifest.get("scenarios", [])
    return [scenario for scenario in scenarios if scenario.get("required", True)]


def normalize_result(result: dict, scenario: dict, dataset_manifest: dict) -> dict:
    scenario_id = scenario.get("scenario_id", "unknown-scenario")
    normalized = dict(result)
    normalized.setdefault("scenario_id", scenario_id)
    normalized.setdefault("dataset_version", dataset_manifest.get("dataset_version"))
    normalized.setdefault("scenario_set", dataset_manifest.get("dataset_name"))
    normalized.setdefault("result", "PASS")
    if normalized["result"] == "PASS":
        normalized.setdefault("passed", 1)
        normalized.setdefault("failed", 0)
    else:
        normalized.setdefault("passed", 0)
        normalized.setdefault("failed", 1)
    return normalized


def run_scenario(repo: pathlib.Path, slug: str, command: str, dataset_manifest: dict, scenario: dict) -> dict:
    if has_shell_metacharacters(command):
        raise ValueError("benchmark command contains unsupported shell metacharacters")

    required_eval_root = repo / ".specify" / "evals" / slug
    required_eval_root.mkdir(parents=True, exist_ok=True)
    observation_root = repo / ".specify" / "observations" / slug
    observation_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="arpinine-benchmark-") as tempdir:
        temp_root = pathlib.Path(tempdir)
        result_path = temp_root / "result.json"
        observation_path = temp_root / "observation.json"
        env = os.environ.copy()
        env.update(
            {
                "ARPININE_HARNESS_SPEC_SLUG": slug,
                "ARPININE_HARNESS_DATASET_NAME": str(dataset_manifest.get("dataset_name", "")),
                "ARPININE_HARNESS_DATASET_VERSION": str(dataset_manifest.get("dataset_version", "")),
                "ARPININE_HARNESS_SCENARIO_ID": str(scenario.get("scenario_id", "")),
                "ARPININE_HARNESS_SCENARIO_JSON": json.dumps(scenario, sort_keys=True),
                "ARPININE_HARNESS_RESULT_PATH": str(result_path),
                "ARPININE_HARNESS_OBSERVATION_PATH": str(observation_path),
            }
        )
        completed = subprocess.run(
            shlex.split(command),
            cwd=repo,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"benchmark command failed for scenario {scenario.get('scenario_id', 'unknown')}: "
                f"{completed.stderr.strip() or completed.stdout.strip() or f'exit {completed.returncode}'}"
            )
        if not result_path.exists():
            raise FileNotFoundError(
                f"benchmark command did not produce result JSON for scenario {scenario.get('scenario_id', 'unknown')}"
            )

        result = normalize_result(read_json(result_path), scenario, dataset_manifest)
        write_eval_run(repo, slug, result, archive=True)

        if observation_path.exists():
            observation = read_json(observation_path)
            observation.setdefault("scenario_id", scenario.get("scenario_id"))
            observation.setdefault("dataset_version", dataset_manifest.get("dataset_version"))
            write_observation_run(repo, slug, observation)

        return result


def run_benchmark(repo: pathlib.Path, slug: str) -> dict:
    eval_root = repo / ".specify" / "evals" / slug
    eval_plan = eval_root / "eval-plan.md"
    dataset_manifest_path = eval_root / "dataset-manifest.json"

    if not eval_plan.exists():
        raise FileNotFoundError("eval-plan.md is required before benchmark execution")
    if not dataset_manifest_path.exists():
        raise FileNotFoundError("dataset-manifest.json is required before benchmark execution")

    eval_plan_text = read_text(eval_plan)
    benchmark_command = parse_command(eval_plan_text, "Benchmark command")
    if not benchmark_command:
        raise ValueError("eval-plan.md must declare a benchmark command")
    if not parse_flag(eval_plan_text, "Benchmark required"):
        raise ValueError("benchmark mode is not enabled in eval-plan.md")

    dataset_manifest = read_json(dataset_manifest_path)
    scenarios = required_scenarios(dataset_manifest)
    if not scenarios:
        raise ValueError("dataset-manifest.json must declare at least one required scenario")

    for scenario in scenarios:
        run_scenario(repo, slug, benchmark_command, dataset_manifest, scenario)

    aggregate = build_report(repo, slug)
    write_eval_run(repo, slug, aggregate, archive=False)
    return aggregate


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True, help="Spec slug under .specify/evals/")
    parser.add_argument("--json", action="store_true", help="Emit the aggregate benchmark JSON")
    args = parser.parse_args(argv)

    repo = find_project_root(pathlib.Path.cwd())
    if repo is None:
        print("Run run_benchmark.py from the project root directory", file=sys.stderr)
        return 1

    try:
        aggregate = run_benchmark(repo, args.slug)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        json.dump(aggregate, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"Benchmark completed for {args.slug} with result {aggregate['result']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
