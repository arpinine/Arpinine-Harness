# Evaluation Plan: User Login Agent

## Governing Spec
`.specify/specs/001-user-login/spec.md`

## Scope
- Evaluate the login support agent that assists with authentication troubleshooting and account access guidance.
- Applies to the current implementation of the login workflow assistant.

## Evaluation Objective
- Prove the agent gives correct, policy-compliant guidance and resolves common login issues without inventing unsupported recovery steps.

## Evaluation Framework
- Framework: DeepEval
- Execution command: `deepeval test run tests/evals/test_login_agent.py`
- Owner: Engineering

## Datasets And Scenarios
| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| happy-path-login | verify correct guidance for valid login flows | curated test cases | Yes |
| locked-account | verify safe handling of rate-limit and lockout scenarios | curated test cases | Yes |
| password-reset-edge-cases | verify no unsupported recovery advice | synthetic scenarios | Yes |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Task success | successful resolution rate | >= 0.90 | refine implementation |
| Safety / compliance | policy adherence score | >= 0.98 | block release |
| Hallucination / grounding | unsupported action rate | <= 0.02 | refine prompts or retrieval |
| Cost / latency | p95 response time | <= 2500 ms | optimize execution |

## Regression Policy
- Any drop below threshold is a release blocker.
- Evaluation must rerun after prompt changes, retrieval changes, or workflow changes.

## Reporting
- Latest results path: `.specify/evals/001-user-login/latest-results.md`
- Historical storage: CI artifacts

## Approval Rule
- Work is not complete until required thresholds pass or an explicit exception is documented.
