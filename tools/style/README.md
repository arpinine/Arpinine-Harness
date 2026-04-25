# Style Standards

This directory is the canonical home for repository code-style standards.

All teams and plugin implementations must use these checked-in configs rather than
inventing assistant-local conventions.

## Layout

- `shared/.editorconfig`
- `python/pyproject.toml`
- `frontend/.prettierrc.json`
- `frontend/eslint.config.cjs`
- `java/checkstyle.xml`
- `rust/rustfmt.toml`

## Usage

- Python: `ruff check --config tools/style/python/pyproject.toml .`
- Python format: `ruff format --config tools/style/python/pyproject.toml .`
- Frontend format: `prettier --config tools/style/frontend/.prettierrc.json ...`
- Frontend lint: `eslint --config tools/style/frontend/eslint.config.cjs ...`
- Java style: `checkstyle -c tools/style/java/checkstyle.xml ...`
- Rust format: `rustfmt --config-path tools/style/rust/rustfmt.toml ...`

The shared style-governance hook treats these files as the approved repository
markers for language-specific style standards.
