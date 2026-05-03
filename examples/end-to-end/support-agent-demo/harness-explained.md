# Harness Usage: What, Why, and How

This document walks through the harness governance lifecycle end-to-end using the support triage demo as the concrete example.

---

## What Is a Harness

A harness is an agent runtime embedded in product code. It provides a tool-calling loop, memory, and permission control for features that go beyond a single LLM call — for example, an agent that classifies a ticket, drafts a reply, and waits for human approval before creating a support case.

Arpinine Harness does not provide the runtime. It governs how the runtime connects to your product.

---

## Why Harness Governance Matters

Without governance:
- product code couples directly to a harness SDK — swapping runtimes rewrites the product
- tool access grows without justification — agents call things they should not
- memory scope is undocumented — session state leaks across users
- approval flows are implicit — write actions happen without human gates
- failures are untested — eval covers the happy path only

With governance:
- one adapter file owns the harness dependency — the rest of the product is unchanged
- every tool is explicit and narrow — observed calls are checked against the allowlist
- memory scope is declared and verified by observations
- approval callbacks are documented and tested
- eval covers harness-specific failure modes, not just feature correctness

---

## Step 1 — Declare the Harness in `plan.md`

Before any code, `plan.md` must contain `## Harness Strategy`. If the section is missing or says `N/A`, `harness-governor` is silent. When a runtime is named, all controls are required.

**This demo's declaration:**

```markdown
## Harness Strategy
| Concern                   | Decision                                                                                   |
|---------------------------|--------------------------------------------------------------------------------------------|
| Why harness is needed     | Agent drafts responses, records tool calls, and requests approval before case creation     |
| Harness/runtime class     | Embedded agent runtime simulated by a fake adapter                                         |
| Product abstraction boundary | `SupportAgentRuntime` interface in the application layer                                |
| Tool access model         | `draft_support_reply` only — no filesystem, shell, email, or CRM access                   |
| Memory/state model        | Session-scoped event list only — no persistent cross-customer memory                       |
| Permission and safety model | `create_support_case` requires a permission check before completion evidence is accepted |
| Swap strategy             | Replace `FakeHarnessRuntime` with a real adapter — domain and application code unchanged   |
```

**What `harness-governor` checks:**

| Control | Missing = |
|---|---|
| Abstraction boundary defined | HIGH — blocks implementation |
| Tool allowlist explicit | HIGH — blocks implementation |
| Memory scope declared | HIGH — blocks implementation |
| Permission model documented | HIGH — blocks implementation |
| Swap path described | HIGH — blocks implementation |

---

## Step 2 — Implement the Boundary

The boundary is an internal interface. Product code depends on it. The harness SDK never appears outside the adapter.

**Internal interface** (`app/support_triage/application/triage_service.py`):

```python
class SupportAgentRuntime:
    """Internal runtime boundary. Product code depends on this, not a harness SDK."""

    def draft_response(self, ticket: Ticket, category: str, priority: str) -> str:
        raise NotImplementedError

    def request_case_creation_approval(self, ticket: Ticket, result: TriageResult) -> bool:
        raise NotImplementedError
```

**Application service** — calls the interface, never the harness:

```python
class SupportTriageService:
    def __init__(self, runtime: SupportAgentRuntime):
        self._runtime = runtime

    def triage(self, ticket: Ticket) -> TriageResult:
        draft = self._runtime.draft_response(ticket, category, priority)
        self._runtime.request_case_creation_approval(ticket, result)
        return result
```

**Adapter** (`app/support_triage/adapters/fake_harness.py`) — only file that knows about the runtime:

```python
class FakeHarnessRuntime(SupportAgentRuntime):
    def draft_response(self, ticket, category, priority):
        self.events.append({"type": "tool_call", "tool": "draft_support_reply", ...})
        return "..."

    def request_case_creation_approval(self, ticket, result):
        self.events.append({"type": "permission_check", "action": "create_support_case", "result": "approved", ...})
        self.events.append({"type": "memory_write", "scope": "session", ...})
        return True
```

**What `quick_drift_check.py` catches after every write:**

```python
OPENHARNESS_IMPORT_RE = re.compile(r"(@openharness/|from\s+openharness\b|...)", re.IGNORECASE)
DOMAIN_PATH_RE = re.compile(r"(^|/)(domain|core|business)(/|$)", re.IGNORECASE)
```

If `openharness` appears outside `adapters/` → HIGH drift warning fires automatically via PostToolUse hook.

**The intentional drift fixture** (`app/support_triage/application/drift_example_bad_direct_harness_import.py`) shows exactly what triggers it:

```python
from openharness import AgentRuntime  # ← OPENHARNESS_IMPORT_RE fires
```

---

## Step 3 — Record Observations

Each benchmark run records a trace per scenario. The trace captures the exact event sequence emitted by the adapter.

**Example trace** (enterprise-outage scenario):

```json
{
  "scenario_id": "enterprise-outage",
  "runtime_implementation": "fake-harness-adapter",
  "events": [
    { "type": "tool_call",       "tool": "draft_support_reply",  "ticket_id": "E-002" },
    { "type": "permission_check","action": "create_support_case","result": "approved", "ticket_id": "E-002" },
    { "type": "memory_write",    "scope": "session",              "key": "triage:E-002" }
  ],
  "final_outcome": "PASS",
  "latency_ms": 240
}
```

**What `drift-detector` checks against `## Harness Strategy`:**

| Observed | Expected | Verdict |
|---|---|---|
| `tool: "draft_support_reply"` | allowlist: `draft_support_reply` only | PASS |
| `action: "create_support_case"` with `result: "approved"` | permission check before case creation | PASS |
| `scope: "session"` on every memory write | session-scoped only | PASS |
| no unknown tools | narrow allowlist enforced | PASS |

**What would trigger CRITICAL drift:**

| Observed | Drift class | Severity |
|---|---|---|
| `tool: "send_email"` — not in allowlist | `TOOL_DRIFT` | CRITICAL |
| `scope: "user"` on memory write | `MEMORY_DRIFT` | CRITICAL |
| no `permission_check` before `memory_write` | `PERMISSION_DRIFT` | CRITICAL |

CRITICAL observation drift blocks completion. Must fix adapter or update `## Harness Strategy` + create ADR.

---

## Step 4 — Run Evaluation

Eval checks both feature correctness and harness-specific failure modes.

**Thresholds from `eval-plan.md`:**

| Dimension | Metric | Threshold | Failure action |
|---|---|---|---|
| Task success | pass rate | >= 1.00 | refine implementation or spec |
| Permission safety | approval check present | >= 1.00 | block completion |
| Memory scope | session-scoped only | >= 1.00 | block completion |
| Latency P95 | ms | <= 500ms | optimize implementation |

**Aggregate result across 3 scenarios:**

| Scenario | Result | Latency |
|---|---|---|
| billing-refund | PASS | 120ms |
| enterprise-outage | PASS | 240ms |
| general-question | PASS | 180ms |
| **Aggregate** | **PASS 3/3** | **P95 234ms** |

All thresholds satisfied. Baseline comparison clean. Completion gate passes.

**If a scenario fails:**

1. `at-implement` blocks completion immediately
2. Failure attributed as precondition (spec unclear) or postcondition (code deviated from clear spec)
3. Precondition → refine `spec.md`, fix code, rerun
4. Postcondition → fix code OR create ADR ratifying the deviation
5. One exception path: failing scenario accepted via ADR — must be explicit, documented, approved

---

## Step 5 — ADR for the Harness Decision

Harness choice is consequential. `tech-architect` pushes it into an ADR during `/at-plan`.

**ADR-0001** covers: `decision:001-support-triage-agent:harness-boundary`

Governs: `specs/001-support-triage-agent`

Records: why fake adapter, what the boundary is, what changes when a real runtime is introduced.

---

## Step 6 — Retro Rule (Compounding)

After the feature ships, `/at-retro` extracts the harness boundary lesson as a permanent rule.

**`harness-001`** (`.specify/rules/harness/harness-001.md`):

```yaml
rule-id: harness-001
triggers:  "Harness runtime import outside adapter or infrastructure layer"
prevents:  "Product code coupling directly to a harness SDK"
source-adr: ADR-0001
evidence-project: 001-support-triage-agent
severity: HIGH
active: true
forbidden_patterns: ["openharness"]
allowed_paths: ["app/support_triage/adapters/**"]
```

On every future spec, `drift-detector` loads active rules before creating ADRs. If `openharness` appears outside `adapters/`:

```
Rule violation: harness-001 — Product code coupling directly to a harness SDK
Skip ADR creation; rule enforcement is the gate.
```

The next project never has to learn this the hard way.

---

## Full Lifecycle Summary

```
plan.md declares harness
        │
        ▼
harness-governor validates 6 controls (boundary, tools, memory, permissions, swap path, evaluation)
        │
        ▼
implementation: SupportAgentRuntime interface ← product code
                FakeHarnessRuntime adapter    ← only file with runtime knowledge
        │
        ▼
quick_drift_check.py fires after every write
  → openharness import outside adapters/ = HIGH drift warning
        │
        ▼
benchmark run records observation trace per scenario
  → tool calls, permission checks, memory writes captured as events
        │
        ▼
drift-detector compares trace against ## Harness Strategy
  → TOOL_DRIFT / PERMISSION_DRIFT / MEMORY_DRIFT = CRITICAL, blocks completion
        │
        ▼
eval checks pass rate, approval rate, memory scope, latency P95
  → any threshold miss = completion blocked
        │
        ▼
ADR documents harness boundary decision
        │
        ▼
retro extracts harness-001 rule → fires on all future specs automatically
```
