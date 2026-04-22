# Spec-Kit Automation Plugin

Bridges product requirements and AI-driven development by layering ADR tracking and drift detection on top of spec-kit's native specification workflow.

## What It Does

| Concern | Owner |
|---------|-------|
| Spec creation, plan, tasks, constitution | **spec-kit** (native) |
| Architecture Decision Records | **This plugin** |
| Spec-code drift detection | **This plugin** |
| ADR-linkage enforcement | **This plugin** |

## Commands

| Command | Purpose |
|---------|---------|
| `/spec-init` | Initialize spec-kit + ADR directory structure |
| `/spec-new` | Create spec (delegates to spec-kit, validates constitution) |
| `/spec-plan` | Generate plan and tasks (delegates to spec-kit) |
| `/spec-implement` | Execute with TDD enforcement (delegates to spec-kit) |
| `/spec-adr` | Create and manage Architecture Decision Records |
| `/spec-audit` | Detect spec-code drift; drive ADR resolution |
| `/spec-review` | Validate spec against constitution |

## Quick Example

```bash
# Initialize
/spec-init

# Product creates spec (spec-kit handles quality checks)
/spec-new "User login with email and password"

# Engineer creates plan; plugin suggests ADRs for each tech decision
/spec-plan .specify/specs/001-user-login/

# Create ADR for an architectural decision
/spec-adr new "Use PostgreSQL for session storage"

# Implement with TDD (spec-kit enforces test-first)
/spec-implement .specify/specs/001-user-login/

# Detect drift — plugin links findings to ADRs
/spec-audit .specify/specs/001-user-login/
# CRITICAL  src/auth/login.py — rate limiting in code, absent from spec
# → Prompt: "Create ADR to document this decision? (yes/no)"
```

## How It Works

```
spec-kit: Product writes spec → Constitution validates → Engineer creates plan → AI implements (TDD)
Plugin:                                                  ↗ ADR tracks WHY    ↗ Drift detects gaps
```

Automatic hooks fire on every file write:
- **PreToolUse**: `check-constitution.sh` blocks tech details in spec.md and hardcoded secrets
- **PostToolUse**: `quick-drift-check.sh` flags spec references missing from disk

## ADR Lifecycle

```
Proposed → Accepted → Implemented → Superseded
                    ↘ Rejected
```

All ADRs live in `.specify/adr/` with a master `ADR-INDEX.md`.
Each ADR has a `governs:` field linking it to its spec.

## Who This Is For

| Role | Benefit |
|------|---------|
| Product Managers | Requirements tied to explicit decisions |
| Engineers | Documented WHY behind every tech choice |
| Tech Leads | Enforced ADR coverage for all critical drift |
| AI Agents | Structured specs + decisions to follow |

## Installation

```bash
# 1. Install spec-kit
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai claude

# 2. Install plugin
/plugin install spec-kit-automation-v1.0.0.zip

# 3. Initialize
/spec-init
```

## License

MIT
