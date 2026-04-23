from support_triage.domain.ticket import Ticket, TriageResult


class SupportAgentRuntime:
    """Internal runtime boundary. Product code depends on this, not a harness SDK."""

    def draft_response(self, ticket: Ticket, category: str, priority: str) -> str:
        raise NotImplementedError

    def request_case_creation_approval(self, ticket: Ticket, result: TriageResult) -> bool:
        raise NotImplementedError


class SupportTriageService:
    def __init__(self, runtime: SupportAgentRuntime):
        self._runtime = runtime

    def triage(self, ticket: Ticket) -> TriageResult:
        category = self._classify(ticket)
        priority = self._priority(ticket)
        draft = self._runtime.draft_response(ticket, category, priority)
        result = TriageResult(
            category=category,
            priority=priority,
            draft_response=draft,
            requires_approval=True,
        )
        self._runtime.request_case_creation_approval(ticket, result)
        return result

    def _classify(self, ticket: Ticket) -> str:
        text = f"{ticket.subject} {ticket.body}".lower()
        if any(word in text for word in ["invoice", "refund", "payment", "billing"]):
            return "billing"
        if any(word in text for word in ["error", "bug", "crash", "api", "login"]):
            return "technical"
        return "general"

    def _priority(self, ticket: Ticket) -> str:
        text = f"{ticket.subject} {ticket.body}".lower()
        if ticket.customer_tier == "enterprise" or any(word in text for word in ["down", "blocked", "urgent"]):
            return "urgent"
        if any(word in text for word in ["soon", "issue", "problem"]):
            return "normal"
        return "low"
