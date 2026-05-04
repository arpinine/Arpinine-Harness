from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import textwrap
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "src" / "arpinine-harness-core" / "scripts" / "spec_status.py"


class SpecStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tempdir.name)
        (self.repo / ".specify" / "specs" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "evals" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "observations" / "001-demo").mkdir(parents=True)
        (self.repo / ".specify" / "adr").mkdir(parents=True)
        (self.repo / ".specify" / "rules").mkdir(parents=True)
        (self.repo / ".specify" / "specs" / "001-demo" / "spec.md").write_text(
            "# Spec: Demo\n\nAgent workflow.\n\n- [ ] AC-001: Demo\n",
            encoding="utf-8",
        )
        (self.repo / ".specify" / "specs" / "001-demo" / "plan.md").write_text(
            textwrap.dedent(
                """
                # Plan: Demo

                ## Module Boundaries
                | Module / Component | Responsibility | Depends On | Interface / Adapter |
                |--------------------|----------------|------------|---------------------|
                | runtime | orchestration | none | adapter |

                ## Dependency Rules
                - Keep dependencies explicit

                ## Testability By Boundary
                | Boundary | Test Type | Isolation Strategy |
                |----------|-----------|--------------------|
                | runtime | unit | fixture |

                ## Harness Strategy
                | Concern | Decision |
                |---------|----------|
                | Why harness is needed | agent runtime |
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (self.repo / ".specify" / "adr" / "ADR-INDEX.md").write_text("# ADR Index\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_status_json(self) -> dict[str, object]:
        result = subprocess.run(
            ["python3", str(SCRIPT), "--json"],
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

    def test_benchmarked_eval_reports_missing_dataset(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan
            Benchmark required: Yes
            Benchmark command: `pytest tests/benchmark.py`
            Baseline required: No
            """
        )
        (self.repo / ".specify" / "evals" / "001-demo" / "latest-results.md").write_text(
            "Result: PASS\n",
            encoding="utf-8",
        )
        payload = self.run_status_json()
        row = payload["specs"][0]
        self.assertEqual(row["eval"], "BENCHMARK-MISSING-DATASET")
        self.assertIn(
            "001-demo: benchmarked evaluation requires dataset-manifest.json",
            payload["blocked_work"],
        )

    def test_benchmarked_eval_reports_missing_baseline(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan
            Benchmark required: Yes
            Benchmark command: `pytest tests/benchmark.py`
            Baseline required: Yes
            """
        )
        (self.repo / ".specify" / "evals" / "001-demo" / "latest-results.md").write_text(
            "Result: PASS\n",
            encoding="utf-8",
        )
        (self.repo / ".specify" / "evals" / "001-demo" / "dataset-manifest.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        payload = self.run_status_json()
        row = payload["specs"][0]
        self.assertEqual(row["eval"], "BENCHMARK-MISSING-BASELINE")

    def test_benchmarked_eval_reports_history_state(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan
            Benchmark required: Yes
            Benchmark command: `pytest tests/benchmark.py`
            Baseline required: No
            """
        )
        eval_dir = self.repo / ".specify" / "evals" / "001-demo"
        (eval_dir / "latest-results.md").write_text("Result: PASS\n", encoding="utf-8")
        (eval_dir / "dataset-manifest.json").write_text("{}\n", encoding="utf-8")
        (eval_dir / "history").mkdir()
        (eval_dir / "history" / "20260428T120000Z-results.json").write_text("{}\n", encoding="utf-8")
        payload = self.run_status_json()
        row = payload["specs"][0]
        self.assertEqual(row["eval"], "PASS")
        self.assertTrue(row["benchmark_required"])

    def test_observation_state_reports_history(self) -> None:
        obs_dir = self.repo / ".specify" / "observations" / "001-demo"
        (obs_dir / "latest-observation.md").write_text("# Observation\n", encoding="utf-8")
        (obs_dir / "trace.json").write_text("{}\n", encoding="utf-8")
        (obs_dir / "index.jsonl").write_text("{}\n", encoding="utf-8")
        (obs_dir / "history").mkdir()
        (obs_dir / "history" / "20260428T120000Z-demo.json").write_text("{}\n", encoding="utf-8")
        payload = self.run_status_json()
        row = payload["specs"][0]
        self.assertEqual(row["obs"], "history")

    def test_observation_state_reports_contract_failures(self) -> None:
        eval_dir = self.repo / ".specify" / "evals" / "001-demo"
        obs_dir = self.repo / ".specify" / "observations" / "001-demo"
        (self.repo / ".specify" / "specs" / "001-demo" / "plan.md").write_text(
            textwrap.dedent(
                """
                # Plan: Demo

                ## Module Boundaries
                | Module / Component | Responsibility | Depends On | Interface / Adapter |
                |--------------------|----------------|------------|---------------------|
                | runtime | orchestration | none | adapter |

                ## Dependency Rules
                - Keep dependencies explicit

                ## Testability By Boundary
                | Boundary | Test Type | Isolation Strategy |
                |----------|-----------|--------------------|
                | runtime | unit | fixture |

                ## Harness Strategy
                | Concern | Decision |
                |---------|----------|
                | Why harness is needed | agent runtime |
                | Runtime selected | OpenHarness |
                | Product abstraction boundary | adapter |
                | Tool access model | `draft_support_reply` only |
                | Memory / state model | session-only |
                | Permission and safety model | `create_case` requires approval |
                | Swap strategy | adapter only |
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (eval_dir / "eval-plan.md").write_text(
            textwrap.dedent(
                """
                # Evaluation Plan: Demo

                ## Runtime Contract Assertions
                - Allowed tools: [`draft_support_reply`]
                - Protected actions requiring approval: [`create_case`]
                - Memory scope invariant: session-only
                - Session reset evidence: [`session_reset`]
                - Required event types: [`model_turn_started`, `tool_requested`, `tool_executed`, `permission_check`, `memory_write`, `session_reset`]
                - Required policy assertions: approval before protected write

                ## Deterministic Replay
                - Replay required: No
                - Replay command: `pytest`
                - Mock / fixture strategy: fixture
                - Replay fixture path: `tests/fixtures`
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        (obs_dir / "latest-observation.md").write_text("# Observation\n", encoding="utf-8")
        (obs_dir / "trace.json").write_text(
            json.dumps(
                {
                    "spec": "001-demo",
                    "runtime_class": "fixture-runtime",
                    "scenario_id": "s1",
                    "timestamp": "2026-05-04T00:00:00Z",
                    "events": [
                        {"type": "model_turn_started"},
                        {"type": "tool_requested", "tool": "draft_support_reply"},
                        {"type": "tool_executed", "tool": "draft_support_reply"},
                        {"type": "permission_check", "action": "create_case", "approved": True},
                        {"type": "memory_write", "scope": "session"},
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        payload = self.run_status_json()
        row = payload["specs"][0]
        self.assertEqual(row["obs"], "contract-fail")
        self.assertIn("001-demo: harness observation contract failed", payload["blocked_work"])

    def test_benchmark_state_is_reported_in_json(self) -> None:
        self.write_eval_plan(
            """
            # Eval Plan
            Benchmark required: Yes
            Benchmark command: `pytest tests/benchmark.py`
            Baseline required: Yes
            """
        )
        eval_dir = self.repo / ".specify" / "evals" / "001-demo"
        (eval_dir / "latest-results.md").write_text("Result: PASS\n", encoding="utf-8")
        (eval_dir / "dataset-manifest.json").write_text("{}\n", encoding="utf-8")
        (eval_dir / "baseline.json").write_text("{}\n", encoding="utf-8")
        (eval_dir / "history").mkdir()
        (eval_dir / "history" / "20260428T120000Z-results.json").write_text("{}\n", encoding="utf-8")
        payload = self.run_status_json()
        row = payload["specs"][0]
        self.assertEqual(row["benchmark_state"]["history_count"], 1)
        self.assertTrue(row["benchmark_state"]["dataset_manifest"])
        self.assertTrue(row["benchmark_state"]["baseline"])


if __name__ == "__main__":
    unittest.main()
