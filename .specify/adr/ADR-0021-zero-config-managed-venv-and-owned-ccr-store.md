---
governs: specs/011-context-compression-governance
supersedes: ~
status: Accepted
date: 2026-06-23
covers:
  - decision:011-context-compression-governance:zero-config-bootstrap
---

# ADR-0021: Zero-config compression — managed venv + provider-owned CCR store

## Status
Accepted

## Context

Enabling compression required manual operator setup: `pip install headroom-ai`,
exporting a safe `HEADROOM_DATABASE_URL`, and creating a `700` CCR dir. That is
avoidable friction, and the manual pip step also couples the *host's* Python to
headroom (the launcher had to `import headroom` in-process, so a host interpreter
without it could not even build the provider).

The toggle (a conscious, lossy-compression decision) and the choice to launch via
the launcher (ADR-0020, inherent) stay manual. The install and CCR-store steps do not.

## Decision

The headroom provider becomes **subprocess-only and self-provisioning**:

1. **Managed venv (#1).** On `activate()`, ensure a managed virtualenv at
   `~/.arpinine/compression-venv` with the pinned `headroom-ai[proxy]==0.27.0`
   installed (idempotent; skipped if already present). The proxy is started from
   that venv's `headroom` executable. The host's own Python no longer needs
   headroom — so the provider **no longer imports headroom in-process**; it runs
   the CLI as a subprocess. (The benchmark's `headroom-simulate` engine still
   imports headroom in its own module, where it is installed.)
2. **Provider-owned CCR store (#2).** On `activate()`, the provider sets a safe
   default store (`~/.arpinine/ccr-store/`, dir `700`), creates it, and passes it
   to the proxy via environment — then validates it against the ADR-0018 no-sync +
   permission invariant. The operator no longer configures the store; an explicit
   override is still validated and rejected if unsafe.

Both bootstrap actions are injectable seams so they are unit-tested without
running real `pip` or starting a real proxy.

## Consequences

- Positive: enabling compression collapses to the `/at-init` toggle + launching
  via the wrapper; install + CCR-store setup are automatic.
- Positive: dropping in-process `import headroom` makes the scaffolded package
  import-safe on any host Python and tightens the import boundary (the package
  imports headroom **nowhere**; the proxy is purely a subprocess).
- Positive: pinned, isolated headroom in a managed venv — no pollution of the
  host environment, version controlled by the provider.
- Negative: first `activate()` pays a one-time venv-create + install cost
  (cached thereafter); needs network on first run.
- Negative: a managed venv under `~/.arpinine` is per-user machine state the
  provider now owns (create/repair).

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Auto-`pip install` into the host's Python | Pollutes/!controls the host env; "which Python" ambiguity; may need sudo |
| Keep manual pip + export | The friction this ADR removes |
| Auto-enable compression too | Lossy; enabling must stay a conscious governed choice (ADR-0016) |
