---
name: evaluation-governor
description: Enforces framework-agnostic evaluation planning, execution, and release gates for agentic work
---

# Evaluation Governor Skill

## Purpose

This skill ensures the team defines and uses evaluation before declaring agentic work complete.
It does not require a specific framework. It enforces the evaluation contract.

## When To Apply

- During planning for any agentic or AI-assisted workflow
- Before implementation is considered complete
- During audit when regressions or drift suggest quality degradation

## Required Evaluation Contract

Every evaluated system must define:
- evaluation objective
- framework or harness
- datasets or scenarios
- metrics
- thresholds
- execution command
- pass/fail rule

## Accepted Framework Examples

- DeepEval
- pytest-based harnesses
- custom benchmark runners
- framework-native eval systems

## Enforcement Rules

| Rule | Severity | Action |
|------|----------|--------|
| Agentic system has no eval plan | HIGH | Block completion |
| Eval plan has no thresholds | HIGH | Block completion |
| Required evaluation has not been run | HIGH | Block completion |
| Required evaluation fails thresholds | CRITICAL | Block completion |
| Results exist but are not linked from plan or delivery summary | MEDIUM | Require documentation |

## Review Questions

1. What behavior is being evaluated?
2. How will the team know the system is good enough?
3. Which metrics are release-blocking?
4. Which scenarios are still uncovered?
5. If results fail, where should the team refine: spec, plan, ADRs, prompts, or code?
