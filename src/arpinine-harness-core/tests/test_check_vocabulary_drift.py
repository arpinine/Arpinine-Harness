from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import tempfile
import textwrap
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "check_vocabulary_drift.py"

SPEC_WITH_VOCAB = textwrap.dedent("""
    # Spec: Order Fulfillment

    ## Domain Vocabulary

    **Bounded Context**: Order Fulfillment

    | Term | Definition | Forbidden Synonyms |
    |------|-----------|-------------------|
    | FulfillmentBatch | A grouped set of orders released for warehouse processing | Batch, Processor, OrderProcessor |
    | SettlementWindow | The time period within which payment settlement must complete | Window, Period, Manager, SettlementManager |
    | InventoryReservation | A hold placed on inventory preventing other allocations | Hold, Lock, Reservation |

    **Disambiguation Notes**:
    - FulfillmentBatch != InventoryReservation: batches group orders; reservations hold stock.
""").strip()

SPEC_WITHOUT_VOCAB = textwrap.dedent("""
    # Spec: Simple Feature

    ## Requirements
    - FR-001: Do something.
""").strip()

PLAN_WITH_GOOD_NAMES = textwrap.dedent("""
    # Plan: Order Fulfillment

    ## Module Boundaries
    | Module / Component | Responsibility | Depends On | Interface / Adapter |
    |--------------------|----------------|------------|---------------------|
    | fulfillment/domain/fulfillment_batch.py | FulfillmentBatch aggregate | none | none |
    | settlement/domain/settlement_window.py | SettlementWindow value object | none | none |
    | inventory/domain/inventory_reservation.py | InventoryReservation entity | none | none |
""").strip()

PLAN_WITH_GENERIC_NAMES = textwrap.dedent("""
    # Plan: Order Fulfillment

    ## Module Boundaries
    | Module / Component | Responsibility | Depends On | Interface / Adapter |
    |--------------------|----------------|------------|---------------------|
    | fulfillment/order_processor.py | Processes orders | none | none |
    | settlement/settlement_manager.py | Manages settlement | none | none |
""").strip()

PLAN_WITH_FORBIDDEN_SYNONYM = textwrap.dedent("""
    # Plan: Order Fulfillment

    ## Module Boundaries
    | Module / Component | Responsibility | Depends On | Interface / Adapter |
    |--------------------|----------------|------------|---------------------|
    | fulfillment/order_processor.py | OrderProcessor class | none | none |
""").strip()


class VocabularyDriftTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "specs" / "001-fulfillment").mkdir(parents=True)
        (self.repo / "src").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_check(self, extra_args: list[str] | None = None) -> tuple[int, list[dict]]:
        args = ["python3", str(SCRIPT), "--spec", "001-fulfillment", "--json"]
        if extra_args:
            args.extend(extra_args)
        result = subprocess.run(
            args,
            cwd=self.repo,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        data = json.loads(result.stdout) if result.stdout.strip() else []
        return result.returncode, data

    def write_spec(self, content: str) -> None:
        (self.repo / ".specify" / "specs" / "001-fulfillment" / "spec.md").write_text(
            content, encoding="utf-8"
        )

    def write_plan(self, content: str) -> None:
        (self.repo / ".specify" / "specs" / "001-fulfillment" / "plan.md").write_text(
            content, encoding="utf-8"
        )

    def write_code(self, filename: str, content: str) -> None:
        path = self.repo / "src" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def violations(self) -> list[dict]:
        _, data = self.run_check()
        return data[0]["violations"] if data else []

    def rule_ids(self) -> list[str]:
        return [v["rule_id"] for v in self.violations()]

    def test_missing_vocab_section_reported(self) -> None:
        self.write_spec(SPEC_WITHOUT_VOCAB)
        ids = self.rule_ids()
        self.assertIn("vocabulary:missing-section", ids)

    def test_no_violations_for_good_names(self) -> None:
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_GOOD_NAMES)
        ids = self.rule_ids()
        self.assertNotIn("vocabulary:forbidden-synonym", ids)

    def test_forbidden_synonym_in_plan_flagged(self) -> None:
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_FORBIDDEN_SYNONYM)
        ids = self.rule_ids()
        self.assertIn("vocabulary:forbidden-synonym", ids)

    def test_forbidden_synonym_is_high_severity(self) -> None:
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_FORBIDDEN_SYNONYM)
        highs = [v for v in self.violations() if v["rule_id"] == "vocabulary:forbidden-synonym"]
        self.assertTrue(all(v["severity"] == "HIGH" for v in highs))

    def test_generic_suffix_in_plan_flagged(self) -> None:
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_GENERIC_NAMES)
        ids = self.rule_ids()
        self.assertIn("vocabulary:generic-name", ids)

    def test_generic_suffix_is_medium_severity(self) -> None:
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_GENERIC_NAMES)
        mediums = [v for v in self.violations() if v["rule_id"] == "vocabulary:generic-name"]
        self.assertTrue(all(v["severity"] == "MEDIUM" for v in mediums))

    def test_uncovered_term_flagged_when_plan_has_no_module_for_term(self) -> None:
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_GENERIC_NAMES)
        ids = self.rule_ids()
        self.assertIn("vocabulary:term-uncovered", ids)

    def test_forbidden_synonym_in_class_name_flagged(self) -> None:
        self.write_spec(
            SPEC_WITH_VOCAB
            + "\n\nImplementation: src/order_processor.py\n"
        )
        self.write_plan(PLAN_WITH_GOOD_NAMES)
        self.write_code(
            "order_processor.py",
            "class OrderProcessor:\n    pass\n",
        )
        ids = self.rule_ids()
        self.assertIn("vocabulary:forbidden-synonym", ids)

    def test_spec_without_vocab_does_not_flag_code_generics(self) -> None:
        self.write_spec(SPEC_WITHOUT_VOCAB)
        ids = self.rule_ids()
        self.assertNotIn("vocabulary:generic-name", ids)

    def test_json_output_structure(self) -> None:
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_FORBIDDEN_SYNONYM)
        _, data = self.run_check()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["slug"], "001-fulfillment")
        self.assertIn("violations", data[0])
        for v in data[0]["violations"]:
            self.assertIn("rule_id", v)
            self.assertIn("severity", v)
            self.assertIn("message", v)

    def test_unreferenced_file_with_forbidden_class_flagged(self) -> None:
        """File in plan module dir but absent from spec refs must still be scanned."""
        self.write_spec(SPEC_WITH_VOCAB)  # no file refs
        plan = textwrap.dedent("""
            # Plan
            ## Module Boundaries
            | Module / Component | Responsibility | Depends On | Interface / Adapter |
            |--------------------|----------------|------------|---------------------|
            | src/order/ | Order domain | none | none |
        """).strip()
        self.write_plan(plan)
        (self.repo / "src" / "order").mkdir(parents=True, exist_ok=True)
        (self.repo / "src" / "order" / "order_processor.py").write_text(
            "class OrderProcessor:\n    pass\n", encoding="utf-8"
        )
        ids = self.rule_ids()
        self.assertIn("vocabulary:forbidden-synonym", ids)

    def test_json_mode_exits_nonzero_on_high_violation(self) -> None:
        """--json must return non-zero exit code when HIGH violations exist."""
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_FORBIDDEN_SYNONYM)
        rc, data = self.run_check()
        highs = [v for v in data[0]["violations"] if v["severity"] == "HIGH"]
        self.assertTrue(highs, "Expected HIGH violations in output")
        self.assertEqual(rc, 1, "Expected non-zero exit code for HIGH violations")

    def test_json_mode_exits_zero_with_no_high_violations(self) -> None:
        """--json must return zero when no HIGH violations exist."""
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_GOOD_NAMES)
        rc, _ = self.run_check()
        self.assertEqual(rc, 0)

    def test_file_path_with_forbidden_synonym_flagged_even_without_classes(self) -> None:
        """Module path containing forbidden synonym must flag even when file has no class definitions."""
        self.write_spec(SPEC_WITH_VOCAB + "\n\nImplementation: src/order_processor.py\n")
        self.write_plan(PLAN_WITH_GOOD_NAMES)
        self.write_code("order_processor.py", "def run():\n    pass\n")  # functions only, no class
        ids = self.rule_ids()
        self.assertIn("vocabulary:forbidden-synonym", ids)

    def test_no_duplicate_violations_for_overlapping_synonyms(self) -> None:
        """Processor and OrderProcessor both forbidden: OrderProcessor class yields exactly one HIGH."""
        spec = textwrap.dedent("""
            # Spec: Fulfillment

            ## Domain Vocabulary

            | Term | Definition | Forbidden Synonyms |
            |------|-----------|-------------------|
            | FulfillmentBatch | Grouped orders for warehouse | Processor, OrderProcessor |
        """).strip()
        plan = textwrap.dedent("""
            # Plan
            ## Module Boundaries
            | Module / Component | Responsibility | Depends On | Interface / Adapter |
            |--------------------|----------------|------------|---------------------|
            | src/fulfillment/ | Fulfillment domain | none | none |
        """).strip()
        (self.repo / "src" / "fulfillment").mkdir(parents=True, exist_ok=True)
        (self.repo / "src" / "fulfillment" / "batch.py").write_text(
            "class OrderProcessor:\n    pass\n", encoding="utf-8"
        )
        (self.repo / ".specify" / "specs" / "001-fulfillment" / "spec.md").write_text(spec, encoding="utf-8")
        (self.repo / ".specify" / "specs" / "001-fulfillment" / "plan.md").write_text(plan, encoding="utf-8")
        highs = [v for v in self.violations() if v["rule_id"] == "vocabulary:forbidden-synonym"]
        # OrderProcessor matches both 'Processor' and 'OrderProcessor' synonyms — must report once only
        class_violations = [v for v in highs if "'OrderProcessor'" in v["message"] and v["message"].startswith("'OrderProcessor'")]
        self.assertEqual(len(class_violations), 1, f"Expected 1 violation for OrderProcessor class, got: {class_violations}")

    def test_compound_synonym_in_snake_case_path_flagged(self) -> None:
        """Compound forbidden synonym 'OrderProcessor' must produce HIGH for src/order_processor.py."""
        spec = textwrap.dedent("""
            # Spec: Fulfillment

            ## Domain Vocabulary

            | Term | Definition | Forbidden Synonyms |
            |------|-----------|-------------------|
            | FulfillmentBatch | Grouped orders | OrderProcessor |
        """).strip()
        self.write_spec(spec + "\n\nImplementation: src/order_processor.py\n")
        self.write_plan(PLAN_WITH_GOOD_NAMES)
        self.write_code("order_processor.py", "def run():\n    pass\n")  # no class — path check only
        highs = [v for v in self.violations() if v["rule_id"] == "vocabulary:forbidden-synonym"]
        self.assertTrue(highs, "Expected HIGH violation for compound synonym in snake_case path")

    def test_generic_hits_message_has_no_duplicate_words(self) -> None:
        """Generic word appearing via multiple split paths must appear once in the violation message."""
        self.write_spec(SPEC_WITH_VOCAB)
        self.write_plan(PLAN_WITH_GENERIC_NAMES)
        mediums = [v for v in self.violations() if v["rule_id"] == "vocabulary:generic-name"]
        for v in mediums:
            # Extract the list portion from the message, e.g. "['processor']"
            import ast
            match = re.search(r"\[([^\]]+)\]", v["message"])
            if match:
                words = [w.strip().strip("'") for w in match.group(1).split(",")]
                self.assertEqual(len(words), len(set(words)), f"Duplicate words in message: {v['message']}")

    def test_all_flag_processes_multiple_specs(self) -> None:
        (self.repo / ".specify" / "specs" / "002-other").mkdir(parents=True)
        (self.repo / ".specify" / "specs" / "002-other" / "spec.md").write_text(
            SPEC_WITHOUT_VOCAB, encoding="utf-8"
        )
        self.write_spec(SPEC_WITH_VOCAB)
        result = subprocess.run(
            ["python3", str(SCRIPT), "--all", "--json"],
            cwd=self.repo,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        data = json.loads(result.stdout)
        self.assertEqual(len(data), 2)


if __name__ == "__main__":
    unittest.main()
