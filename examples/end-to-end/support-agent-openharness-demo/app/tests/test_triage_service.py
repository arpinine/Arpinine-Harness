import pathlib
import sys
import unittest

_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_APP_ROOT = _TESTS_DIR.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from support_triage.application.triage_service import SupportAgentRuntime, SupportTriageService
from support_triage.domain.ticket import Ticket, TriageResult


class FakeRuntime(SupportAgentRuntime):
    def __init__(self):
        self.events = []

    def draft_response(self, ticket: Ticket, category: str, priority: str) -> str:
        self.events.append({"type": "tool_call", "tool": "draft_support_reply"})
        return f"Draft for {ticket.ticket_id}: {category}/{priority}"

    def request_case_creation_approval(self, ticket: Ticket, result: TriageResult) -> bool:
        self.events.append({"type": "permission_check", "action": "create_support_case", "result": "approved"})
        self.events.append({"type": "memory_write", "scope": "session", "key": f"triage:{ticket.ticket_id}"})
        return True


class SupportTriageServiceTest(unittest.TestCase):
    def test_billing_classification(self):
        runtime = FakeRuntime()
        service = SupportTriageService(runtime)
        ticket = Ticket("T-001", "Invoice issue", "I need a refund for my payment.")
        result = service.triage(ticket)
        self.assertEqual(result.category, "billing")

    def test_technical_classification(self):
        runtime = FakeRuntime()
        service = SupportTriageService(runtime)
        ticket = Ticket("T-002", "API error", "Getting a crash on login.")
        result = service.triage(ticket)
        self.assertEqual(result.category, "technical")

    def test_general_classification(self):
        runtime = FakeRuntime()
        service = SupportTriageService(runtime)
        ticket = Ticket("T-003", "Question", "Where are the docs?")
        result = service.triage(ticket)
        self.assertEqual(result.category, "general")

    def test_enterprise_tier_is_urgent(self):
        runtime = FakeRuntime()
        service = SupportTriageService(runtime)
        ticket = Ticket("T-004", "Setup help", "Need help getting started.", customer_tier="enterprise")
        result = service.triage(ticket)
        self.assertEqual(result.priority, "urgent")

    def test_urgency_keyword_is_urgent(self):
        runtime = FakeRuntime()
        service = SupportTriageService(runtime)
        ticket = Ticket("T-005", "System down", "Everything is blocked and urgent.")
        result = service.triage(ticket)
        self.assertEqual(result.priority, "urgent")

    def test_requires_approval_is_set(self):
        runtime = FakeRuntime()
        service = SupportTriageService(runtime)
        ticket = Ticket("T-006", "Question", "How does billing work?")
        result = service.triage(ticket)
        self.assertTrue(result.requires_approval)

    def test_approval_event_is_recorded(self):
        runtime = FakeRuntime()
        service = SupportTriageService(runtime)
        ticket = Ticket("T-007", "Refund", "Please process refund.")
        service.triage(ticket)
        event_types = [e["type"] for e in runtime.events]
        self.assertIn("permission_check", event_types)
        self.assertIn("memory_write", event_types)


if __name__ == "__main__":
    unittest.main()
