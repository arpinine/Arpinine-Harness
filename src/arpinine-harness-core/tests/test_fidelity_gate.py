"""
Tests for fidelity_gate.py — the zero-divergence governance-outcome diff.

Governs: specs/011-context-compression-governance (TASK-009)
ADRs: ADR-0017 (zero divergence — any single differing field is a FAIL; no
      materiality tolerance).
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "fidelity_gate.py"
)
FIELDS = ["interpretation", "route", "confidence", "command_class", "requires_confirmation"]


def _load():
    spec = importlib.util.spec_from_file_location("fidelity_gate", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module  # dataclass introspection needs this
    spec.loader.exec_module(module)
    return module


def _outcome(route="/at-status", confidence="medium"):
    return {
        "interpretation": "status request with open drift",
        "route": route,
        "confidence": confidence,
        "command_class": "return",
        "requires_confirmation": False,
    }


class TestFidelityGate(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE_PATH.exists(), f"missing module at {MODULE_PATH}")
        self.m = _load()
        self.gate = self.m.FidelityGate(FIELDS)

    def test_identical_outcomes_pass_with_no_divergences(self) -> None:
        verdict = self.gate.compare(_outcome(), _outcome())
        self.assertTrue(verdict.passed)
        self.assertEqual(verdict.divergences, [])

    def test_single_field_difference_fails(self) -> None:
        verdict = self.gate.compare(_outcome(), _outcome(route="/at-implement"))
        self.assertFalse(verdict.passed)
        self.assertEqual(len(verdict.divergences), 1)
        d = verdict.divergences[0]
        self.assertEqual(d["field"], "route")
        self.assertEqual(d["off"], "/at-status")
        self.assertEqual(d["on"], "/at-implement")

    def test_zero_tolerance_confidence_shift_fails(self) -> None:
        verdict = self.gate.compare(_outcome(), _outcome(confidence="high"))
        self.assertFalse(verdict.passed)
        self.assertEqual(verdict.divergences[0]["field"], "confidence")

    def test_only_declared_fields_are_compared(self) -> None:
        on = _outcome()
        on["session_slug"] = "ignored-extra-field"
        verdict = self.gate.compare(_outcome(), on)
        self.assertTrue(verdict.passed)

    def test_missing_field_is_a_divergence(self) -> None:
        on = _outcome()
        del on["route"]
        verdict = self.gate.compare(_outcome(), on)
        self.assertFalse(verdict.passed)
        self.assertEqual(verdict.divergences[0]["field"], "route")

    def test_aggregate_over_scenarios_all_pass(self) -> None:
        pairs = [(_outcome(), _outcome()), (_outcome(route="/at-eval"), _outcome(route="/at-eval"))]
        report = self.gate.aggregate(pairs)
        self.assertTrue(report["passed"])
        self.assertEqual(report["divergent_scenarios"], 0)

    def test_compare_with_per_scenario_keys(self) -> None:
        off = {"AC-001": False, "AC-002": True}
        on = {"AC-001": False, "AC-002": True}
        self.assertTrue(self.gate.compare(off, on, keys=["AC-001", "AC-002"]).passed)
        bad = {"AC-001": True, "AC-002": True}
        v = self.gate.compare(off, bad, keys=["AC-001", "AC-002"])
        self.assertFalse(v.passed)
        self.assertEqual(v.divergences[0]["field"], "AC-001")

    def test_aggregate_honours_per_pair_keys(self) -> None:
        pairs = [
            ({"findings": ["a"]}, {"findings": ["a"]}, ["findings"]),
            ({"findings": ["a"]}, {"findings": ["a", "b"]}, ["findings"]),
        ]
        report = self.gate.aggregate(pairs)
        self.assertFalse(report["passed"])
        self.assertEqual(report["divergent_scenarios"], 1)

    def test_aggregate_flags_any_divergence(self) -> None:
        pairs = [(_outcome(), _outcome()), (_outcome(), _outcome(route="/at-implement"))]
        report = self.gate.aggregate(pairs)
        self.assertFalse(report["passed"])
        self.assertEqual(report["divergent_scenarios"], 1)


if __name__ == "__main__":
    unittest.main()
