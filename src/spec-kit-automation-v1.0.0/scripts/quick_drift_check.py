#!/usr/bin/env python3
import json
import pathlib
import re
import sys


REPO = pathlib.Path(".")
SPEC_ROOT = REPO / ".specify" / "specs"

CODE_ROOT_PREFIXES = ("src/", "lib/", "app/", "packages/", "services/", "internal/", "cmd/")
CODE_EXTS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".kt", ".swift"}
ROUTE_EXTS = {".py", ".js", ".ts", ".go", ".rb", ".java", ".kt"}
SPEC_PATH_RE = re.compile(r"(src|lib|app|packages|services|internal|cmd)/[A-Za-z0-9_/.\-]+\.(py|js|ts|go|rs|java|rb|kt|swift)")
SPEC_ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+(/[A-Za-z0-9_./{}:\-]*)")
AGENTIC_HINT_RE = re.compile(r"\b(agent|assistant|prompt|llm|model|inference|eval)\b", re.IGNORECASE)
CODE_ENDPOINT_PATTERNS = [
    re.compile(r"""@(get|post|put|delete|patch)\(\s*["']([^"']+)["']""", re.IGNORECASE),
    re.compile(r"""\b(?:app|router)\.(get|post|put|delete|patch)\(\s*["']([^"']+)["']""", re.IGNORECASE),
    re.compile(r"""\b\w+\.(get|post|put|delete|patch)\(\s*["']([^"']+)["']""", re.IGNORECASE),
]


def read_stdin_payload():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return {}
    return payload.get("tool_input", {})


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text()
    except Exception:
        return ""


def iter_specs():
    return sorted(SPEC_ROOT.glob("*/spec.md"))


def endpoints_from_spec(text: str):
    return {f"{m.group(1).upper()} {m.group(2)}" for m in SPEC_ENDPOINT_RE.finditer(text)}


def endpoints_from_code(text: str):
    endpoints = set()
    for pattern in CODE_ENDPOINT_PATTERNS:
        for match in pattern.finditer(text):
            method, path = match.groups()
            endpoints.add(f"{method.upper()} {path}")
    return endpoints


def spec_refs(text: str):
    return sorted(set(m.group(0) for m in SPEC_PATH_RE.finditer(text)))


def target_specs(edited_file: str):
    specs = []
    if edited_file and edited_file.startswith(".specify/specs/") and edited_file.endswith("/spec.md"):
        edited_spec = pathlib.Path(edited_file)
        if edited_spec.exists():
            specs = [edited_spec]

    if not specs and edited_file:
        for spec in iter_specs():
            if edited_file in read_text(spec):
                specs.append(spec)

    if not specs:
        specs = list(iter_specs())

    return specs


def main():
    if not SPEC_ROOT.exists():
        return 0

    tool_input = read_stdin_payload()
    edited_file = tool_input.get("file_path", "")
    edited_path = pathlib.Path(edited_file) if edited_file else None
    edited_text = read_text(edited_path) if edited_path and edited_path.exists() else ""
    edited_is_code = bool(
        edited_file
        and edited_file.startswith(CODE_ROOT_PREFIXES)
        and edited_path
        and edited_path.suffix in CODE_EXTS
    )

    outputs = []

    for spec in target_specs(edited_file):
        spec_text = read_text(spec)
        slug = spec.parent.name
        findings = []

        for rel in spec_refs(spec_text):
            if not (REPO / rel).exists():
                findings.append(f"HIGH file reference missing: {rel}")

        spec_endpoints = endpoints_from_spec(spec_text)
        code_endpoints = set()

        for rel in spec_refs(spec_text):
            code_path = REPO / rel
            if code_path.exists() and code_path.suffix in ROUTE_EXTS:
                code_endpoints |= endpoints_from_code(read_text(code_path))

        if edited_is_code and edited_path.suffix in ROUTE_EXTS:
            code_endpoints |= endpoints_from_code(edited_text)

        for endpoint in sorted(code_endpoints - spec_endpoints)[:3]:
            findings.append(f"HIGH endpoint in code but not spec: {endpoint}")
        for endpoint in sorted(spec_endpoints - code_endpoints)[:3]:
            findings.append(f"MEDIUM endpoint in spec but not found in code: {endpoint}")

        eval_plan = REPO / ".specify" / "evals" / slug / "eval-plan.md"
        latest_results = REPO / ".specify" / "evals" / slug / "latest-results.md"
        if AGENTIC_HINT_RE.search(spec_text):
            if not eval_plan.exists():
                findings.append("HIGH missing eval plan for agentic spec")
            elif edited_is_code:
                if not latest_results.exists():
                    findings.append("HIGH eval plan exists but no latest results were found")
                else:
                    try:
                        if edited_path.stat().st_mtime > latest_results.stat().st_mtime:
                            findings.append("MEDIUM code changed after latest eval results; rerun /spec-eval")
                    except Exception:
                        pass

        if findings:
            outputs.append(f"Quick Drift Check ({slug}):")
            outputs.extend(f"  - {finding}" for finding in findings)
            outputs.append(f"  Run /spec-audit {spec} for full analysis and ADR resolution.")

    if outputs:
        print("\n".join(outputs))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
