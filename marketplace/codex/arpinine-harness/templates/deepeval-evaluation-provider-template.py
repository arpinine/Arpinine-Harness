"""
DeepEvalProvider — default EvaluationProvider implementation.

Wraps the DeepEval SDK. All deepeval imports stay in this file.
Product test code must import EvaluationProvider from src/evaluation/base.py only.

Optional env vars:
  DEEPEVAL_API_KEY   — Confident AI key (enables cloud dashboard; local eval works without it)

Install: pip install deepeval

Metric examples:
  from deepeval.metrics import (
      AnswerRelevancyMetric,
      FaithfulnessMetric,
      ContextualPrecisionMetric,
      ContextualRecallMetric,
      HallucinationMetric,
      ToxicityMetric,
  )
"""

from __future__ import annotations

import logging
from typing import Any

import deepeval
from deepeval import evaluate as _dv_evaluate
from deepeval.test_case import LLMTestCase as DVTestCase

from src.evaluation.base import (
    EvalPolicy,
    EvalResult,
    EvaluationError,
    EvaluationProvider,
    LLMTestCase,
    MetricResult,
)

logger = logging.getLogger(__name__)


def _to_dv_test_case(tc: LLMTestCase) -> DVTestCase:
    return DVTestCase(
        input=tc.input,
        actual_output=tc.actual_output,
        expected_output=tc.expected_output,
        context=tc.context,
        retrieval_context=tc.retrieval_context,
        name=tc.name,
    )


def _metric_result_from_data(md: Any) -> MetricResult:
    """Build MetricResult from a deepeval TestResult.metrics_data entry."""
    return MetricResult(
        name=getattr(md, "name", md.__class__.__name__),
        score=float(getattr(md, "score", 0.0) or 0.0),
        threshold=float(getattr(md, "threshold", 0.5)),
        passed=bool(getattr(md, "success", False)),
        reason=getattr(md, "reason", None),
    )


class DeepEvalProvider:
    """
    EvaluationProvider backed by DeepEval.

    Uses deepeval.evaluate() for batch runs. Per-test-case results are read
    from the EvaluationResult object returned by deepeval.evaluate() —
    specifically from TestResult.metrics_data — so each EvalResult reflects
    its own test case outcome, not the shared metric instance's final state.

    Does not require Confident AI key for local evaluation.
    Set DEEPEVAL_API_KEY only for cloud dashboard access.
    """

    def evaluate(
        self,
        test_cases: list[LLMTestCase],
        metrics: list[Any],
        *,
        run_async: bool = False,
    ) -> list[EvalResult]:
        dv_cases = [_to_dv_test_case(tc) for tc in test_cases]

        eval_result = _dv_evaluate(
            test_cases=dv_cases,
            metrics=metrics,
            run_async=run_async,
            print_results=False,
            write_cache=True,
        )

        # deepeval.evaluate() returns an EvaluationResult with a .test_results
        # list (one TestResult per test case). Each TestResult.metrics_data
        # carries per-case scores. Reading from shared metric instances after
        # the batch run is wrong — all cases would see the last case's scores.
        test_results = getattr(eval_result, "test_results", None)
        if test_results is None or len(test_results) != len(test_cases):
            raise RuntimeError(
                f"deepeval.evaluate() returned {len(test_results) if test_results else 'None'} "
                f"test_results for {len(test_cases)} test cases. "
                "Ensure deepeval>=0.21 is installed."
            )

        results: list[EvalResult] = []
        for tc, test_result in zip(test_cases, test_results):
            metric_results = [
                _metric_result_from_data(md)
                for md in (getattr(test_result, "metrics_data", None) or [])
            ]
            if not metric_results:
                # Fallback if metrics_data is unavailable — log and surface as failures
                logger.warning(
                    "No metrics_data on TestResult for case '%s'. "
                    "Check deepeval version compatibility.",
                    tc.name or tc.input[:60],
                )
            results.append(EvalResult(test_case=tc, metric_results=metric_results))

        return results

    def assert_passes(
        self,
        results: list[EvalResult],
        policy: EvalPolicy | None = None,
    ) -> None:
        effective_policy = policy or EvalPolicy(strict=True)

        failures: list[str] = []
        for result in results:
            for mr in result.metric_results:
                is_blocking = (
                    not effective_policy.blocking_metrics
                    or mr.name in effective_policy.blocking_metrics
                )
                if not mr.passed and (effective_policy.strict or is_blocking):
                    case_name = result.test_case.name or result.test_case.input[:60]
                    failures.append(
                        f"[{mr.name}] score={mr.score:.3f} < threshold={mr.threshold}"
                        f" | case='{case_name}'"
                        + (f" | reason: {mr.reason}" if mr.reason else "")
                    )

        if failures:
            report = "\n".join(failures)
            raise EvaluationError(
                f"Evaluation failed ({len(failures)} violation(s)):\n{report}"
            )


assert isinstance(DeepEvalProvider, type)
_ = EvaluationProvider  # structural check: DeepEvalProvider satisfies the Protocol
