from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "src" / "arpinine-harness-core" / "scripts"
SCRIPT = SCRIPTS_DIR / "semantic_drift_prep.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import semantic_drift_prep as sdp  # noqa: E402


class NumberedExcerptInvariantTests(unittest.TestCase):
    """Locks the judge contract: prefix N == real source line, for any start offset."""

    def test_whole_file_starts_at_one(self) -> None:
        rng, content = sdp.numbered_excerpt("a\nb\nc\n")
        self.assertEqual(rng, "1-3")
        self.assertEqual(content.splitlines()[0], "1\ta")

    def test_snippet_offset_preserves_true_source_lines(self) -> None:
        # A future narrow-snippet caller must pass the real start_line.
        rng, content = sdp.numbered_excerpt("def charge():\n    pass\n", start_line=42)
        self.assertEqual(rng, "42-43")
        self.assertEqual(content.splitlines()[0], "42\tdef charge():")
        self.assertEqual(content.splitlines()[1], "43\t    pass")

    def test_rejects_non_positive_start_line(self) -> None:
        with self.assertRaises(ValueError):
            sdp.numbered_excerpt("x\n", start_line=0)


class SemanticDriftPrepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "specs" / "001-demo").mkdir(parents=True)
        (self.repo / "src").mkdir()
        self.ratelimit_src = "# header\ndef limit(request):\n    return bucket(request.remote_addr)\n"
        (self.repo / "src" / "ratelimit.py").write_text(self.ratelimit_src, encoding="utf-8")
        (self.repo / ".specify" / "specs" / "001-demo" / "spec.md").write_text(
            "# Spec: Demo\n\n"
            "## Functional Requirements\n"
            "Rate-limit each authenticated user. Implementation path: src/ratelimit.py\n\n"
            "## Domain Vocabulary\n"
            "| Term | Definition | Forbidden |\n|------|-----------|-----------|\n",
            encoding="utf-8",
        )
        (self.repo / ".specify" / "specs" / "001-demo" / "plan.md").write_text(
            "# Plan\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def add_spec(self, slug: str, body: str) -> None:
        (self.repo / ".specify" / "specs" / slug).mkdir(parents=True)
        (self.repo / ".specify" / "specs" / slug / "spec.md").write_text(body, encoding="utf-8")

    def run_prep(self) -> dict[str, dict[str, object]]:
        result = subprocess.run(
            ["python3", str(SCRIPT), "--all"],
            cwd=self.repo,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return {r["slug"]: r for r in json.loads(result.stdout)}

    def clause(self, spec: dict[str, object], heading: str) -> dict[str, object]:
        return next(c for c in spec["clauses"] if c["heading"] == heading)

    def test_emits_one_clause_per_implementable_section(self) -> None:
        spec = self.run_prep()["001-demo"]
        headings = {c["heading"] for c in spec["clauses"]}
        self.assertIn("Functional Requirements", headings)

    def test_skips_non_behavioral_sections(self) -> None:
        spec = self.run_prep()["001-demo"]
        headings = {c["heading"] for c in spec["clauses"]}
        self.assertNotIn("Domain Vocabulary", headings)

    def test_clause_id_is_stable_and_slug_scoped(self) -> None:
        clause = self.clause(self.run_prep()["001-demo"], "Functional Requirements")
        self.assertEqual(clause["clause_id"], "001-demo:functionalrequirements")

    def test_excerpt_line_numbers_map_to_real_source_lines(self) -> None:
        clause = self.clause(self.run_prep()["001-demo"], "Functional Requirements")
        excerpt = next(e for e in clause["code_excerpts"] if e["path"] == "src/ratelimit.py")
        source_lines = self.ratelimit_src.splitlines()
        # Every "N\tcontent" prefix must equal the real 1-based source line.
        for row in excerpt["content"].splitlines():
            num, _, content = row.partition("\t")
            self.assertEqual(content, source_lines[int(num) - 1])
        self.assertEqual(excerpt["line_range"], f"1-{len(source_lines)}")

    def test_clause_specific_pairing_does_not_cross_contaminate(self) -> None:
        # Two sections referencing different files: each clause must see only its own.
        (self.repo / "src" / "auth.py").write_text("def login():\n    pass\n", encoding="utf-8")
        (self.repo / "src" / "billing.py").write_text("def charge():\n    pass\n", encoding="utf-8")
        self.add_spec(
            "002-multi",
            "# Spec: Multi\n\n"
            "## Authentication\nUsers log in. Implementation path: src/auth.py\n\n"
            "## Billing\nUsers are charged. Implementation path: src/billing.py\n",
        )
        spec = self.run_prep()["002-multi"]
        auth_files = {e["path"] for e in self.clause(spec, "Authentication")["code_excerpts"]}
        billing_files = {e["path"] for e in self.clause(spec, "Billing")["code_excerpts"]}
        self.assertEqual(auth_files, {"src/auth.py"})
        self.assertEqual(billing_files, {"src/billing.py"})

    def test_clause_without_code_reference_gets_empty_excerpts(self) -> None:
        self.add_spec(
            "003-nocode",
            "# Spec: NoCode\n\n## Functional Requirements\nDo a thing, no file named.\n",
        )
        spec = self.run_prep()["003-nocode"]
        self.assertFalse(spec["has_code"])
        for clause in spec["clauses"]:
            self.assertEqual(clause["code_excerpts"], [])


if __name__ == "__main__":
    unittest.main()
