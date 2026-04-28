import unittest
import pathlib
import sys


_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_APP_ROOT = _TESTS_DIR.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from support_triage.adapters.fake_harness import FakeHarnessRuntime
from support_triage.application.triage_service import SupportTriageService
from support_triage.domain.ticket import Ticket


class SupportTriageServiceTest(unittest.TestCase):
    def test_billing_ticket_gets_billing_category(self):
        runtime = FakeHarnessRuntime()
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
        runtime = FakeHarnessRuntime()
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

    def test_case_creation_approval_is_recorded(self):
        runtime = FakeHarnessRuntime()
        service = SupportTriageService(runtime)

        service.triage(Ticket(ticket_id="T-003", subject="Login bug", body="I cannot login."))

        event_types = [event["type"] for event in runtime.events]
        self.assertIn("tool_call", event_types)
        self.assertIn("permission_check", event_types)
        self.assertIn("memory_write", event_types)


if __name__ == "__main__":
    unittest.main()
