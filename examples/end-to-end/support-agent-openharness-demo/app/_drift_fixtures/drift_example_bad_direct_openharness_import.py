"""Intentional drift example.

Do not copy this pattern into real application code.
This simulates product application code importing OpenHarness directly,
bypassing the adapter boundary required by ADR-0001 and harness-001 rule.
"""

from openharness.tools.base import BaseTool  # noqa: F401
from openharness.engine.query_engine import QueryEngine  # noqa: F401


def create_engine_inside_product_code():
    return QueryEngine()
