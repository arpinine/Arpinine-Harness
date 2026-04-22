# Spec: [FEATURE NAME]

## User Stories
As a [persona], I want [action], so that [value].

## Requirements
- FR-001: The system SHALL [do something measurable]

## Non-Functional Requirements
- NFR-001: [Performance/security/reliability requirement — include metric, e.g., "under 200ms p99"]

## Acceptance Criteria
- [ ] AC-001: [Measurable criterion — numbers, not vague terms like "fast" or "easy"]

## Out of Scope
- [Explicitly list excluded items to prevent scope creep]

## AI-Nativeness Assessment

**AIN Target Level**: [1 = no AI / 2 = AI-assisted internal tooling / 3 = AI in workflow / 4 = AI-native product]

**Agent-Callable Operations** (for AIN ≥ 3):
- [List operations that AI agents should be able to invoke — e.g., `search_products(query)`, `submit_order(cart_id)`]
- [Include input schema, expected output shape, and failure modes]

**Human-in-the-Loop Gates** (for AIN ≥ 3):
- [Which decisions require human approval before the agent proceeds?]
- [e.g., "Order total > $500 requires human confirmation before submission"]

**Feedback Channels**:
- [How does the system capture signal about agent errors or quality issues?]
- [e.g., thumbs up/down, correction log, escalation path]

**Evaluation Required**: [YES / NO — if YES, an eval-plan.md is required before implementation]

## Related ADRs
- ADR-XXXX: [Title] — [How it governs this spec]
