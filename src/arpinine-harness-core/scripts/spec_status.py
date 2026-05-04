#!/usr/bin/env python3
"""Generate a project-wide Arpinine Harness governance report."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent

import importlib.util

_spec = importlib.util.spec_from_file_location("quick_drift_check", SCRIPT_DIR / "quick_drift_check.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
qdc = _module

_checker_spec = importlib.util.spec_from_file_location("check_harness_observation", SCRIPT_DIR / "check_harness_observation.py")
_checker_module = importlib.util.module_from_spec(_checker_spec)
_checker_spec.loader.exec_module(_checker_module)
cho = _checker_module


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


REPO = find_project_root(pathlib.Path.cwd()) or pathlib.Path(".").resolve()
SPEC_ROOT = REPO / ".specify" / "specs"
ADR_ROOT = REPO / ".specify" / "adr"
OBS_ROOT = REPO / ".specify" / "observations"
EVAL_ROOT = REPO / ".specify" / "evals"
RULE_ROOT = REPO / ".specify" / "rules"
PLACEHOLDER_RE = re.compile(
    r"\[(module|choice|quality dimension|risk|feature name|spec-number|name"
    r"|single clear concern|allowed dependencies|api / port / adapter"
    r"|unit / contract / integration|mock adapter / in-memory fake / fixture"
    r"|reason|internal service / adapter / port"
    r"|session / persistent / none / bounded context"
    r"|approval flow / policy / limits)\]",
    re.IGNORECASE,
)
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def section_body(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for idx, match in enumerate(matches):
        if match.group(1).strip().lower() == title.lower():
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""


def cleaned_section(text: str, title: str) -> str:
    body = section_body(text, title)
    return "\n".join(
        line for line in body.splitlines() if line.strip() and not set(line.strip()) <= {"|", "-", " "}
    ).strip()


def checkbox_counts(spec_text: str) -> tuple[int, int]:
    total = len(re.findall(r"\[(?: |x|X)\]", spec_text))
    checked = len(re.findall(r"\[(?:x|X)\]", spec_text))
    return checked, total


def eval_requirements(slug: str) -> dict[str, bool]:
    eval_plan = EVAL_ROOT / slug / "eval-plan.md"
    if not eval_plan.exists():
        return {
            "exists": False,
            "benchmark_required": False,
            "baseline_required": False,
            "perf_sensitive": False,
        }
    eval_text = read_text(eval_plan)
    return {
        "exists": True,
        "benchmark_required": bool(
            re.search(r"benchmark required:\s*yes", eval_text, re.IGNORECASE)
            or re.search(r"benchmark command:\s*`.+`", eval_text)
        ),
        "baseline_required": bool(re.search(r"baseline required:\s*yes", eval_text, re.IGNORECASE)),
        "perf_sensitive": bool(
            re.search(r"(latency p\d+|token|cost usd|cost / latency|cost per run|token input|token output)", eval_text, re.IGNORECASE)
        ),
    }


def benchmark_state(slug: str) -> dict[str, object]:
    root = EVAL_ROOT / slug
    history_dir = root / "history"
    dataset_manifest = root / "dataset-manifest.json"
    baseline = root / "baseline.json"
    session_file = root / "latest-benchmark-session.json"
    latest_session = None
    if session_file.exists():
        try:
            latest_session = json.loads(read_text(session_file)).get("session_id")
        except Exception:
            latest_session = None
    history_count = len(list(history_dir.rglob("*-results.json"))) if history_dir.exists() else 0
    return {
        "dataset_manifest": dataset_manifest.exists(),
        "baseline": baseline.exists(),
        "history_count": history_count,
        "latest_session": latest_session,
    }


def eval_state(slug: str) -> str:
    eval_plan = EVAL_ROOT / slug / "eval-plan.md"
    latest = EVAL_ROOT / slug / "latest-results.md"
    history_dir = EVAL_ROOT / slug / "history"
    baseline = EVAL_ROOT / slug / "baseline.json"
    dataset_manifest = EVAL_ROOT / slug / "dataset-manifest.json"
    requirements = eval_requirements(slug)
    if not eval_plan.exists():
        return "MISSING"
    if not latest.exists():
        return "PLANNED"
    if requirements["benchmark_required"]:
        if not dataset_manifest.exists():
            return "BENCHMARK-MISSING-DATASET"
        if requirements["baseline_required"] and not baseline.exists():
            return "BENCHMARK-MISSING-BASELINE"
        if not history_dir.exists() or not any(history_dir.rglob("*-results.json")):
            return "BENCHMARK-NO-HISTORY"
    text = read_text(latest)
    if re.search(r"^Result:\s*FAIL\b", text, re.MULTILINE | re.IGNORECASE):
        return "FAIL"
    if re.search(r"^Result:\s*REGRESSION\b", text, re.MULTILINE | re.IGNORECASE):
        return "REGRESSION"
    if re.search(r"^Result:\s*WARN\b", text, re.MULTILINE | re.IGNORECASE):
        return "WARN"
    if re.search(r"^Result:\s*PASS\b", text, re.MULTILINE | re.IGNORECASE):
        return "PASS"
    if re.search(r"^-\s*Failed:\s*[1-9]\d*\b", text, re.MULTILINE | re.IGNORECASE):
        return "FAIL"
    if re.search(r"\bthreshold not met\b", text, re.IGNORECASE):
        return "FAIL"
    if requirements["benchmark_required"]:
        return "BENCHMARKED"
    if re.search(r"\b(pass|passed|all thresholds met)\b", text, re.IGNORECASE):
        return "PASS"
    return "RECORDED"


def architecture_state(plan_text: str) -> str:
    required = ["Module Boundaries", "Dependency Rules", "Testability By Boundary"]
    for section in required:
        cleaned = cleaned_section(plan_text, section)
        if not cleaned or PLACEHOLDER_RE.search(cleaned):
            return "✗"
    return "✓"


def harness_state(spec_text: str, plan_text: str) -> str:
    cleaned = cleaned_section(plan_text, "Harness Strategy")
    if re.search(r"\b(n/?a|not applicable)\b", cleaned, re.IGNORECASE):
        return "n/a"
    harness_needed = bool(re.search(r"\b(agent|assistant|prompt|llm|model|inference|harness|openharness)\b", spec_text + "\n" + plan_text, re.IGNORECASE))
    if not harness_needed and not cleaned:
        return "n/a"
    if not cleaned or PLACEHOLDER_RE.search(cleaned):
        return "✗"
    return "✓"


def observation_state(slug: str) -> str:
    latest = OBS_ROOT / slug / "latest-observation.md"
    trace = OBS_ROOT / slug / "trace.json"
    history_dir = OBS_ROOT / slug / "history"
    index = OBS_ROOT / slug / "index.jsonl"
    history_exists = history_dir.exists() and any(history_dir.iterdir()) if history_dir.exists() else False
    if trace.exists():
        try:
            contract = cho.evaluate_slug(slug)
        except FileNotFoundError:
            contract = None
        if contract and contract.get("harness_required") and contract.get("verdict") == "FAIL":
            return "contract-fail"
    if latest.exists() and trace.exists():
        if history_exists and index.exists():
            return "history"
        return "recorded"
    if latest.exists() or trace.exists():
        return "partial"
    return "none"


def adr_count_for_spec(spec: pathlib.Path) -> int:
    target1 = f"governs: specs/{spec.parent.name}"
    target2 = f"governs: .specify/specs/{spec.parent.name}"
    count = 0
    for adr in sorted(ADR_ROOT.glob("*.md")):
        if adr.name == "ADR-INDEX.md":
            continue
        text = read_text(adr)
        if target1 in text or target2 in text:
            count += 1
    return count


def rule_summary() -> dict[str, object]:
    categories: dict[str, int] = {}
    active = 0
    for rule in sorted(RULE_ROOT.glob("**/*.md")):
        text = read_text(rule)
        if re.search(r"^active:\s*true\s*$", text, re.MULTILINE | re.IGNORECASE):
            active += 1
            category = rule.parent.name
            categories[category] = categories.get(category, 0) + 1
    return {"active": active, "categories": categories}


def adr_summary() -> dict[str, int]:
    summary = {"total": 0, "active": 0, "superseded": 0, "open": 0}
    for adr in sorted(ADR_ROOT.glob("*.md")):
        if adr.name == "ADR-INDEX.md":
            continue
        text = read_text(adr)
        summary["total"] += 1
        if re.search(r"^status:\s*(accepted|implemented)\s*$", text, re.MULTILINE | re.IGNORECASE):
            summary["active"] += 1
        elif re.search(r"^status:\s*superseded\s*$", text, re.MULTILINE | re.IGNORECASE):
            summary["superseded"] += 1
        elif re.search(r"^status:\s*proposed\s*$", text, re.MULTILINE | re.IGNORECASE):
            summary["open"] += 1
    return summary


def dependency_report() -> dict[str, object]:
    script = SCRIPT_DIR / "check_dependencies.py"
    if not script.exists():
        return {"summary": {"blocking": ["dependency checker missing"]}, "global": [], "specs": []}

    try:
        result = subprocess.run(
            [sys.executable, str(script), "--json"],
            check=True,
            capture_output=True,
            text=True,
            cwd=REPO,
        )
        return json.loads(result.stdout)
    except Exception:
        return {"summary": {"blocking": ["dependency check failed"]}, "global": [], "specs": []}


def spec_rows(spec_filter: str | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    specs = qdc.iter_specs()
    for spec in specs:
        slug = spec.parent.name
        if spec_filter and slug != spec_filter:
            continue
        spec_text = read_text(spec)
        plan_text = read_text(spec.parent / "plan.md")
        checked, total = checkbox_counts(spec_text)
        analysis = qdc.analyze_spec(spec)
        eval_requirements_state = eval_requirements(slug)
        benchmark_state_info = benchmark_state(slug)
        rows.append(
            {
                "slug": slug,
                "acs": f"{checked}/{total}",
                "drift": "CLEAN" if not analysis["findings"] else f"{len(analysis['findings'])} HINTS",
                "adrs": adr_count_for_spec(spec),
                "eval": eval_state(slug),
                "benchmark_required": eval_requirements_state["benchmark_required"],
                "baseline_required": eval_requirements_state["baseline_required"],
                "benchmark_state": benchmark_state_info,
                "arch": architecture_state(plan_text),
                "harness": harness_state(spec_text, plan_text),
                "obs": observation_state(slug),
                "findings": analysis["findings"],
                "summary": first_nonempty_line(spec_text),
            }
        )
    return rows


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:120]
    return "No summary available."


def blocked_work(rows: list[dict[str, object]], deps: dict[str, object]) -> list[str]:
    blocked: list[str] = []
    for item in deps.get("summary", {}).get("blocking", []):
        blocked.append(f"Environment: missing required dependency `{item}`")

    for row in rows:
        if row["eval"] == "MISSING" and row["harness"] != "n/a":
            blocked.append(f"{row['slug']}: missing eval plan on harness or agentic feature")
        if row["eval"] == "BENCHMARK-MISSING-DATASET":
            blocked.append(f"{row['slug']}: benchmarked evaluation requires dataset-manifest.json")
        if row["eval"] == "BENCHMARK-MISSING-BASELINE":
            blocked.append(f"{row['slug']}: regression-sensitive benchmark requires baseline.json")
        if row["eval"] == "BENCHMARK-NO-HISTORY":
            blocked.append(f"{row['slug']}: benchmarked evaluation requires archived history results")
        if row["arch"] == "✗":
            blocked.append(f"{row['slug']}: architecture sections absent or still placeholders")
        if row["harness"] == "✗":
            blocked.append(f"{row['slug']}: harness strategy missing or still placeholder")
        if row["drift"] != "CLEAN":
            blocked.append(f"{row['slug']}: unresolved drift or conformance hints need audit")
        if row["obs"] == "contract-fail":
            blocked.append(f"{row['slug']}: harness observation contract failed")
    return blocked


def render_table(rows: list[dict[str, object]]) -> list[str]:
    lines = [
        "SPEC STATUS",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "Spec                      ACs    Drift     ADRs  Eval     Arch  Harness  Obs",
    ]
    for row in rows:
        lines.append(
            f"{row['slug']:<25} {row['acs']:<6} {row['drift']:<9} {str(row['adrs']):<5} "
            f"{row['eval']:<8} {row['arch']:<5} {row['harness']:<8} {row['obs']}"
        )
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return lines


def render_onboarding(rows: list[dict[str, object]], blocked: list[str], deps: dict[str, object]) -> list[str]:
    lines = [
        "TEAM ONBOARDING BRIEF",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "WORKFLOW",
        "/at-init -> /at-new -> /at-review -> /at-plan -> /at-eval -> /at-observe -> /at-implement -> /at-audit -> /at-retro",
        "",
        "ACTIVE SPECS",
    ]
    for row in rows:
        lines.append(f"- {row['slug']}: {row['summary']}")
    lines.extend(["", "DEPENDENCY STATE"])
    blocking = deps.get("summary", {}).get("blocking", [])
    if blocking:
        lines.extend(f"- Missing: {item}" for item in blocking)
    else:
        lines.append("- Required baseline tools are available.")
    lines.extend(["", "OPEN ITEMS"])
    if blocked:
        lines.extend(f"- {item}" for item in blocked)
    else:
        lines.append("- No blocking governance issues found.")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    return lines


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", help="Specific spec slug")
    parser.add_argument("--onboard", action="store_true", help="Include onboarding brief")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    if find_project_root(pathlib.Path.cwd()) is None:
        print("Run spec_status.py from the project root directory")
        return 1

    if not SPEC_ROOT.exists():
        print("Run /at-init first")
        return 1

    rows = spec_rows(args.spec)
    if not rows:
        print("No specs yet. Run /at-new to create the first one")
        return 1

    deps = dependency_report()
    adr = adr_summary()
    rules = rule_summary()
    blocked = blocked_work(rows, deps)
    payload = {
        "specs": rows,
        "dependencies": deps,
        "adr_summary": adr,
        "rule_summary": rules,
        "blocked_work": blocked,
    }

    if args.json:
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    lines = render_table(rows)
    lines.append(
        f"{len(rows)} specs  |  {sum(1 for row in rows if row['drift'] == 'CLEAN')} clean  |  "
        f"{sum(1 for row in rows if row['drift'] != 'CLEAN')} open drift  |  "
        f"{sum(1 for row in rows if row['eval'] == 'MISSING')} missing eval  |  "
        f"{sum(1 for row in rows if row['harness'] == '✗')} missing harness  |  "
        f"{sum(1 for row in rows if row['benchmark_required'])} benchmarked"
    )
    lines.extend(
        [
            "",
            "BENCHMARK READINESS",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
    )
    benchmarked = [row for row in rows if row["benchmark_required"]]
    if benchmarked:
        for row in benchmarked:
            state = row["benchmark_state"]
            lines.append(
                f"{row['slug']}: dataset={'yes' if state['dataset_manifest'] else 'no'}, "
                f"baseline={'yes' if state['baseline'] else 'no'}, history={state['history_count']}"
            )
    else:
        lines.append("No specs currently require benchmarked evaluation.")
    lines.extend(
        [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "ADR COVERAGE",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Total ADRs:      {adr['total']}",
            f"Active:          {adr['active']}",
            f"Superseded:      {adr['superseded']}",
            f"Open (Proposed): {adr['open']}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "RULES",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Active rules:    {rules['active']}",
        ]
    )
    for category, count in sorted(rules["categories"].items()):
        lines.append(f"  {category}: {count}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if blocked:
        lines.extend(["", "BLOCKED WORK"])
        lines.extend(f"- {item}" for item in blocked)
    if args.onboard:
        lines.extend([""] + render_onboarding(rows, blocked, deps))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
