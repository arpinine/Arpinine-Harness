# Arpinine Harness End-to-End Demo: Support Triage Agent With OpenHarness

This demo shows the support triage application pattern using [OpenHarness](https://github.com/HKUDS/OpenHarness) as the real agent runtime behind the application boundary.

> A support triage agent classifies inbound tickets, drafts first responses via the OpenHarness agent loop, and requires human approval before creating a support case.

## What This Demonstrates

- product logic isolated from the OpenHarness SDK behind `SupportAgentRuntime` interface
- `DraftSupportReplyTool` registered as a `BaseTool` with a narrow `ToolRegistry` allowlist
- `PermissionSettings` with `allowed_tools=["draft_support_reply"]` enforcing no other tools
- `QueryEngine` used for the agent loop with injectable engine for offline tests
- `engine.clear()` enforcing session-scoped memory — no MEMORY.md persistence
- `DraftSupportReplyTool` unit tests run offline (no API key required)
- adapter integration tests run against the real OpenHarness + Anthropic stack (skipped if no key)
- live evaluation script exercises the full end-to-end path
- full harness governance artifacts: spec, plan, eval-plan, ADR, rule, drift fixture

## Prerequisites

```bash
pip install openharness-ai
```

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

Optional — override the default model:

```bash
export ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

## Demo Flow

From this directory:

```bash
pwd
# .../examples/end-to-end/support-agent-openharness-demo
```

1. Run the tests (`DraftSupportReplyTool` runs offline; adapter tests skip without `ANTHROPIC_API_KEY`):

```bash
python3 -m unittest discover -s app/tests
```

1. Run the live evaluation (real OpenHarness + Anthropic API):

```bash
python3 app/eval/run_live_eval.py
```

This writes `.specify/evals/001-support-triage-openharness-agent/latest-results.md`.

1. Review the governed artifacts:

- `.specify/specs/001-support-triage-openharness-agent/spec.md`
- `.specify/specs/001-support-triage-openharness-agent/plan.md`
- `.specify/evals/001-support-triage-openharness-agent/eval-plan.md`
- `.specify/adr/ADR-0001-openharness-adapter-boundary.md`
- `.specify/rules/harness/harness-001.md`

1. Try the static drift check from the demo directory:

```bash
python3 ../../../src/arpinine-harness-core/scripts/quick_drift_check.py \
  --spec .specify/specs/001-support-triage-openharness-agent/spec.md
```

## Intentional Drift Examples

Two drift fixtures demonstrate what `quick_drift_check.py` catches:

- `app/_drift_fixtures/drift_example_bad_direct_openharness_import.py` — OpenHarness import outside adapter layer
- `app/support_triage/application/drift_example_bad_direct_openharness_import.py` — same anti-pattern inside application layer

To simulate the post-edit hook check:

```bash
printf '{"tool_input":{"file_path":"app/_drift_fixtures/drift_example_bad_direct_openharness_import.py"}}' \
  | python3 ../../../src/arpinine-harness-core/scripts/quick_drift_check.py
```

## Architecture

```text
SupportTriageService (application layer — no openharness imports)
        │
        ▼
SupportAgentRuntime interface
        │
        ▼
OpenHarnessAdapter (adapters/ — only file with openharness imports)
  ├── DraftSupportReplyTool (BaseTool)
  ├── ToolRegistry (allowed_tools: ["draft_support_reply"])
  ├── PermissionSettings (mode: DEFAULT)
  ├── PermissionChecker
  └── QueryEngine (AnthropicApiClient + tool loop)
```

## Key OpenHarness Governance Controls

| Control | How enforced |
|---|---|
| Narrow tool allowlist | `ToolRegistry` registers only `DraftSupportReplyTool`; `PermissionSettings(allowed_tools=["draft_support_reply"])` |
| Auto-approval for read-only tool | `DraftSupportReplyTool.is_read_only()` returns `True` |
| Session-scoped memory | `engine.clear()` called after every triage call — no MEMORY.md written |
| Product-level approval | `request_case_creation_approval()` uses product callback — not an OpenHarness tool |
| Import boundary | `openharness.*` imports appear only in `adapters/openharness_adapter.py` — `quick_drift_check.py` catches leakage |

## Practical Takeaway

The harness lives entirely in the adapter:

- `SupportTriageService` owns business logic — no harness knowledge
- `OpenHarnessAdapter` owns tool registration, engine lifecycle, event recording, and session reset
- `DraftSupportReplyTool` is the only registered tool — everything else is denied
- switching to another harness means replacing `openharness_adapter.py` only
