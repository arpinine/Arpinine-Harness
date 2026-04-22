# Spec: User Login

## User Stories
As a registered user, I want to log in with email and password, so that I can access my account.

## Requirements
- FR-001: The system SHALL authenticate users by email and password
- FR-002: The system SHALL limit failed login attempts to 5 per minute per IP
- FR-003: The system SHALL invalidate sessions after 30 days of inactivity

## Non-Functional Requirements
- NFR-001: Login endpoint responds in under 500ms at p99

## Acceptance Criteria
- [ ] AC-001: Correct credentials return a session token within 500ms
- [ ] AC-002: 6th failed attempt in 60 seconds returns HTTP 429
- [ ] AC-003: Session inactive for 30 days is rejected with HTTP 401

## Out of Scope
- Social login (Google, GitHub)
- Two-factor authentication
- Password reset flow

## Related ADRs
- ADR-0001: Use PostgreSQL for session storage — governs session persistence strategy
