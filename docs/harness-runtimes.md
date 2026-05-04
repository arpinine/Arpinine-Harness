# Harness Runtimes: Why, What, and How the Plugin Governs Them

This is the canonical conceptual guide for harness selection and governance.

For a step-by-step operator flow, use [agent-application-checklist.md](agent-application-checklist.md).
For an example-driven walkthrough, use [examples/end-to-end/support-agent-demo/harness-explained.md](../examples/end-to-end/support-agent-demo/harness-explained.md).

---

## Why Harness

A harness is an agent runtime embedded in product code. Where a single LLM call takes a prompt and returns a response, a harness wraps the model in an operational layer that runs a loop: call the model, detect tool requests, execute approved tools, feed results back, repeat until the task resolves. That loop is what makes an agent — and the harness is the infrastructure that runs it.

Concretely, a harness provides:

- **Tool execution** — the model requests a tool call; the harness validates it against a registered allowlist, checks permissions, executes it, and returns the result to the next model turn
- **Memory** — state that persists across turns within a session (conversation history, intermediate results, working context) and optionally across sessions
- **Permission control** — a gate between tool requests and execution; write actions can require human approval before proceeding
- **Session lifecycle** — initialization, turn management, and teardown with explicit reset boundaries

Without a harness, you write this loop yourself. With one, you get a framework that handles the loop mechanics — but you take on a dependency that sits between your product and the model. That dependency is what governance targets.

Without governance, three failure modes appear consistently:

**Coupling failure** — product code imports the harness SDK directly, everywhere. Swapping runtimes means rewriting the product, not swapping a file.

**Scope creep** — tool access grows without justification. Agents call things they should not. No audit trail, no approved list.

**Silent state** — memory scope is undocumented. Session state leaks across users. Approval flows are implicit. Write actions happen without human gates.

Arpinine Harness does not provide a runtime. It governs how a runtime connects to the product by requiring explicit documentation before implementation starts and verifying that documentation against observed runtime behavior after execution.

---

## How To Evaluate A Harnessed Agent

Evaluate a harnessed agent at two levels:

1. **Task quality** — did the agent produce the correct business outcome?
2. **Runtime behavior** — did the harness use tools, memory, permissions, and session state the way the plan said it would?

An agent is not "working" just because the final text looks plausible. A governed harness must produce evidence that the runtime stayed inside its declared boundaries.

### What To Check

| Area | Questions to answer |
|---|---|
| Task outcome | Did it solve the task correctly? Did it finish within acceptable latency and cost? |
| Tool behavior | Did it call the right tool? Were arguments valid? Did it avoid unnecessary or repeated tool calls? |
| Permission behavior | Did protected actions require approval? Did denied actions stay blocked? |
| Memory behavior | Did state persist only within the allowed scope? Did reset actually clear it? |
| Session behavior | Did a new session start clean? Did the loop terminate correctly instead of spinning? |
| Safety behavior | Did it resist prompt injection, avoid forbidden tools, and stay within the documented boundary? |

### Evidence The Harness Must Expose

To make those checks possible, the harness or its adapter should expose structured evidence:

- **tool events** — requested, started, completed, denied
- **permission events** — approval required, approved, denied
- **memory events** — read, write, scope, reset
- **session lifecycle events** — started, cleared, ended
- **trace metadata** — model, turn count, retries, latency, token/cost telemetry where relevant

Text logs are not enough. Governance needs structured events that can be compared against `## Harness Strategy` and `eval-plan.md`.

### Practical Evaluation Pattern

For each eval case, score both the output and the runtime evidence.

Example assertions:

- the final classification or answer is correct
- only approved tools were called
- a `permission_check` happened before any protected write
- memory stayed in `session` scope when the plan said session-only
- reset cleared prior context before the next run

This is why Arpinine Harness requires both:

- `## Harness Strategy` in `plan.md`
- harness-specific checks in `## Evaluation Strategy` and `eval-plan.md`

---

## Mandatory Capabilities

For a framework to satisfy harness governance controls, it must support seven capabilities. These are not preferences — each maps to a specific enforcement point in the plugin.

### 1. Explicit Tool Allowlist

Framework must allow a fixed allowlist declared at registration time, not at call time. Unknown tools must be rejected before execution.

**Why:** `drift-detector` compares observed tool calls against the allowlist documented in `## Harness Strategy`. A framework that permits undeclared tools at runtime makes this check meaningless.

### 2. Approval Callbacks for Write Actions

Write actions must trigger a callback before execution. The caller must explicitly approve or deny. Pattern: `onApprovalRequired(action, context)` → `approve(id)` or `deny(id)`.

**Why:** observation traces must contain a `permission_check` event before any write tool completes. Missing approval event = `PERMISSION_DRIFT` = CRITICAL, blocks completion.

### 3. Session-Scoped Memory

Memory must be scopeable to a session with an explicit reset condition. Framework must not write cross-session state by default.

**Why:** `memory_write` events in observation traces carry a `scope` field. `drift-detector` verifies scope matches the declared memory model. Cross-session writes without documentation = `MEMORY_DRIFT` = CRITICAL.

### 4. Observable Event Stream

Every tool call, permission check, and memory write must emit inspectable structured events — not just logs. Events are the evidence that runtime behavior matched the documented strategy.

**Why:** observation traces are the artifact `at-audit` uses. Frameworks that produce only text logs cannot generate the structured per-event evidence the governance model requires.

### 5. Wrappable Behind an Interface

Framework must be instantiable through an adapter class. No mandatory static globals, no forced SDK imports throughout product code.

**Why:** `quick_drift_check.py` detects harness imports outside adapter or infrastructure paths after every file write. A framework that forces its imports into domain or application layers will generate continuous HIGH drift warnings.

### 6. Testable Without Full Runtime

Framework must be replaceable with a stub or fake for unit tests. Tests cannot depend on a live model, network, or credentials.

**Why:** `tdd-guide` enforces RED→GREEN→REFACTOR per task. If tests require a live runtime, the TDD loop breaks and the test suite cannot serve as implementation evidence.

### 7. Swap Path Feasibility

Switching frameworks must require changing the adapter only. A framework that bleeds abstractions into product layers — custom decorators, mandatory base classes, file conventions in domain code — fails this.

**Why:** `## Harness Strategy` requires a documented swap path. If the honest answer is "rewrite the whole product," `harness-governor` blocks implementation until the team either picks a different runtime or documents an ADR ratifying the coupling.

---

## Framework Comparison

| Capability | LangGraph | Pydantic AI | OpenHarness | Semantic Kernel | CrewAI |
|---|---|---|---|---|---|
| Explicit tool allowlist | Yes | Yes | Yes | Yes | Partial |
| Approval callbacks | Yes (interrupt) | Partial | Yes | Partial | No |
| Session-scoped memory | Yes | Yes | Needs config | Yes | Partial |
| Observable event stream | Yes | Partial | Partial | Yes | No |
| Wrappable behind interface | Yes | Yes | Likely | Yes | Yes |
| Testable without runtime | Yes | Yes | Partial | Yes | Yes |
| Clean swap path | Yes | Yes | Medium | Harder | Harder |

**LangGraph** and **Pydantic AI** satisfy all seven with no extra configuration. Best default choices.

**OpenHarness** ([github.com/HKUDS/OpenHarness](https://github.com/HKUDS/OpenHarness)) — Python, 11.8k stars, MIT. Satisfies most capabilities but has two governance risks that require explicit mitigation:

- Memory is cross-session by default (MEMORY.md persists across sessions). Teams must configure and document session scope in `## Harness Strategy` or `MEMORY_DRIFT` will fire.
- 43+ tools available out of the box. Tool allowlist must be explicitly restricted at registration time. Broad default access fails the narrow-allowlist requirement.

### What OpenHarness Provides In Practice

OpenHarness is viable, but not "governed by default." In the demo in this repo, some required evidence comes from OpenHarness and some is added by the adapter:

| Capability | OpenHarness alone | In this repo's adapter |
|---|---|---|
| Tool loop | Yes | `QueryEngine.submit_message(...)` runs the loop |
| Tool allowlist | Yes | `ToolRegistry` + `PermissionSettings(allowed_tools=[...])` narrow it |
| Permission gate for tools | Yes | `PermissionChecker` enforces tool permission settings |
| Session reset | Partial | `engine.clear()` is called explicitly after each triage run |
| Structured tool event stream | Partial | adapter records `tool_call` when `ToolExecutionStarted` is observed |
| Product-level approval evidence | No | adapter emits `permission_check` for `create_support_case` |
| Memory-scope evidence | No direct proof by itself | adapter emits `memory_write` with `scope: "session"` |
| Eval harness | No | repo adds `run_live_eval.py`, governed eval plan, and drift checks |

So the practical answer is:

- **yes**, OpenHarness provides the core agent runtime loop, tool registration, and permission primitives
- **partially**, it provides the observability needed for governance
- **no**, it does not by itself satisfy the full Arpinine Harness evidence model unless your adapter adds the missing runtime signals

In this repository's OpenHarness example, that missing evidence is intentionally added in `app/support_triage/adapters/openharness_adapter.py`.

**Semantic Kernel** — approval callbacks and swap path require workarounds. Document them in `## Harness Strategy` before `harness-governor` passes.

**CrewAI** — no approval callbacks, no structured event stream. Two hard gaps. Requires significant adapter work to satisfy governance controls. Not recommended without custom event instrumentation.

Any framework not listed is valid. Governance controls apply regardless of runtime — the team documents the controls, `harness-governor` enforces that documentation exists and `drift-detector` verifies it against observations.

---

## How the Plugin Manages Frameworks

The plugin is runtime-agnostic. It does not install, wrap, or call any harness SDK. It governs through four mechanisms:

### 1. Pre-Implementation Gate (`harness-governor` skill)

Fires during `/at-plan` when `## Harness Strategy` names a runtime. Checks all seven harness-strategy controls are documented: why, runtime, boundary, tools, memory, permissions, and swap path. Missing any = HIGH block, `/at-implement` cannot start. Harness-specific evaluation is checked separately in `## Evaluation Strategy` and `eval-plan.md`.

When `plan.md` names OpenHarness specifically, three additional checks fire:

| Check | Severity |
|---|---|
| Adapter-layer isolation not defined | HIGH |
| Approval callback or permission flow undocumented | HIGH |
| Session or state handling undocumented | HIGH |

### 2. Post-Write Drift Detection (`quick_drift_check.py`)

Runs automatically via PostToolUse hook after every file write. Checks:

- Harness imports outside adapter or infrastructure paths
- Framework imports inside domain or business layers
- Endpoint mismatches between spec and code

```python
OPENHARNESS_IMPORT_RE = re.compile(
    r"(@openharness/|from\s+openharness\b|import\s+openharness\b"
    r"|from\s+[\"'][^\"']*openharness[^\"']*[\"']"
    r"|require\([\"'][^\"']*openharness[^\"']*[\"']\))",
    re.IGNORECASE,
)

FRAMEWORK_IMPORT_RE = re.compile(
    r"\b(fastapi|flask|django|express|nestjs|sqlalchemy|typeorm|sequelize|prisma|redis)\b",
    re.IGNORECASE,
)

DOMAIN_PATH_RE = re.compile(r"(^|/)(domain|core|business)(/|$)", re.IGNORECASE)
```

Harness import found outside adapter path → HIGH drift warning. Framework import found in domain layer → HIGH drift warning. Both fire on every write, not just at audit time.

### 3. Observation Verification (`drift-detector` skill)

After benchmark runs, `drift-detector` compares the observation trace against `## Harness Strategy`:

| Trace event | Checked against |
|---|---|
| `tool_call.tool` | documented tool allowlist |
| `permission_check.action` | documented permission model |
| `memory_write.scope` | documented memory model |

Contradictions produce named drift classes:

| Class | Trigger | Severity |
|---|---|---|
| `TOOL_DRIFT` | Tool call not in allowlist | CRITICAL |
| `PERMISSION_DRIFT` | Write action without approval event | CRITICAL |
| `MEMORY_DRIFT` | Memory write scope contradicts strategy | CRITICAL |
| `EVAL_COVERAGE_DRIFT` | Observed failure path not in eval plan | HIGH |
| `RUNTIME_BEHAVIOR_DRIFT` | Runtime behavior contradicts adapter assumptions | HIGH |

CRITICAL drift blocks completion. The team must fix the adapter or update `## Harness Strategy` and create an ADR ratifying the change.

### 4. Dependency Check (`check_dependencies.py`)

Validates toolchain readiness before governance-required commands run. Triggered conditionally:

```python
if "## Harness Strategy" in plan_text and re.search(r"openharness", plan_text, re.IGNORECASE):
    checks.append(command_status("Node.js for OpenHarness workflows", "node", False))
    checks.append(command_status("npm for OpenHarness workflows", "npm", False))
```

Only runs the check when the plan names the runtime. No unnecessary toolchain requirements for teams that chose a different framework.

---

## Summary

The plugin enforces one rule regardless of which framework a team picks:

> The harness runtime must be isolated behind an adapter. Product code depends on an internal interface. Observed runtime behavior must match documented strategy.

Framework choice is the team's decision. Governance of that choice is the plugin's job.
