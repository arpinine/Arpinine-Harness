"""
Validates the context-compression golden-session fixture and re-verifies every
recorded outcome against the LIVE router, so a stale/invented golden fails loudly.

Governs: specs/011-context-compression-governance (TASK-008)
ADRs: ADR-0017 (golden-session = the fidelity benchmark input; recorded real
      router outcomes), ADR-0017 adversarial-case requirement (data boundary).
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_CORE_DIR = _TESTS_DIR.parent                      # src/arpinine-harness-core
_REPO_ROOT = _CORE_DIR.parents[1]                  # specops repo root
_ROUTER = _CORE_DIR / "scripts" / "route_at.py"
_BENCH = _CORE_DIR / "scripts" / "run_golden_session_benchmark.py"
_MANIFEST = (
    _REPO_ROOT
    / ".specify"
    / "evals"
    / "011-context-compression-governance"
    / "golden-session"
    / "manifest.json"
)


def _load_bench():
    spec = importlib.util.spec_from_file_location("run_golden_session_benchmark", _BENCH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_router(intent: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(_ROUTER), "--repo", str(_REPO_ROOT), "--intent", intent, "--indent", "0"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


class TestGoldenSessionFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _MANIFEST.exists():
            raise unittest.SkipTest(f"manifest missing at {_MANIFEST}")
        cls.manifest = json.loads(_MANIFEST.read_text())

    def test_manifest_shape(self) -> None:
        self.assertEqual(self.manifest["spec"], "011-context-compression-governance")
        self.assertTrue(self.manifest["outcome_fields"])
        scenarios = self.manifest["scenarios"]
        self.assertGreaterEqual(len(scenarios), 5, "golden session needs >=5 runs")
        self.assertTrue(
            any(s["category"] == "adversarial" for s in scenarios),
            "golden session needs >=1 adversarial case",
        )

    def test_covers_full_ac001_outcome_set(self) -> None:
        """AC-001 requires routing + ac_state + drift categories."""
        cats = {s["category"] for s in self.manifest["scenarios"]}
        self.assertIn("routing", cats)
        self.assertIn("ac_state", cats)
        self.assertIn("drift", cats)

    def test_ac_state_and_drift_match_live_extractors(self) -> None:
        """Re-verify non-routing categories against the live extractors."""
        bench = _load_bench()
        for s in self.manifest["scenarios"]:
            if s["category"] == "ac_state":
                with self.subTest(scenario=s["id"]):
                    live = bench.extract_ac_state(_REPO_ROOT, s["target"])
                    self.assertEqual(live, s["expected"], f"AC golden stale for {s['id']}")
            elif s["category"] == "drift":
                with self.subTest(scenario=s["id"]):
                    live = bench.extract_drift(_REPO_ROOT, s["target"])
                    self.assertEqual(live, s["expected"], f"drift golden stale for {s['id']}")

    def test_scenarios_have_unique_ids_and_required_keys(self) -> None:
        ids = [s["id"] for s in self.manifest["scenarios"]]
        self.assertEqual(len(ids), len(set(ids)), "scenario ids must be unique")
        for s in self.manifest["scenarios"]:
            for key in ("id", "category", "expected"):
                self.assertIn(key, s)
            # routing/adversarial address a target via `intent`; ac_state/drift via `target`.
            self.assertTrue(
                ("intent" in s) or ("target" in s),
                f"{s['id']} must declare intent or target",
            )
            if s["category"] in ("routing", "adversarial"):
                for field in self.manifest["outcome_fields"]:
                    self.assertIn(field, s["expected"], f"{s['id']} missing expected.{field}")

    def test_recorded_outcomes_match_live_router(self) -> None:
        """Routing/adversarial goldens must reflect the real router — re-verify live."""
        fields = self.manifest["outcome_fields"]
        for s in self.manifest["scenarios"]:
            if s["category"] not in ("routing", "adversarial"):
                continue
            with self.subTest(scenario=s["id"]):
                live = _run_router(s["intent"])
                actual = {f: live[f] for f in fields}
                self.assertEqual(
                    actual, s["expected"], f"golden stale for {s['id']}"
                )

    def test_adversarial_directive_is_treated_as_data(self) -> None:
        """Embedded 'ignore previous instructions' must NOT force /at-implement."""
        adv = [s for s in self.manifest["scenarios"] if s["category"] == "adversarial"]
        self.assertTrue(adv)
        for s in adv:
            self.assertNotEqual(s["expected"]["route"], "/at-implement")
            # And the live router agrees (data boundary holds without compression).
            live = _run_router(s["intent"])
            self.assertNotEqual(live["route"], "/at-implement")


if __name__ == "__main__":
    unittest.main()
