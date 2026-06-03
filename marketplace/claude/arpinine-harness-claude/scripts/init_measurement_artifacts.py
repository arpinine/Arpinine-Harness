#!/usr/bin/env python3
"""Scaffold benchmark measurement artifacts for a governed spec."""

from __future__ import annotations

import argparse
import pathlib
import sys

from measurement_artifacts import eval_paths


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
TEMPLATE_DIR = SCRIPT_DIR.parent / "templates"


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def write_if_missing(path: pathlib.Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def scaffold(repo: pathlib.Path, slug: str) -> list[str]:
    paths = eval_paths(repo, slug)
    created: list[str] = []

    dataset_template = TEMPLATE_DIR / "dataset-manifest-template.json"
    baseline_template = TEMPLATE_DIR / "baseline-template.json"

    if write_if_missing(paths["dataset_manifest"], read_text(dataset_template) + "\n"):
        created.append(str(paths["dataset_manifest"].relative_to(repo)))
    if write_if_missing(paths["baseline"], read_text(baseline_template) + "\n"):
        created.append(str(paths["baseline"].relative_to(repo)))

    history_dir = paths["history"]
    history_dir.mkdir(parents=True, exist_ok=True)
    created.append(str(history_dir.relative_to(repo)) + "/")
    return created


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", required=True, help="Spec slug under .specify/evals/")
    args = parser.parse_args(argv)

    repo = find_project_root(pathlib.Path.cwd())
    if repo is None:
        print("Run init_measurement_artifacts.py from the project root directory", file=sys.stderr)
        return 1

    created = scaffold(repo, args.slug)
    if created:
        print("Scaffolded measurement artifacts:")
        for item in created:
            print(f"- {item}")
    else:
        print("No new measurement artifacts were created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
