from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCAFFOLD_SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "scaffold_observability_setup.py"
CHECK_SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "check-observability-setup.sh"


def plan_text(observability_body: str, harness_body: str) -> str:
    return (
        "# Plan: Demo\n\n"
        "## Harness Strategy\n"
        f"{harness_body}\n\n"
        "## Observability Strategy\n"
        f"{observability_body}\n"
    )


class CheckObservabilitySetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "specs" / "001-demo").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_plan(self, observability_body: str, harness_body: str) -> None:
        plan_path = self.repo / ".specify" / "specs" / "001-demo" / "plan.md"
        plan_path.write_text(plan_text(observability_body, harness_body), encoding="utf-8")

    def run_scaffold(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCAFFOLD_SCRIPT), "--spec", "001-demo", "--json"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_check(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(CHECK_SCRIPT), "--spec", "001-demo", "--json"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_raw_plan(self, text: str) -> None:
        plan_path = self.repo / ".specify" / "specs" / "001-demo" / "plan.md"
        plan_path.write_text(text, encoding="utf-8")

    def test_harness_based_workflow_passes_when_scaffolded(self) -> None:
        self.write_plan(
            textwrap.dedent(
                """\
                | Concern | Decision |
                |---------|----------|
                | Observation required | Yes |
                | ObservationProvider interface | `src/observability/base.py` |
                | Default implementation | OpenTelemetry |
                | Specialized implementation | Langfuse |
                | Env var configuration | `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` |
                | Evaluation required | Yes |
                | EvaluationProvider interface | `src/evaluation/base.py` |
                | Default implementation | DeepEval |
                | Observation-evaluation bridge | Attach eval metric scores to traces |
                | Swap strategy | Replace adapter only |
                """
            ),
            harness_body="- Runtime: OpenAI Agents\n- Why harness is needed: multi-step tool loop\n",
        )

        scaffold = self.run_scaffold()
        self.assertEqual(scaffold.returncode, 0, scaffold.stdout + scaffold.stderr)
        check = self.run_check()
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        payload = json.loads(check.stdout)
        self.assertTrue(payload["passed"], payload)

    def test_harness_based_workflow_fails_without_langfuse(self) -> None:
        self.write_plan(
            textwrap.dedent(
                """\
                | Concern | Decision |
                |---------|----------|
                | Observation required | Yes |
                | ObservationProvider interface | `src/observability/base.py` |
                | Default implementation | OpenTelemetry |
                | Env var configuration | `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT` |
                | Evaluation required | Yes |
                | EvaluationProvider interface | `src/evaluation/base.py` |
                | Default implementation | DeepEval |
                | Observation-evaluation bridge | Attach eval metric scores to traces |
                | Swap strategy | Replace adapter only |
                """
            ),
            harness_body="- Runtime: OpenAI Agents\n- Why harness is needed: multi-step tool loop\n",
        )
        (self.repo / "src" / "observability").mkdir(parents=True)
        (self.repo / "src" / "evaluation").mkdir(parents=True)
        (self.repo / "src" / "observability" / "base.py").write_text(
            "from typing import Protocol\nclass ObservationProvider(Protocol):\n    pass\n",
            encoding="utf-8",
        )
        (self.repo / "src" / "observability" / "opentelemetry.py").write_text(
            "from opentelemetry import trace\nclass OpenTelemetryObservationProvider:\n    def flush(self):\n        return None\n",
            encoding="utf-8",
        )
        (self.repo / "src" / "observability" / "noop.py").write_text("class NoopObservationProvider:\n    pass\n", encoding="utf-8")
        (self.repo / "src" / "evaluation" / "base.py").write_text(
            "from typing import Protocol\nclass EvaluationProvider(Protocol):\n    pass\n",
            encoding="utf-8",
        )
        (self.repo / "src" / "evaluation" / "deepeval.py").write_text(
            "from deepeval import evaluate\nclass DeepEvalProvider:\n    pass\n",
            encoding="utf-8",
        )
        (self.repo / "src" / "evaluation" / "noop.py").write_text("class NoopEvaluationProvider:\n    pass\n", encoding="utf-8")

        check = self.run_check()
        payload = json.loads(check.stdout)
        self.assertFalse(payload["passed"], payload)
        self.assertTrue(any(f["check"] == "langfuse-provider-missing" for f in payload["findings"]), payload)

    def test_harness_based_workflow_fails_when_observability_section_missing(self) -> None:
        self.write_raw_plan(
            "# Plan: Demo\n\n"
            "## Harness Strategy\n"
            "- Runtime: OpenAI Agents\n"
            "- Why harness is needed: multi-step tool loop\n"
        )

        check = self.run_check()
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        payload = json.loads(check.stdout)
        self.assertFalse(payload["passed"], payload)
        self.assertTrue(any(f["check"] == "harness-observability-required" for f in payload["findings"]), payload)


if __name__ == "__main__":
    unittest.main()
