# Spec: Context Compression Governance

## Business Case

Every governed turn in Arpinine Harness sends a large outbound context to the LLM provider: the full conversation, tool and command stdout, file dumps, and specialist-agent history. As governed sessions grow, this drives high token cost, added latency, and context-window crowding — the same pressure that motivated dual-cost governance, now attacked at the source instead of only being measured.

Headroom-style context compression can reduce outbound tokens substantially (headroom publishes 60–95% for live multi-request proxy operation; the in-harness model-free pipeline measures ~38–56% — see ADR-0017) while preserving answer quality. But compression is lossy and **can** change what the AI assistant produces. In a governance harness that is unacceptable unless the change is bounded and provable: routing decisions, drift findings, and acceptance-criteria outcomes must not silently diverge because context was compressed.

Arpinine Harness therefore needs a governed context-compression capability with the same shape as its other integrations (specs 001, 009, 010): one shared core abstraction, a swappable default implementation, and consistent wiring across Claude, Codex, and Copilot. Because compression can affect results, it must be **optional** — enabled or disabled at constitution creation — and gated by a fidelity benchmark that proves governance outcomes are unchanged before any team relies on it.

Release 1 targets the harness's own execution. The same abstraction must not preclude later wiring the capability into the product a vibe coder builds.

## User Stories

- As a harness operator running governed `/at-*` delivery, I want outbound context compressed so long sessions cost less and stay inside the context window.
- As a maintainer, I want compression to be optional and chosen at constitution creation so a team can opt out entirely when result fidelity must be exact.
- As an auditor, I want proof that compression does not change governance outcomes before it is trusted, via a repeatable benchmark.
- As an operator, I want compression to fail safe to uncompressed passthrough when the compression proxy is unavailable, never to a broken or silently-altered session.
- As an engineering lead, I want one shared compression abstraction wired identically across Claude, Codex, and Copilot so behavior is consistent across hosts.

## Requirements

- FR-001: The plugin SHALL define one shared core abstraction, a `ContextCompressionProvider` contract, used for all governed context compression.
- FR-002: The plugin SHALL ship a default `ContextCompressionProvider` implementation that consumes headroom (https://github.com/chopratejas/headroom) as an external dependency, operating as a local-first compression proxy.
- FR-003: The plugin SHALL ship a noop `ContextCompressionProvider` implementation that performs no compression and imposes no proxy.
- FR-004: Compression SHALL be optional, with the enable/disable choice made at constitution creation (`/at-init`) and recorded in the constitution.
- FR-005: When compression is disabled, the harness SHALL run with no compression proxy and no compression overhead, behaving identically to a pre-feature install.
- FR-006: When compression is enabled, the host (Claude, Codex, or Copilot) SHALL route its outbound LLM provider calls through the local compression proxy via base-URL/environment configuration, so the entire outbound context is compressed.
- FR-007: The harness SHALL configure, start, and lifecycle-manage the compression proxy across all three host implementations.
- FR-008: If the compression proxy is unavailable or fails, the harness SHALL fall back to uncompressed passthrough without aborting or altering the session.
- FR-009: When the default implementation uses engine-owned reversible retrieval (CCR), the harness SHALL NOT re-implement that retrieval on the `ContextCompressionProvider` interface and SHALL instead validate the configured engine CCR directory against the ADR-0018 no-sync + 700/600 invariant.
- FR-010: The `ContextCompressionProvider` abstraction SHALL be implementation-neutral and selectable, so the default headroom implementation can be replaced without changing harness wiring.
- FR-011: The plugin SHALL provide a fidelity benchmark that replays a fixed golden harness session with compression ON and OFF and compares governance outcomes.
- FR-012: The compression abstraction SHALL NOT preclude a later release wiring the same provider into the product the vibe coder builds.

## Non-Functional Requirements

- NFR-001: Compression SHALL be local-first; no governed artifact content SHALL leave the machine to a third-party service as part of compression.
- NFR-002: The enabled compression path SHALL keep governance outcomes (routing decisions, drift findings, acceptance-criteria pass/fail) unchanged relative to the disabled path on the fidelity benchmark.
- NFR-003: The design SHALL remain implementation-neutral across Claude, Codex, Copilot, and future assistant implementations.
- NFR-004: The disabled path SHALL impose zero measurable compression overhead.
- NFR-005: The failure path (proxy down) SHALL degrade safely and observably, never silently corrupting context.

## Acceptance Criteria

- [ ] AC-001: Given compression is enabled, when the fixed golden harness session is replayed with compression ON versus OFF, the benchmark tooling produces a structured field-level diff over the **governance outcome set** — (a) routing-decision fields (`route`, `confidence`, `command_class`, `requires_confirmation`) from the router output for each routed turn, (b) drift-finding records (file, line, severity, finding id), and (c) acceptance-criteria checkbox states — and that diff is **empty (zero divergence)**. Any single differing field is a FAIL.
- [ ] AC-002: Given the representative payloads fixture, the **total outbound prompt-token reduction** measured via the proxy pipeline (`headroom-simulate`, model-free) is between **30% and 95%** (band measured/justified in TASK-012 — the in-harness-measurable single-pass pipeline tops out ~38–56%; 60–95% needs live multi-request CCR/cache accumulation, out of harness scope). Above 95% is a FAIL.
- [ ] AC-003: Given `/at-init`, the operator can choose compression enabled or disabled, and the choice is recorded in the constitution.
- [ ] AC-004: Given compression is disabled, no compression proxy is started and harness behavior is identical to a pre-feature install.
- [ ] AC-005: Given compression is enabled and the compression proxy is unreachable (process not started or refusing connections), the harness completes the session via uncompressed passthrough, produces a governance outcome set that passes the same zero-divergence diff defined in AC-001, and emits an observable signal (log entry or status event) indicating passthrough fallback was activated.
- [ ] AC-006: Given the shipped artifacts, one shared `ContextCompressionProvider` abstraction exists; the working default (headroom) implementation and the noop implementation are each callable through that abstraction; and all three host integrations (Claude, Codex, Copilot) use the same lifecycle API to configure, start, and stop the provider, differing only in host-specific base-URL/environment plumbing.
- [ ] AC-007: Given the default implementation is configured with engine-owned reversible retrieval (CCR), the harness validates the configured engine CCR directory at setup and activation time: it is outside the git worktree and known cloud-sync paths, and enforces 700/600 permissions.
- [ ] AC-008: Given the harness-provided launcher and compression **enabled**, launching a host (Claude/Codex/Copilot) through it starts the local proxy, points the host at it via the host's base-URL env, runs the interactive session, and tears the proxy down on exit. Given compression **disabled**, the launcher execs the host directly with no proxy and behavior identical to launching the host without the harness. Given the proxy fails to start, the launcher runs the host **uncompressed (passthrough)** and emits the fallback signal — the session always runs. (The launcher is a shell entry point that runs *around* the host, not an `/at-*` command — ADR-0020.)

## Out of Scope

- Product-side integration into the vibe coder's own application (deferred to a later release; the abstraction must not preclude it)
- Replacing or forking headroom internals; it is consumed as the default provider
- Compression or summarization of LLM response content; this spec governs outbound context compression only
- Compression of content the harness does not route through the LLM provider
- Per-command or mid-session toggling of compression beyond the constitution-level enable/disable choice

## AI-Nativeness Assessment

**AIN Target Level**: 2 = AI-assisted internal tooling

**Agent-Callable Operations** (for AIN >= 3):
- Not applicable. This feature governs an outbound-context compression boundary and its abstraction; it does not introduce a new product-facing agent API.

**Human-in-the-Loop Gates** (for AIN >= 3):
- The enable/disable decision is human-controlled at constitution creation.
- Acceptance of the fidelity-benchmark result remains human-controlled.

**Feedback Channels**:
- Fidelity benchmark outcome (governance outcomes ON vs OFF)
- Token-reduction measurement from the benchmark
- Passthrough-fallback signal when the proxy is unavailable

**Evaluation Required**: YES

The fidelity benchmark is release-blocking: compression-enabled behavior may not be trusted until the golden harness-session replay proves governance outcomes are unchanged and token reduction lands within the target band.

## Operating Constraints

- The plugin runs inside the host and cannot rewrite the host's outbound provider calls in-process; whole-payload compression is therefore necessarily proxy-based (the host is pointed at a local proxy).
- Governance-bearing context (specs, plans, ADRs, drift reports, routing inputs) flows through the same outbound path; compression must not change the governance outcomes derived from it.
- Per-host base-URL/environment wiring differs across Claude, Codex, and Copilot and must be handled per implementation while preserving one shared abstraction.
- The compression toggle is set once at constitution creation and recorded in the constitution; existing installs without the setting default to disabled (no behavior change).
- The default implementation consumes headroom as an external package dependency; this is a supply-chain constraint and SHALL be governed by an ADR at plan time.
- Outbound prompt-token counts for the fidelity benchmark SHALL be measured at the compression proxy (the single point that sees both the uncompressed and compressed payloads), not estimated from provider billing.
- The fixed golden harness session and its expected governance outcome set SHALL be stored as a governed fixture under `.specify/evals/011-context-compression-governance/golden-session/`.

## Open Questions

- OQ-001: Where is the compression toggle recorded in the constitution, and what is its exact key/shape? (governed by ADR-0016; exact key shape settled in TASK-004)
- OQ-003: RESOLVED by ADR-0019 — per-session activate/deactivate lifecycle.

## Resolved Decisions

- RD-001: Context compression uses one shared `ContextCompressionProvider` abstraction with a swappable default implementation, following the 001/009/010 pattern.
- RD-002: The default implementation is modeled on headroom and runs as a local-first compression proxy; a noop implementation is also shipped.
- RD-003: Compression is optional and chosen at constitution creation; disabled means no proxy and no behavior change.
- RD-004: Whole-payload compression is proxy-based because the plugin cannot intercept the host's outbound calls in-process.
- RD-005: Compression-enabled behavior is gated by a release-blocking golden harness-session fidelity benchmark (identical governance outcomes plus 30–95% token reduction; band measured/justified in TASK-012, see ADR-0017).
- RD-013: Live interception is delivered by a harness-provided **launcher** — a shell entry point that starts the proxy, launches the host pointed at it, and tears it down — because a plugin running *inside* an already-started host cannot repoint its own session. The launcher is not an `/at-*` command. (ADR-0020)
- RD-006: Proxy failure degrades to uncompressed passthrough, never to a broken or silently-altered session.
- RD-007: Release 1 covers harness-side execution only; the abstraction must not preclude later product-side wiring.
- RD-008: The default implementation consumes headroom as an external dependency (not an internally re-implemented pattern); the supply-chain choice is governed by an ADR at plan time.
- RD-009: The fidelity gate uses **zero-divergence** comparison over a defined governance outcome set (routing-decision fields, drift-finding records, AC checkbox states); any single differing field is a FAIL. (resolves former OQ-004)
- RD-010: Token reduction is measured as total outbound prompt tokens summed across the full golden-session replay, counted at the compression proxy, with the compression-OFF run as the baseline. (resolves AC-002 measurement basis)
- RD-011: The fixed golden harness session and its expected outcome set are a governed fixture stored under `.specify/evals/011-context-compression-governance/golden-session/`. (resolves former OQ-002)
- RD-012: Proxy-unavailable is a controlled test condition meaning the proxy is not started or refuses connections; the passthrough path must pass the same zero-divergence diff and emit an observable fallback signal.

## Domain Vocabulary

- **ContextCompressionProvider** — the shared core abstraction for governed context compression. Avoid generic terms such as `compressor`, `manager`, or `handler`.
- **Compression proxy** — the local-first interception point the host routes outbound provider calls through; the default implementation is headroom.
- **Golden harness-session benchmark** — the fixed recorded set of `/at-*` runs replayed with compression ON vs OFF; the fidelity-plus-reduction gate.
- **Fidelity gate** — the assertion that governance outcomes are unchanged between compression ON and OFF.
- **Reversible retrieval (CCR)** — engine-owned recovery of exact original content for a compressed segment; not a harness-interface method under the proxy-only model.
- **Passthrough fallback** — the uncompressed degrade path used when the compression proxy is unavailable.
- **Compression toggle** — the enable/disable choice set at `/at-init` and recorded in the constitution.

## Related ADRs

Authored during implementation (TASK-000), all Accepted:

- ADR-0013: `ContextCompressionProvider` abstraction (lifecycle-only, neutral lifecycle naming)
- ADR-0014: headroom as external default-implementation dependency (supply chain + runtime network behavior)
- ADR-0015: whole-payload compression via local proxy interception + passthrough-fallback degrade
- ADR-0016: compression enable/disable toggle recorded in the constitution at `/at-init`
- ADR-0017: deterministic golden-session replay benchmark as evaluation framework (not DeepEval)
- ADR-0018: engine-owned CCR directory policy, access policy, no-sync invariant
- ADR-0019: compression proxy lifecycle model — per-session activate/deactivate (resolves OQ-003)
- ADR-0020: out-of-host launcher as the runtime delivery mechanism for live compression (AC-008)
