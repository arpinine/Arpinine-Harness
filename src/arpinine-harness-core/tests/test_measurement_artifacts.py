from __future__ import annotations

import json
import importlib.util
import pathlib
import tempfile
import unittest

class MeasurementArtifactsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify").mkdir()
        script = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "measurement_artifacts.py"
        spec = importlib.util.spec_from_file_location("measurement_artifacts", script)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.module = module

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_write_observation_run_updates_latest_and_history(self) -> None:
        payload = {
            "run_id": "20260428T120000Z-demo-a",
            "scenario_id": "demo",
            "runtime_class": "embedded agent runtime",
            "latency_ms": 120,
            "token_count_input": 10,
            "token_count_output": 5,
            "cost_usd": 0.01,
            "final_outcome": "PASS",
        }
        paths = self.module.write_observation_run(self.repo, "001-demo", payload)
        self.assertTrue(paths["latest_trace"].exists())
        self.assertTrue(paths["history_json"].exists())
        self.assertTrue(paths["index"].exists())
        lines = paths["index"].read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["run_id"], payload["run_id"])

    def test_write_eval_run_updates_latest_and_history(self) -> None:
        payload = {
            "run_id": "20260428T120000Z-results-a",
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "scenario_set": "core",
            "result": "PASS",
            "passed": 3,
            "failed": 0,
        }
        paths = self.module.write_eval_run(self.repo, "001-demo", payload)
        self.assertTrue(paths["latest_markdown"].exists())
        self.assertTrue(paths["history_json"].exists())
        stored = json.loads(paths["history_json"].read_text(encoding="utf-8"))
        self.assertEqual(stored["run_id"], payload["run_id"])

    def test_write_eval_run_archive_false_skips_history(self) -> None:
        payload = {
            "run_id": "20260428T120000Z-results-b",
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "scenario_set": "core",
            "result": "PASS",
            "passed": 1,
            "failed": 0,
        }
        paths = self.module.write_eval_run(self.repo, "001-demo", payload, archive=False)
        self.assertTrue(paths["latest_markdown"].exists())
        self.assertFalse(paths["history_json"].exists())
        self.assertFalse(paths["history_markdown"].exists())

    def test_compare_baseline_dimensions_flags_mismatches(self) -> None:
        baseline = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-a",
            "model_name": "m1",
            "model_version": "vA",
            "scenario_set": "core",
        }
        result = {
            "dataset_version": "v1.0.0",
            "variant_id": "variant-b",
            "model_name": "m1",
            "model_version": "vA",
            "scenario_set": "core",
        }
        compatible, mismatches = self.module.compare_baseline_dimensions(baseline, result)
        self.assertFalse(compatible)
        self.assertEqual(mismatches, ["variant_id"])


if __name__ == "__main__":
    unittest.main()
