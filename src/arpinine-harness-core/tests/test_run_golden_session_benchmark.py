"""
Tests for run_golden_session_benchmark.py — category extractors (routing,
ac_state, drift), FidelityGate, the 60-95% band, runnable noop engine, and
fail-closed semantics.

Governs: specs/011-context-compression-governance (TASK-009)
ADRs: ADR-0017 (zero divergence across ALL categories + 60-95% reduction;
      >95% FAIL; fail closed if engine unavailable).
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest

MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "run_golden_session_benchmark.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("run_golden_session_benchmark", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _manifest():
    return {
        "spec": "011-context-compression-governance",
        "scenarios": [
            {"id": "R", "category": "routing", "intent": "i1", "expected": {"route": "/at-status"}},
            {"id": "AC", "category": "ac_state", "target": "011", "expected": {"AC-001": False}},
            {"id": "D", "category": "drift", "target": "011", "expected": {"findings": [{"file": "spec.md", "line": None, "severity": "HIGH", "finding_id": "qdc-x", "message": "x"}]}},
        ],
    }


def _extractors():
    return {
        "routing": lambda t: {"route": "/at-status", "confidence": "medium"},
        "ac_state": lambda t: {"AC-001": False, "AC-002": False},
        "drift": lambda t: {"findings": [{"file": "spec.md", "line": None, "severity": "HIGH", "finding_id": "qdc-x", "message": "x"}]},
    }


class _FakeEngine:
    available = True
    name = "fake"

    def __init__(self, reduction=0.70, diverge=False):
        self._reduction = reduction
        self._diverge = diverge

    def on_outcome(self, off):
        if self._diverge and "route" in off:
            return dict(off, route="/at-implement")
        return dict(off)

    def measure(self, outcome, mode):
        return 100 if mode == "off" else int(100 * (1 - self._reduction))


class TestRunBenchmark(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(MODULE_PATH.exists())
        self.m = _load()
        self.manifest = _manifest()
        self.ex = _extractors()

    def test_all_categories_extracted_and_in_band_passes(self) -> None:
        report = self.m.run_benchmark(self.manifest, self.ex, _FakeEngine(reduction=0.70))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(sorted(report["categories"]), ["ac_state", "drift", "routing"])
        self.assertTrue(report["fidelity"]["passed"])

    def test_reduction_below_band_fails(self) -> None:
        report = self.m.run_benchmark(self.manifest, self.ex, _FakeEngine(reduction=0.30))
        self.assertEqual(report["status"], "fail")
        self.assertTrue(report["fidelity"]["passed"])

    def test_reduction_above_band_fails(self) -> None:
        report = self.m.run_benchmark(self.manifest, self.ex, _FakeEngine(reduction=0.98))
        self.assertEqual(report["status"], "fail")

    def test_routing_divergence_fails(self) -> None:
        report = self.m.run_benchmark(self.manifest, self.ex, _FakeEngine(reduction=0.70, diverge=True))
        self.assertEqual(report["status"], "fail")
        self.assertFalse(report["fidelity"]["passed"])
        self.assertGreaterEqual(report["fidelity"]["divergent_scenarios"], 1)

    def test_missing_extractor_for_category_fails_closed(self) -> None:
        report = self.m.run_benchmark(self.manifest, {"routing": self.ex["routing"]}, _FakeEngine())
        self.assertEqual(report["status"], "incomplete")

    def test_unavailable_engine_fails_closed(self) -> None:
        report = self.m.run_benchmark(self.manifest, self.ex, self.m.HeadroomEngine())
        self.assertEqual(report["status"], "incomplete")
        self.assertFalse(report.get("passed"))
        self.assertIn("headroom", report["reason"].lower())

    def test_empty_scenarios_fails_closed(self) -> None:
        report = self.m.run_benchmark({"scenarios": []}, self.ex, _FakeEngine())
        self.assertEqual(report["status"], "incomplete")

    def test_noop_engine_is_runnable_and_fidelity_passes_band_fails(self) -> None:
        """Runnable self-test: noop => fidelity PASS, 0% reduction => band FAIL."""
        report = self.m.run_benchmark(self.manifest, self.ex, self.m.NoopEngine())
        self.assertEqual(report["status"], "fail")        # runnable, not incomplete
        self.assertTrue(report["fidelity"]["passed"])      # noop preserves outcomes
        self.assertEqual(report["token_reduction"], 0.0)   # noop compresses nothing


class TestBandConstant(unittest.TestCase):
    def test_band_is_60_to_95(self) -> None:
        m = _load()
        self.assertEqual((m.MIN_REDUCTION, m.MAX_REDUCTION), (0.60, 0.95))


if __name__ == "__main__":
    unittest.main()
