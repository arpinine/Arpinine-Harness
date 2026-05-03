from dataclasses import dataclass


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    subject: str
    body: str
    customer_tier: str = "standard"


@dataclass(frozen=True)
class TriageResult:
    category: str
    priority: str
    draft_response: str
    requires_approval: bool
