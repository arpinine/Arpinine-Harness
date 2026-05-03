"""Tests for OpenHarnessAdapter.

DraftSupportReplyTool tests run offline — no API key required.
OpenHarnessAdapter tests run against the real OpenHarness + Anthropic stack.
Set ANTHROPIC_API_KEY to run the adapter tests; they are skipped otherwise.
"""

import os
import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_APP_ROOT = _TESTS_DIR.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from openharness.tools.base import ToolExecutionContext

from support_triage.adapters.openharness_adapter import (
    DraftSupportReplyTool,
    DraftSupportReplyInput,
    OpenHarnessAdapter,
)
from support_triage.domain.ticket import Ticket, TriageResult


_REQUIRES_API_KEY = unittest.skipUnless(
    os.environ.get("ANTHROPIC_API_KEY"),
    "requires ANTHROPIC_API_KEY",
)


class DraftSupportReplyToolTest(unittest.IsolatedAsyncioTestCase):
    async def test_execute_returns_draft_containing_category_and_priority(self):
        tool = DraftSupportReplyTool()
        args = DraftSupportReplyInput(
            ticket_id="T-001",
            category="technical",
            priority="urgent",
            subject="API down",
            body="Our integration is blocked.",
            customer_tier="enterprise",
        )
        ctx = ToolExecutionContext(cwd=pathlib.Path("."))
        result = await tool.execute(args, ctx)
        self.assertFalse(result.is_error)
        self.assertIn("technical", result.output)
        self.assertIn("urgent", result.output)

    async def test_is_read_only_returns_true(self):
        tool = DraftSupportReplyTool()
        args = DraftSupportReplyInput(
            ticket_id="T-001",
            category="general",
            priority="low",
            subject="Question",
            body="Where are the docs?",
            customer_tier="standard",
        )
        self.assertTrue(tool.is_read_only(args))

    def test_tool_schema_exposes_correct_name(self):
        tool = DraftSupportReplyTool()
        schema = tool.to_api_schema()
        self.assertEqual(schema["name"], "draft_support_reply")
        self.assertIn("input_schema", schema)


@_REQUIRES_API_KEY
class OpenHarnessAdapterTest(unittest.TestCase):
    def test_draft_response_returns_non_empty_text(self):
        adapter = OpenHarnessAdapter()
        ticket = Ticket("T-100", "API down", "Our integration is blocked.", customer_tier="enterprise")
        draft = adapter.draft_response(ticket, "technical", "urgent")
        self.assertTrue(draft.strip())

    def test_draft_response_records_tool_call_event(self):
        adapter = OpenHarnessAdapter()
        ticket = Ticket("T-101", "Refund request", "I need a refund for my payment.")
        adapter.draft_response(ticket, "billing", "low")
        tool_events = [e for e in adapter.events if e["type"] == "tool_call"]
        self.assertEqual(len(tool_events), 1)
        self.assertEqual(tool_events[0]["tool"], "draft_support_reply")
        self.assertEqual(tool_events[0]["provider"], "openharness")

    def test_draft_response_resets_session_between_calls(self):
        adapter = OpenHarnessAdapter()
        t1 = Ticket("T-200", "Login issue", "Cannot log in.")
        t2 = Ticket("T-201", "Billing question", "Invoice question.")
        adapter.draft_response(t1, "technical", "normal")
        adapter.draft_response(t2, "billing", "low")
        tool_events = [e for e in adapter.events if e["type"] == "tool_call"]
        self.assertEqual(len(tool_events), 2)
        self.assertEqual(tool_events[0]["ticket_id"], "T-200")
        self.assertEqual(tool_events[1]["ticket_id"], "T-201")

    def test_only_allowlisted_tool_fires(self):
        adapter = OpenHarnessAdapter()
        ticket = Ticket("T-303", "General question", "Where can I find docs?")
        adapter.draft_response(ticket, "general", "low")
        for event in adapter.events:
            if event["type"] == "tool_call":
                self.assertEqual(event["tool"], "draft_support_reply")

    def test_approval_records_permission_and_memory_events(self):
        adapter = OpenHarnessAdapter()
        ticket = Ticket("T-300", "Refund", "Please refund this charge.")
        result = TriageResult("billing", "low", "Draft.", True)
        approved = adapter.request_case_creation_approval(ticket, result)
        self.assertTrue(approved)
        event_types = [e["type"] for e in adapter.events]
        self.assertIn("permission_check", event_types)
        self.assertIn("memory_write", event_types)

    def test_approval_denied_when_callback_returns_false(self):
        adapter = OpenHarnessAdapter(approval_callback=lambda _t, _r: False)
        ticket = Ticket("T-301", "Cancel", "Cancel my subscription.")
        result = TriageResult("billing", "normal", "Draft.", True)
        approved = adapter.request_case_creation_approval(ticket, result)
        self.assertFalse(approved)
        perm = next(e for e in adapter.events if e["type"] == "permission_check")
        self.assertEqual(perm["result"], "denied")

    def test_memory_writes_are_session_scoped(self):
        adapter = OpenHarnessAdapter()
        ticket = Ticket("T-302", "Bug report", "Found a bug.")
        result = TriageResult("technical", "normal", "Draft.", True)
        adapter.request_case_creation_approval(ticket, result)
        memory_events = [e for e in adapter.events if e["type"] == "memory_write"]
        self.assertTrue(all(e.get("scope") == "session" for e in memory_events))


if __name__ == "__main__":
    unittest.main()
