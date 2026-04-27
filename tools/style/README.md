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
- `swift/.swift-format`
- `lua/stylua.toml`
- `cpp/.clang-format`
- `erlang/elvis.config`

## Usage

- Python: `ruff check --config tools/style/python/pyproject.toml .`
- Python format: `ruff format --config tools/style/python/pyproject.toml .`
- Frontend format: `prettier --config tools/style/frontend/.prettierrc.json ...`
- Frontend lint: `eslint --config tools/style/frontend/eslint.config.cjs ...`
- Java style: `checkstyle -c tools/style/java/checkstyle.xml ...`
- Rust format: `rustfmt --config-path tools/style/rust/rustfmt.toml ...`
- Swift format: `swift-format format --configuration tools/style/swift/.swift-format ...`
- Lua format: `stylua --config-path tools/style/lua/stylua.toml ...`
- C / Objective-C format: `clang-format -style=file:tools/style/cpp/.clang-format ...`
- Erlang lint/style: `elvis rock` using `tools/style/erlang/elvis.config`

The shared style-governance hook treats these files as the approved repository
markers for language-specific style standards.
