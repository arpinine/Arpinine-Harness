"""Intentional drift example.

Do not copy this pattern into real application code.
This simulates product application code importing OpenHarness directly,
bypassing the adapter boundary defined in ADR-0001.
"""

from openharness.tools.base import BaseTool  # noqa: F401


def create_tool_inside_application_code():
    return BaseTool()
