# State Inspector Contract

The state inspector produces a normalized JSON object describing the current Arpinine Harness governance state of a repository. It is consumed by the `/at` facade to drive routing decisions.

The inspector computes **facts only**. It does not produce recommendations. All interpretation of the output belongs to the routing policy.

---

## Invocation

```bash
python3 scripts/inspect_state.py [--repo <path>] [--indent <n>]
```

- `--repo`: absolute or relative path to the project root; auto-detected from CWD if omitted
- `--indent`: JSON indent width (default: 2; use 0 for compact output)

Output is written to stdout as a single JSON object. Exit code is always 0; errors are reported inside `warnings`.

---

## Output Schema

### Top-level fields

| Field | Type | Meaning | Source of truth | Empty value |
|-------|------|---------|-----------------|-------------|
| `repo_root` | `string \| null` | Absolute path to the detected project root | First ancestor with `.specify/` or `.git/` | `null` if not found |
| `governed` | `bool` | `.specify/` directory exists and is a directory | Filesystem | `false` |
| `has_specs` | `bool` | At least one spec directory with `spec.md` exists | `.specify/specs/*/spec.md` | `false` |
| `spec_count` | `int` | Number of spec directories containing `spec.md` | `.specify/specs/` | `0` |
| `active_map_sessions` | `string[]` | Slugs of map sessions in an in-progress state | `.specify/map/*/map.md` frontmatter `state:` | `[]` |
| `completed_map_sessions` | `string[]` | Slugs of map sessions with `state: completed` | `.specify/map/*/map.md` frontmatter `state:` | `[]` |
| `active_discovery_sessions` | `string[]` | Slugs of discovery sessions in an in-progress state | `.specify/discovery/*/discovery.md` frontmatter `state:` | `[]` |
| `completed_discovery_sessions` | `string[]` | Slugs of discovery sessions with `state: promoted-to-spec` | `.specify/discovery/*/discovery.md` frontmatter `state:` | `[]` |
| `specs_without_plan` | `string[]` | Spec slugs that have `spec.md` but no `plan.md` | `.specify/specs/<slug>/` | `[]` |
| `specs_with_plan` | `string[]` | Spec slugs that have both `spec.md` and `plan.md` | `.specify/specs/<slug>/` | `[]` |
| `specs_with_open_drift` | `string[]` | Spec slugs with canonical drift reports containing unresolved markers | `.specify/specs/<slug>/drift-report.md` | `[]` |
| `eval_gaps` | `string[]` | Spec slugs with `plan.md` but no eval plan artifact | `.specify/specs/<slug>/`, `.specify/evals/<slug>/eval-plan.md` | `[]` |
| `observation_gaps` | `string[]` | Spec slugs with an eval plan but no latest observation artifact | `.specify/evals/<slug>/eval-plan.md`, `.specify/observations/<slug>/latest-observation.md` | `[]` |
| `has_existing_codebase` | `bool` | Source files or project markers exist outside `.specify/` | Filesystem scan (see derivation rules) | `false` |
| `bootstrap_candidate` | `bool` | Existing codebase present but no governed specs yet | Derived (see below) | `false` |
| `incomplete_state` | `bool` | Any field could not be reliably determined | Set by inspector on scan error | `false` |
| `warnings` | `string[]` | Human-readable notes about scan anomalies | Inspector runtime | `[]` |

---

## Derivation Rules

### `governed`
`true` if and only if `.specify/` exists as a directory at the detected repo root.

### `active_map_sessions`
States considered active: `needs-clarification`, `backlog-ready-awaiting-selection`, `promoting-features`.
States excluded: `completed`, `abandoned`.
Source: `frontmatter state:` field in `.specify/map/<slug>/map.md`.

### `completed_map_sessions`
State: `completed` only.
`abandoned` sessions are excluded from all lists — they are audit artifacts, not actionable state.

### `active_discovery_sessions`
States considered active: `needs-clarification`, `spec-ready-awaiting-confirmation`.
States excluded: `promoted-to-spec`, `abandoned`.
Source: `frontmatter state:` field in `.specify/discovery/<slug>/discovery.md`.

### `completed_discovery_sessions`
State: `promoted-to-spec` only.

### `specs_with_open_drift`
A spec slug is included if `.specify/specs/<slug>/drift-report.md` exists and contains unresolved markers such as:
- `CRITICAL unresolved`
- `Remaining:` with a non-zero count
- `<n> OPEN` with `n > 0`

This is a heuristic signal, not authoritative. The routing policy must treat it as advisory. Mere mention of the word `drift` is not sufficient.

### `has_existing_codebase`
`true` if any of the following are found outside `.specify/`, `.git/`, `node_modules/`, `__pycache__/`, `.venv/`, `venv/`, `dist/`, `build/`:
- A file with extension: `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.go`, `.rs`, `.java`, `.rb`, `.php`, `.cs`, `.cpp`, `.c`
- A project marker at repo root: `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile`, `composer.json`

### `bootstrap_candidate`
`true` if `has_existing_codebase` is `true` AND (`governed` is `false` OR `spec_count` is `0`).

### `incomplete_state`
Set to `true` if any filesystem read error occurs during the scan, including map/discovery session scans, spec/eval/observation scans, or codebase inspection. The affected fields are set to their empty value. A warning is added describing which scan failed.

---

## Stability Guarantees

- Field names are stable. New fields may be added in future versions but existing fields will not be renamed or removed without a version bump.
- All list fields return `[]` (never `null`) when empty.
- All boolean fields return `false` (never `null`) when the source cannot be determined.
- `repo_root` and `warnings` are the only fields that may be `null` or contain strings describing internal state.
- The inspector is safe to run repeatedly. It is read-only and makes no mutations.

---

## Example Output

### Ungoverned repo with existing codebase

```json
{
  "repo_root": "/path/to/project",
  "governed": false,
  "has_specs": false,
  "spec_count": 0,
  "active_map_sessions": [],
  "completed_map_sessions": [],
  "active_discovery_sessions": [],
  "completed_discovery_sessions": [],
  "specs_without_plan": [],
  "specs_with_plan": [],
  "specs_with_open_drift": [],
  "eval_gaps": [],
  "observation_gaps": [],
  "has_existing_codebase": true,
  "bootstrap_candidate": true,
  "incomplete_state": false,
  "warnings": []
}
```

### Governed repo, active map session, two specs one missing plan

```json
{
  "repo_root": "/path/to/project",
  "governed": true,
  "has_specs": true,
  "spec_count": 2,
  "active_map_sessions": ["support-assistant-20260520"],
  "completed_map_sessions": [],
  "active_discovery_sessions": [],
  "completed_discovery_sessions": ["onboarding-20260510"],
  "specs_without_plan": ["001-auth-login"],
  "specs_with_plan": ["002-payment-flow"],
  "specs_with_open_drift": [],
  "eval_gaps": ["002-payment-flow"],
  "observation_gaps": [],
  "has_existing_codebase": true,
  "bootstrap_candidate": false,
  "incomplete_state": false,
  "warnings": []
}
```
