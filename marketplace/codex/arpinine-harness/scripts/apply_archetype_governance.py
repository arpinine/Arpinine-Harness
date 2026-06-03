#!/usr/bin/env python3
"""Apply archetype-specific constitution addenda and starter rules."""

from __future__ import annotations

import argparse
import pathlib
import sys

from archetype_support import archetypes_dir, find_constitution_path, load_manifest, load_selected_archetype, write_metadata
from spec_provider import find_project_root


START_MARKER = "<!-- ARPININE:ARCHETYPE-CONSTITUTION:START -->"
END_MARKER = "<!-- ARPININE:ARCHETYPE-CONSTITUTION:END -->"


def render_constitution_addendum(archetype_name: str, manifest: dict) -> str:
    principles = manifest.get("constitution_principles", [])
    lines = [
        START_MARKER,
        "## Archetype Addendum",
        "",
        f"This repository uses the `{archetype_name}` archetype.",
        "These archetype invariants extend the base constitution and stay active unless superseded by an ADR and matching rule update.",
        "",
        "### Principles",
    ]
    for idx, principle in enumerate(principles, start=1):
        lines.append(f"{idx}. {principle}")
    lines.append(END_MARKER)
    return "\n".join(lines) + "\n"


def upsert_marked_section(text: str, section: str) -> str:
    if START_MARKER in text and END_MARKER in text:
        start = text.index(START_MARKER)
        end = text.index(END_MARKER) + len(END_MARKER)
        replaced = text[:start].rstrip() + "\n\n" + section
        tail = text[end:].lstrip("\n")
        return replaced + ("\n" + tail if tail else "")
    return text.rstrip() + "\n\n" + section


def render_rule(rule: dict) -> str:
    triggers = rule.get("triggers", [])
    lines = [
        "---",
        f"rule-id: {rule['rule_id']}",
        "category: archetype",
        "triggers:",
    ]
    for trigger in triggers:
        lines.append(f'  - {trigger!r}')
    lines.extend(
        [
            f"prevents: {rule['prevents']}",
            "source-adr: ~",
            f"evidence-project: archetype-{rule['rule_id']}",
            f"severity: {rule['severity']}",
            "active: true",
            "---",
            "",
            "## Rule",
            rule["rule"],
            "",
            "## Detection Pattern",
            rule["detection_pattern"],
            "",
            "## Correct Pattern",
            rule["correct_pattern"],
            "",
        ]
    )
    return "\n".join(lines)


def apply_rules(repo: pathlib.Path, manifest: dict) -> list[str]:
    rules_dir = repo / ".specify" / "rules" / "archetype"
    rules_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for rule in manifest.get("starter_rules", []):
        path = rules_dir / f"{rule['rule_id']}.md"
        path.write_text(render_rule(rule), encoding="utf-8")
        written.append(str(path.relative_to(repo)))
    return written


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archetype", help="Archetype name to apply; falls back to .specify/archetype.json")
    parser.add_argument("--repo", default=".", help="Project root (default: cwd)")
    args = parser.parse_args(argv)

    repo = find_project_root(pathlib.Path(args.repo).resolve()) or pathlib.Path(args.repo).resolve()
    archetype_name = (args.archetype or load_selected_archetype(repo)).strip()
    if not archetype_name:
        print("No archetype metadata found; skipping archetype governance.")
        return 0

    manifest = load_manifest(archetypes_dir(pathlib.Path(__file__).parent), archetype_name)
    write_metadata(repo, archetype_name)

    constitution_path = find_constitution_path(repo)
    if constitution_path is None:
        print("ERROR: Could not locate the generated constitution file.", file=sys.stderr)
        return 2

    constitution_text = constitution_path.read_text(encoding="utf-8")
    constitution_path.write_text(
        upsert_marked_section(constitution_text, render_constitution_addendum(archetype_name, manifest)),
        encoding="utf-8",
    )
    written_rules = apply_rules(repo, manifest)

    print(f"Archetype governance applied: {archetype_name}")
    print(f"Constitution updated: {constitution_path.relative_to(repo)}")
    if written_rules:
        print("Rules written:")
        for rule_path in written_rules:
            print(f"  - {rule_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
