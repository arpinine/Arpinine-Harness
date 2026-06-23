---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-23
covers:
  - decision:011-context-compression-governance:launcher-runtime-delivery
---

# ADR-0020: Out-of-host launcher as the runtime delivery mechanism for compression

## Status
Accepted

## Context

Spec 011 (Option A / ADR-0015) routes a host's outbound LLM calls through a local
`headroom proxy` by setting the host's base-URL env (e.g. `ANTHROPIC_BASE_URL`).
But the Arpinine Harness plugin runs **inside an already-started host** (Claude
Code / Codex / Copilot). A plugin cannot set the base-URL of the process that
launched it, nor relaunch its own host. Consequently the providers, host-wiring,
toggle, benchmark, and security checks were all built and tested, but **nothing
actually compresses a live session** — there is no in-plugin point that can start
the proxy and point the running host at it.

The base-URL must be set **before the host starts**. That can only happen from a
layer that runs *around* the host, not from a slash command *inside* it.

## Decision

Deliver live compression with a **harness-provided launcher**: a shell entry
point the operator runs to start a host session, which:

1. reads the constitution toggle; **disabled → exec the host directly** (no proxy);
2. enabled → validates the CCR directory (ADR-0018), `activate()`s the provider
   (starts the loopback proxy, ADR-0015/0019), and computes the host base-URL env
   via the host-wiring map (ADR-0015);
3. spawns the host with that env, forwarding stdio/tty/signals for an interactive
   session;
4. tears the proxy down on host exit (`deactivate()`);
5. if `activate()` fails, runs the host **uncompressed (passthrough)** and emits
   the `compression_passthrough_fallback` signal — the session always runs.

The launcher is explicitly **NOT** an `/at-*` command (those run inside the host,
the wrong layer). To support it, the `context_compression` provider package is
promoted from template-only to a **live importable plugin package** the launcher
imports.

## Consequences

- Positive: closes the end-to-end gap — the harness now *provides* working live
  compression, not just a scaffold (AC-008).
- Positive: one orchestration path reuses the existing provider, host-wiring,
  toggle, and fallback — no new compression logic.
- Negative: the launcher must spawn-and-wait (forwarding an interactive tty) and
  guarantee teardown — it cannot `exec`-replace itself or the proxy would leak.
- Negative: a true live run still requires `headroom-ai[proxy]` installed in the
  operator's runtime + a real host + API key; the launcher logic is unit-testable
  with mocks, but live interception is an operator-side smoke step.
- Negative: per-host base-URL plumbing differs (Claude `ANTHROPIC_BASE_URL`;
  Codex/Copilot `OPENAI_BASE_URL` + `/v1`); Copilot routing needs confirmation.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| An `/at-*` slash command that turns on compression | Runs inside the already-started host; cannot set its base-URL or relaunch it |
| Document a manual `ANTHROPIC_BASE_URL=… claude` recipe | Not harness-provided; error-prone; no toggle/validation/fallback/teardown |
| Product-side wiring only (the built app adopts the package) | Deferred in release 1; does not make the *harness itself* provide compression |
