# 📋 Drift Report: 011-context-compression-governance

Audited: 2026-06-23 (`/at-audit 011`)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESOLVED  HIGH    benchmarked eval declared but dataset-manifest.json missing
RESOLVED  HIGH    regression-sensitive eval declared but baseline.json missing
RESOLVED  MEDIUM  benchmarked eval declared but no latest benchmark results
ACCEPTED  MEDIUM  benchmarked eval declared but no observation history directory
ACCEPTED  MEDIUM  benchmarked eval declared but no observation index
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5 findings → 3 resolved, 2 accepted (non-blocking). 0 unresolved.
```

## Attribution: PRECONDITION FAILURE (checker-model mismatch)

All five findings come from `quick_drift_check.py` assuming the **observation-backed
benchmark model** (the 009 operational-measurement shape: `dataset-manifest.json`
+ `baseline.json` + runtime observation history/index). Spec 011 deliberately uses
a **different, ADR-0017-governed eval shape**: a deterministic golden-session
replay (zero-divergence FidelityGate + proxy-pipeline token reduction), which is
not observation/telemetry-backed.

This is a precondition mismatch between a generic checker and an ADR-governed
alternative eval model — not an implementation deviation. No business case, scope,
or acceptance-criteria change (the findings are eval-artifact-convention only).

## Resolution

- **2 HIGH + 1 MEDIUM — resolved by providing the truthful equivalents** 011 actually has:
  - `dataset-manifest.json` — the golden-session scenarios + payloads fixture (v1.0.0).
  - `baseline.json` — the compression-OFF run is the baseline (ADR-0017).
  - `latest-results.md` — the recorded `headroom-simulate` PASS (zero divergence + 37.9% in band).
- **2 MEDIUM — accepted, non-blocking** (observation history/index): 011's deterministic
  replay produces **no runtime observation telemetry** by design (ADR-0017 chose this
  over the observation/DeepEval model). Fabricating empty observation ledgers would be
  dishonest. These remain as expected, explained false-positives of the generic checker.

## ADR coverage

- The eval-shape decision is already governed by **ADR-0017** (deterministic golden-session
  replay instead of the observation/DeepEval benchmark). No new ADR required; the drift
  is explained by an existing accepted decision.

## Summary

```
5 drift items → 3 resolved (artifacts created), 2 accepted (ADR-0017 deterministic
model; no runtime observation telemetry by design). 0 CRITICAL, 0 unresolved HIGH.
No ADR created (ADR-0017 already covers the eval-shape decision). Not blocking.
```

> Note: AC-008 (live host interception) remains unchecked pending the operator
> live-smoke run — that is a separate, documented integration step, not drift.
