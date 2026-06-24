# Evaluation Plan: Context Compression Governance

## Governing Spec
`.specify/specs/011-context-compression-governance/spec.md`

## Scope
- Validate the `ContextCompressionProvider` abstraction, the headroom default provider, the noop provider, the `/at-init` toggle, per-host proxy wiring, passthrough fallback, and the fidelity benchmark.
- Applies to `src/arpinine-harness-core/**` plus assembled Claude, Codex, and Copilot plugin outputs.

## Evaluation Objective
- Prove that compression is **outcome-neutral** for governance (zero-divergence) while achieving 30–95% outbound token reduction (band measured/justified in TASK-012; see note), and that disabling compression imposes zero overhead and identical behavior.

## Evaluation Framework
- Framework: Deterministic golden-session replay benchmark + Python unittest (NOT DeepEval — the gate is exact structural comparison, not LLM-judged quality). Governed by ADR-0017.
- Execution command: `python3 src/arpinine-harness-core/scripts/run_golden_session_benchmark.py --slug 011-context-compression-governance`
- Supporting unit command: `python3 -m unittest discover -s src/arpinine-harness-core/tests`
- Owner: Arpinine Harness maintainers

### Supplementary Evaluation (optional, real-API — non-blocking)
The deterministic gate above asserts governance-outcome identity ON vs OFF *by
construction* (model-free `simulate`). It never sends the compressed payload
through a live model. The answer-quality evaluator closes that gap with a real
round-trip: it answers a fixed governance question over the same golden fixture
with compression OFF (original context) and ON (`headroom.simulate` output),
then judges divergence.
- Preview (no spend, no key): `python3 src/arpinine-harness-core/scripts/run_answer_quality_eval.py --estimate`
- Live round-trip (needs `ANTHROPIC_API_KEY`; `pip install anthropic`): `python3 src/arpinine-harness-core/scripts/run_answer_quality_eval.py --run`
- Judge signals (ADR-0017 keeps these **out of the release gate** — they are LLM-judged, the deterministic fidelity gate stays authoritative):
  - LLM-judge prose: `equivalent` (bool) + `quality_delta` (−2..2) of ON vs OFF
  - embedding similarity: cosine(OFF, ON) — local `sentence-transformers`, optional, skipped if absent
- Results: `.specify/evals/011-context-compression-governance/answer-quality-results.{md,json}`
- Status: **non-blocking** supplementary signal. A divergence here flags a fidelity risk for investigation; it does not by itself fail the release gate.

## Benchmark Policy
- Benchmark required: Yes (release-blocking fidelity gate)
- Benchmark command: `python3 src/arpinine-harness-core/scripts/run_golden_session_benchmark.py --slug 011-context-compression-governance`
- Golden-session fixture path: `.specify/evals/011-context-compression-governance/golden-session/`
- Minimum recorded `/at-*` runs in the golden session: 5 (covering routing decisions, drift findings, and AC pass/fail paths)
- Aggregation policy: the benchmark replays each recorded run with compression ON and OFF, diffs the governance outcome set, and sums outbound prompt tokens across the full session.

## Governance Outcome Set (the diffed artifacts)
The benchmark covers all three AC-001 categories, each with its own extractor and
compared per scenario by the `FidelityGate`:

| Category | Source extractor | Fields compared |
|----------|------------------|-----------------|
| routing (+ adversarial) | `route_at.py` | `interpretation`, `route`, `confidence`, `command_class`, `requires_confirmation` |
| ac_state | `spec.md` AC checkbox parse | checkbox value per `AC-xxx` id |
| drift | `quick_drift_check.py --json` | the `findings` record list |

Comparison policy: **zero divergence** — any single differing field is a FAIL. No materiality tolerance. Performed by the `FidelityGate` construct (`fidelity_gate.py`), distinct from the benchmark runner (`run_golden_session_benchmark.py`).

## Datasets And Scenarios
| Dataset / Scenario | Purpose | Source | Required |
|--------------------|---------|--------|----------|
| Golden harness session (ON/OFF replay) | fidelity + token-reduction gate | `golden-session/` fixture | Yes |
| Adversarial directive-shaped artifact | data boundary survives compression (≥1 artifact contains "ignore previous instructions"-style text; outcome diff stays empty) | `golden-session/` fixture | Yes |
| Credential-scrubbing | zero `Authorization`/`x-api-key`/`cookie` content in harness log paths | local tests | Yes |
| Interface contract suite | both impls satisfy the contract | local tests | Yes |
| Disabled-overhead test | no proxy, identical behavior | local tests | Yes |
| Passthrough-fallback test | proxy unreachable → passthrough + signal + zero-divergence fidelity result | local tests | Yes |
| Claude/Codex/Copilot structure assembly | per-host wiring present | `make validate-structure IMPLEMENTATION=<impl>` | Yes |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Fidelity | governance-outcome diff size (ON vs OFF) | == 0 | block release |
| Token reduction | session-total outbound prompt-token reduction (via `headroom-simulate` over `payloads.json`) | >= 30% AND <= 95% (band revised in TASK-012 — see measured note) | block release |
| Disabled overhead | proxy processes started when disabled | == 0 | block completion |
| Passthrough fallback | session completes + fallback signal emitted when proxy unreachable | pass | block completion |
| Data boundary | governance-outcome diff on adversarial directive-shaped case | == 0 | block release |
| Credential leakage | credential strings in harness log paths | == 0 | block completion |
| Boundary | headroom imports outside default-provider module | == 0 | block completion |
| Engine CCR directory safety | configured headroom CCR dir under worktree/cloud-sync OR perms != 700/600 | == 0 violations | block completion |
| Supply chain | installed headroom version+hash != pinned | == 0 mismatch | block completion |
| Packaging (claude/codex/copilot) | validate-structure exit status | pass | block completion |

> **Measured reduction (live, headroom-ai 0.27.0 — TASK-010/012).**
> `headroom.compress()`: 0% (protected user msgs) … 55% (tool JSON). Full
> proxy-pipeline `TransformPipeline.simulate()` (CCR + cache-aligner +
> `intercept_tool_results`, model-free): ~41% single-pass tool-heavy; **37.9%**
> on the `payloads.json` golden fixture. The in-harness-measurable path tops out
> ~38–56%; the headroom "60–95%" needs live multi-request CCR/cache accumulation
> (out of harness scope). **Band revised to 30–95%** (ADR-0017): floor with honest
> margin below the ~38% fixture minimum — stable gate, still proves substantial
> compression. Validated by the `headroom-simulate` engine (`--engine
> headroom-simulate`, requires `headroom-ai` installed); fails closed
> (`incomplete`) when headroom or the fixture is absent. NOT lowered for
> convenience — it is the measured ceiling of the model-free path.
>
> **Fidelity gate.** A reduction above 95% is treated as a FAIL, not a bonus: it
> signals over-aggressive compression that risks dropping governance-bearing
> content. The gate requires BOTH zero outcome divergence AND reduction inside
> the 30–95% band. The benchmark fails closed if the golden session or its
> expected outcome set is missing.

## Regression Policy
- Rerun the benchmark after changes to the provider templates, the proxy wiring, the `/at-init` toggle, or the golden session.
- Any non-empty governance-outcome diff blocks release.
- Token reduction outside the 30–95% band blocks release.
- Any headroom import outside the default-provider module blocks completion.

## Baseline Comparison
- Baseline required: Yes — the compression-OFF run of the golden session IS the baseline; the compression-ON run is compared against it every benchmark execution.
