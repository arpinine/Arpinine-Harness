# Evaluation Plan: Context Compression Governance

## Governing Spec
`.specify/specs/011-context-compression-governance/spec.md`

## Scope
- Validate the `ContextCompressionProvider` abstraction, the headroom default provider, the noop provider, the `/at-init` toggle, per-host proxy wiring, passthrough fallback, and the fidelity benchmark.
- Applies to `src/arpinine-harness-core/**` plus assembled Claude, Codex, and Copilot plugin outputs.

## Evaluation Objective
- Prove that compression is **outcome-neutral** for governance (zero-divergence) while achieving 60–95% outbound token reduction, and that disabling compression imposes zero overhead and identical behavior.

## Evaluation Framework
- Framework: Deterministic golden-session replay benchmark + Python unittest (NOT DeepEval — the gate is exact structural comparison, not LLM-judged quality). Governed by Pending ADR-E.
- Execution command: `python3 src/arpinine-harness-core/scripts/run_golden_session_benchmark.py --slug 011-context-compression-governance`
- Supporting unit command: `python3 -m unittest discover -s src/arpinine-harness-core/tests`
- Owner: Arpinine Harness maintainers

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
| Credential-scrubbing | zero `Authorization`/`x-api-key`/`cookie` content in proxy logs or CCR store | local tests | Yes |
| Interface contract suite | both impls satisfy the contract | local tests | Yes |
| Reversible-retrieval test | byte-equality of recovered originals | local tests | Yes |
| Disabled-overhead test | no proxy, identical behavior | local tests | Yes |
| Passthrough-fallback test | proxy unreachable → passthrough + signal | local tests | Yes |
| Claude/Codex/Copilot structure assembly | per-host wiring present | `make validate-structure IMPLEMENTATION=<impl>` | Yes |

## Metrics And Thresholds
| Dimension | Metric | Threshold | Failure Action |
|-----------|--------|-----------|----------------|
| Fidelity | governance-outcome diff size (ON vs OFF) | == 0 | block release |
| Token reduction | session-total outbound prompt-token reduction | >= 60% AND <= 95% | block release |
| Disabled overhead | proxy processes started when disabled | == 0 | block completion |
| Passthrough fallback | session completes + fallback signal emitted when proxy unreachable | pass | block completion |
| Reversibility | recovered-vs-original byte equality | pass | block completion |
| Data boundary | governance-outcome diff on adversarial directive-shaped case | == 0 | block release |
| Credential leakage | credential strings in proxy logs / CCR store | == 0 | block completion |
| Boundary | headroom imports outside default-provider module | == 0 | block completion |
| CCR store safety | store path under worktree/cloud-sync OR perms != 700/600 | == 0 violations | block completion |
| Supply chain | installed headroom version+hash != pinned | == 0 mismatch | block completion |
| Packaging (claude/codex/copilot) | validate-structure exit status | pass | block completion |

> **Fidelity gate.** A reduction above 95% is treated as a FAIL, not a bonus: it
> signals over-aggressive compression that risks dropping governance-bearing
> content. The gate requires BOTH zero outcome divergence AND reduction inside
> the 60–95% band. The benchmark fails closed if the golden session or its
> expected outcome set is missing.

## Regression Policy
- Rerun the benchmark after changes to the provider templates, the proxy wiring, the `/at-init` toggle, or the golden session.
- Any non-empty governance-outcome diff blocks release.
- Token reduction outside the 60–95% band blocks release.
- Any headroom import outside the default-provider module blocks completion.

## Baseline Comparison
- Baseline required: Yes — the compression-OFF run of the golden session IS the baseline; the compression-ON run is compared against it every benchmark execution.
