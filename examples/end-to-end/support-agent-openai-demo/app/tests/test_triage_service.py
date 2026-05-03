import pathlib
import sys
import unittest


_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_APP_ROOT = _TESTS_DIR.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from support_triage.application.triage_service import SupportAgentRuntime, SupportTriageService
from support_triage.domain.ticket import Ticket, TriageResult


class RecordingRuntime(SupportAgentRuntime):
    def __init__(self):
        self.calls = []

    def draft_response(self, ticket: Ticket, category: str, priority: str) -> str:
        self.calls.append(("draft", ticket.ticket_id, category, priority))
        return f"Draft for {category} / {priority}"

    def request_case_creation_approval(self, ticket: Ticket, result: TriageResult) -> bool:
        self.calls.append(("approve", ticket.ticket_id, result.category, result.priority))
        return True


class SupportTriageServiceTest(unittest.TestCase):
    def test_billing_ticket_gets_billing_category(self):
        runtime = RecordingRuntime()
        service = SupportTriageService(runtime)

        result = service.triage(
            Ticket(
                ticket_id="T-001",
                subject="Invoice question",
                body="Can you explain this billing charge?",
            )
        )

        self.assertEqual(result.category, "billing")
        self.assertEqual(result.priority, "low")
        self.assertTrue(result.requires_approval)
        self.assertIn("billing", result.draft_response)

    def test_enterprise_outage_gets_urgent_priority(self):
        runtime = RecordingRuntime()
        service = SupportTriageService(runtime)

        result = service.triage(
            Ticket(
                ticket_id="T-002",
                subject="API is down",
                body="Our production integration is blocked.",
                customer_tier="enterprise",
            )
        )

        self.assertEqual(result.category, "technical")
        self.assertEqual(result.priority, "urgent")

    def test_runtime_boundary_is_used_for_draft_and_approval(self):
        runtime = RecordingRuntime()
        service = SupportTriageService(runtime)

        service.triage(Ticket(ticket_id="T-003", subject="Login bug", body="I cannot login."))

        self.assertEqual(runtime.calls[0][0], "draft")
        self.assertEqual(runtime.calls[1][0], "approve")


if __name__ == "__main__":
    unittest.main()
