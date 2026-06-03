#!/usr/bin/env python3
"""Check code and plan naming decisions against spec Domain Vocabulary for vocabulary drift."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

GENERIC_SUFFIXES = re.compile(
    r"\b(manager|handler|processor|dataobject|helper|util|utils|utilities)\b",
    re.IGNORECASE,
)
GENERIC_WORDS = frozenset(
    ["manager", "handler", "processor", "dataobject", "helper", "util", "utils", "utilities"]
)
CODE_EXTS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".kt", ".swift"}
CODE_ROOT_PREFIXES = ("src/", "lib/", "app/", "packages/", "services/", "internal/", "cmd/")
IDENTIFIER_RE = re.compile(r"\b([A-Z][A-Za-z0-9]+)\b")
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")


def find_project_root(start: pathlib.Path) -> pathlib.Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / ".specify").exists():
            return candidate
    return pathlib.Path(".").resolve()


REPO = find_project_root(pathlib.Path.cwd())
SPEC_ROOT = REPO / ".specify" / "specs"


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
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


def parse_vocabulary_table(section_text: str) -> list[dict[str, str]]:
    """Parse Domain Vocabulary table: columns Term, Definition, Forbidden Synonyms."""
    terms: list[dict[str, str]] = []
    rows: list[list[str]] = []
    for line in section_text.splitlines():
        m = TABLE_ROW_RE.match(line.strip())
        if not m:
            continue
        cells = [c.strip().strip("`") for c in m.group(1).split("|")]
        rows.append(cells)
    if len(rows) <= 1:
        return terms
    for row in rows[1:]:
        if len(row) < 1:
            continue
        term = row[0].strip()
        if not term or term.startswith("-") or set(term.replace("-", "").replace(":", "").strip()) == set():
            continue
        definition = row[1].strip() if len(row) > 1 else ""
        synonyms_raw = row[2].strip() if len(row) > 2 else ""
        synonyms = [s.strip() for s in re.split(r"[,;]", synonyms_raw) if s.strip()]
        terms.append({"term": term, "definition": definition, "forbidden_synonyms": synonyms})
    return terms


def parse_spec_file_refs(spec_text: str) -> list[str]:
    pattern = re.compile(
        r"(src|lib|app|packages|services|internal|cmd)/[A-Za-z0-9_/.\-]+\.(py|js|ts|go|rs|java|rb|kt|swift)"
    )
    return sorted(set(m.group(0) for m in pattern.finditer(spec_text)))


def iter_plan_code_files(plan_module_names: list[str], repo: pathlib.Path) -> list[str]:
    """Derive candidate code file paths from plan module boundary entries."""
    found: set[str] = set()
    for module in plan_module_names:
        candidate = repo / module.rstrip("/")
        if candidate.is_file() and candidate.suffix in CODE_EXTS:
            found.add(str(pathlib.Path(module.rstrip("/"))))
        elif candidate.is_dir():
            for code_file in sorted(candidate.rglob("*")):
                if code_file.is_file() and code_file.suffix in CODE_EXTS:
                    found.add(str(code_file.relative_to(repo)))
    return sorted(found)


def extract_class_names(text: str) -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for pattern in (
        re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)[\s:(]", re.MULTILINE),
        re.compile(r"^\s*type\s+([A-Z][A-Za-z0-9_]*)\s+struct\b", re.MULTILINE),
        re.compile(r"^\s*(?:pub\s+)?struct\s+([A-Z][A-Za-z0-9_]*)\b", re.MULTILINE),
        re.compile(r"^\s*(?:pub\s+)?enum\s+([A-Z][A-Za-z0-9_]*)\b", re.MULTILINE),
        re.compile(r"^\s*(?:pub\s+)?trait\s+([A-Z][A-Za-z0-9_]*)\b", re.MULTILINE),
        re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+([A-Z][A-Za-z0-9_]*)\b", re.MULTILINE),
        re.compile(r"^\s*(?:pub(?:\(crate\))?\s+)?(?:struct|enum|trait)\s+([A-Z][A-Za-z0-9_]*)\b", re.MULTILINE),
    ):
        for m in pattern.finditer(text):
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                names.append(name)
    return names


def extract_plan_module_names(plan_text: str) -> list[str]:
    section = section_body(plan_text, "Module Boundaries")
    names: list[str] = []
    for line in section.splitlines():
        m = TABLE_ROW_RE.match(line.strip())
        if not m:
            continue
        cells = [c.strip().strip("`") for c in m.group(1).split("|")]
        if cells and cells[0] and not cells[0].startswith("[") and not set(cells[0].replace("-", "").strip()) == set():
            names.append(cells[0])
    return names


def _ident_words(ident: str) -> list[str]:
    """Split an identifier (file path, CamelCase, snake_case) into unique lowercase words."""
    stem = pathlib.Path(ident).stem
    words = re.split(r"[_\-/. ]+", stem.lower())
    camel = re.findall(r"[a-z]+|[A-Z][a-z]*", ident)
    seen: set[str] = set()
    result: list[str] = []
    for w in words + [c.lower() for c in camel]:
        if w and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def _camel_words(term: str) -> list[str]:
    """Extract semantic words from a CamelCase or plain term."""
    return [w.lower() for w in re.findall(r"[A-Z][a-z]+|[A-Z]+(?=[A-Z]|$)|[a-z]+", term) if w]


def check_forbidden_synonyms(
    identifiers: list[str], terms: list[dict[str, str]], source: str
) -> list[dict[str, str | None]]:
    violations: list[dict[str, str | None]] = []
    for term_entry in terms:
        canonical_words = _camel_words(term_entry["term"])
        for ident in identifiers:
            ident_words = _ident_words(ident)
            # Skip: canonical term already present in identifier
            if all(cw in ident_words for cw in canonical_words):
                continue
            # Find the most specific (longest) matching synonym to avoid duplicate reports
            best_synonym: str | None = None
            best_length = 0
            for synonym in term_entry["forbidden_synonyms"]:
                syn_words = _camel_words(synonym)
                if syn_words and all(sw in ident_words for sw in syn_words):
                    if len(syn_words) > best_length:
                        best_synonym = synonym
                        best_length = len(syn_words)
            if best_synonym is not None:
                violations.append({
                    "rule_id": "vocabulary:forbidden-synonym",
                    "severity": "HIGH",
                    "file": source,
                    "line": None,
                    "message": (
                        f"'{ident}' uses forbidden synonym '{best_synonym}' "
                        f"— canonical term is '{term_entry['term']}'"
                    ),
                })
    return violations


def check_generic_names(
    identifiers: list[str], terms: list[dict[str, str]], source: str
) -> list[dict[str, str | None]]:
    violations: list[dict[str, str | None]] = []
    declared_term_words = [_ident_words(t["term"]) for t in terms]
    if not declared_term_words:
        return violations
    for ident in identifiers:
        ident_words = _ident_words(ident)
        generic_hits = [w for w in ident_words if w in GENERIC_WORDS]
        if not generic_hits:
            continue
        # Not a violation if the identifier already contains a full declared domain term
        has_domain_term = any(
            all(tw in ident_words for tw in term_words) for term_words in declared_term_words
        )
        if has_domain_term:
            continue
        example_terms = ", ".join(t["term"] for t in terms[:3])
        violations.append({
            "rule_id": "vocabulary:generic-name",
            "severity": "MEDIUM",
            "file": source,
            "line": None,
            "message": (
                f"'{ident}' uses generic word(s) {generic_hits} — prefer a name derived from "
                f"declared domain vocabulary: {example_terms}"
            ),
        })
    return violations


def check_vocabulary_coverage(
    plan_module_names: list[str], terms: list[dict[str, str]], slug: str
) -> list[dict[str, str | None]]:
    violations: list[dict[str, str | None]] = []
    if not terms or not plan_module_names:
        return violations
    all_names_lower = " ".join(n.lower() for n in plan_module_names)
    for term_entry in terms:
        term_lower = term_entry["term"].lower().replace(" ", "")
        if term_lower and term_lower not in all_names_lower.replace(" ", "").replace("_", "").replace("/", ""):
            violations.append({
                "rule_id": "vocabulary:term-uncovered",
                "severity": "MEDIUM",
                "file": f".specify/specs/{slug}/plan.md",
                "line": None,
                "message": (
                    f"Domain term '{term_entry['term']}' has no representation in plan module names "
                    f"— verify the concept is expressed in the implementation structure"
                ),
            })
    return violations


def analyze_spec(slug: str) -> dict[str, object]:
    spec_path = SPEC_ROOT / slug / "spec.md"
    plan_path = SPEC_ROOT / slug / "plan.md"
    spec_text = read_text(spec_path)
    plan_text = read_text(plan_path)

    vocab_section = section_body(spec_text, "Domain Vocabulary")
    terms = parse_vocabulary_table(vocab_section) if vocab_section else []

    violations: list[dict[str, str | None]] = []

    if not vocab_section and spec_text:
        violations.append({
            "rule_id": "vocabulary:missing-section",
            "severity": "MEDIUM",
            "file": f".specify/specs/{slug}/spec.md",
            "line": None,
            "message": "Spec is missing '## Domain Vocabulary' section — add before planning for non-trivial features",
        })

    plan_module_names = extract_plan_module_names(plan_text) if plan_text else []

    if terms and plan_module_names:
        violations.extend(check_vocabulary_coverage(plan_module_names, terms, slug))
        plan_source = f".specify/specs/{slug}/plan.md"
        violations.extend(check_forbidden_synonyms(plan_module_names, terms, plan_source))
        violations.extend(check_generic_names(plan_module_names, terms, plan_source))

    # Scan: spec-referenced files + files under plan module boundary paths (deduped)
    all_code_rels = sorted(set(parse_spec_file_refs(spec_text)) | set(iter_plan_code_files(plan_module_names, REPO)))

    if terms:
        for rel in all_code_rels:
            code_path = REPO / rel
            if not code_path.exists() or code_path.suffix not in CODE_EXTS:
                continue
            # Check the module path itself for vocabulary violations
            violations.extend(check_forbidden_synonyms([rel], terms, rel))
            violations.extend(check_generic_names([rel], terms, rel))
            # Check class/type names declared inside the file
            code_text = read_text(code_path)
            class_names = extract_class_names(code_text)
            if class_names:
                violations.extend(check_forbidden_synonyms(class_names, terms, rel))
                violations.extend(check_generic_names(class_names, terms, rel))

    return {"slug": slug, "violations": violations}


def print_results(results: list[dict[str, object]]) -> int:
    exit_code = 0
    for result in results:
        violations = result.get("violations", [])
        if not violations:
            continue
        print(f"Vocabulary Drift Check ({result['slug']}):")
        for v in violations:
            print(f"  {v['severity']}  {v['file']} — {v['message']}")
        high_count = sum(1 for v in violations if v.get("severity") == "HIGH")
        if high_count:
            print(f"  {high_count} HIGH violation(s) — block completion until resolved.")
            exit_code = 1
    return exit_code


def iter_slugs() -> list[str]:
    if not SPEC_ROOT.exists():
        return []
    return [p.name for p in sorted(SPEC_ROOT.iterdir()) if p.is_dir() and (p / "spec.md").exists()]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check vocabulary drift against spec Domain Vocabulary")
    parser.add_argument("--spec", help="Spec slug (e.g., 001-user-login)")
    parser.add_argument("--all", action="store_true", help="Check all specs")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args, _ = parser.parse_known_args(argv)

    if args.spec:
        results = [analyze_spec(args.spec)]
    elif args.all:
        results = [analyze_spec(slug) for slug in iter_slugs()]
    else:
        parser.print_help(sys.stderr)
        return 0

    has_high = any(
        v.get("severity") == "HIGH"
        for r in results
        for v in r.get("violations", [])
    )

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1 if has_high else 0

    return print_results(results)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
