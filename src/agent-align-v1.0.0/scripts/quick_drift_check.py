#!/usr/bin/env python3
"""Lightweight drift and conformance checks for AgentAlign."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


REPO = find_project_root(pathlib.Path.cwd()) or pathlib.Path(".").resolve()
SPEC_ROOT = REPO / ".specify" / "specs"

CODE_ROOT_PREFIXES = ("src/", "lib/", "app/", "packages/", "services/", "internal/", "cmd/")
CODE_EXTS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".kt", ".swift"}
ROUTE_EXTS = {".py", ".js", ".ts", ".go", ".rb", ".java", ".kt"}
SPEC_PATH_RE = re.compile(r"(src|lib|app|packages|services|internal|cmd)/[A-Za-z0-9_/.\-]+\.(py|js|ts|go|rs|java|rb|kt|swift)")
SPEC_ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH)\s+(/[A-Za-z0-9_./{}:\-]*)")
AGENTIC_HINT_RE = re.compile(r"\b(agent|assistant|prompt|llm|model|inference|eval|harness)\b", re.IGNORECASE)
OPENHARNESS_HINT_RE = re.compile(r"openharness", re.IGNORECASE)
OPENHARNESS_IMPORT_RE = re.compile(
    r"(@openharness/|from\s+[\"'][^\"']*openharness[^\"']*[\"']|require\([\"'][^\"']*openharness[^\"']*[\"']\))",
    re.IGNORECASE,
)
FRAMEWORK_IMPORT_RE = re.compile(
    r"\b(fastapi|flask|django|express|nestjs|sqlalchemy|typeorm|sequelize|prisma|redis)\b",
    re.IGNORECASE,
)
DOMAIN_PATH_RE = re.compile(r"(^|/)(domain|core|business)(/|$)", re.IGNORECASE)
ADAPTER_PATH_RE = re.compile(r"(^|/)(adapter|adapters|gateway|gateways|integration|integrations|infrastructure)(/|$)", re.IGNORECASE)
CODE_ENDPOINT_PATTERNS = [
    re.compile(r"""@(get|post|put|delete|patch)\(\s*["']([^"']+)["']""", re.IGNORECASE),
    re.compile(r"""\b(?:app|router)\.(get|post|put|delete|patch)\(\s*["']([^"']+)["']""", re.IGNORECASE),
    re.compile(r"""\b\w+\.(get|post|put|delete|patch)\(\s*["']([^"']+)["']""", re.IGNORECASE),
]
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
IMPORT_PATTERNS = [
    re.compile(r'^\s*from\s+([A-Za-z0-9_./@\-]+)\s+import\b', re.MULTILINE),
    re.compile(r'^\s*import\s+([A-Za-z0-9_.,\s/@\-]+)', re.MULTILINE),
    re.compile(r'^\s*import\s+.*?\s+from\s+[\"\']([^\"\']+)[\"\']', re.MULTILINE),
    re.compile(r'require\([\"\']([^\"\']+)[\"\']\)'),
]


def read_stdin_payload() -> dict[str, object]:
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


def iter_specs() -> list[pathlib.Path]:
    return sorted(SPEC_ROOT.glob("*/spec.md"))


def endpoints_from_spec(text: str) -> set[str]:
    return {f"{m.group(1).upper()} {m.group(2)}" for m in SPEC_ENDPOINT_RE.finditer(text)}


def endpoints_from_code(text: str) -> set[str]:
    endpoints: set[str] = set()
    for pattern in CODE_ENDPOINT_PATTERNS:
        for match in pattern.finditer(text):
            method, path = match.groups()
            endpoints.add(f"{method.upper()} {path}")
    return endpoints


def spec_refs(text: str) -> list[str]:
    return sorted(set(m.group(0) for m in SPEC_PATH_RE.finditer(text)))


def target_specs(edited_file: str) -> list[pathlib.Path]:
    specs: list[pathlib.Path] = []
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


def section_body(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for idx, match in enumerate(matches):
        if match.group(1).strip().lower() == title.lower():
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def parse_markdown_table(section_text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        rows.append(cells)
    if len(rows) <= 1:
        return []
    return rows[1:]


def split_dependency_cell(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r",|\n|\band\b", value)
    return [part.strip().strip("`") for part in parts if part.strip() and part.strip().lower() not in {"none", "n/a", "not applicable"}]


def module_aliases(module_name: str) -> set[str]:
    raw = module_name.strip().strip("`")
    aliases = {raw}
    path = pathlib.PurePosixPath(raw)
    if path.name:
        aliases.add(path.name)
    normalized = {normalize_token(alias) for alias in aliases if alias}
    return {alias for alias in aliases if alias} | normalized


def parse_module_boundaries(plan_text: str) -> list[dict[str, object]]:
    section = section_body(plan_text, "Module Boundaries")
    boundaries: list[dict[str, object]] = []
    for row in parse_markdown_table(section):
        if len(row) < 4:
            continue
        module, _, depends_on, interface = row[:4]
        if not module or "[" in module:
            continue
        boundaries.append(
            {
                "module": module,
                "depends_on": split_dependency_cell(depends_on),
                "interface": interface,
                "aliases": module_aliases(module),
            }
        )
    return boundaries


def owning_boundary(rel_path: str, boundaries: list[dict[str, object]]) -> dict[str, object] | None:
    rel_norm = normalize_token(rel_path)
    rel_parts = {normalize_token(part) for part in pathlib.Path(rel_path).parts if part}
    ranked: list[tuple[int, dict[str, object]]] = []
    for boundary in boundaries:
        score = 0
        module = str(boundary["module"])
        if "/" in module and rel_path.startswith(module.rstrip("/") + "/"):
            score += 4
        for alias in boundary["aliases"]:
            alias_norm = normalize_token(alias)
            if not alias_norm:
                continue
            if alias_norm in rel_parts:
                score += 3
            elif alias_norm in rel_norm:
                score += 1
        if score >= 2:
            ranked.append((score, boundary))
    if not ranked:
        return None
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def extract_import_targets(text: str) -> set[str]:
    targets: set[str] = set()
    for pattern in IMPORT_PATTERNS:
        for match in pattern.finditer(text):
            raw = match.group(1).strip()
            if "," in raw and " " in raw and not raw.startswith((".", "@", "src/", "lib/", "app/")):
                for part in [p.strip() for p in raw.split(",")]:
                    if part:
                        targets.add(part)
            else:
                targets.add(raw)
    return targets


def referenced_boundaries(import_targets: set[str], boundaries: list[dict[str, object]]) -> set[str]:
    refs: set[str] = set()
    normalized_targets: set[str] = set()
    for target in import_targets:
        normalized_targets.add(normalize_token(target))
        if "/" in target:
            normalized_targets |= {normalize_token(part) for part in target.split("/") if part}
        if "." in target:
            normalized_targets |= {normalize_token(part) for part in target.split(".") if part}

    for boundary in boundaries:
        for alias in boundary["aliases"]:
            alias_norm = normalize_token(alias)
            if alias_norm and alias_norm in normalized_targets:
                refs.add(str(boundary["module"]))
                break
    return refs


def related_code_paths(spec_text: str, edited_file: str = "") -> list[str]:
    paths = set(spec_refs(spec_text))
    if edited_file and edited_file.startswith(CODE_ROOT_PREFIXES):
        paths.add(edited_file)
    return sorted(paths)


def static_conformance_findings(spec: pathlib.Path, spec_text: str, edited_file: str = "", edited_text: str = "") -> list[str]:
    findings: list[str] = []
    plan_text = read_text(spec.parent / "plan.md")
    harness_strategy = section_body(plan_text, "Harness Strategy")
    harness_feature = bool(AGENTIC_HINT_RE.search(spec_text) or OPENHARNESS_HINT_RE.search(plan_text) or OPENHARNESS_HINT_RE.search(harness_strategy))
    boundaries = parse_module_boundaries(plan_text)

    for rel in related_code_paths(spec_text, edited_file):
        code_path = REPO / rel
        if rel == edited_file and edited_text:
            text = edited_text
        elif code_path.exists() and code_path.suffix in CODE_EXTS:
            text = read_text(code_path)
        else:
            continue

        if harness_feature and OPENHARNESS_IMPORT_RE.search(text) and not ADAPTER_PATH_RE.search(rel):
            findings.append(f"HIGH harness runtime import outside adapter/infrastructure: {rel}")

        if DOMAIN_PATH_RE.search(rel) and FRAMEWORK_IMPORT_RE.search(text):
            findings.append(f"HIGH framework import in domain/business layer: {rel}")

        if boundaries:
            owner = owning_boundary(rel, boundaries)
            if owner:
                imports = extract_import_targets(text)
                refs = referenced_boundaries(imports, boundaries)
                allowed = {str(owner["module"])}
                allowed |= set(str(dep).strip().strip("`") for dep in owner["depends_on"])
                for ref in sorted(refs):
                    if ref not in allowed:
                        findings.append(
                            f"HIGH module boundary violation: {rel} imports `{ref}` "
                            f"outside declared dependencies for `{owner['module']}`"
                        )

    if len(findings) > 5:
        extra = len(findings) - 5
        findings = findings[:5]
        findings.append(f"... and {extra} more conformance findings - run /spec-audit for full analysis")
    return findings


def analyze_spec(spec: pathlib.Path, edited_file: str = "", edited_text: str = "") -> dict[str, object]:
    spec_text = read_text(spec)
    slug = spec.parent.name
    findings: list[str] = []

    for rel in spec_refs(spec_text):
        if not (REPO / rel).exists():
            findings.append(f"HIGH file reference missing: {rel}")

    spec_endpoints = endpoints_from_spec(spec_text)
    code_endpoints: set[str] = set()

    for rel in spec_refs(spec_text):
        code_path = REPO / rel
        if code_path.exists() and code_path.suffix in ROUTE_EXTS:
            code_endpoints |= endpoints_from_code(read_text(code_path))

    edited_path = pathlib.Path(edited_file) if edited_file else None
    edited_is_code = bool(
        edited_file
        and edited_file.startswith(CODE_ROOT_PREFIXES)
        and edited_path
        and edited_path.suffix in CODE_EXTS
    )
    if edited_is_code and edited_path and edited_path.suffix in ROUTE_EXTS:
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
        elif edited_is_code and edited_path:
            if not latest_results.exists():
                findings.append("HIGH eval plan exists but no latest results were found")
            else:
                try:
                    if edited_path.stat().st_mtime > latest_results.stat().st_mtime:
                        findings.append("MEDIUM code changed after latest eval results; rerun /spec-eval")
                except Exception:
                    pass

    findings.extend(static_conformance_findings(spec, spec_text, edited_file, edited_text))
    return {"slug": slug, "spec": str(spec), "findings": findings}


def print_results(results: list[dict[str, object]]) -> int:
    outputs: list[str] = []
    for result in results:
        findings = result["findings"]
        if findings:
            outputs.append(f"Quick Drift Check ({result['slug']}):")
            outputs.extend(f"  - {finding}" for finding in findings)
            outputs.append(f"  Run /spec-audit {result['spec']} for full analysis and ADR resolution.")
    if outputs:
        print("\n".join(outputs))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--spec", help="Path to a specific spec.md")
    parser.add_argument("--all", action="store_true", help="Analyze all specs")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args, _ = parser.parse_known_args(argv)

    if not SPEC_ROOT.exists():
        if find_project_root(pathlib.Path.cwd()) is None:
            print("Run quick_drift_check.py from the project root directory", file=sys.stderr)
            return 1
        return 0

    if args.spec:
        results = [analyze_spec(pathlib.Path(args.spec))]
    elif args.all:
        results = [analyze_spec(spec) for spec in iter_specs()]
    else:
        tool_input = read_stdin_payload()
        edited_file = str(tool_input.get("file_path", ""))
        edited_path = pathlib.Path(edited_file) if edited_file else None
        edited_text = read_text(edited_path) if edited_path and edited_path.exists() else ""
        results = [analyze_spec(spec, edited_file, edited_text) for spec in target_specs(edited_file)]

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    return print_results(results)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
