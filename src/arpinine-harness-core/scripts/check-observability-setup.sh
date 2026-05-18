#!/bin/bash
# Observability readiness gate.
# Verifies that ObservationProvider and EvaluationProvider abstractions are
# correctly scaffolded before /at-implement proceeds for LLM/agentic features.
# Run automatically by /at-implement when ## Observability Strategy is required.
# Usage: scripts/check-observability-setup.sh [--spec <slug>] [--json]
set -euo pipefail

SPEC_SLUG=""
JSON_OUTPUT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --spec) SPEC_SLUG="$2"; shift 2 ;;
    --json) JSON_OUTPUT=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if ! command -v python3 &>/dev/null; then
  echo "python3 not found — skipping observability setup check" >&2
  exit 0
fi

python3 - "$SPEC_SLUG" "$JSON_OUTPUT" <<'PYEOF'
import json
import pathlib
import re
import sys

spec_slug = sys.argv[1]
json_output = sys.argv[2] == "1"

repo = pathlib.Path(".")
specify_root = repo / ".specify"

# ── locate plan.md ──────────────────────────────────────────────────────────

if spec_slug:
    candidate_plans = [specify_root / "specs" / spec_slug / "plan.md"]
else:
    candidate_plans = (
        sorted((specify_root / "specs").glob("*/plan.md"))
        if (specify_root / "specs").exists()
        else []
    )

if not candidate_plans:
    result = {"status": "skip", "reason": "no plan.md found — run /at-plan first"}
    if json_output:
        print(json.dumps(result))
    else:
        print(f"SKIP: {result['reason']}")
    sys.exit(0)

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)

def _plan_names_provider(body: str, *patterns: str) -> bool:
    """Return True if the plan body explicitly names any of the given providers."""
    for p in patterns:
        if re.search(p, body, re.IGNORECASE):
            return True
    return False

def _section_is_na(body: str) -> bool:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--") or set(stripped) <= {"|", "-", " "}:
            continue
        return bool(re.match(r"N/?A\b", stripped, re.IGNORECASE))
    return False

PLACEHOLDER_RE = re.compile(
    r"\[(?:"
    r"file path|justify if not|env var|swap strategy|reason if N/A"
    r"|e\.g\.|your-|TBD|TODO|FIXME"
    r")",
    re.IGNORECASE,
)

OBS_PROVIDER_RE = re.compile(
    r"class\s+\w*ObservationProvider\b|ObservationProvider\s*=\s*Protocol|"
    r"ObservationProvider\s*\(Protocol\)|ObservationProvider\s*\(ABC\)",
)
EVAL_PROVIDER_RE = re.compile(
    r"class\s+\w*EvaluationProvider\b|EvaluationProvider\s*=\s*Protocol|"
    r"EvaluationProvider\s*\(Protocol\)|EvaluationProvider\s*\(ABC\)",
)

LANGFUSE_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+langfuse\b", re.MULTILINE)
OTEL_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+opentelemetry(?:\b|\.)", re.MULTILINE)
DEEPEVAL_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+deepeval\b", re.MULTILINE)
FLUSH_RE = re.compile(r"\.flush\(\)")


def section_body(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for idx, m in enumerate(matches):
        if m.group(1).strip().lower() == title.lower():
            start = m.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""


findings = []

for plan_path in candidate_plans:
    slug_label = plan_path.parent.name

    try:
        plan_text = plan_path.read_text()
    except Exception as exc:
        findings.append({
            "level": "ERROR", "check": "plan-readable", "slug": slug_label,
            "message": f"cannot read plan.md: {exc}",
        })
        continue

    obs_body = section_body(plan_text, "Observability Strategy")

    # No observability section — nothing declared, skip source checks
    if not obs_body:
        continue

    # N/A declared — intentionally opted out, nothing to check
    if _section_is_na(obs_body):
        continue

    # Section present and required — validate it is filled in
    if PLACEHOLDER_RE.search(obs_body):
        findings.append({
            "level": "HIGH",
            "check": "observability-strategy-complete",
            "slug": slug_label,
            "message": (
                "## Observability Strategy contains unfilled placeholders. "
                "Complete all rows (observation provider, evaluation provider, env vars, swap strategy) "
                "before implementation."
            ),
        })

    # ── source tree checks ──────────────────────────────────────────────────
    src_roots = [d for d in ["app", "src", "lib"] if (repo / d).is_dir()]
    if not src_roots:
        findings.append({
            "level": "HIGH",
            "check": "source-root-missing",
            "slug": slug_label,
            "message": (
                "No source root (app/, src/, lib/) found. "
                "Scaffold src/observability/ and src/evaluation/ before implementation."
            ),
        })
        continue

    # ── observation provider checks ─────────────────────────────────────────
    obs_base_candidates = []
    obs_langfuse_candidates = []
    obs_otel_candidates = []
    obs_noop_candidates = []
    langfuse_leak_files = []
    otel_leak_files = []
    flush_present = False

    for src_root in src_roots:
        obs_dir = repo / src_root / "observability"
        if obs_dir.is_dir():
            for py_file in obs_dir.rglob("*.py"):
                rel = str(py_file.relative_to(repo))
                text = py_file.read_text(errors="replace")

                if OBS_PROVIDER_RE.search(text):
                    obs_base_candidates.append(rel)
                if LANGFUSE_IMPORT_RE.search(text):
                    obs_langfuse_candidates.append(rel)
                if OTEL_IMPORT_RE.search(text):
                    obs_otel_candidates.append(rel)
                if FLUSH_RE.search(text):
                    flush_present = True
                # noop provider
                if "noop" in py_file.name.lower() or "null" in py_file.name.lower():
                    obs_noop_candidates.append(rel)

    # Detect Langfuse imports leaking outside observability layer.
    # Scans src roots AND tests/ AND evals/ — all are bound by the same convention.
    leak_scan_roots = [repo / r for r in src_roots] + [repo / "tests", repo / "evals"]
    for scan_root in leak_scan_roots:
        if not scan_root.is_dir():
            continue
        for py_file in scan_root.rglob("*.py"):
            rel = str(py_file.relative_to(repo))
            rel_path = py_file.relative_to(repo).as_posix()
            if re.search(r"(^|/)(src|app|lib)/observability/", rel_path):
                continue
            text = py_file.read_text(errors="replace")
            if LANGFUSE_IMPORT_RE.search(text):
                langfuse_leak_files.append(rel)
            if OTEL_IMPORT_RE.search(text):
                otel_leak_files.append(rel)

    if not obs_base_candidates:
        findings.append({
            "level": "HIGH",
            "check": "observation-provider-interface",
            "slug": slug_label,
            "message": (
                "No ObservationProvider interface found. "
                "Create src/observability/base.py with ObservationProvider Protocol. "
                "Use templates/observation-provider-template.py as scaffold."
            ),
        })

    plan_chose_langfuse = _plan_names_provider(obs_body, r'\blangfuse\b')
    plan_chose_opentelemetry = _plan_names_provider(obs_body, r'\bopentelemetry\b', r'\botel\b')
    plan_chose_alternative = _plan_names_provider(
        obs_body,
        r'\blangfuse\b', r'\blangsmith\b',
        r'\bphoenix\b', r'\barize\b', r'\bhoneyhive\b',
    )

    if obs_base_candidates:
        if (plan_chose_opentelemetry or not plan_chose_alternative) and not obs_otel_candidates:
            findings.append({
                "level": "HIGH",
                "check": "opentelemetry-provider-missing",
                "slug": slug_label,
                "message": (
                    "ObservationProvider interface exists but no OpenTelemetryObservationProvider found. "
                    "Create src/observability/opentelemetry.py (default implementation) and keep OpenTelemetry SDK imports there only. "
                    "Use templates/opentelemetry-observation-provider-template.py as scaffold."
                ),
            })
        if plan_chose_langfuse and not obs_langfuse_candidates:
            findings.append({
                "level": "HIGH",
                "check": "langfuse-provider-missing",
                "slug": slug_label,
                "message": (
                    "ObservationProvider interface exists but no LangfuseObservationProvider found. "
                    "Create src/observability/langfuse.py (specialized implementation). "
                    "Use templates/langfuse-observation-provider-template.py as scaffold. "
                    "Declare Langfuse explicitly in ## Observability Strategy when LLM-specific observability is required."
                ),
            })
        elif plan_chose_alternative and not plan_chose_langfuse:
            findings.append({
                "level": "MEDIUM",
                "check": "alternative-observation-provider-adr",
                "slug": slug_label,
                "message": (
                    "## Observability Strategy names a non-default specialized observation backend. "
                    "Ensure an ADR exists justifying the alternative provider and that "
                    "the custom implementation satisfies the ObservationProvider Protocol."
                ),
            })

    if obs_base_candidates and not obs_noop_candidates:
        findings.append({
            "level": "MEDIUM",
            "check": "noop-observation-provider",
            "slug": slug_label,
            "message": (
                "No NoopObservationProvider found. "
                "Create src/observability/noop.py for test isolation."
            ),
        })

    if (obs_langfuse_candidates or obs_otel_candidates) and not flush_present:
        findings.append({
            "level": "MEDIUM",
            "check": "observation-flush",
            "slug": slug_label,
            "message": (
                "Observation provider exists but no .flush() call found. "
                "Ensure flush() is called at application shutdown (atexit or shutdown handler)."
            ),
        })

    if langfuse_leak_files:
        findings.append({
            "level": "HIGH",
            "check": "langfuse-boundary",
            "slug": slug_label,
            "message": (
                "Langfuse SDK imported outside src/observability/ — boundary violation:\n"
                + "\n".join(f"  - {f}" for f in langfuse_leak_files)
            ),
        })

    if otel_leak_files:
        findings.append({
            "level": "HIGH",
            "check": "opentelemetry-boundary",
            "slug": slug_label,
            "message": (
                "OpenTelemetry SDK imported outside src/observability/ — boundary violation:\n"
                + "\n".join(f"  - {f}" for f in otel_leak_files)
            ),
        })

    # ── evaluation provider checks ──────────────────────────────────────────
    eval_base_candidates = []
    eval_deepeval_candidates = []
    eval_noop_candidates = []
    deepeval_leak_files = []

    for src_root in src_roots:
        eval_dir = repo / src_root / "evaluation"
        if eval_dir.is_dir():
            for py_file in eval_dir.rglob("*.py"):
                rel = str(py_file.relative_to(repo))
                text = py_file.read_text(errors="replace")

                if EVAL_PROVIDER_RE.search(text):
                    eval_base_candidates.append(rel)
                if DEEPEVAL_IMPORT_RE.search(text):
                    eval_deepeval_candidates.append(rel)
                if "noop" in py_file.name.lower() or "null" in py_file.name.lower():
                    eval_noop_candidates.append(rel)

    # Detect DeepEval imports leaking outside evaluation layer.
    # Scans src roots AND tests/ AND evals/ — no SDK direct imports allowed outside provider.
    for scan_root in leak_scan_roots:
        if not scan_root.is_dir():
            continue
        for py_file in scan_root.rglob("*.py"):
            rel = str(py_file.relative_to(repo))
            rel_path = py_file.relative_to(repo).as_posix()
            if re.search(r"(^|/)(src|app|lib)/evaluation/", rel_path):
                continue
            text = py_file.read_text(errors="replace")
            if DEEPEVAL_IMPORT_RE.search(text):
                deepeval_leak_files.append(rel)

    if not eval_base_candidates:
        findings.append({
            "level": "HIGH",
            "check": "evaluation-provider-interface",
            "slug": slug_label,
            "message": (
                "No EvaluationProvider interface found. "
                "Create src/evaluation/base.py with EvaluationProvider Protocol. "
                "Use templates/evaluation-provider-template.py as scaffold."
            ),
        })

    if eval_base_candidates and not eval_deepeval_candidates:
        plan_chose_deepeval = _plan_names_provider(obs_body, r'\bdeepeval\b')
        plan_chose_alternative = _plan_names_provider(
            obs_body,
            r'\bragas\b', r'\btruelens\b', r'\bconfluent\b',
            r'\bphoenix\b', r'\brageval\b', r'\bcustom\s+eval\b',
        )
        if plan_chose_deepeval or not plan_chose_alternative:
            # Plan explicitly chose DeepEval, or no alternative was declared — require default impl
            findings.append({
                "level": "HIGH",
                "check": "deepeval-provider-missing",
                "slug": slug_label,
                "message": (
                    "EvaluationProvider interface exists but no DeepEvalProvider found. "
                    "Create src/evaluation/deepeval.py (default implementation). "
                    "Use templates/deepeval-evaluation-provider-template.py as scaffold. "
                    "If using a non-DeepEval framework, declare it explicitly in ## Observability Strategy."
                ),
            })
        else:
            # Plan declared a non-DeepEval alternative — ADR advisory only
            findings.append({
                "level": "MEDIUM",
                "check": "alternative-evaluation-provider-adr",
                "slug": slug_label,
                "message": (
                    "## Observability Strategy names a non-DeepEval evaluation framework. "
                    "Ensure an ADR exists justifying the alternative provider and that "
                    "the custom implementation satisfies the EvaluationProvider Protocol."
                ),
            })

    if eval_base_candidates and not eval_noop_candidates:
        findings.append({
            "level": "MEDIUM",
            "check": "noop-evaluation-provider",
            "slug": slug_label,
            "message": (
                "No NoopEvaluationProvider found. "
                "Create src/evaluation/noop.py for test isolation."
            ),
        })

    if deepeval_leak_files:
        findings.append({
            "level": "HIGH",
            "check": "deepeval-boundary",
            "slug": slug_label,
            "message": (
                "DeepEval SDK imported outside src/evaluation/ — boundary violation:\n"
                + "\n".join(f"  - {f}" for f in deepeval_leak_files)
            ),
        })

# ── output ───────────────────────────────────────────────────────────────────

if json_output:
    print(json.dumps({"findings": findings, "passed": len(findings) == 0}))
else:
    high_count = sum(1 for f in findings if f["level"] in ("HIGH", "ERROR"))
    if not findings:
        print("check-observability-setup: all checks passed")
    else:
        for f in findings:
            print(f"[{f['level']}] ({f['check']}) {f['slug']}: {f['message']}")
        if high_count:
            print(f"\n{high_count} HIGH/ERROR finding(s) — resolve before /at-implement.")
            sys.exit(1)
        else:
            print("\nNo HIGH findings. MEDIUM items are advisory.")

PYEOF
