---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-22
covers:
  - decision:011-context-compression-governance:proxy-interception
---

# ADR-0015: Whole-payload compression via local proxy interception with passthrough fallback

## Status
Accepted

## Context

Spec 011 requires compressing the entire outbound context — including the live conversation — before it reaches the model provider (FR-006, RD-004). The Arpinine Harness plugin runs inside the host (Claude Code, Codex, Copilot) and cannot rewrite the host's outbound LLM provider calls in-process. The only way to transform the whole payload is to interpose a process the host routes through.

This interposition is a significant decision: the proxy sees all outbound traffic, so it carries the security surface addressed in ADR-0014 and ADR-0018. It also introduces a failure mode — if the proxy is down, the session must not break or be silently altered.

## Decision

Implement whole-payload compression by pointing each host's LLM provider base-URL at a local compression proxy via environment/configuration. The headroom default provider owns the proxy lifecycle (ADR-0013 `activate`/`deactivate`; lifecycle model in ADR-0019).

Coupled into this single decision (not split out):

1. Host wirings receive an opaque endpoint token plus a provider-supplied, ready-to-use `base_url`. They set `base_url` **verbatim** (e.g. `ANTHROPIC_BASE_URL`) and MUST NOT parse or derive a port/host from it or construct network coordinates themselves; `base_url is None` means no override (disabled/noop → host talks direct). The endpoint exposes no separate port/host field.
2. Proxy-unreachable (process not started or refusing connections) degrades to uncompressed passthrough — the session always completes.
3. The passthrough path emits a structured signal `compression_passthrough_fallback` at WARN or above, with mandatory fields `timestamp`, `reason`, `session_id`, surfaced in the harness's main output stream.
4. The passthrough run's governance outcomes must still pass the `FidelityGate` zero-divergence diff (it is identical to compression-OFF by construction).

## Consequences

- Positive: It is the only viable approach given the in-process interception constraint, and it works uniformly across all three hosts.
- Positive: The fallback guarantees compression can never break a governed session, only forgo savings.
- Negative: Proxy lifecycle management becomes a hard harness responsibility (start, monitor, stop) and the passthrough path must be test-covered (TASK-007/TASK-010).
- Negative: The proxy is a full-traffic interception point; its security controls (credential scrubbing, no full-payload logging, no egress) are mandatory, not optional.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| In-process payload rewriting | Impossible — the plugin cannot rewrite the host's outbound provider calls |
| Compress only content the plugin itself controls | Fails FR-006; the live conversation would not be compressed |
| Hard-fail the session when the proxy is down | Violates RD-006; compression must never break a governed session |
| Split passthrough fallback into a separate ADR | Fallback is the other half of committing to a proxy intercept model; they are one decision |
