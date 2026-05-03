import pathlib
import sys
import unittest


_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_APP_ROOT = _TESTS_DIR.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from support_triage.adapters.openai_harness import OpenAIHarnessRuntime
from support_triage.domain.ticket import Ticket, TriageResult


class FakeResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class FakeResponsesAPI:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse("Thanks for the report. We marked this as technical with urgent priority.")


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponsesAPI()


class OpenAIHarnessRuntimeTest(unittest.TestCase):
    def test_draft_response_calls_openai_and_records_event(self):
        client = FakeOpenAIClient()
        runtime = OpenAIHarnessRuntime(client=client, model="gpt-test-mini")
        ticket = Ticket("T-100", "API down", "Our integration is blocked.", customer_tier="enterprise")

        draft = runtime.draft_response(ticket, "technical", "urgent")

        self.assertIn("technical", draft)
        self.assertEqual(runtime.events[0]["type"], "tool_call")
        self.assertEqual(runtime.events[0]["provider"], "openai")
        self.assertEqual(client.responses.calls[0]["model"], "gpt-test-mini")
        self.assertEqual(client.responses.calls[0]["input"][0]["role"], "system")
        self.assertEqual(client.responses.calls[0]["input"][1]["role"], "user")

    def test_request_case_creation_approval_records_permission_and_memory(self):
        client = FakeOpenAIClient()
        runtime = OpenAIHarnessRuntime(
            client=client,
            approval_callback=lambda _ticket, _result: True,
        )
        ticket = Ticket("T-101", "Refund", "Please refund this charge.")
        result = TriageResult("billing", "low", "Draft", True)

        approved = runtime.request_case_creation_approval(ticket, result)

        self.assertTrue(approved)
        event_types = [event["type"] for event in runtime.events]
        self.assertIn("permission_check", event_types)
        self.assertIn("memory_write", event_types)


if __name__ == "__main__":
    unittest.main()
