#!/bin/bash
# Harness readiness gate.
# Verifies that a named harness runtime is correctly bounded before /at-plan completes.
# Run automatically by /at-plan when ## Harness Strategy names a runtime.
# Usage: scripts/check-harness-readiness.sh [--spec <slug>] [--json]
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
  echo "python3 not found — skipping harness readiness check" >&2
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
    candidate_plans = sorted((specify_root / "specs").glob("*/plan.md")) if (specify_root / "specs").exists() else []

if not candidate_plans:
    result = {"status": "skip", "reason": "no plan.md found — run /at-plan first"}
    if json_output:
        print(json.dumps(result))
    else:
        print(f"SKIP: {result['reason']}")
    sys.exit(0)

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
NA_RE = re.compile(r"\bN/?A\b", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(
    r"\[(?:describe why|interface name|explicit allowlist|scope:|which actions|what changes"
    r"|e\.g\.|runtime selected|e\.g\. OpenHarness|reason)\b",
    re.IGNORECASE,
)

HARNESS_RUNTIME_RE = re.compile(
    r"openharness|langgraph|pydantic[\s_-]?ai|semantic[\s_-]?kernel|crewai|autogen|custom",
    re.IGNORECASE,
)

HARNESS_IMPORT_RE = re.compile(
    r"^\s*(?:from|import)\s+(openharness|langgraph|pydantic_ai|semantic_kernel|crewai|autogen)",
    re.MULTILINE,
)

ADAPTERS_PATH_RE = re.compile(r"(?:^|/)adapters?/")
SESSION_RESET_RE = re.compile(r"engine\.clear\(\)|\.reset\(\)|session\.clear\(\)|memory\.clear\(\)")
TOOL_REGISTRY_RE = re.compile(r"ToolRegistry|tool_registry|register_tool|register\(")


def section_body(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for idx, m in enumerate(matches):
        if m.group(1).strip().lower() == title.lower():
            start = m.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""


findings = []  # list of {level, check, message}

for plan_path in candidate_plans:
    slug_label = plan_path.parent.name

    try:
        plan_text = plan_path.read_text()
    except Exception as exc:
        findings.append({"level": "ERROR", "check": "plan-readable", "slug": slug_label,
                         "message": f"cannot read plan.md: {exc}"})
        continue

    harness_body = section_body(plan_text, "Harness Strategy")

    # No harness section — skip all checks for this spec
    if not harness_body:
        continue

    # N/A — harness intentionally absent, nothing to check
    if NA_RE.search(harness_body):
        continue

    # Harness is required — validate all controls are documented
    if PLACEHOLDER_RE.search(harness_body):
        findings.append({
            "level": "HIGH",
            "check": "harness-controls-complete",
            "slug": slug_label,
            "message": (
                "## Harness Strategy contains unfilled placeholders. "
                "Complete all seven controls (runtime, boundary, tools, memory, permissions, swap path, why) "
                "before implementation."
            ),
        })

    runtime_match = HARNESS_RUNTIME_RE.search(harness_body)
    if not runtime_match:
        findings.append({
            "level": "HIGH",
            "check": "runtime-named",
            "slug": slug_label,
            "message": (
                "## Harness Strategy does not name a runtime. "
                "Specify the runtime (e.g. OpenHarness, LangGraph) or set N/A."
            ),
        })

    # ── source tree checks (only when source code exists) ──────────────────
    src_roots = [d for d in ["app", "src", "lib", "packages", "services"] if (repo / d).is_dir()]
    if not src_roots:
        continue

    harness_files = []
    non_adapter_violations = []
    missing_session_reset = []
    missing_tool_registry = []
    adapter_files = []

    for src_root in src_roots:
        for py_file in (repo / src_root).rglob("*.py"):
            rel = str(py_file.relative_to(repo))
            text = py_file.read_text(errors="replace")

            if HARNESS_IMPORT_RE.search(text):
                harness_files.append(rel)
                if ADAPTERS_PATH_RE.search(rel):
                    adapter_files.append(rel)
                else:
                    non_adapter_violations.append(rel)

            if ADAPTERS_PATH_RE.search(rel) and HARNESS_IMPORT_RE.search(text):
                if not SESSION_RESET_RE.search(text):
                    missing_session_reset.append(rel)
                if not TOOL_REGISTRY_RE.search(text):
                    missing_tool_registry.append(rel)

    if non_adapter_violations:
        findings.append({
            "level": "HIGH",
            "check": "harness-import-boundary",
            "slug": slug_label,
            "message": (
                f"Harness imports found outside adapters/ — move to adapter layer:\n"
                + "\n".join(f"  - {f}" for f in non_adapter_violations)
            ),
        })

    if adapter_files and missing_session_reset:
        findings.append({
            "level": "HIGH",
            "check": "session-reset",
            "slug": slug_label,
            "message": (
                f"Adapter files with harness imports have no session reset call "
                f"(engine.clear() / session.clear()):\n"
                + "\n".join(f"  - {f}" for f in missing_session_reset)
            ),
        })

    if adapter_files and missing_tool_registry:
        findings.append({
            "level": "MEDIUM",
            "check": "tool-registry",
            "slug": slug_label,
            "message": (
                f"Adapter files with harness imports have no ToolRegistry usage — "
                f"verify tool allowlist is explicitly declared:\n"
                + "\n".join(f"  - {f}" for f in missing_tool_registry)
            ),
        })

# ── output ───────────────────────────────────────────────────────────────────

if json_output:
    print(json.dumps({"findings": findings, "passed": len(findings) == 0}))
else:
    high_count = sum(1 for f in findings if f["level"] in ("HIGH", "ERROR"))
    if not findings:
        print("check-harness-readiness: all checks passed")
    else:
        for f in findings:
            print(f"[{f['level']}] ({f['check']}) {f['slug']}: {f['message']}")
        if high_count:
            print(f"\n{high_count} HIGH/ERROR finding(s) — resolve before /at-implement.")
            sys.exit(1)
        else:
            print("\nNo HIGH findings. MEDIUM items are advisory.")

PYEOF
