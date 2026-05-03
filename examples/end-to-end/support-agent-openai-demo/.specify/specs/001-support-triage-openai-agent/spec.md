# Spec: Support Triage Agent With OpenAI

## Business Case
Reduce time-to-first-response for inbound support tickets while keeping account-impacting actions under human control.

## User Stories
As a customer support specialist, I want inbound tickets classified locally and drafted with an LLM, so that I can respond faster while retaining approval over case creation.

## Requirements
- FR-001: The system SHALL classify each inbound ticket as billing, technical, or general.
- FR-002: The system SHALL assign priority as low, normal, or urgent.
- FR-003: The system SHALL draft a first response using OpenAI through an adapter boundary.
- FR-004: The system SHALL require approval before creating a support case.

## Non-Functional Requirements
- NFR-001: The application layer SHALL not import the OpenAI SDK directly.
- NFR-002: The system SHALL avoid persistent cross-customer memory.
- NFR-003: The live demo SHALL be runnable with only Python, the `openai` package, and environment credentials.

## Acceptance Criteria
- [x] AC-001: Given a billing ticket, the result category is billing.
- [x] AC-002: Given an enterprise outage ticket, the result priority is urgent.
- [x] AC-003: Given any ticket, the runtime records a draft-generation event before returning the result.
- [x] AC-004: Given any ticket, case creation approval is requested before completion evidence is accepted.
- [x] AC-005: The application service can be tested without making a live API call.

## Out Of Scope
- Creating tickets in a real CRM
- Persistent customer memory
- Autonomous case creation
- Multi-turn conversation state

## AI-Nativeness Assessment

**AIN Target Level**: 3

**Agent-Callable Operations**:
- `triage_ticket(ticket_id, subject, body, customer_tier)` returns category, priority, draft response, and approval requirement.
- `draft_support_reply(ticket_id, category, priority, ticket_text)` drafts the first response through the harness adapter.

**Human-In-The-Loop Gates**:
- Creating a support case requires approval before completion.

**Feedback Channels**:
- Unit tests verify boundary isolation and runtime event recording.
- Live evaluation verifies approval evidence, session-scoped memory, and non-empty draft output.

**Evaluation Required**: YES

## Implementation References
- app/support_triage/application/triage_service.py
- app/support_triage/adapters/openai_harness.py
- app/tests/test_triage_service.py
- app/tests/test_openai_harness.py
- app/eval/run_live_eval.py

## Related ADRs
- ADR-0001: OpenAI Responses adapter boundary
