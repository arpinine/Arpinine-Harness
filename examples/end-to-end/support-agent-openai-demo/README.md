# Arpinine Harness End-to-End Demo: Support Triage Agent With OpenAI

This demo shows the same support triage application pattern as the fake harness demo, but with a real OpenAI-backed adapter behind the application boundary.

> A support triage agent classifies inbound customer tickets, drafts a first response with OpenAI, and requires human approval before creating a support case.

## What This Demonstrates

- product logic isolated from the model SDK
- an adapter-backed harness runtime using the OpenAI Python SDK
- unit tests that do not require network access
- a live evaluation script that exercises the real adapter
- harness governance artifacts for boundary, evaluation, and drift

## Prerequisites

- Python 3.10+
- `pip install openai`
- `OPENAI_API_KEY` set in the environment

Optional:

- `OPENAI_MODEL` to override the default model used by the adapter

## Demo Flow

From this directory:

```bash
pwd
# .../examples/end-to-end/support-agent-openai-demo
```

1. Run the unit tests:

```bash
python3 -m unittest discover -s app/tests
```

2. Run the live evaluation:

```bash
python3 app/eval/run_live_eval.py
```

This writes `.specify/evals/001-support-triage-openai-agent/latest-results.md`.

3. Review the governed artifacts:

- `.specify/specs/001-support-triage-openai-agent/spec.md`
- `.specify/specs/001-support-triage-openai-agent/plan.md`
- `.specify/evals/001-support-triage-openai-agent/eval-plan.md`
- `.specify/adr/ADR-0001-openai-responses-adapter-boundary.md`

## Intentional Drift Example

See `app/_drift_fixtures/drift_example_bad_direct_openai_import.py`.

That file shows the anti-pattern this demo is designed to avoid: importing a concrete model SDK directly into application code instead of keeping it behind the adapter boundary.

## Practical Takeaway

The harness application is the adapter layer, not the product layer:

- `SupportTriageService` owns business logic
- `OpenAIHarnessRuntime` owns model invocation, prompt construction, and runtime event recording
- approval and memory events are explicit and testable
- switching providers should require changing the adapter, not the application service
