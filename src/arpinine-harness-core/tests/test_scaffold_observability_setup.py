from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "scaffold_observability_setup.py"


def plan_with_strategy(strategy_body: str, harness_body: str = "N/A — single LLM call sufficient.") -> str:
    return (
        "# Plan: Demo\n\n"
        "## Harness Strategy\n"
        f"{harness_body}\n\n"
        "## Observability Strategy\n"
        f"{strategy_body}\n"
    )


class ScaffoldObservabilitySetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "specs" / "001-demo").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=self.repo,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_plan(self, body: str, harness_body: str = "N/A — single LLM call sufficient.") -> None:
        plan_path = self.repo / ".specify" / "specs" / "001-demo" / "plan.md"
        plan_path.write_text(plan_with_strategy(body, harness_body=harness_body), encoding="utf-8")

    def test_scaffolds_default_opentelemetry_and_deepeval_layout(self) -> None:
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
                | Swap strategy | Replace provider file only |
                """
            )
        )

        result = self.run_script("--spec", "001-demo", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["status"], "ok")
        self.assertTrue((self.repo / "src" / "observability" / "base.py").exists())
        self.assertTrue((self.repo / "src" / "observability" / "opentelemetry.py").exists())
        self.assertTrue((self.repo / "src" / "observability" / "noop.py").exists())
        self.assertTrue((self.repo / "src" / "evaluation" / "base.py").exists())
        self.assertTrue((self.repo / "src" / "evaluation" / "deepeval.py").exists())
        self.assertTrue((self.repo / "src" / "evaluation" / "noop.py").exists())
        env_text = (self.repo / ".env.example").read_text(encoding="utf-8")
        self.assertIn("OTEL_SERVICE_NAME=", env_text)
        self.assertIn("DEEPEVAL_API_KEY=", env_text)

    def test_skips_when_strategy_is_na(self) -> None:
        self.write_plan("N/A — feature makes no LLM calls and produces no AI-driven output.")

        result = self.run_script("--spec", "001-demo", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["status"], "skip")
        self.assertFalse((self.repo / "src").exists())

    def test_scaffolds_opentelemetry_provider_when_selected(self) -> None:
        self.write_plan(
            textwrap.dedent(
                """\
                | Concern | Decision |
                |---------|----------|
                | Observation required | Yes |
                | ObservationProvider interface | `app/observability/base.py` |
                | Default implementation | OpenTelemetry |
                | Env var configuration | `OTEL_EXPORTER_OTLP_ENDPOINT` |
                | Evaluation required | Yes |
                | EvaluationProvider interface | `app/evaluation/base.py` |
                | Default implementation | Ragas |
                | Observation-evaluation bridge | Custom bridge |
                | Swap strategy | Replace adapter only |
                """
            )
        )

        result = self.run_script("--spec", "001-demo", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / "app" / "observability" / "base.py").exists())
        self.assertTrue((self.repo / "app" / "observability" / "opentelemetry.py").exists())
        self.assertTrue((self.repo / "app" / "observability" / "noop.py").exists())
        self.assertFalse((self.repo / "app" / "observability" / "langfuse.py").exists())
        self.assertTrue((self.repo / "app" / "evaluation" / "base.py").exists())
        self.assertTrue((self.repo / "app" / "evaluation" / "noop.py").exists())
        self.assertFalse((self.repo / "app" / "evaluation" / "deepeval.py").exists())
        env_text = (self.repo / ".env.example").read_text(encoding="utf-8")
        self.assertIn("OTEL_SERVICE_NAME=", env_text)
        self.assertIn("OTEL_EXPORTER_OTLP_ENDPOINT=", env_text)
        self.assertNotIn("LANGFUSE_PUBLIC_KEY=", env_text)

    def test_scaffolds_langfuse_only_when_explicitly_selected(self) -> None:
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
            )
        )

        result = self.run_script("--spec", "001-demo", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / "src" / "observability" / "opentelemetry.py").exists())
        self.assertTrue((self.repo / "src" / "observability" / "langfuse.py").exists())
        env_text = (self.repo / ".env.example").read_text(encoding="utf-8")
        self.assertIn("OTEL_SERVICE_NAME=", env_text)
        self.assertIn("LANGFUSE_PUBLIC_KEY=", env_text)

    def test_harness_based_plan_scaffolds_otel_langfuse_and_deepeval(self) -> None:
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

        result = self.run_script("--spec", "001-demo", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        defaults = payload["results"][0]["scaffolded_defaults"]
        self.assertTrue(defaults["harness_required"])
        self.assertTrue(defaults["opentelemetry"])
        self.assertTrue(defaults["langfuse"])
        self.assertTrue(defaults["deepeval"])
        self.assertTrue((self.repo / "src" / "observability" / "opentelemetry.py").exists())
        self.assertTrue((self.repo / "src" / "observability" / "langfuse.py").exists())
        self.assertTrue((self.repo / "src" / "evaluation" / "deepeval.py").exists())

    def test_partial_scaffold_creates_missing_files_only(self) -> None:
        """base.py already exists — scaffold must create opentelemetry.py without overwriting base.py."""
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
                | Swap strategy | Replace provider file only |
                """
            )
        )
        sentinel = "# sentinel — must not be overwritten\n"
        obs_base = self.repo / "src" / "observability" / "base.py"
        obs_base.parent.mkdir(parents=True, exist_ok=True)
        obs_base.write_text(sentinel, encoding="utf-8")

        result = self.run_script("--spec", "001-demo", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["results"][0]["status"], "ok")

        # base.py was NOT overwritten
        self.assertEqual(obs_base.read_text(encoding="utf-8"), sentinel)
        # opentelemetry.py WAS created
        self.assertTrue((self.repo / "src" / "observability" / "opentelemetry.py").exists())
        # noop.py WAS created
        self.assertTrue((self.repo / "src" / "observability" / "noop.py").exists())
        # eval layer WAS fully created
        self.assertTrue((self.repo / "src" / "evaluation" / "base.py").exists())
        self.assertTrue((self.repo / "src" / "evaluation" / "deepeval.py").exists())
        self.assertTrue((self.repo / "src" / "evaluation" / "noop.py").exists())

        skipped = payload["results"][0]["skipped"]
        self.assertIn("src/observability/base.py", skipped)

    def test_env_example_update_is_idempotent(self) -> None:
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
                | Swap strategy | Replace provider file only |
                """
            )
        )

        first = self.run_script("--spec", "001-demo")
        second = self.run_script("--spec", "001-demo")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        env_text = (self.repo / ".env.example").read_text(encoding="utf-8")
        self.assertEqual(env_text.count("OTEL_SERVICE_NAME="), 1)
        self.assertEqual(env_text.count("DEEPEVAL_API_KEY="), 1)


if __name__ == "__main__":
    unittest.main()
