# Context Compression

Governed by spec `011-context-compression-governance` (ADRs 0013–0019).

Context compression reduces the outbound LLM token cost of governed harness
sessions by routing the host's provider calls through a local compression proxy.
It is **optional, disabled by default**, and gated by a release-blocking fidelity
benchmark — because compression is lossy and *can* change the assistant's output.

> Release 1 covers **harness-side** execution (the cost of running `/at-*` and
> specialist agents). The same `ContextCompressionProvider` abstraction is built
> so the vibe coder's product can wire it in later, but product-side wiring is
> out of scope for this release.

---

## Enabling / disabling

The choice is made once, at constitution creation (`/at-init`), and recorded in
`.specify/CONSTITUTION.md` (ADR-0016).

- **Disabled (default).** No proxy is started, zero overhead, behavior identical
  to a pre-feature install. The `NoopContextCompressionProvider` is selected.
  Repositories with no compression key in the constitution read as disabled.
- **Enabled.** The host routes provider calls through the local headroom proxy.

Set or change it:

```bash
python3 "<plugin>/scripts/compression_config.py" --repo <project-root> \
    set --enabled <true|false> [--network-restriction-ack <true|false>]
# inspect:
python3 "<plugin>/scripts/compression_config.py" --repo <project-root> get
```

There is **no** per-command or mid-session toggle — it is a constitution-level
decision (re-run `/at-init` or edit the constitution to change it).

### Why a toggle exists

Compression is lossy and can alter results. Teams that cannot accept any output
variance keep it **off**. Teams prioritizing token savings turn it **on** and
rely on the fidelity gate to bound the risk.

---

## The fidelity gate (release-blocking)

Compression-enabled behavior is trusted only if it provably does not change
governance outcomes. The gate (ADR-0017) replays a fixed **golden harness
session** with compression ON and OFF and requires **both**:

1. **Zero divergence** across the full governance outcome set — any single
   differing field is a FAIL. Covered categories (AC-001):
   - **routing** — `route_at` decision fields
   - **ac_state** — a spec's acceptance-criteria checkbox states
   - **drift** — a spec's drift-finding records (structured: file, line,
     severity, finding_id, message)
2. **30–95%** session-total outbound prompt-token reduction, measured via the
   `headroom-simulate` engine over the payloads fixture (model-free). **Above 95%
   is a FAIL**, not a bonus — it signals over-aggressive compression that risks
   dropping governance-bearing content. (Band measured/justified in TASK-012: the
   in-harness model-free pipeline reaches ~38–56%; headroom's 60–95% needs live
   multi-request CCR/cache accumulation, out of harness scope — see ADR-0017.)

Run it:

```bash
# runnable self-test: noop engine -> fidelity PASS, 0% reduction -> band FAIL.
# Proves the pipeline end to end without pretending noop compresses anything.
python3 "<plugin>/scripts/run_golden_session_benchmark.py" --engine noop

# real engine: fails closed ("incomplete") until the headroom _engine_* seams
# are wired against the installed SDK — never a silent green.
python3 "<plugin>/scripts/run_golden_session_benchmark.py" --engine headroom
```

The golden session lives at
`.specify/evals/011-context-compression-governance/golden-session/manifest.json`.
Its expected values are recorded from the **real** scripts and re-verified against
the live extractors by the fixture test, so a stale golden fails loudly. It
includes an **adversarial** scenario: an intent containing directive-shaped text
("ignore previous instructions…") must be treated as DATA — the route must not
flip to `/at-implement` — and compression must not weaken that boundary.

---

## Architecture (abstraction + default + noop)

One shared abstraction with swappable implementations (ADR-0013), mirroring the
001/009/010 provider pattern:

- `ContextCompressionProvider` — the interface (`activate` / `deactivate` /
  `compress` / `retrieve`). Zero dependencies; vendor/transport-neutral names; a
  host receives only an **opaque endpoint token**, never a raw proxy port.
- **headroom default** — wraps `headroom-ai[proxy]` (ADR-0014), confined to the
  headroom provider module. Per-session lifecycle (ADR-0019).
- **noop** — the disabled path: passthrough, no proxy, no socket.

Scaffolded into a product as the importable package **`context_compression/`**
(not `compression` — that shadows the Python 3.14+ stdlib package). Consume via
package imports, never ad-hoc file-path loading (keeps one interface identity).

---

## Security posture

- **Local-first, no third-party egress.** The proxy runs locally; headroom must
  run network-restricted to loopback so governed content never leaves the machine
  (NFR-001, ADR-0014).
- **Supply chain.** headroom is pinned (`headroom-ai==0.27.0`) and SHA256-verified
  at install; the pin is asserted by `check_compression_setup.py`. headroom
  imports are confined to the headroom provider module (boundary-checked).
- **Credential hygiene.** `Authorization` / `x-api-key` / `cookie` are scrubbed
  before any **log** path; full-payload/debug logging is prohibited and checked.
- **Passthrough fallback.** If the proxy is unreachable, the session completes
  uncompressed and emits a structured `compression_passthrough_fallback` signal
  (WARN+, in the main output stream) — never a broken or silently-altered session
  (ADR-0015).
- **Engine-owned CCR directory.** If headroom CCR is configured, its configured
  directory must stay outside the git worktree and any cloud-sync path, with dir
  mode `700` and files mode `600`. This ADR-0018 invariant is actively checked at
  setup and at proxy activation. The harness does not ship its own CCR store or
  at-rest seal under Option A.

---

## Status / current limitations

- Disabled path, abstraction, noop, `/at-init` toggle, scaffolder, setup checks,
  golden session, FidelityGate, and the benchmark runner are implemented and
  tested.
- The headroom default provider is a structural template: the actual
  `headroom-ai` SDK calls live behind `_engine_*` seams that must be wired and
  verified against the installed SDK before the ON path can run live. Until then
  the `--engine headroom` benchmark reports `incomplete` (fail-closed).
- Per-host proxy wiring (Claude/Codex/Copilot) and live integration tests are the
  remaining work and require a live headroom runtime.
