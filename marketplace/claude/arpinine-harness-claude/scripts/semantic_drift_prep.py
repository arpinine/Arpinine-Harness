#!/usr/bin/env python3
"""Deterministic prep for semantic drift detection (Layer 2, ADR-0012).

This script does NOT judge drift. It pairs each spec clause (## section) with
the related code excerpts, emitting JSON the LLM-as-judge (the /at-audit agent)
consumes via skills/drift-detector/semantic-judge-prompt.md. The judging step is
the non-deterministic layer; this preparation is deterministic and testable.

Reuses the related-code resolution from quick_drift_check.py so structural and
semantic layers agree on which code belongs to a spec.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import quick_drift_check as qdc

# Bound excerpt size so a large file cannot blow up the judge prompt.
MAX_EXCERPT_LINES = 400
# Sections that carry no implementable behavior — skip to save judge calls.
SKIP_SECTIONS = {
    "domain vocabulary",
    "module boundaries",
    "harness strategy",
    "references",
    "changelog",
}


def clause_id(slug: str, heading: str) -> str:
    return f"{slug}:{qdc.normalize_token(heading) or 'body'}"


def spec_clauses(spec_text: str) -> list[dict[str, str]]:
    """Split a spec into ## sections. Each section is one judge-able clause."""
    matches = list(qdc.SECTION_RE.finditer(spec_text))
    clauses: list[dict[str, str]] = []
    for idx, match in enumerate(matches):
        heading = match.group(1).strip()
        if heading.lower() in SKIP_SECTIONS:
            continue
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(spec_text)
        body = spec_text[start:end].strip()
        if not body:
            continue
        clauses.append({"id": heading, "heading": heading, "text": body})
    return clauses


def numbered_excerpt(text: str, start_line: int = 1) -> tuple[str, str]:
    """Return (line_range, numbered_content) numbered from ABSOLUTE source lines.

    INVARIANT (judge contract): the `N\t` prefix on every emitted row equals the
    real source line N, so the judge cites file:line directly. `start_line` is the
    1-based source line of `text`'s first line. Today callers pass whole files
    (start_line=1) and only the tail past MAX_EXCERPT_LINES is dropped. If a future
    caller extracts a narrower snippet starting mid-file, it MUST pass the real
    start_line here — never re-number a snippet from 1, or citations point at the
    wrong source line. `test_excerpt_line_numbers...` and `test_snippet_offset...`
    lock this invariant.
    """
    if start_line < 1:
        raise ValueError("start_line must be 1-based (>= 1)")
    lines = text.splitlines()
    truncated = lines[:MAX_EXCERPT_LINES]
    numbered = "\n".join(f"{start_line + i}\t{line}" for i, line in enumerate(truncated))
    first = start_line
    last = start_line + len(truncated) - 1
    suffix = "" if len(lines) <= MAX_EXCERPT_LINES else f" (file has {len(lines)} lines; tail not shown)"
    return f"{first}-{last}{suffix}", numbered


def code_excerpts_for(clause_text: str) -> list[dict[str, str]]:
    """Code files referenced *within this clause's text*, line-numbered.

    Pairing is clause-specific (ADR-0012, semantic-judge-prompt.md): a clause is
    judged only against code it actually references, so a Billing clause is not
    judged against Auth code. Refs are resolved from the clause body alone using
    the same regex as the structural layer (`quick_drift_check.related_code_paths`).
    """
    excerpts: list[dict[str, str]] = []
    for rel in qdc.related_code_paths(clause_text):
        code_path = qdc.REPO / rel
        if not (code_path.exists() and code_path.suffix in qdc.CODE_EXTS):
            continue
        line_range, content = numbered_excerpt(qdc.read_text(code_path))
        excerpts.append({"path": rel, "line_range": line_range, "content": content})
    return excerpts


def prep_spec(spec: pathlib.Path) -> dict[str, object]:
    spec_text = qdc.read_text(spec)
    slug = spec.parent.name
    clauses = []
    has_code = False
    for clause in spec_clauses(spec_text):
        excerpts = code_excerpts_for(clause["text"])
        has_code = has_code or bool(excerpts)
        clauses.append(
            {
                "clause_id": clause_id(slug, clause["heading"]),
                "heading": clause["heading"],
                "clause_text": clause["text"],
                "code_excerpts": excerpts,
            }
        )
    return {
        "slug": slug,
        "spec": str(spec),
        "has_code": has_code,
        "clauses": clauses,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--spec", help="Path to a specific spec.md")
    parser.add_argument("--all", action="store_true", help="Prep all specs")
    args, _ = parser.parse_known_args(argv)

    if not qdc.SPEC_ROOT.exists():
        if qdc.find_project_root(pathlib.Path.cwd()) is None:
            print("Run semantic_drift_prep.py from the project root directory", file=sys.stderr)
            return 1
        return 0

    if args.spec:
        results = [prep_spec(pathlib.Path(args.spec))]
    else:
        results = [prep_spec(spec) for spec in qdc.iter_specs()]

    json.dump(results, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
