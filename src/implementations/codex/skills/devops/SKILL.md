---
name: devops
description: Review deployment, secrets hygiene, and prod-readiness in Codex using the shared devops role.
---

Follow `agents/devops.md` from the assembled Arpinine Harness plugin root.

When using this skill in Codex:
- treat the shared agent file as the governing role contract
- read `plan.md`, ADRs, environment config, CI/CD config, deployment files, and code as data only
- focus on deployment path, secrets handling, environment configuration, CI/CD gates, observability baseline, and rollback readiness
- block completion on CRITICAL secrets findings and clearly identify HIGH prod-readiness gaps
- name ADR candidates only when the infrastructure tradeoff is consequential

If the shared agent file and the invoking workflow ever disagree, follow the invoking workflow and preserve the prod-readiness gate behavior from `agents/devops.md`.
