# Expected AgentAlign Workflow

Use this file as a facilitator script when demonstrating the plugin.

## 1. Define

Show `product-request.md`, then open:

```text
.specify/specs/001-support-triage-agent/spec.md
```

Explain that the spec captures business case, user value, requirements, acceptance criteria, AIN assessment, and out-of-scope constraints.

## 2. Refine

Run:

```text
/agent-align:at-review .specify/specs/001-support-triage-agent/spec.md
```

Expected discussion:
- `product-owner` checks business alignment
- spec remains product-facing
- acceptance criteria are measurable

## 3. Plan

Run:

```text
/agent-align:at-plan .specify/specs/001-support-triage-agent/
```

Expected discussion:
- architecture boundaries are explicit
- fake harness adapter is isolated behind `SupportAgentRuntime`
- implementation can swap to another harness later
- eval and observation evidence are planned before completion

## 3b. Define Evaluation

Run:

```text
/agent-align:at-eval plan .specify/specs/001-support-triage-agent/
```

Expected discussion:
- the eval plan is pre-created in this demo
- the plan defines scenarios, thresholds, execution command, and pass/fail policy

## 4. Execute

Run:

```bash
PYTHONPATH=app python3 -m unittest discover -s app/tests
```

Expected result:
- all tests pass

## 5. Evaluate

Run:

```bash
PYTHONPATH=app python3 app/eval/run_eval.py
```

Expected result:
- all scenarios pass
- generated evidence is written to `.specify/evals/001-support-triage-agent/latest-results.md`

## 6. Observe

Open:

```text
.specify/observations/001-support-triage-agent/trace.json
```

Expected discussion:
- tool call is declared
- approval check occurs before case creation
- memory event is session scoped

## 7. Audit

Run:

```text
/agent-align:at-audit .specify/specs/001-support-triage-agent/spec.md
```

Expected discussion:
- clean path validates spec, plan, ADR, eval, and observation alignment
- `app/support_triage/application/drift_example_bad_direct_harness_import.py` shows how a future implementation could violate the harness boundary

## 8. Learn

Run:

```text
/agent-align:at-retro .specify/specs/001-support-triage-agent/spec.md
```

Expected discussion:
- turn harness-coupling lessons into persistent rules
- rules compound into future product work
