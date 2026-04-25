# Project Constitution

## Principles
1. spec.md = WHAT/WHY (Product)
2. plan.md = HOW (Engineering)
3. Tests before code
4. Measurable acceptance criteria
5. Security by default
6. Modular boundaries before implementation
7. Business rules isolated from framework and infrastructure concerns
8. Repository-defined, language-specific code style standards are mandatory for every team and plugin

## Enforcement
- Code style standards MUST be defined by checked-in repository tooling or configuration for each language used in implementation files.
- Claude, Codex, and any future implementation team MUST follow the same repository-defined style standards for a given language.
- Hooks and automated validation SHOULD block implementation-path edits when a language is used without a declared repository style standard.
