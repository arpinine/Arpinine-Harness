# Evaluation Results

Result: PASS
Run ID: 20260531T000000Z-shared-core-validation
Dataset Version: governance-feature
Variant ID: shared-core
Scenario Set: shared-core-tests
Passed: 152
Failed: 0

Latency P50 ms: n/a
Latency P95 ms: n/a
Token Input Total: n/a
Token Output Total: n/a
Cost USD Total: n/a

Verification evidence:
- `python3 -m unittest discover -s src/arpinine-harness-core/tests` passed (152 tests)
- `make validate-structure IMPLEMENTATION=claude` passed
- `make validate-structure IMPLEMENTATION=codex` passed
- `make validate-structure IMPLEMENTATION=copilot` passed
