"""
EvaluationProvider — abstract interface for LLM output evaluation.

Product code depends on this Protocol only. SDK-specific implementations
(e.g. DeepEvalProvider) live in src/evaluation/<provider>.py and are
injected at the composition root.

Swap the provider by changing the composition root import — no product code changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class LLMTestCase:
    input: str
    actual_output: str
    expected_output: str | None = None
    context: list[str] | None = None
    retrieval_context: list[str] | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricResult:
    name: str
    score: float
    threshold: float
    passed: bool
    reason: str | None = None


@dataclass
class EvalResult:
    test_case: LLMTestCase
    metric_results: list[MetricResult]

    @property
    def passed(self) -> bool:
        return all(m.passed for m in self.metric_results)


@dataclass
class EvalPolicy:
    """
    Defines pass/fail behaviour for a set of results.

    strict=True  — all metrics must pass (default for release gates)
    strict=False — any metric pass counts (for exploratory/diagnostic runs)
    """
    strict: bool = True
    blocking_metrics: list[str] = field(default_factory=list)


class EvaluationError(Exception):
    """Raised when evaluation fails a required threshold in strict mode."""


@runtime_checkable
class EvaluationProvider(Protocol):
    """
    Thin abstraction over LLM evaluation backends.

    Implementations must be deterministic given the same inputs and metrics.
    Product test code must never import from concrete implementation modules.
    """

    def evaluate(
        self,
        test_cases: list[LLMTestCase],
        metrics: list[Any],
        *,
        run_async: bool = False,
    ) -> list[EvalResult]:
        """
        Run evaluation metrics against test cases.

        Returns one EvalResult per test case. Order is preserved.
        Implementations must not raise on individual metric failures —
        failures are encoded in MetricResult.passed.
        """
        ...

    def assert_passes(
        self,
        results: list[EvalResult],
        policy: EvalPolicy | None = None,
    ) -> None:
        """
        Assert that all results satisfy the policy.

        Raises EvaluationError with a structured report when policy fails.
        Default policy: strict=True, all metrics blocking.
        """
        ...
