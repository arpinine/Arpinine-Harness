from support_triage.application.triage_service import SupportAgentRuntime
from support_triage.domain.ticket import Ticket, TriageResult


class FakeHarnessRuntime(SupportAgentRuntime):
    """Fake harness adapter for demos and tests."""

    def __init__(self):
        self.events = []

    def draft_response(self, ticket: Ticket, category: str, priority: str) -> str:
        self.events.append(
            {
                "type": "tool_call",
                "tool": "draft_support_reply",
                "ticket_id": ticket.ticket_id,
            }
        )
        return (
            f"Thanks for contacting support. We classified your request as "
            f"{category} with {priority} priority. A specialist will review it next."
        )

    def request_case_creation_approval(self, ticket: Ticket, result: TriageResult) -> bool:
        self.events.append(
            {
                "type": "permission_check",
                "action": "create_support_case",
                "result": "approved",
                "ticket_id": ticket.ticket_id,
            }
        )
        self.events.append(
            {
                "type": "memory_write",
                "scope": "session",
                "key": f"triage:{ticket.ticket_id}",
            }
        )
        return True
