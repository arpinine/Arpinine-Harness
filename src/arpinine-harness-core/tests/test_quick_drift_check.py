from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "quick_drift_check.py"


class QuickDriftCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "specs" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "evals" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "observations" / "001-demo").mkdir(parents=True)
        (self.repo / "src").mkdir()
        (self.repo / "src" / "demo.py").write_text("print('demo')\n", encoding="utf-8")
        (self.repo / ".specify" / "specs" / "001-demo" / "spec.md").write_text(
            "# Spec: Demo Agent\n\nThis feature uses an agent runtime.\n\nImplementation path: src/demo.py\n",
            encoding="utf-8",
        )
        (self.repo / ".specify" / "specs" / "001-demo" / "plan.md").write_text(
            "# Plan: Demo\n\n## Harness Strategy\n- Runtime: demo\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_qdc(self) -> list[dict[str, object]]:
        result = subprocess.run(
            ["python3", str(SCRIPT), "--all", "--json"],
            cwd=self.repo,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def write_eval_plan(self, body: str) -> None:
        (self.repo / ".specify" / "evals" / "001-demo" / "eval-plan.md").write_text(
            textwrap.dedent(body).strip() + "\n",
            encoding="utf-8",
        )

    def findings(self) -> list[str]:
        return self.run_qdc()[0]["findings"]

    def test_benchmarked_eval_without_dataset_manifest_is_flagged(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan

            Benchmark required: Yes
            Benchmark command: `pytest tests/benchmark.py`
            Baseline required: No
            """
        )
        findings = self.findings()
        self.assertIn("HIGH benchmarked eval declared but dataset-manifest.json is missing", findings)

    def test_regression_sensitive_eval_without_baseline_is_flagged(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan

            Benchmark required: Yes
            Benchmark command: `pytest tests/benchmark.py`
            Baseline required: Yes
            """
        )
        findings = self.findings()
        self.assertIn("HIGH regression-sensitive eval declared but baseline.json is missing", findings)

    def test_perf_sensitive_eval_without_trace_is_flagged(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan

            Benchmark required: No
            Metrics:
            - latency P95 <= 200ms
            - token input <= 4000
            - cost usd <= 0.01
            """
        )
        (self.repo / ".specify" / "observations" / "001-demo" / "latest-observation.md").write_text(
            "# Observation\n",
            encoding="utf-8",
        )
        findings = self.findings()
        self.assertIn("MEDIUM perf-sensitive eval declared but no trace.json exists for telemetry review", findings)

    def test_perf_sensitive_eval_with_missing_trace_fields_is_flagged(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan

            Benchmark required: No
            Metrics:
            - latency P95 <= 200ms
            - token input <= 4000
            - cost usd <= 0.01
            """
        )
        (self.repo / ".specify" / "observations" / "001-demo" / "trace.json").write_text(
            json.dumps({"latency_ms": 100}),
            encoding="utf-8",
        )
        findings = self.findings()
        self.assertTrue(
            any("latest trace is missing telemetry fields" in finding for finding in findings),
            findings,
        )

    def test_non_benchmarked_eval_does_not_require_dataset_manifest(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan

            Benchmark required: No
            Execution command: `pytest`
            """
        )
        findings = self.findings()
        self.assertFalse(
            any("dataset-manifest.json is missing" in finding for finding in findings),
            findings,
        )


if __name__ == "__main__":
    unittest.main()
