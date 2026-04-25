---
description: Define and run evaluation for a spec or agent using any suitable framework. Require explicit metrics, thresholds, datasets, and pass/fail outcomes before work is considered complete.
---

# /at-eval

Define or run evaluation for the current spec.

## Usage
- `/agent-align:at-eval plan <slug>` — create or update the evaluation plan
- `/agent-align:at-eval run <slug>` — run the chosen evaluation framework and record results
- `/agent-align:at-eval review <slug>` — review the latest evaluation results against thresholds

`<slug>`: feature slug matching a directory under `.specify/specs/`, e.g. `001-user-login`

## Principles

- The plugin enforces the evaluation contract, not a single evaluation vendor
- Teams may use DeepEval, custom pytest suites, benchmark harnesses, or another framework
- Every agentic workflow must define metrics, datasets, thresholds, and a pass/fail policy

## Workflow: `plan`

1. Locate `.specify/specs/<slug>/spec.md` and `.specify/specs/<slug>/plan.md`.
2. Create or update `.specify/evals/<spec-slug>/eval-plan.md` from `templates/eval-plan-template.md`.
3. Determine whether the spec produces agentic behavior, AI-assisted decisioning, or prompt-driven output.
4. If yes, define:
   - evaluation objective
   - evaluation framework
   - datasets or scenarios
   - metrics
   - pass thresholds
   - regression policy
   - execution command
5. Ensure `plan.md` links to the eval plan and includes evaluation tasks.
6. If the work is non-agentic, document why lightweight or conventional testing is sufficient.

## Workflow: `run`

1. Read `.specify/evals/<spec-slug>/eval-plan.md`.
2. Validate that the framework command exists in the current environment.
3. If the command is unavailable, stop and report the missing dependency instead of attempting installation.
4. Run the framework command defined there.
5. Save results to `.specify/evals/<spec-slug>/latest-results.md`.
6. Summarize:
   - framework used
   - datasets or scenarios covered
   - metric scores
   - thresholds
   - pass/fail result
7. If a threshold fails, mark the spec as needing refinement or implementation changes before completion.

## Workflow: `review`

1. Compare `latest-results.md` against the thresholds in `eval-plan.md`.
2. Report each metric as `PASS`, `WARN`, or `FAIL`.
3. If any required threshold fails:
   - block completion
   - identify whether the fix belongs in code, spec, plan, prompts, or ADRs
4. If the system passes, summarize residual risks and uncovered scenarios.

## Required Outputs

- `.specify/evals/<spec-slug>/eval-plan.md`
- `.specify/evals/<spec-slug>/latest-results.md`

## Error Conditions

- Eval plan missing → "Run `/agent-align:at-eval plan` first"
- Framework command missing → "Add an execution command to eval-plan.md"
- Framework dependency unavailable → "Install the tool declared in eval-plan.md before running `/agent-align:at-eval run`"
- Results missing thresholds → "Define thresholds before evaluation can pass"
