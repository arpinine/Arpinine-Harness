# Spec: Support Triage Agent

## Business Case
Reduce time-to-first-response for inbound support tickets while keeping account-impacting actions under human control.

## User Stories
As a customer support specialist, I want inbound tickets classified and drafted automatically, so that I can respond faster while retaining approval over case creation.

## Requirements
- FR-001: The system SHALL classify each inbound ticket as billing, technical, or general.
- FR-002: The system SHALL assign priority as low, normal, or urgent.
- FR-003: The system SHALL draft a first response using only the ticket content and classification result.
- FR-004: The system SHALL require approval before creating a support case.

## Non-Functional Requirements
- NFR-001: The triage operation SHALL complete in under 500ms for the local demo scenarios.
- NFR-002: The system SHALL avoid persistent cross-customer memory.

## Acceptance Criteria
- [x] AC-001: Given a billing ticket, the result category is billing.
- [x] AC-002: Given an enterprise outage ticket, the result priority is urgent.
- [x] AC-003: Given any ticket, the draft response includes the selected category and priority.
- [x] AC-004: Given any ticket, case creation approval is requested before completion evidence is accepted.

## Out of Scope
- Sending customer email
- Creating tickets in a real CRM
- Persistent customer memory
- Autonomous account-impacting actions

## AI-Nativeness Assessment

**AIN Target Level**: 3

**Agent-Callable Operations** (for AIN >= 3):
- `triage_ticket(ticket_id, subject, body, customer_tier)` returns category, priority, draft response, and approval requirement.
- Input schema: ticket id, subject, body, customer tier.
- Output shape: category, priority, draft response, requires approval.
- Failure modes: unknown category, unsafe draft, missing approval event.

**Human-in-the-Loop Gates** (for AIN >= 3):
- Creating a support case requires approval before completion.

**Feedback Channels**:
- Evaluation scenarios measure classification, priority, approval, and memory scope.
- Observation trace records tool calls, permission checks, and memory writes.

**Evaluation Required**: YES

## Implementation References
- app/support_triage/domain/ticket.py
- app/support_triage/application/triage_service.py
- app/support_triage/adapters/fake_harness.py
- app/tests/test_triage_service.py
- app/eval/run_eval.py

## Related ADRs
- ADR-0001: Fake harness adapter boundary - governs harness abstraction and runtime swap strategy
