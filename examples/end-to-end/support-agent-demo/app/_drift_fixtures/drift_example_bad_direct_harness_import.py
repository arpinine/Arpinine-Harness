"""Intentional drift example.

Do not copy this pattern into real application code.
This simulates product application code importing a concrete harness runtime directly.
"""

from openharness import AgentRuntime  # noqa: F401


def create_runtime_inside_product_code():
    return AgentRuntime()
