---
idea: 'Context-compress feature for the Arpinine Harness. Add a context-window compression capability across all plugin implementations (claude, codex, copilot). Same strategy as existing features: a core abstraction plus a swappable default implementation. Default implementation modeled on https://github.com/chopratejas/headroom'
state: promoted-to-spec
started: 2026-06-22
updated: 2026-06-22 (turn 9 — promoted)
spec_slug: 011-context-compression-governance
---

## Original Idea
Context-compress feature for the Arpinine Harness. Add a context-window compression capability across all plugin implementations (claude, codex, copilot). Same strategy as existing features: a core abstraction plus a swappable default implementation. Default implementation modeled on https://github.com/chopratejas/headroom (local-first context-compression layer for LLM agents — compresses tool outputs, files, RAG chunks, and conversation history; `compress(messages, model)` core function; ContentRouter dispatches to specialized compressors; proxy/library/MCP integration modes).

## Q&A
**Q1:** Whose context gets compressed — the Arpinine Harness's own execution (token cost of running /at-* commands and specialist agents during governed delivery), the product the vibe coder builds with the harness, or both?
**A1:** Both — the harness's own execution AND the product the vibe coder builds.

**Q2:** For both scopes, one shared core abstraction (a single `ContextCompressionProvider` contract used in harness execution and wired into the product) vs. two separate integrations? And does release 1 ship both at once, or phase one first?
**A2:** One shared core abstraction; phase harness-side first (release 1 = harness execution; product-side wiring later).

**Q3:** In harness execution, what gets compressed vs. what must stay verbatim? Large tool outputs / command stdout / specialist-agent conversation history are obvious candidates — but governance artifacts (specs, plans, ADRs, drift reports) are read as security-bounded DATA and feed routing/decisions. Lossy summarizing them could corrupt governance integrity. Where's the line?
**A3:** Compress ALL content — including the live conversation/full outbound context before it is sent to the AI assistant. Not selective; whole-payload interception model (headroom proxy/wrap style).

**Q4:** Interception mechanism. The harness is a plugin running INSIDE the host (Claude Code / Codex / Copilot); it does NOT control the host's outbound LLM API calls, so it can't rewrite the conversation payload in-process. Headroom does whole-payload compression via a local proxy (point the host at it via base-URL/env, e.g. `headroom proxy` / `headroom wrap`). Is release-1's harness-side integration that proxy model — the harness configures + governs a local compression proxy the host routes through — and what's the measurable token-reduction / fidelity target?
**A4:** Yes, proxy model. Target: 60–95% token reduction with decisions unchanged.

**Q5:** "Decisions unchanged" is the risky acceptance criterion — needs a measurable verification method. Proposed: a fixed golden harness-session benchmark (a recorded set of /at-* runs) replayed with compression ON vs OFF, asserting identical governance outcomes (same routing decisions, same drift findings, same AC pass/fail). Compression passes only if outcomes match AND token reduction lands in 60–95%. Acceptable as the success gate, or do you want a different fidelity check?
**A5:** Yes — golden harness-session benchmark replayed ON vs OFF is the success gate.

**Q6:** New constraint added: compression must be OPTIONAL, chosen at constitution creation time (`/at-init`) — enabled or not when the constitution is first created.
**A6:** Confirmed. Opt-in/opt-out toggle set during `/at-init`, recorded in the constitution. When disabled, the harness behaves exactly as today (noop provider, no proxy, zero overhead).

**Q7 (rationale):** Why the toggle matters — confirm motivation.
**A7:** Compression is lossy and CAN change the AI assistant's results/output. The operator must be able to enable/disable it to trade token savings against output fidelity. This is the core reason the toggle exists and why the golden-session fidelity gate is mandatory: a team that cannot accept any result variance keeps it OFF; a team prioritizing token savings turns it ON and relies on the fidelity gate to bound the risk.

## Current Brief

**Feature:** Context Compression Governance (harness-side, release 1)

- **Users:**
  - Primary (release 1): the harness operator / vibe coder running governed delivery (`/at-*` commands and specialist agents) inside Claude Code, Codex, or Copilot, who hits token cost, latency, and context-window pressure.
  - Secondary (later phase): the product the vibe coder builds — same shared abstraction wired into their app, like the observability/eval providers.
- **Problem:** Governed harness execution sends large outbound context (full conversation, tool/command stdout, file dumps, agent history) to the LLM provider on every turn, driving high token cost and latency and crowding the context window.
- **Value:** 60–95% fewer tokens sent to the model with governance decisions unchanged — cheaper, longer-running, lower-latency governed sessions without losing fidelity.
- **Why the toggle exists:** compression is lossy and CAN alter the AI assistant's results. The enable/disable choice lets each team trade token savings against output fidelity; the golden-session fidelity gate bounds the risk for teams that turn it ON.
- **In scope (release 1):**
  - One shared core abstraction: a `ContextCompressionProvider` contract.
  - Default implementation modeled on headroom (https://github.com/chopratejas/headroom), as a local-first compression proxy.
  - Whole-payload interception: the host (Claude/Codex/Copilot) routes its provider calls through the local compression proxy (base-URL/env config) — compresses the entire outbound context including the live conversation.
  - Harness configures, governs, and lifecycle-manages the proxy across all three host implementations.
  - Mirrored wiring across claude / codex / copilot, following the existing core-abstraction + swappable-default-impl + per-host pattern (specs 001, 009, 010).
  - **Optional, decided at constitution creation (`/at-init`):** the operator chooses compression enabled or disabled when the constitution is first created; the choice is recorded in the constitution. Disabled = noop provider, no proxy, no behavior change vs. today.
- **Out of scope (release 1):**
  - Product-side integration (the vibe coder's own app) — deferred to a later phase, but the abstraction must not preclude it.
  - Replacing or forking headroom internals; it is consumed as the default provider.
  - Output-token / response-side compression beyond what the default provider does out of the box.
- **Constraints / assumptions:**
  - The plugin runs INSIDE the host and cannot rewrite outbound provider calls in-process → integration is necessarily proxy-based (host pointed at a local proxy).
  - Local-first: compression runs locally; no governed artifact content leaves the machine to a third party.
  - Provider is swappable (default = headroom, noop fallback) consistent with existing provider abstractions.
  - Reversible retrieval (headroom CCR) available where exact originals are needed on demand.
- **Risks / edge cases:**
  - Lossy compression of governance-bearing context (specs, plans, ADRs, drift reports, routing inputs) could silently corrupt governance decisions — the central risk.
  - Proxy lifecycle failure (proxy down/misconfigured) must degrade safely to uncompressed passthrough, never to a broken or silently-altered session.
  - Per-host base-URL/env wiring differs across Claude/Codex/Copilot.
- **Acceptance criteria (measurable):**
  - Success gate = a fixed golden harness-session benchmark (recorded set of `/at-*` runs) replayed with compression ON vs OFF.
  - PASS requires: identical governance outcomes ON vs OFF (same routing decisions, same drift findings, same AC pass/fail) AND outbound token reduction within 60–95% on that benchmark.
  - `/at-init` exposes the enable/disable choice; the constitution records it; when disabled the harness runs with zero compression overhead (noop, no proxy) and identical behavior to a pre-feature install.
  - Proxy-down path verified to fall back to uncompressed passthrough with no outcome change.
  - One shared `ContextCompressionProvider` abstraction present, with a working default (headroom) and a noop provider, wired on all three hosts.
- **Domain vocabulary:**
  - `ContextCompressionProvider` — the shared core abstraction (avoid generic "compressor"/"manager"/"handler").
  - Compression proxy — the local-first interception point the host routes through (default impl = headroom).
  - Golden harness-session benchmark — the recorded ON/OFF fidelity + reduction gate.
  - Fidelity gate — the "decisions unchanged" assertion.
  - Reversible retrieval (CCR) — on-demand recovery of exact originals.
  - Passthrough fallback — uncompressed degrade path when the proxy is unavailable.
  - Compression toggle — the enable/disable choice set at `/at-init` and recorded in the constitution.
