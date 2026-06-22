#!/usr/bin/env python3
"""
fidelity_gate.py — the zero-divergence governance-outcome diff (the "fidelity
gate", distinct from the benchmark runner).

ADR-0017: compression-enabled behavior is trusted only if governance outcomes are
IDENTICAL with compression ON vs OFF. Comparison is over a declared outcome field
set; ANY single differing (or missing) field is a FAIL. No materiality tolerance.

Pure and dependency-free so it is fully unit-testable without a proxy.

Governs: specs/011-context-compression-governance (TASK-009).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FidelityVerdict:
    passed: bool
    divergences: list[dict] = field(default_factory=list)


_MISSING = object()


class FidelityGate:
    """
    Compares OFF vs ON governance outcome sets over `fields` with zero tolerance.
    """

    def __init__(self, fields: list[str]) -> None:
        if not fields:
            raise ValueError("FidelityGate requires at least one outcome field")
        self._fields = list(fields)

    def compare(self, off: dict, on: dict, keys: list[str] | None = None) -> FidelityVerdict:
        """
        Diff one OFF/ON outcome pair. Any differing/missing field => FAIL.

        `keys` overrides the instance fields for this comparison — used when each
        scenario carries its own outcome shape (routing vs ac_state vs drift).
        """
        divergences: list[dict] = []
        for f in (keys if keys is not None else self._fields):
            off_v = off.get(f, _MISSING)
            on_v = on.get(f, _MISSING)
            if off_v != on_v:
                divergences.append(
                    {
                        "field": f,
                        "off": None if off_v is _MISSING else off_v,
                        "on": None if on_v is _MISSING else on_v,
                    }
                )
        return FidelityVerdict(passed=not divergences, divergences=divergences)

    def aggregate(self, pairs: list[tuple]) -> dict:
        """
        Run compare() over many pairs. Each pair is (off, on) or (off, on, keys).
        PASS only if every pair passes.
        """
        results = []
        divergent = 0
        for idx, pair in enumerate(pairs):
            off, on = pair[0], pair[1]
            keys = pair[2] if len(pair) > 2 else None
            verdict = self.compare(off, on, keys)
            if not verdict.passed:
                divergent += 1
            results.append({"index": idx, "passed": verdict.passed, "divergences": verdict.divergences})
        return {
            "passed": divergent == 0,
            "total_scenarios": len(pairs),
            "divergent_scenarios": divergent,
            "results": results,
        }
