---
governs: specs/004-ain-readiness-gates
supersedes: ~
status: Accepted
date: 2026-05-04
covers:
  - decision:004-ain-readiness-gates:machine-readable-ain-source-of-truth
---

# ADR-0010: Machine-readable AIN fields in spec.md as the gating source of truth

## Status
Accepted

## Context
AIN (AI Nativity) readiness gates block implementation-path edits until a spec declares the required level of AI integration readiness. The gate logic must parse spec state to determine readiness. Two parsing approaches are possible: extracting state from prose sections (brittle, requires model interpretation), or reading from machine-readable structured fields in the spec file.

Prose-only parsing depends on consistent natural-language phrasing across all specs. Any paraphrase of a required statement causes a false negative (gate blocks when it should pass) or false positive (gate passes when it should block). Either failure mode erodes trust in the enforcement system.

AIN readiness is a long-term format commitment: all existing specs must declare AIN fields, all future specs must include them from creation, and all enforcement scripts must parse the same format. Changing the format after adoption requires migrating all specs.

## Decision
AIN readiness state is declared in structured fields within `spec.md`. The `at-new` and spec templates include AIN field scaffolding. Enforcement scripts (`check-architecture-readiness.sh` and the shared validation layer) parse AIN fields directly — no prose interpretation.

The AIN field schema is defined in `templates/schemas/spec-schema.yaml` and is the authoritative contract for all parsers. Any change to the schema is a breaking change and requires updating all existing specs.

## Consequences
- Positive: Gate behavior is deterministic — same spec content always produces the same gate result.
- Positive: Scripts are testable with spec fixtures without model involvement.
- Positive: AIN declarations are visible in PR review, making readiness state a code-reviewable artifact.
- Negative: Spec authors must explicitly populate AIN fields; a spec missing fields fails the gate even if the intent is clear from prose.
- Negative: Changing the AIN field schema is a migration that touches every spec in the repository.
- Negative: The schema must be kept synchronized with templates, validation scripts, and status reporting — three consumers that can drift independently.

## Alternatives Considered
| Option | Rejected Because |
|--------|-----------------|
| Prose-only parsing (model-interpreted) | Non-deterministic; any paraphrase of a required statement breaks gate behavior |
| Separate AIN manifest file per spec | Fragmentation; the spec file is already the canonical source of truth for feature state |
| AIN state stored in ADR frontmatter | ADRs govern decisions, not feature readiness; mixing concerns adds confusion |
