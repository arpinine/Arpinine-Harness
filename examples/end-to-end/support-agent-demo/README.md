# AgentAlign End-to-End Demo: Support Triage Agent

This demo shows AgentAlign in action on a small product feature:

> A support triage agent classifies inbound customer tickets, drafts a first response, and requires human approval before creating a support case.

The demo is intentionally small. It is not a production service. Its purpose is to make the AgentAlign workflow visible from product intent to execution evidence.

## What This Demonstrates

- product intent captured in `spec.md`
- business alignment via the `product-owner` agent
- architecture boundaries in `plan.md`
- harness strategy without requiring a real harness runtime
- evaluation plan and runnable evaluation script
- runtime observation trace
- ADR for the harness boundary decision
- retro rule that prevents direct harness coupling
- intentional drift example for audit discussion

## Prerequisites

- Python 3.10+
- AgentAlign plugin installed in Claude Code

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

2. Run the AgentAlign workflow in Claude Code:

```text
/at-init
/at-review .specify/specs/001-support-triage-agent/spec.md
/at-plan .specify/specs/001-support-triage-agent/
/at-eval plan .specify/specs/001-support-triage-agent/
/at-eval review .specify/specs/001-support-triage-agent/
/at-observe review .specify/specs/001-support-triage-agent/
/at-status --onboard
/at-audit .specify/specs/001-support-triage-agent/spec.md
```

3. Run the implementation tests:

```bash
PYTHONPATH=app python3 -m unittest discover -s app/tests
```

4. Run the evaluation evidence:

```bash
PYTHONPATH=app python3 app/eval/run_eval.py
```

This writes `.specify/evals/001-support-triage-agent/latest-results.md`.

5. Try the static drift/conformance checker from the demo directory:

```bash
python3 ../../../src/agent-align-v1.0.0/scripts/quick_drift_check.py \
  --spec .specify/specs/001-support-triage-agent/spec.md
```

For full local script behavior, run AgentAlign commands from this demo directory so `.specify/` is the project root.

## Intentional Drift Example

See `app/support_triage/application/drift_example_bad_direct_harness_import.py`.

That file intentionally imports a harness runtime concept outside an adapter/infrastructure boundary. It represents the kind of issue AgentAlign should surface as harness drift or a rule violation.

To simulate the post-edit hook check:

```bash
printf '{"tool_input":{"file_path":"app/support_triage/application/drift_example_bad_direct_harness_import.py"}}' \
  | python3 ../../../src/agent-align-v1.0.0/scripts/quick_drift_check.py
```

## Expected Result

The happy path should show:

- spec exists and is product-facing
- plan has module boundaries, dependency rules, testability, harness strategy, and eval strategy
- tests pass
- eval passes required thresholds
- observation trace is recorded
- ADR documents the harness boundary
- status report gives a new engineer the governance state

The drift path should show:

- runtime or harness coupling outside the planned adapter boundary is not aligned with the plan
- the fix is to move runtime-specific code behind the adapter or update the plan/ADR if the decision changed
