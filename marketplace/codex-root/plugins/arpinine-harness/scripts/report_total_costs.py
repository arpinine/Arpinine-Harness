#!/usr/bin/env python3
"""Report combined product/runtime and Arpinine Harness delivery cost."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from report_costs import aggregate_costs, discover_slugs, find_project_root as find_runtime_project_root
from report_harness_costs import aggregate_harness_costs


def aggregate_total_costs(repo: pathlib.Path, slug: str | None = None) -> dict:
    runtime_slugs = [slug] if slug else discover_slugs(repo)
    runtime = aggregate_costs(repo, runtime_slugs)
    harness = aggregate_harness_costs(repo, slug)
    return {
        "scope": [slug] if slug else sorted(set(runtime.get("slugs", [])) | set(harness.get("scope", []))),
        "product_runtime": runtime,
        "harness_delivery": harness,
        "combined_total_cost_usd": round(runtime["total_cost_usd"] + harness["total_cost_usd"], 6),
        "combined_total_token_input": runtime["total_token_input"] + harness["total_token_input"],
        "combined_total_token_output": runtime["total_token_output"] + harness["total_token_output"],
        "combined_total_tokens": runtime["total_tokens"] + harness["total_tokens"],
    }


def render_report(report: dict) -> str:
    width = 72
    bar = "━" * width
    scope = ", ".join(report["scope"]) if report["scope"] else "(no cost data found)"
    runtime = report["product_runtime"]
    harness = report["harness_delivery"]
    lines = [bar, "TOTAL DELIVERY COST REPORT", bar]
    lines.append(f"Scope: {scope}")
    lines.append(bar)
    lines.append(
        f"Product/runtime subtotal: ${runtime['total_cost_usd']:.4f} "
        f"({runtime['total_tokens']:,} tokens, {runtime['measured_runs']}/{runtime['total_runs']} runs measured)"
    )
    lines.append(
        f"Harness delivery subtotal: ${harness['total_cost_usd']:.4f} "
        f"({harness['total_tokens']:,} tokens, {harness['measured_runs']}/{harness['total_runs']} runs measured)"
    )
    lines.append(bar)
    lines.append(
        f"Combined total: ${report['combined_total_cost_usd']:.4f} "
        f"({report['combined_total_tokens']:,} tokens)"
    )
    lines.append(bar)
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Report total delivery cost across product/runtime and harness usage")
    parser.add_argument("--slug", help="Limit the report to one governed spec slug")
    parser.add_argument("--json", action="store_true", help="Emit aggregate JSON instead of a rendered summary")
    args = parser.parse_args(argv)

    repo = find_runtime_project_root(pathlib.Path.cwd())
    if repo is None:
        print("Run report_total_costs.py from the project root directory", file=sys.stderr)
        return 1

    report = aggregate_total_costs(repo, args.slug)
    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(render_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
