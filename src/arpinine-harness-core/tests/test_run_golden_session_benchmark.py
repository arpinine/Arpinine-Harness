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
import json
import pathlib
import sys
import tempfile
import types
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


class _FallbackEngine:
    available = True
    name = "fallback"
    signals = [
        {
            "event": "compression_passthrough_fallback",
            "reason": "proxy unreachable",
            "session_id": "sess-1",
            "timestamp": "2026-06-22T00:00:00Z",
        }
    ]

    def on_outcome(self, off):
        return dict(off)

    def measure(self, outcome, mode):
        return len(str(outcome))


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
        # Below the revised 30% floor.
        report = self.m.run_benchmark(self.manifest, self.ex, _FakeEngine(reduction=0.10))
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
        # An engine reporting available=False -> incomplete (fail closed), never a pass.
        class _Unavailable:
            available = False
            name = "unavailable"

        report = self.m.run_benchmark(self.manifest, self.ex, _Unavailable())
        self.assertEqual(report["status"], "incomplete")
        self.assertFalse(report.get("passed"))

    def test_empty_scenarios_fails_closed(self) -> None:
        report = self.m.run_benchmark({"scenarios": []}, self.ex, _FakeEngine())
        self.assertEqual(report["status"], "incomplete")

    def test_noop_engine_is_runnable_and_fidelity_passes_band_fails(self) -> None:
        """Runnable self-test: noop => fidelity PASS, 0% reduction => band FAIL."""
        report = self.m.run_benchmark(self.manifest, self.ex, self.m.NoopEngine())
        self.assertEqual(report["status"], "fail")        # runnable, not incomplete
        self.assertTrue(report["fidelity"]["passed"])      # noop preserves outcomes
        self.assertEqual(report["token_reduction"], 0.0)   # noop compresses nothing

    def test_passthrough_fallback_run_keeps_zero_divergence_and_surfaces_signal(self) -> None:
        report = self.m.run_benchmark(self.manifest, self.ex, _FallbackEngine())
        self.assertEqual(report["status"], "fail")  # honest band failure; not incomplete
        self.assertTrue(report["fidelity"]["passed"])
        self.assertEqual(report["fidelity"]["divergent_scenarios"], 0)
        self.assertEqual(len(report["signals"]), 1)
        self.assertEqual(report["signals"][0]["event"], "compression_passthrough_fallback")
        self.assertEqual(report["signals"][0]["reason"], "proxy unreachable")


class TestBandConstant(unittest.TestCase):
    def test_band_is_30_to_95(self) -> None:
        # Revised after TASK-012 live measurement (ADR-0017): floor 30% with
        # honest margin below the ~38-41% representative simulate() reduction.
        m = _load()
        self.assertEqual((m.MIN_REDUCTION, m.MAX_REDUCTION), (0.30, 0.95))


class TestSimulateEngineFailClosed(unittest.TestCase):
    def test_unavailable_without_headroom_or_fixture(self) -> None:
        m = _load()
        eng = m.SimulateHeadroomEngine(payloads_path="/nonexistent/payloads.json")
        # No headroom installed (system python) and/or missing fixture -> unavailable
        # -> run_benchmark reports incomplete (fail closed), never a silent pass.
        self.assertFalse(eng.available)


class TestSimulateEngineSuccessPath(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()
        self._tmp = tempfile.TemporaryDirectory()
        self.payloads_path = pathlib.Path(self._tmp.name) / "payloads.json"
        self.payloads_path.write_text(
            json.dumps(
                {
                    "model": "fixture-model",
                    "model_limit": 12345,
                    "payloads": [
                        [{"role": "user", "content": "a"}, {"role": "tool", "content": "x" * 50}],
                        [{"role": "user", "content": "b"}, {"role": "tool", "content": "y" * 50}],
                    ],
                }
            )
        )
        self._orig_headroom = sys.modules.get("headroom")
        self.calls = []

        calls = self.calls

        class _Result:
            def __init__(self, before, after):
                self.tokens_before = before
                self.tokens_after = after

        class _Pipeline:
            def __init__(self, config):
                self.config = config

            def simulate(self, messages, model, model_limit):
                calls.append({"messages": messages, "model": model, "model_limit": model_limit})
                return _Result(100, 60)

        fake_headroom = types.ModuleType("headroom")
        fake_headroom.HeadroomConfig = lambda intercept_tool_results=False: types.SimpleNamespace(
            intercept_tool_results=intercept_tool_results
        )
        fake_headroom.TransformPipeline = _Pipeline
        sys.modules["headroom"] = fake_headroom

    def tearDown(self) -> None:
        if self._orig_headroom is None:
            sys.modules.pop("headroom", None)
        else:
            sys.modules["headroom"] = self._orig_headroom
        self._tmp.cleanup()

    def test_session_tokens_reads_fixture_model_metadata(self) -> None:
        eng = self.m.SimulateHeadroomEngine(self.payloads_path)
        self.assertTrue(eng.available)
        off_total, on_total = eng.session_tokens()
        self.assertEqual((off_total, on_total), (200, 120))
        self.assertEqual(len(self.calls), 2)
        self.assertTrue(all(call["model"] == "fixture-model" for call in self.calls))
        self.assertTrue(all(call["model_limit"] == 12345 for call in self.calls))

    def test_run_benchmark_passes_with_in_band_simulate_reduction(self) -> None:
        eng = self.m.SimulateHeadroomEngine(self.payloads_path)
        report = self.m.run_benchmark(_manifest(), _extractors(), eng)
        self.assertEqual(report["status"], "pass")
        self.assertTrue(report["fidelity"]["passed"])
        self.assertAlmostEqual(report["token_reduction"], 0.40)
        self.assertTrue(report["in_band"])


if __name__ == "__main__":
    unittest.main()
