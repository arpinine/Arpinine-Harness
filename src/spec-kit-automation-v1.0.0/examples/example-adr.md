---
governs: specs/001-user-login
supersedes: ~
status: Accepted
date: 2026-04-22
---

# ADR-0001: Use PostgreSQL for Session Storage

## Status
Accepted

## Context
Session data must survive service restarts. During load testing, Redis (our first candidate) dropped in-memory sessions on crash without AOF persistence configured, causing users to be logged out unexpectedly.

## Decision
Use PostgreSQL for session storage. Sessions stored as rows in a `sessions` table with TTL enforced by a nightly cleanup job.

## Consequences
- Positive: Sessions survive restarts; ACID guarantees; single data store reduces ops overhead
- Negative: Higher read latency (~5ms) vs Redis (~1ms); requires index on `expires_at` for cleanup job

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Redis (in-memory) | Data loss on restart without AOF; adds second data store |
| JWT (stateless) | Cannot invalidate individual sessions server-side |
