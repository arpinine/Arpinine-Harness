# Arpinine Harness End-to-End Demo: Support Triage Agent

This demo shows Arpinine Harness in action on a small product feature:

> A support triage agent classifies inbound customer tickets, drafts a first response, and requires human approval before creating a support case.

The demo is intentionally small. It is not a production service. Its purpose is to make the Arpinine Harness workflow visible from product intent to execution evidence.

## What This Demonstrates

- product intent captured in `spec.md`
- business alignment via the `product-owner` agent
- architecture boundaries in `plan.md`
- harness strategy without requiring a real harness runtime
- evaluation plan and runnable evaluation script
- benchmark dataset, baseline, and history artifacts
- runtime observation trace
- ADR for the harness boundary decision
- retro rule that prevents direct harness coupling
- intentional drift example for audit discussion

## Prerequisites

- Python 3.10+
- Arpinine Harness plugin installed in Claude Code

No OpenHarness installation is required. The app uses a fake harness adapter so the demo is runnable anywhere.

## Demo Flow

From this directory:

```bash
pwd
# .../examples/end-to-end/support-agent-demo
```

1. Inspect the product request:

```bash
cat product-request.md
```

2. Run the Arpinine Harness workflow in Claude Code:

```text
/arpinine-harness:at-init
/arpinine-harness:at-review .specify/specs/001-support-triage-agent/spec.md
/arpinine-harness:at-plan .specify/specs/001-support-triage-agent/
/arpinine-harness:at-eval plan .specify/specs/001-support-triage-agent/
/arpinine-harness:at-eval review .specify/specs/001-support-triage-agent/
/arpinine-harness:at-observe review .specify/specs/001-support-triage-agent/
/arpinine-harness:at-status --onboard
/arpinine-harness:at-audit .specify/specs/001-support-triage-agent/spec.md
```

3. Run the implementation tests:

```bash
python3 -m unittest discover -s app/tests
```

4. Run the single-run evaluation evidence:

```bash
python3 app/eval/run_eval.py
```

This writes `.specify/evals/001-support-triage-agent/latest-results.md`.

5. Run the benchmarked measurement path:

```bash
python3 ../../../src/arpinine-harness-core/scripts/run_benchmark.py \
  --slug 001-support-triage-agent
```

This writes:
- `.specify/evals/001-support-triage-agent/history/*-results.json`
- `.specify/evals/001-support-triage-agent/latest-results.md`
- `.specify/observations/001-support-triage-agent/history/*.json`
- `.specify/observations/001-support-triage-agent/latest-observation.md`

Notes:
- `baseline-results.json` in this demo includes domain-specific metrics such as `approval_check_rate` and `memory_scope_rate`. The generic shared-core baseline comparison currently evaluates `pass_rate`, `latency_p95_ms`, and `cost_total_usd`. Additional metric regression rules require product-specific comparison logic.
- Benchmark history is append-only. Re-running the benchmark adds more scenario result files to `history/`, and aggregate reporting reads the full accumulated history set. For an isolated benchmark session, clear or partition history before rerunning.

6. Try the static drift/conformance checker from the demo directory:

```bash
python3 ../../../src/arpinine-harness-core/scripts/quick_drift_check.py \
  --spec .specify/specs/001-support-triage-agent/spec.md
```

For full local script behavior, run Arpinine Harness commands from this demo directory so `.specify/` is the project root.

## Intentional Drift Example

See `app/support_triage/application/drift_example_bad_direct_harness_import.py`.

That file intentionally imports a harness runtime concept outside an adapter/infrastructure boundary. It represents the kind of issue Arpinine Harness should surface as harness drift or a rule violation.

To simulate the post-edit hook check:

```bash
printf '{"tool_input":{"file_path":"app/support_triage/application/drift_example_bad_direct_harness_import.py"}}' \
  | python3 ../../../src/arpinine-harness-core/scripts/quick_drift_check.py
```

## Expected Result

The happy path should show:

- spec exists and is product-facing
- plan has module boundaries, dependency rules, testability, harness strategy, and eval strategy
- tests pass
- eval passes required thresholds
- benchmark history and observation history are recorded
- baseline and dataset manifest make benchmark results reproducible
- ADR documents the harness boundary
- status report gives a new engineer the governance state

The drift path should show:

- runtime or harness coupling outside the planned adapter boundary is not aligned with the plan
- the fix is to move runtime-specific code behind the adapter or update the plan/ADR if the decision changed
