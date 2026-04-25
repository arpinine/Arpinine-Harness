#!/bin/bash
# Pre-edit architecture readiness gate.
# Block implementation edits until the governing plan defines architecture boundaries.

INPUT=$(cat)

if ! command -v python3 &>/dev/null; then
  exit 0
fi

RESULT=$(
  printf '%s' "$INPUT" | python3 -c '
import json
import pathlib
import re
import sys

CODE_PREFIXES = ("src/", "lib/", "app/", "packages/", "services/", "internal/", "cmd/")
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(
    r"\[(module|choice|quality dimension|risk|feature name|spec-number|name"
    r"|single clear concern|allowed dependencies|api / port / adapter"
    r"|unit / contract / integration|mock adapter / in-memory fake / fixture"
    r"|reason|internal service / adapter / port"
    r"|session / persistent / none / bounded context"
    r"|approval flow / policy / limits)\]",
    re.IGNORECASE,
)
HARNESS_HINT_RE = re.compile(r"(harness|agent runtime|openharness)", re.IGNORECASE)
NOT_APPLICABLE_RE = re.compile(r"\b(n/?a|not applicable)\b", re.IGNORECASE)

try:
    payload = json.load(sys.stdin)
except Exception:
    raise SystemExit(0)

tool_input = payload.get("tool_input", {})
file_path = tool_input.get("file_path", "")

if not file_path or not file_path.startswith(CODE_PREFIXES):
    raise SystemExit(0)

repo = pathlib.Path(".")
spec_root = repo / ".specify" / "specs"
if not spec_root.exists():
    print("VIOLATION: implementation edit attempted before workflow setup")
    print("Run /at-init and create a governing spec/plan before editing implementation files.")
    raise SystemExit(1)

specs = sorted(spec_root.glob("*/spec.md"))
if not specs:
    print("VIOLATION: no governing spec found for implementation work")
    print("Run /at-new before editing implementation files.")
    raise SystemExit(1)

candidate_specs = []
for spec in specs:
    try:
        text = spec.read_text()
    except Exception:
        text = ""
    if file_path in text:
        candidate_specs.append(spec)

if not candidate_specs:
    if len(specs) == 1:
        candidate_specs = specs
    else:
        print(f"VIOLATION: cannot determine governing spec for {file_path}")
        print("Reference the implementation path in the relevant spec or narrow work to a single active spec before coding.")
        raise SystemExit(1)

def section_body(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for idx, match in enumerate(matches):
        if match.group(1).strip().lower() == title.lower():
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""

violations = []
for spec in candidate_specs:
    plan = spec.parent / "plan.md"
    if not plan.exists():
        violations.append(f"{spec.parent.name}: missing plan.md")
        continue

    try:
        plan_text = plan.read_text()
    except Exception:
        violations.append(f"{spec.parent.name}: plan.md not readable")
        continue

    required_sections = [
        "Module Boundaries",
        "Dependency Rules",
        "Testability By Boundary",
    ]

    for section in required_sections:
        body = section_body(plan_text, section)
        if not body:
            violations.append(f"{spec.parent.name}: missing section `{section}`")
            continue
        cleaned = "\n".join(
            line for line in body.splitlines()
            if line.strip() and not set(line.strip()) <= {"|", "-", " "}
        ).strip()
        if not cleaned or PLACEHOLDER_RE.search(cleaned):
            violations.append(f"{spec.parent.name}: section `{section}` is still a placeholder")

    harness_needed = HARNESS_HINT_RE.search(file_path) is not None or HARNESS_HINT_RE.search(plan_text) is not None
    if harness_needed:
        body = section_body(plan_text, "Harness Strategy")
        if not body:
            violations.append(f"{spec.parent.name}: missing section `Harness Strategy`")
        else:
            cleaned = "\n".join(
                line for line in body.splitlines()
                if line.strip() and not set(line.strip()) <= {"|", "-", " "}
            ).strip()
            if NOT_APPLICABLE_RE.search(cleaned):
                pass
            elif not cleaned or PLACEHOLDER_RE.search(cleaned):
                violations.append(
                    f"{spec.parent.name}: section `Harness Strategy` is still a placeholder "
                    f"- fill it in or write 'N/A' if no harness is needed"
                )

if violations:
    print("VIOLATION: architecture requirements must be defined before implementation")
    for item in violations:
        print(f"- {item}")
    print("Run /at-plan and complete the architecture sections before editing implementation files.")
    raise SystemExit(1)
' 2>/dev/null
)

if [[ -n "$RESULT" ]]; then
  printf '%s\n' "$RESULT"
  exit 1
fi

exit 0
