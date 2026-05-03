# Spec: Support Triage Agent With OpenHarness

## Problem
Support teams receive inbound tickets and need a first response drafted quickly and consistently. Manual drafting is slow and inconsistent across agents.

## User Value
A support agent submits a ticket and receives a classified triage result with a drafted first response, without writing the reply from scratch.

## Scope
- Classify inbound tickets into billing, technical, or general categories
- Assign priority based on content and customer tier
- Draft a first response using the OpenHarness agent runtime
- Gate case creation behind an explicit approval step

## Out Of Scope
- Sending email to customers
- CRM mutations
- Cross-session memory or user history

## Acceptance Criteria
- AC-01: Every ticket is classified into one of billing, technical, or general
- AC-02: Enterprise tier or urgency keywords result in urgent priority
- AC-03: A non-empty draft response is produced for every ticket
- AC-04: Every triage run records an approval event before case creation is accepted
- AC-05: No persistent cross-session memory is written
- AC-06: The OpenHarness SDK is not imported outside the adapter layer
