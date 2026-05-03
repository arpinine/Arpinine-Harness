import os
from typing import Callable

from support_triage.application.triage_service import SupportAgentRuntime
from support_triage.domain.ticket import Ticket, TriageResult

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised through constructor guard
    OpenAI = None


SYSTEM_PROMPT = """You are a support triage drafting assistant.

Write a short professional first response to the customer.
Use only the ticket content and the provided classification.
Do not say a support case has already been created.
Do not promise a resolution you cannot verify.
Do not mention internal tooling or model behavior.
"""


class OpenAIHarnessRuntime(SupportAgentRuntime):
    """OpenAI-backed harness adapter for demos and tests."""

    def __init__(
        self,
        client=None,
        model: str | None = None,
        approval_callback: Callable[[Ticket, TriageResult], bool] | None = None,
    ):
        if client is None:
            if OpenAI is None:
                raise RuntimeError("Install the openai package or inject a compatible client.")
            client = OpenAI()
        self._client = client
        self._model = model or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        self._approval_callback = approval_callback or (lambda _ticket, _result: True)
        self.events: list[dict[str, object]] = []

    def draft_response(self, ticket: Ticket, category: str, priority: str) -> str:
        self.events.append(
            {
                "type": "tool_call",
                "tool": "draft_support_reply",
                "provider": "openai",
                "model": self._model,
                "ticket_id": ticket.ticket_id,
            }
        )
        prompt = self._build_prompt(ticket, category, priority)
        response = self._client.responses.create(
            model=self._model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        text = getattr(response, "output_text", "").strip()
        if not text:
            raise RuntimeError("OpenAI response did not include output_text.")
        return text

    def request_case_creation_approval(self, ticket: Ticket, result: TriageResult) -> bool:
        approved = bool(self._approval_callback(ticket, result))
        self.events.append(
            {
                "type": "permission_check",
                "action": "create_support_case",
                "result": "approved" if approved else "denied",
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
        return approved

    def _build_prompt(self, ticket: Ticket, category: str, priority: str) -> str:
        return (
            f"Ticket ID: {ticket.ticket_id}\n"
            f"Customer tier: {ticket.customer_tier}\n"
            f"Category: {category}\n"
            f"Priority: {priority}\n"
            f"Subject: {ticket.subject}\n"
            f"Body: {ticket.body}\n\n"
            "Write a concise first reply. Mention the issue type and urgency in plain language. "
            "Invite the customer to share extra details if useful."
        )
