# Latest Evaluation Results — Context Compression Governance

**Eval:** deterministic golden-session fidelity benchmark (ADR-0017)
**Runner:** `run_golden_session_benchmark.py --engine headroom-simulate`
**Engine:** `headroom-ai==0.27.0` `TransformPipeline.simulate()` (model-free, no live proxy)
**Dataset:** `golden-session/` (manifest v1.0.0) + `payloads.json`
**Baseline:** compression-OFF run (`baseline.json`, dataset v1.0.0)
**Recorded:** 2026-06-23

## Result: PASS

| Metric | Threshold | Measured | Verdict |
|--------|-----------|----------|---------|
| Fidelity (governance-outcome divergence ON vs OFF) | == 0 | 0 (routing + ac_state + drift) | PASS |
| Token reduction (session-total, proxy pipeline) | 30–95% | 37.9% | PASS (in band) |

- Fidelity: zero divergence across all categories (routing/adversarial, ac_state, drift).
- Reduction: 37.9% via the simulate pipeline over the payloads fixture.

## Notes
- Run in an environment with `headroom-ai[proxy]` installed (the harness CI uses
  system Python where the engine is absent → the benchmark fails closed as
  `incomplete`, never a false pass).
- This is a deterministic-replay benchmark (ADR-0017), not an observation-backed
  one — it produces no runtime observation telemetry (`.specify/observations/`),
  by design. See the drift report for the accepted MEDIUM findings on that.
