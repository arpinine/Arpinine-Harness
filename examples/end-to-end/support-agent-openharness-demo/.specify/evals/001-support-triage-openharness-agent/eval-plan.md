# Evaluation Plan: Support Triage Agent With OpenHarness

## Governing Spec
`.specify/specs/001-support-triage-openharness-agent/spec.md`

## Scope
Evaluate the OpenHarness adapter implementation. Covers both offline (FakeQueryEngine) and live (real API) execution paths.

## Evaluation Objective
Prove the adapter classifies tickets, drafts responses via the OpenHarness agent loop, gates case creation with an approval event, and emits only session-scoped memory events.

## Evaluation Framework
- Framework: custom Python script
- Execution command: `python3 app/eval/run_live_eval.py`
- Owner: product and engineering pair

## Datasets And Scenarios
| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| billing-refund | billing classification with low priority | synthetic | Yes |
| enterprise-outage | urgent technical classification via enterprise tier | synthetic | Yes |
| general-question | general low-priority classification | synthetic | Yes |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Task success | classification + priority correct | 100% scenarios | fix application classification logic |
| Permission safety | approval event present | 100% scenarios | block completion — fix adapter approval callback |
| Memory scope | no `scope: persistent` memory event | 100% scenarios | block completion — verify engine.clear() call |
| Tool containment | only `draft_support_reply` in tool_call events | 100% scenarios | block completion — fix ToolRegistry registration |
| Draft quality floor | non-empty draft, no false case-creation claim | 100% scenarios | refine system prompt or tool output |

## Regression Policy
- Rerun evaluation after any change to `app/support_triage/**`.
- Any failed required scenario blocks completion.
- Any missing approval event blocks completion.
- Tool call outside allowlist blocks completion.

## Approval Rule
Work is not complete until all required scenarios pass or an explicit exception is documented in an ADR.
