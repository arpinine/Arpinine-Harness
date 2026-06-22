#!/usr/bin/env python3
"""
run_golden_session_benchmark.py — replay the golden harness session with
compression ON and OFF, then gate on fidelity + token reduction.

AC-001 governance outcome set (compared per scenario, zero divergence):
  - routing   : router decision fields from route_at
  - ac_state  : acceptance-criteria checkbox states of a spec
  - drift     : drift-finding records of a spec
Each scenario declares its `category`; the matching extractor produces an
outcome dict and the FidelityGate diffs ON vs OFF over that scenario's keys.

ADR-0017: PASS requires zero divergence across ALL categories AND 60-95%
session-total outbound prompt-token reduction (>95% is a FAIL).

Engines:
  - `noop`     : ON outcome == OFF outcome, no token reduction (0%). Runnable —
    yields fidelity PASS but band FAIL, proving the pipeline end to end and
    honestly showing compression is inert.
  - `headroom` : not wired yet (TASK-002 `_engine_*` seams) -> `incomplete`,
    fail-closed. Never a silent green.

Fail-closed: missing golden, empty scenarios, or an unavailable engine => the
result is `incomplete`/`fail`, never a pass.

Governs: specs/011-context-compression-governance (TASK-009).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fidelity_gate import FidelityGate  # noqa: E402

MIN_REDUCTION = 0.60
MAX_REDUCTION = 0.95

_ROUTER_FIELDS = ["interpretation", "route", "confidence", "command_class", "requires_confirmation"]
_AC_RE = re.compile(r"- \[([ x])\]\s*(AC-\d+)")


# ----------------------- OFF (uncompressed) extractors -----------------------

def extract_routing(repo: pathlib.Path, intent: str) -> dict:
    router = pathlib.Path(__file__).resolve().parent / "route_at.py"
    result = subprocess.run(
        [sys.executable, str(router), "--repo", str(repo), "--intent", intent, "--indent", "0"],
        capture_output=True, text=True, check=True,
    )
    d = json.loads(result.stdout)
    return {f: d.get(f) for f in _ROUTER_FIELDS}


def extract_ac_state(repo: pathlib.Path, slug: str) -> dict:
    spec = repo / ".specify" / "specs" / slug / "spec.md"
    text = spec.read_text()
    return {ac: (mark == "x") for mark, ac in _AC_RE.findall(text)}


def extract_drift(repo: pathlib.Path, slug: str) -> dict:
    checker = pathlib.Path(__file__).resolve().parent / "quick_drift_check.py"
    spec = repo / ".specify" / "specs" / slug / "spec.md"
    result = subprocess.run(
        [sys.executable, str(checker), "--spec", str(spec), "--json"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout)
    findings = data[0]["findings"] if data else []
    spec_path = str(repo / ".specify" / "specs" / slug / "spec.md")
    records = []
    for idx, finding in enumerate(findings):
        text = str(finding)
        severity = "UNKNOWN"
        parts = text.split(" ", 1)
        if parts and parts[0] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            severity = parts[0]
            message = parts[1] if len(parts) > 1 else ""
        else:
            message = text
        finding_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        records.append(
            {
                "file": spec_path,
                "line": None,
                "severity": severity,
                "finding_id": f"qdc-{finding_id}",
                "message": message,
            }
        )
    return {"findings": records}


def default_extractors(repo: pathlib.Path) -> dict:
    return {
        "routing": lambda target: extract_routing(repo, target),
        "adversarial": lambda target: extract_routing(repo, target),
        "ac_state": lambda target: extract_ac_state(repo, target),
        "drift": lambda target: extract_drift(repo, target),
    }


def _scenario_target(s: dict) -> str:
    # routing/adversarial scenarios use `intent`; ac_state/drift use `target` slug.
    return s.get("target") or s["intent"]


# ----------------------------- engines -----------------------------

class NoopEngine:
    """Runnable self-test: ON == OFF, zero token reduction."""
    available = True
    name = "noop"

    def on_outcome(self, off_outcome: dict) -> dict:
        return dict(off_outcome)

    def measure(self, off_outcome: dict, mode: str) -> int:
        # Deterministic token proxy: serialized length. Equal ON/OFF (noop).
        return len(json.dumps(off_outcome, sort_keys=True))


class HeadroomEngine:
    """Not wired yet — the headroom `_engine_*` seams land at integration."""
    available = False
    name = "headroom"


def run_benchmark(manifest: dict, extractors: dict, engine) -> dict:
    scenarios = manifest.get("scenarios") or []
    if not scenarios:
        return {"status": "incomplete", "passed": False,
                "reason": "golden session has no scenarios (fail closed)"}
    if engine is None or not getattr(engine, "available", False):
        return {"status": "incomplete", "passed": False,
                "reason": f"compression engine '{getattr(engine, 'name', None)}' not wired/available "
                          "— headroom _engine_* seams pending integration; fail closed"}

    gate = FidelityGate(_ROUTER_FIELDS)  # default fields; per-scenario keys override
    pairs = []
    off_total = 0
    on_total = 0
    for s in scenarios:
        category = s["category"]
        extractor = extractors.get(category)
        if extractor is None:
            return {"status": "incomplete", "passed": False,
                    "reason": f"no extractor for category '{category}' (fail closed)"}
        off_outcome = extractor(_scenario_target(s))
        on_outcome = engine.on_outcome(off_outcome)
        keys = sorted(set(off_outcome) | set(on_outcome) | set(s.get("expected", {})))
        pairs.append((off_outcome, on_outcome, keys))
        off_total += engine.measure(off_outcome, "off")
        on_total += engine.measure(on_outcome, "on")

    fidelity = gate.aggregate(pairs)
    reduction = (off_total - on_total) / off_total if off_total else 0.0
    in_band = MIN_REDUCTION <= reduction <= MAX_REDUCTION
    passed = bool(fidelity["passed"] and in_band)
    return {
        "status": "pass" if passed else "fail",
        "passed": passed,
        "engine": engine.name,
        "fidelity": fidelity,
        "token_reduction": reduction,
        "off_tokens": off_total,
        "on_tokens": on_total,
        "in_band": in_band,
        "band": [MIN_REDUCTION, MAX_REDUCTION],
        "categories": sorted({s["category"] for s in scenarios}),
    }


def _load_manifest(repo: pathlib.Path, slug: str) -> dict | None:
    path = repo / ".specify" / "evals" / slug / "golden-session" / "manifest.json"
    return json.loads(path.read_text()) if path.exists() else None


_ENGINES = {"noop": NoopEngine, "headroom": HeadroomEngine}


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the golden-session fidelity benchmark.")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--slug", default="011-context-compression-governance")
    parser.add_argument("--engine", choices=list(_ENGINES), default="noop",
                        help="noop = runnable self-test (band fails, no compression); "
                             "headroom = real engine (incomplete until wired)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    repo = pathlib.Path(args.repo)
    manifest = _load_manifest(repo, args.slug)
    if manifest is None:
        report = {"status": "incomplete", "passed": False,
                  "reason": "golden-session manifest not found (fail closed)"}
    else:
        report = run_benchmark(manifest, default_extractors(repo), _ENGINES[args.engine]())

    if args.json:
        print(json.dumps(report))
    else:
        print(f"status={report['status']} passed={report.get('passed')} engine={report.get('engine')}")
        if "reason" in report:
            print(f"  reason: {report['reason']}")
        if "token_reduction" in report:
            print(f"  categories={report['categories']}")
            print(f"  token_reduction={report['token_reduction']:.2%} band={report['band']} in_band={report['in_band']}")
            print(f"  fidelity_passed={report['fidelity']['passed']} divergent={report['fidelity']['divergent_scenarios']}")
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
