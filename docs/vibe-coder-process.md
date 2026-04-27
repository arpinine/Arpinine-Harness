# Arpinine Harness Operating Process

This document defines the operating process teams should follow to use Arpinine Harness successfully.

It is written as an execution playbook:
- each step has a clear scope
- each step has an expected deliverable
- each step states what is manual and what is automatic

The process assumes:
- Arpinine Harness is registered for the current assistant implementation
- the repository uses the `.specify/` artifact model
- the user wants fast AI-assisted delivery without losing control of scope, architecture, or quality

## You Are Working With A Virtual Delivery Team

Arpinine Harness is not a single assistant command wrapper.
It is a coordinated team of agent roles operating through one plugin interface.

When a user runs an Arpinine Harness command, the plugin should behave like a delivery team:
- `product-owner`: clarifies user value, scope, constraints, and acceptance criteria
- `tech-architect`: defines boundaries, dependencies, sequencing, and ADR-worthy decisions
- `tdd-guide`: keeps implementation task-aligned, incremental, and test-first
- `security-reviewer`: identifies risky assumptions, unsafe shortcuts, and missing controls
- `evaluation-governor`: makes quality expectations explicit and measurable
- `drift-detector`: checks that spec, plan, ADRs, implementation, and observations still agree

The user should experience one conversation, but behind that conversation the plugin is expected to apply the right specialist posture for the current step.

## You May Also Be Working Alongside Another Assistant Team

Arpinine Harness supports multiple assistant teams sharing the same governed repository at the same time.

Typical example:

- one delivery lane runs in Claude
- one delivery lane runs in Codex
- both operate on the same spec, plan, ADR, evaluation, and delivery artifacts
- implementation work is coordinated through task claims and optional team tags in `plan.md`

So the operating model has two layers:

- specialist roles inside one assistant session
- multiple assistant teams coordinated through the same governed artifacts

## Operating Principle

Arpinine Harness is not a prompt pack for "just build it".
It is a governed delivery loop:

1. define intent
2. refine intent
3. plan the work
4. record important decisions
5. implement task by task
6. evaluate where needed
7. observe runtime behavior where needed
8. audit drift
9. extract reusable lessons

The user should never skip directly from idea to code when the work is non-trivial.

## Manual Means "Answer Questions", Not "Edit Artifacts"

Arpinine Harness should minimize document editing by the user.

Default rule:
- the plugin asks focused questions when information is missing
- the user answers in chat
- the plugin updates the correct artifact directly

The user should only edit `spec.md`, `plan.md`, ADRs, eval files, or rule files manually when they explicitly want to override or fine-tune the generated content.

## Role Posture By Step

Each workflow step should feel like the right part of the agent team is leading:

- `at-new`: primarily `product-owner`
- `at-review`: `product-owner` plus `evaluation-governor`
- `at-plan`: primarily `tech-architect`
- `at-adr`: `tech-architect` plus governance roles
- `at-implement`: primarily `tdd-guide` with `security-reviewer`
- `at-eval`: primarily `evaluation-governor`
- `at-observe`: primarily `drift-detector`
- `at-audit`: `drift-detector` plus architecture/evaluation governance
- `at-retro`: governance roles extracting reusable lessons

This framing matters because the plugin should not ask generic questions. It should ask the kind of questions the responsible role would ask at that stage, then update the corresponding artifacts directly.

## Step 0: Register And Prepare The Plugin

**Goal**
Make the plugin available in the current assistant and confirm the repo can use the workflow.

**Scope**
- plugin registration
- dependency readiness
- local repo readiness

**How**
- Register the plugin for the current implementation:
  - `make register IMPLEMENTATION=claude`
  - `make register IMPLEMENTATION=codex`
- If using Claude, native install is available:
  - `make install IMPLEMENTATION=claude`
- Confirm `spec-kit` exists:
  - `specify --version`

**Manual**
- choose the implementation
- enable the plugin in the assistant UI if required
- confirm dependencies are installed

**Automatic**
- assembled plugin generation
- marketplace registration
- delivery matrix generation support

**Expected Deliverable**
- plugin available in the assistant
- repo ready to run `/arpinine-harness:*` workflow commands

## Step 1: Initialize Governance

**Command**
- `/arpinine-harness:at-init`

**Goal**
Create the shared governance structure for the repo.

**Scope**
- initialize `.specify/`
- create ADR index
- confirm workflow conventions

**Manual**
- run the command
- inspect the output for dependency warnings

**Automatic**
- `.specify/specs/`
- `.specify/adr/`
- `.specify/evals/`
- `.specify/observations/`
- `.specify/rules/`
- `.specify/coordination/`
- `ADR-INDEX.md` if missing

**Expected Deliverable**
- initialized governance workspace
- agreed repository contract for spec, plan, ADR, eval, observation, and rule artifacts

## Step 2: Define The Feature

**Command**
- `/arpinine-harness:at-new <feature name>`

**Goal**
Turn an idea or request into a product-facing specification.

**Scope**
- user stories
- requirements
- acceptance criteria
- out-of-scope boundaries
- product constraints

**Manual**
- provide the feature request
- answer the plugin's scope, constraint, and open-question prompts in chat
- review the generated `spec.md`

**Automatic**
- slug generation
- spec file placement under `.specify/specs/<slug>/spec.md`
- initial spec generation via spec-kit
- the plugin asks the minimum clarification questions needed to remove ambiguity
- writing clarification answers into `spec.md`

**Expected Deliverable**
- `.specify/specs/<slug>/spec.md`

**Exit Criteria**
- the spec says what and why
- the spec does not say how
- acceptance criteria are measurable

## Step 3: Refine The Spec

**Command**
- `/arpinine-harness:at-review <slug>`

**Goal**
Make the spec safe to implement.

**Scope**
- business case alignment
- measurability
- ambiguity removal
- readiness for planning

**Manual**
- review findings
- answer the plugin's follow-up questions in chat when the spec is ambiguous, incomplete, or untestable
- decide whether to proceed after the plugin updates the spec

**Automatic**
- product-facing checks
- measurability checks
- identification of missing structure or weak scope boundaries
- the plugin asks the minimum review questions needed to resolve critical or high ambiguity
- direct updates to `spec.md` based on the user's answers

**Expected Deliverable**
- refined `spec.md` that is ready for engineering planning

**Exit Criteria**
- no major ambiguity remains
- the spec is still product-facing
- planning can proceed without guessing intent

## Step 4: Plan The Work

**Command**
- `/arpinine-harness:at-plan <slug>`

**Goal**
Convert the approved spec into an executable engineering plan.

**Scope**
- architecture
- task breakdown
- module boundaries
- dependency rules
- testability
- harness strategy if relevant
- evaluation strategy if relevant
- optional cross-assistant task ownership

When multiple assistant instances will run concurrently, assign tasks in `plan.md` with optional tags such as `[team: claude]` and `[team: codex]`. Execution then claims tasks through `.specify/coordination/<slug>.json` so each runtime takes only eligible work that is not already leased by another team.

**Manual**
- inspect the generated plan
- answer the plugin's planning questions in chat about architecture, sequencing, evaluation, and harness strategy
- decide whether any technical choice needs an ADR

**Automatic**
- `plan.md` generation
- task list generation
- architecture/governance checks
- evaluation planning prompts where relevant
- the plugin asks the minimum planning questions needed to complete missing decisions
- direct updates to `plan.md` and related artifacts based on the user's answers

**Expected Deliverable**
- `.specify/specs/<slug>/plan.md`
- optional `.specify/evals/<slug>/eval-plan.md`

**Exit Criteria**
- `plan.md` defines HOW
- tasks are explicit enough to execute one by one
- architecture sections are complete

## Step 5: Record Consequential Decisions

**Command**
- `/arpinine-harness:at-adr new "<decision title>"`

**Goal**
Capture decisions that should not remain implicit in code.

**Scope**
- architecture choices
- boundary decisions
- drift ratification
- operational/security tradeoffs

**Manual**
- decide which choices deserve an ADR
- answer the plugin's ADR questions in chat to complete context, decision, consequences, and alternatives
- approve lifecycle status changes

**Automatic**
- ADR numbering
- ADR file creation
- ADR index updates
- the plugin asks the minimum ADR questions needed to complete the record
- direct population of ADR content from the user's answers

**Expected Deliverable**
- `.specify/adr/ADR-NNNN-<title>.md`
- updated `.specify/adr/ADR-INDEX.md`

**Exit Criteria**
- any consequential decision referenced by the plan is traceable

## Step 6: Implement Task By Task

**Command**
- `/arpinine-harness:at-implement <slug>`

**Goal**
Execute the plan without drifting from the spec, architecture, or ADRs.

**Scope**
- code changes
- tests
- task status tracking
- security review

**Manual**
- review and accept code changes
- answer the plugin's implementation questions in chat if the current task is ambiguous or blocked
- decide whether to accept a re-plan or ADR update when the plugin detects consequential drift

**Automatic**
- the plugin claims the next eligible task through `.specify/coordination/<slug>.json`
- the plugin uses task tags such as `[team: claude]` and `[team: codex]` to restrict ownership when present
- the PreToolUse task-claim gate blocks implementation-path edits until the current team identity owns an active claim
- the plugin updates the task state in `plan.md` from `[ ]` to `[~]` after the claim succeeds
- the plugin updates the task state in `plan.md` from `[~]` to `[x]` when work is complete
- the `PostToolUse` delivery hook regenerates `.specify/delivery.md` after `plan.md` changes
- the `PostToolUse` drift hook runs after file writes and surfaces lightweight alignment issues
- the `PreToolUse` governance hooks block invalid implementation edits before they land

**Expected Deliverable**
- implementation for the selected tasks
- tests proving the work
- updated `plan.md` task status
- updated `.specify/delivery.md`

**Exit Criteria**
- code matches the plan
- tests pass
- completed tasks are marked `[x]` by the plugin

## Step 7: Evaluate Where Required

**Command**
- `/arpinine-harness:at-eval plan <slug>`
- `/arpinine-harness:at-eval run <slug>`
- `/arpinine-harness:at-eval review <slug>`

**Goal**
Prove quality with explicit metrics when the feature needs more than conventional tests.

**Scope**
- eval criteria
- datasets or scenarios
- thresholds
- pass/fail decision

**Manual**
- decide whether the feature needs a formal eval
- choose the evaluation framework
- review pass/fail outcomes

**Automatic**
- eval plan artifact generation
- results capture
- threshold comparison

**Expected Deliverable**
- `.specify/evals/<slug>/eval-plan.md`
- `.specify/evals/<slug>/latest-results.md`

**Exit Criteria**
- required thresholds pass
- or failures are explicitly routed back into implementation/refinement

## Step 8: Observe Runtime Behavior Where Relevant

**Command**
- `/arpinine-harness:at-observe record <slug>`
- `/arpinine-harness:at-observe review <slug>`

**Goal**
Capture what the system actually did at runtime and compare that to the plan.

**Scope**
- runtime traces
- tool usage
- approvals
- memory/state behavior
- runtime drift signals

**Manual**
- choose the scenario to observe
- provide or capture the runtime evidence
- review the resulting drift implications

**Automatic**
- observation artifact structure
- normalization targets
- drift classification prompts during review

**Expected Deliverable**
- `.specify/observations/<slug>/latest-observation.md`
- `.specify/observations/<slug>/trace.json`

**Exit Criteria**
- observed behavior is documented
- runtime mismatches are visible, not implicit

## Step 9: Audit Drift

**Command**
- `/arpinine-harness:at-audit <slug>`

**Goal**
Detect where implementation, spec, plan, ADRs, evals, and observations no longer agree.

**Scope**
- spec drift
- architecture drift
- ADR coverage gaps
- evaluation regression
- observation drift

**Manual**
- review findings
- decide whether each item means:
  - refine spec/plan
  - fix implementation
  - create ADR
  - add rule candidate later

**Automatic**
- static drift hints
- severity classification
- ADR coverage checks
- attribution prompts for precondition vs postcondition failure

**Expected Deliverable**
- drift findings
- explicit next action per finding

**Exit Criteria**
- no critical unresolved drift remains before continuing

## Step 10: Capture Lessons

**Command**
- `/arpinine-harness:at-retro <slug>`

**Goal**
Turn one feature's learning into reusable team rules.

**Scope**
- delivery retrospective
- process failures
- repeatable lessons
- new rules

**Manual**
- answer the retro questions honestly
- decide which lessons are generalizable

**Automatic**
- rule artifact creation when confirmed
- linkages to source ADR/spec where applicable
- writing the answers into generated retro outputs and rule artifacts

**Expected Deliverable**
- updated `.specify/rules/`
- explicit retro summary

**Exit Criteria**
- important lessons are preserved as reusable constraints, not just remembered informally

## Step 11: Use Status As The Daily Control Surface

**Command**
- `/arpinine-harness:at-status`

**Goal**
Give the user one safe place to understand project state before making changes.

**Scope**
- spec coverage
- open drift
- ADR state
- eval state
- observation state
- dependency readiness

**Manual**
- run it before starting a new session or major task
- decide what is blocked versus ready

**Automatic**
- status synthesis from repo artifacts
- onboarding summary when needed

**Expected Deliverable**
- a current governance snapshot

**Exit Criteria**
- the next action is chosen from visible repo state, not memory

## Recommended Day-To-Day Loop

For a new feature:

1. `/arpinine-harness:at-new`
2. `/arpinine-harness:at-review`
3. `/arpinine-harness:at-plan`
4. `/arpinine-harness:at-adr new ...` when a decision is consequential
5. `/arpinine-harness:at-implement`
6. `/arpinine-harness:at-eval ...` if needed
7. `/arpinine-harness:at-observe ...` if runtime evidence matters
8. `/arpinine-harness:at-audit`
9. `/arpinine-harness:at-retro`

For an existing feature already in progress:

1. `/arpinine-harness:at-status`
2. read the spec, plan, ADRs, and delivery matrix
3. continue the next planned task with `/arpinine-harness:at-implement`
4. audit if drift appears

## What Is Manual vs Automatic Overall

**Manual responsibilities**
- deciding what problem to solve
- approving scope
- answering focused clarification questions
- reviewing spec quality
- approving architecture decisions
- choosing the next task
- reviewing generated code and tests
- deciding whether drift is acceptable
- deciding whether a lesson becomes a rule

**Automatic responsibilities**
- file structure and artifact placement
- hook-based guardrails
- delivery matrix refresh
- static drift hints
- script-backed status summaries
- ADR indexing
- plan/eval/observation scaffolding

## Anti-Patterns

Do not:
- start coding before `plan.md` exists
- leave tasks only in chat instead of `plan.md`
- keep acceptance criteria vague
- let code redefine the product scope without a spec or ADR update
- ignore drift findings and continue implementation
- treat the delivery matrix as a task editor; it is a status surface, not the source task definition

## Minimum Successful Usage

If the team is lightweight and wants the smallest process that still works:

1. `/arpinine-harness:at-init`
2. `/arpinine-harness:at-new`
3. `/arpinine-harness:at-review`
4. `/arpinine-harness:at-plan`
5. `/arpinine-harness:at-implement`
6. `/arpinine-harness:at-status`

That is the minimum viable governed delivery loop.
