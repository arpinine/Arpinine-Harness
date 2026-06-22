# Plan: Context Compression Governance

## Governing Spec
`.specify/specs/011-context-compression-governance/spec.md`

## Technical Decisions

| Decision | Rationale | ADR |
|----------|-----------|-----|
| One shared `ContextCompressionProvider` abstraction with swappable implementations | Mirrors the 001/009/010 core-abstraction + default-impl pattern; keeps headroom replaceable | ADR-0013 |
| Default implementation consumes headroom as an external dependency | User decision; "default should be headroom"; avoids re-implementing compression | ADR-0014 (supply chain) |
| Whole-payload compression via a local proxy the host is pointed at (base-URL/env) | Plugin runs inside the host and cannot rewrite outbound provider calls in-process | ADR-0015 |
| Ship a noop provider; compression OFF starts no proxy | Optionality requirement; zero overhead and identical behavior when disabled | ADR-0013 |
| Enable/disable recorded in the constitution, chosen at `/at-init` | Single, auditable, governed toggle location | ADR-0016 |
| Proxy-unreachable degrades to uncompressed passthrough with an observable signal | Compression must never break or silently alter a governed session | ADR-0015 |
| Fidelity gate = deterministic golden-session replay with zero-divergence diff + session-total token reduction | Spec AC-001/AC-002; deterministic, not LLM-judged | ADR-0017 (eval framework) |
| CCR originals stored at `~/.arpinine/ccr-store/` (700/600), never in worktree or cloud-sync | Reversible retrieval needs local originals without leaking governed content | ADR-0018 |
| Proxy lifecycle model (per-session vs long-running) resolved before host wiring | Affects interface, host wiring, and benchmark; OQ-003 | ADR-0019 |

## Architecture

```text
src/arpinine-harness-core/
  templates/
    context-compression-provider-template.py        ← ContextCompressionProvider interface (abstraction)
    headroom-context-compression-provider-template.py ← default impl; wraps headroom proxy lifecycle
    noop-context-compression-provider-template.py     ← noop impl; no proxy, no compression
  scripts/
    scaffold_compression_setup.py                    ← idempotent scaffolder (mirrors scaffold_observability_setup.py)
    check-compression-setup.sh / check_compression_setup.py ← boundary + config + CCR-store-safety + logging checks
    run_golden_session_benchmark.py                  ← golden-session ON/OFF replay + token delta (the benchmark runner)
    fidelity_gate.py (FidelityGate)                  ← zero-divergence governance-outcome diff (the gate, distinct from the runner)
  commands/at-init.md                                ← adds the enable/disable choice; records it in the constitution
src/implementations/{claude,codex,copilot}/
  <host-specific proxy wiring>                        ← base-URL/env plumbing to route host→provider through the proxy
.specify/CONSTITUTION.md                              ← records the compression toggle (enabled/disabled)
.specify/evals/011-context-compression-governance/
  golden-session/                                     ← fixed recorded /at-* runs + expected governance outcome set
  eval-plan.md                                        ← fidelity + reduction thresholds and runner command
```

## Module Boundaries

| Module | Responsibility | Depends On | Must Not |
|--------|----------------|------------|----------|
| `ContextCompressionProvider` interface | Define compress / retrieve / activate-deactivate lifecycle + segment-key contract | Nothing host- or vendor-specific | Reference headroom, any proxy/port concept, or any host API in method names |
| Headroom default provider | Activate/deactivate the local headroom proxy; expose compress + reversible retrieval | headroom (external dep), interface | Leak headroom imports outside this module; expose raw proxy port/address through the lifecycle API |
| Noop provider | Satisfy the interface with passthrough; no proxy | interface | Start any process or touch the network |
| `/at-init` toggle | Capture enable/disable; persist to constitution | constitution artifact, interface selection | Hardcode a provider class or default to enabled |
| Per-host proxy wiring | Point Claude/Codex/Copilot at the proxy via an opaque endpoint token (base-URL/env) when enabled | host config surface, provider lifecycle API | Diverge in lifecycle API; couple to raw network coordinates; differ beyond host plumbing |
| `run_golden_session_benchmark.py` (runner) | Replay golden session ON/OFF, measure session-total tokens at the proxy | provider, golden-session fixture | Apply any tolerance; mutate governed artifacts |
| `FidelityGate` (gate) | Zero-divergence diff over the governance outcome set; PASS/FAIL verdict | route_at output, drift artifacts, AC states | Apply any materiality tolerance; mutate governed artifacts |

## Dependency Rules

- Host integrations and the benchmark MUST depend only on the `ContextCompressionProvider` interface, never on headroom directly.
- headroom imports/usage MUST be confined to the headroom default-provider module.
- The noop path MUST start no process and open no socket.
- When compression is disabled, no module on the compression path may execute (no proxy, no provider selection beyond noop).
- Benchmark runner and `FidelityGate` MUST be read-only over governed artifacts and apply zero tolerance.
- Token measurement MUST occur at the proxy boundary, not be estimated from provider billing.
- The provider lifecycle API MUST expose only an opaque endpoint token (or a configure-host callback), never the proxy's raw local port/address, so host integrations do not couple to network coordinates.
- Interface method names MUST stay vendor/transport-neutral (`activate`/`deactivate`, not `start_proxy`); the noop impl satisfies them as no-ops.
- The scaffolded provider files form an importable Python package named **`context_compression/`** (with `__init__.py`) — deliberately NOT `compression`, which would shadow the Python 3.14+ stdlib `compression` package. Consumers and host wiring MUST consume them through the import system (package imports), NOT by ad-hoc file-path loading. Two independent file-path loads of the interface file produce distinct `CompressionEndpoint`/`CompressionResult` classes (a Python invariant), breaking `isinstance`; package imports are cached by name and keep one interface identity regardless of import order. TASK-006 host wiring must import the `context_compression` package, not path-load it.

## Testability By Boundary

| Boundary | Test Type | Verification Method |
|----------|-----------|---------------------|
| `ContextCompressionProvider` interface | Unit | Contract tests run against both default and noop impls |
| Headroom default provider | Unit/Integration | Proxy starts, compresses a known payload, reversible retrieval asserts byte-equality |
| Noop provider | Unit | No process started; payload unchanged |
| `/at-init` toggle | Unit | Choice persisted to constitution; absent setting → disabled |
| Passthrough fallback | Integration | Proxy not started / refuses connections → session completes, fallback signal emitted |
| Per-host wiring | Integration | `make validate-structure IMPLEMENTATION=<impl>` confirms claude/codex/copilot wiring present |
| Fidelity benchmark | Integration | Golden-session ON vs OFF → empty governance-outcome diff AND 60–95% session-total token reduction |

## Harness Strategy

N/A — single LLM call sufficient. No agent loop, tool execution, or session state required.

(Determination per the harness decision gate: this feature is harness *infrastructure* — a local compression proxy in front of the host's existing provider calls. It introduces no product-side multi-turn tool-calling loop, no agent session state, no human-in-the-loop approval inside an agent loop, and no multi-agent orchestration. The compression proxy is a passthrough/transform service, not an agent harness.)

## Observability Strategy

**Observation required: NO.** This feature makes no product-runtime LLM calls of its own to instrument; it is the compression boundary that the host's existing calls pass through. Standard logging plus the explicit passthrough-fallback signal is sufficient. No `ObservationProvider`/OpenTelemetry/Langfuse instrumentation is introduced by this feature.

**Evaluation required: YES.** Compression is lossy and can alter results, so it is release-gated by a deterministic fidelity benchmark (see `## Evaluation Strategy` and `eval-plan.md`). The evaluation framework is a deterministic golden-session replay + zero-divergence diff + token-reduction measurement — NOT DeepEval, because the gate is exact structural comparison, not LLM-judged quality scoring. This deviation from the DeepEval default is governed by ADR-0017.

## AI Design Decisions

| Decision | Choice | Notes / ADR |
|----------|--------|-------------|
| Compression model/strategy | Delegated to headroom default (its internal routing/compressors are headroom-vendor concepts, NOT harness vocabulary) | Consumed as-is; not re-tuned. ADR-B |
| Context-overflow handling | Compression reduces outbound tokens; reversible retrieval (CCR) recovers exact originals on demand | ADR-A |
| Prompt-injection surface | Proxy sees all governed content incl. artifacts read as DATA; compression must not introduce injected directives or alter the data boundary | Mitigation: interface contract preserves DATA role boundary on compressed artifacts; adversarial directive-shaped case in benchmark asserts empty outcome diff; headroom local-first, no egress. See Security section. |
| Fidelity safeguard | Zero-divergence governance-outcome diff gates any reliance on compression | ADR-E |

## Deployment Strategy

N/A as a deployed service. The compression proxy is a **local-first** process on the operator's machine, lifecycle-managed by the harness. No remote hosting, no inbound network surface. headroom is an external package dependency installed locally (supply-chain governed by ADR-B). No secrets are introduced by this feature; the proxy must not require credentials beyond the host's existing provider auth, which it must pass through unchanged.

## Vocabulary Decisions

| Domain term (spec) | Code construct | Notes |
|--------------------|----------------|-------|
| ContextCompressionProvider | `ContextCompressionProvider` interface (incl. `activate`/`deactivate`/`compress`/`retrieve` + segment-key contract) | No generic `Compressor`/`Manager`/`Handler`; no proxy/port in method names |
| Compression proxy | the running local process, referenced via constant/config key `compression_proxy`; lifecycle owned by the headroom default provider | Local-first |
| Golden harness-session benchmark | `run_golden_session_benchmark.py` + `golden-session/` fixture | the runner (replay + token measurement) |
| Fidelity gate | `FidelityGate` (`fidelity_gate.py`) — the zero-divergence governance-outcome diff | distinct construct from the runner |
| Reversible retrieval (CCR) | `retrieve()` on the provider interface; segment-key scheme defined in ADR-A | byte-equality |
| Passthrough fallback | `passthrough` path + structured signal keyed `compression_passthrough_fallback` | WARN+, main output stream |
| Compression toggle | constitution key set by `/at-init` | — |

> Note: headroom-internal constructs (its content-routing and per-type compressors) are **vendor terms**, not harness domain vocabulary, and are intentionally not surfaced as harness constructs.

## Tasks

> **ADR sequencing gate:** ADR-A, ADR-B, ADR-C, ADR-F (CCR store), and ADR-G (proxy lifecycle) MUST be authored and reviewed BEFORE the implementation tasks they govern begin — specifically ADR-B/ADR-F before TASK-002, ADR-C/ADR-G before TASK-006/TASK-007. TASK-000 covers this.

- [x] TASK-000: Author ADRs A–G (abstraction+segment-key, headroom supply chain, proxy interception+fallback, constitution toggle, deterministic eval framework, CCR store location/policy, proxy lifecycle model). `[team: claude]` → ADR-0013..0019, all Accepted.
- [x] TASK-001: Define the `ContextCompressionProvider` interface template (`compress`, `retrieve` + segment-key scheme, `activate`/`deactivate` lifecycle; opaque endpoint token; DATA-boundary preservation on compressed artifacts). `[team: claude]` → `templates/context-compression-provider-template.py` + contract tests (5, green).
- [x] TASK-002: Implement the headroom default provider template (proxy lifecycle + reversible retrieval) using PyPI `headroom-ai[proxy]==0.27.0` (Python 3.10+); confine headroom imports here; pin+SHA256-verify; run headroom network-restricted. `[team: claude]` → `compression-security-template.py` (headroom-free, 8 tests: credential scrub + CCR 700/600 byte-equal) + `headroom-context-compression-provider-template.py` (structural; headroom import confined; concrete security/CCR/lifecycle via tested helpers; headroom SDK isolated behind marked `_engine_*` seams to wire at golden-session integration). Scaffolder emits `security.py` + `headroom_provider.py` (kept out of `__init__` so the disabled path stays import-safe). headroom verified on PyPI; SHA256 pin recorded in ADR-0014. Store path now scrubs credential bytes (scrub_bytes) before any CCR write (fixes review HIGH #3). 17 tests.
- [x] TASK-003: Implement the noop provider template (passthrough, no proxy, no network). `[team: claude]` → `templates/noop-context-compression-provider-template.py` + 7 tests (green; proves no subprocess/socket).
- [x] TASK-004: Add the enable/disable choice to `/at-init` and persist it to the constitution; absent setting defaults to disabled; surface the network-restriction residual-risk ack if applicable. `[team: claude]` → `scripts/compression_config.py` (constitution-block reader/writer, default-disabled) + `at-init.md` step 12a + 9 tests (green).
- [x] TASK-005: Implement `scaffold_compression_setup.py` (idempotent) and `check_compression_setup.py` checks: no headroom imports outside the default-provider module; CCR store path safety (not in worktree/cloud-sync; mode 700/600); no full-payload/debug logging active; pinned headroom version+hash. `[team: claude]` → both scripts + 28 tests (green). Scaffolds an importable **`context_compression/`** package (NOT `compression` — avoids Python 3.14 stdlib shadow); noop's dev path-loader rewritten to a package import → single CompressionEndpoint identity in both orders; `run_checks()` invokes all helpers; `check_store_permissions` walks files for 600. Fixed 1 CRITICAL + 5 HIGH from review.
- [ ] TASK-006: Wire per-host proxy routing for Claude, Codex, Copilot via one shared lifecycle API using an opaque endpoint token (no raw port coupling). `[team: codex]`
- [ ] TASK-007: Implement passthrough fallback + structured `compression_passthrough_fallback` signal (WARN+, `timestamp`/`reason`/`session_id`, main output stream) when the proxy is unreachable. `[team: codex]`
- [x] TASK-008: Build the golden-session fixture under `.specify/evals/011-.../golden-session/` (≥5 recorded `/at-*` runs + expected governance outcome set + ≥1 adversarial directive-shaped artifact case). `[team: claude]` → `golden-session/manifest.json` (6 distinct-route scenarios + 1 adversarial injection) + README + 4 tests that re-verify every recorded outcome against the LIVE router (stale golden fails loudly) and assert the adversarial directive routes as DATA, not `/at-implement`. Outcomes recorded from real `route_at.py` runs, not invented. Extended to cover the FULL AC-001 outcome set — added `ac_state` (spec AC checkbox states) and `drift` (quick_drift_check findings) scenarios with live-extractor re-verification (fixes review HIGH #1).
- [x] TASK-009: Implement `run_golden_session_benchmark.py` (ON/OFF replay, proxy-side session-total token measurement) and `FidelityGate` (`fidelity_gate.py`, zero-divergence governance-outcome diff). `[team: claude]` → `fidelity_gate.py` (pure zero-tolerance diff, 7 tests) + `run_golden_session_benchmark.py` (ON/OFF replay, 60–95% band, >95% is FAIL; 7 tests). Fails closed (`incomplete`, exit 1) when golden missing or compression engine not wired — no silent green. OFF runs live; ON/token-measurement injected (headroom seams pending integration). Benchmark covers routing+ac_state+drift via category extractors; `--engine noop` makes it RUNNABLE (fidelity PASS, 0% band FAIL) while `--engine headroom` stays fail-closed until wired (fixes review HIGH #1/#2). 18 gate+runner tests; suite 285/285.
- [ ] TASK-010: Tests: interface contract; reversible byte-equality; noop no-op; disabled zero-overhead; **passthrough fallback run passes the `FidelityGate` zero-divergence diff** + signal emitted; credential-scrubbing (zero creds in logs/CCR store); no full-payload logging; per-host structure validation. `[team: codex]`
- [x] TASK-011: Documentation: enabling/disabling compression, the fidelity gate, the CCR store location, and the local-first / no-egress / credential-scrubbing security posture. `[team: copilot]` → `docs/context-compression.md` (enable/disable, fidelity gate + 3 categories, architecture, full security posture incl. the honest CCR-seal scope caveat + status/limitations). Also relabeled the at-rest seal claim across the security template + ADR-0018 (plaintext-avoidance / defense-in-depth, not confidential vs a store reader).

## Evaluation Strategy

| Dimension | Check | Method |
|-----------|-------|--------|
| Fidelity (decisions unchanged) | Empty governance-outcome diff ON vs OFF | `run_compression_benchmark.py` zero-divergence diff |
| Token reduction | 60–95% session-total outbound prompt-token reduction | proxy-side token counting across golden-session replay |
| Optionality | Disabled = no proxy, identical behavior | structure + behavior tests |
| Safety degrade | Proxy-unreachable → passthrough + signal | integration test |
| Reversibility | Exact original recovered | byte-equality test |
| Packaging | claude/codex/copilot all wired | `make validate-structure IMPLEMENTATION=<impl>` |

Evaluation plan: `.specify/evals/011-context-compression-governance/eval-plan.md`

## Security

The compression proxy sits inline on the entire outbound payload (prompts, governed artifacts, AND auth headers). The following are **mandatory enforced controls**, not prose assertions — each has a covering check or test.

### Credential scrubbing (HIGH)
- A credential-scrubbing layer at the proxy boundary MUST strip/mask `Authorization`, `x-api-key`, and `cookie` headers before ANY log or CCR-store write.
- Provider authentication MUST pass through to the model provider unchanged; scrubbing applies only to logging/storage paths.
- TASK-010 MUST include a test asserting zero credential content appears in proxy logs or the CCR store.

### No full-payload logging (HIGH)
- Debug-level full request/response payload logging MUST be disabled in every configuration the harness ships.
- `check_compression_setup.py` MUST assert no full-payload/debug logging config is active in the default headroom setup.

### CCR original store (HIGH)
- Store root MUST be `~/.arpinine/ccr-store/` (dir mode `700`, files mode `600`), explicitly NOT under the git worktree, `~/Desktop`, `~/Documents`, or any cloud-sync prefix (`~/Library/Mobile Documents`, Dropbox, OneDrive, Google Drive).
- `check_compression_setup.py` MUST actively verify the configured store path is not under a known cloud-sync prefix and not inside the git worktree — at setup time AND at proxy activation.
- Governed by ADR-F.

### No third-party egress (HIGH)
- headroom MUST run with outbound network restricted to loopback (sandboxed subprocess / firewall allow-list); governed content MUST NOT leave the machine (NFR-001).
- ADR-B MUST document headroom's actual runtime network behavior (not assume it). If headroom cannot run network-restricted, this is a residual risk requiring explicit operator acknowledgment at `/at-init`.

### Supply chain (HIGH)
- headroom MUST be version-pinned (exact hash or lockfile-pinned artifact, not a semver range) and verified by SHA256 at install.
- `check_compression_setup.py` MUST assert the installed headroom version+hash match the pinned values. Blocker on ADR-B authorship.

### Data boundary / prompt injection (MEDIUM)
- All `.specify/` content remains DATA, not instructions. The `ContextCompressionProvider` interface contract MUST require compressed output of governed artifacts to preserve the same DATA delimiter/role boundary as uncompressed artifacts — compression must not emit text the model could read as new instructions.
- The fidelity benchmark MUST include an adversarial case where an artifact contains directive-shaped text (e.g. "ignore previous instructions") and assert the governance-outcome diff stays empty (boundary survived compression).

### Passthrough fallback signal (MEDIUM)
- Proxy-unreachable MUST degrade to passthrough, never a broken/silently-altered session.
- The fallback signal MUST be a structured log entry at WARN or above with mandatory fields `timestamp`, `reason`, `session_id`, surfaced in the harness's MAIN output stream (not only a background log). Construct key: `compression_passthrough_fallback`.

## Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Lossy compression silently changes governance outcomes | High | Zero-divergence fidelity gate; default OFF; per-team opt-in |
| Proxy intercepts all traffic → credential/data leak surface | Medium | Local-first, no egress, no credential logging, security review gate |
| headroom external dependency (supply chain) | Medium | Governed by ADR-B; pinned version; local install |
| Per-host base-URL/env wiring drift across claude/codex/copilot | Medium | One shared lifecycle API; structure validation tests |
| CCR original store leaks governed content to a synced path | Medium | Store outside repo/synced dirs; documented; checked |
| Benchmark golden session not representative | Medium | Compose from real `/at-*` routing/drift/AC paths; expand over time |

## ADRs (authored in TASK-000, all Accepted)

- ADR-0013 (Accepted): Adopt one shared `ContextCompressionProvider` abstraction with swappable default + noop implementations. Covers the FULL interface contract incl. the `retrieve()` segment-key scheme and vendor/transport-neutral lifecycle naming; the interface has zero dependencies (no headroom, no proxy/port, no host API, no constitution). `decision:011-context-compression-governance:provider-abstraction`
- ADR-0014 (Accepted): Consume headroom as the external default-implementation dependency (supply chain). MUST document headroom's runtime network behavior and require version+hash pinning before authorship is complete. `decision:011-context-compression-governance:headroom-dependency`
- ADR-0015 (Accepted): Whole-payload compression via local proxy interception (opaque-endpoint base-URL/env) with passthrough-fallback degrade (fallback is part of this ADR, not split). `decision:011-context-compression-governance:proxy-interception`
- ADR-0016 (Accepted): Record the compression enable/disable toggle in the constitution, chosen at `/at-init`; default-to-disabled-on-absent-key is an invariant. `decision:011-context-compression-governance:constitution-toggle`
- ADR-0017 (Accepted): Use a deterministic golden-session replay benchmark (zero-divergence diff + proxy-side token reduction) as the evaluation framework instead of the DeepEval default; token measurement at the proxy boundary is a hard constraint. `decision:011-context-compression-governance:eval-framework`
- ADR-0018 (Accepted): CCR original store location (`~/.arpinine/ccr-store/`), access policy (700/600), and no-sync/no-worktree invariant. `decision:011-context-compression-governance:ccr-store-location`
- ADR-0019 (Accepted): Compression proxy lifecycle model — per-session activate/deactivate vs. long-running local service (resolves OQ-003). `decision:011-context-compression-governance:proxy-lifecycle-model`
