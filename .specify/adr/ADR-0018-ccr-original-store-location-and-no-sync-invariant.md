---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-22
covers:
  - decision:011-context-compression-governance:ccr-store-location
---

# ADR-0018: CCR original store location, access policy, and no-sync invariant

## Status
Accepted — **amended by the Option A (proxy-only) decision (see ADR-0013).**

> **Amendment (Option A).** Under proxy-only integration, reversible retrieval
> (CCR) is owned by the **headroom engine**, not re-implemented in the harness.
> The harness no longer ships its own CCR store, sealing, or `store_original`/
> `read_original` path — those are retired. This ADR's location/permission/no-sync
> guidance now applies to **headroom's** CCR store: when compression is enabled,
> `check_compression_setup.py` must verify headroom's configured CCR directory is
> not under the git worktree or a cloud-sync path and is mode 700/600. The
> "primary protection is the no-sync + permission invariant, not encryption"
> reasoning below still holds and now governs headroom's store configuration.

## Context

Reversible retrieval (CCR, FR-009/AC-007) stores the exact original content of compressed segments locally so it can be recovered on demand. Those originals are full governed content — prompts, specs, plans, ADRs, drift findings. Where that store lives is a security decision: if it lands inside the git worktree it can be committed; if it lands in a cloud-synced directory it leaves the machine, violating the local-first / no-egress requirement (NFR-001). The security review flagged that "outside synced/committed paths" as prose is not enforceable without a concrete path and an active check.

## Decision

Store CCR originals at a fixed, non-synced location with enforced permissions and an active path-safety check.

1. Store root: `~/.arpinine/ccr-store/`, directory mode `700`, files mode `600`.
2. The store MUST NOT be under the git worktree, `~/Desktop`, `~/Documents`, or any cloud-sync prefix (`~/Library/Mobile Documents`, Dropbox, OneDrive, Google Drive).
3. `check_compression_setup.py` actively verifies the configured store path is not under a known cloud-sync prefix and not inside the git worktree — at setup time AND at proxy activation (not only at setup).
4. CCR originals are stored **byte-exact** (AC-007 reversible retrieval holds for all content, including credential-bearing bytes) and **sealed at rest** with a store-local key so the store contains no PLAINTEXT secrets.

### Seal scope (do not over-trust it)
The seal key (`.ccr-store.key`) is co-located in the store directory for portability. The seal is therefore **plaintext-avoidance / defense-in-depth only** — it is NOT confidential against anyone who can read the store directory, because they obtain the key as well. Any threat that leaks the store (cloud-sync, backup, world-readable copy) leaks the key with it.

The **primary** protection of CCR originals is invariants 1–3 above (no-sync location + 700/600 + active path check), NOT the seal. The seal does not relax those invariants. For real at-rest confidentiality (protecting originals from a reader of the store), the key must be derived from outside the store — e.g. an OS keychain or an env var — which is a deliberate future option, not the current portable default. The seal is also unauthenticated (no MAC): it provides no tamper detection on the stored bytes.

## Consequences

- Positive: Reversible retrieval works without risking governed content leaking to a synced path or the repository.
- Positive: The path-safety check is an enforced control, runs at activation, and fails closed.
- Negative: A fixed home-directory store assumes a single-user machine layout; multi-user or containerized setups must override the root explicitly and re-pass the safety check.
- Negative: Restrictive permissions (700/600) must be maintained; the check asserts them.

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Store under `.specify/` | Inside the worktree; risks committing governed originals |
| Let headroom choose the default path | Commonly resolves under `~/Documents`/`~/Library`, often cloud-synced; violates NFR-001 |
| Validate path only at setup time | A path can become synced/moved later; activation-time check is required |
| Keep no originals (non-reversible) | Fails FR-009/AC-007 reversible-retrieval requirement |
