#!/usr/bin/env python3
"""
check_compression_setup.py — enforced security/boundary checks for context
compression. Gated by the constitution toggle: when compression is disabled
there is nothing to enforce.

Checks (HIGH findings block; ADR-0014 / ADR-0016 / ADR-0018):
  - CCR store path safety: not inside the git worktree, not under a cloud-sync
    prefix; directory permissions 700.
  - headroom import boundary: `headroom`/`headroom_ai` imports only in the
    designated default-provider module.
  - headroom pin: installed version+hash match the pinned values.
  - no full-payload/debug body logging configured.

The check functions are pure so they can be unit-tested without an installed
headroom or a live proxy. `run_checks()` wires them together and is toggle-gated.

Governs: specs/011-context-compression-governance (TASK-005).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import stat
import sys

# compression_config lives alongside this script.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
try:
    from compression_config import read_compression_enabled
except Exception:  # pragma: no cover - import guard
    read_compression_enabled = None  # type: ignore[assignment]


CLOUD_SYNC_RELATIVE_PREFIXES = (
    "Library/Mobile Documents",
    "Dropbox",
    "OneDrive",
    "Google Drive",
    "Documents",
    "Desktop",
)

_HEADROOM_IMPORT_RE = re.compile(
    r"^\s*(?:import\s+headroom(?:_ai)?\b|from\s+headroom(?:_ai)?\b)", re.MULTILINE
)

_FULL_PAYLOAD_LOG_KEYS = ("log_full_payload", "debug_log_bodies", "log_request_bodies")


def _finding(severity: str, code: str, message: str, **extra) -> dict:
    f = {"severity": severity, "code": code, "message": message}
    f.update(extra)
    return f


def _is_relative_to(child: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False


def check_ccr_store_path(
    store: pathlib.Path,
    repo_root: pathlib.Path,
    home: pathlib.Path,
) -> dict | None:
    """ADR-0018: CCR store must not be in the worktree or a cloud-sync path."""
    store = pathlib.Path(store)
    if _is_relative_to(store, pathlib.Path(repo_root)):
        return _finding(
            "HIGH",
            "ccr-store-in-worktree",
            f"CCR store {store} is inside the git worktree; governed originals could be committed.",
            path=str(store),
        )
    for rel in CLOUD_SYNC_RELATIVE_PREFIXES:
        if _is_relative_to(store, pathlib.Path(home) / rel):
            return _finding(
                "HIGH",
                "ccr-store-cloud-synced",
                f"CCR store {store} is under a cloud-sync path ({rel}); governed content could leave the machine.",
                path=str(store),
            )
    return None


def check_store_permissions(store: pathlib.Path) -> dict | None:
    """
    ADR-0018: store directory must be 700 and every stored-original file 600
    (no group/other access). A world/group-readable file inside a 700 dir is
    exactly the leak this control must catch, so files are walked too.
    """
    store = pathlib.Path(store)
    if not store.exists():
        return None
    dir_mode = stat.S_IMODE(store.stat().st_mode)
    if dir_mode & 0o077:
        return _finding(
            "HIGH",
            "ccr-store-permissions",
            f"CCR store {store} has mode {oct(dir_mode)}; require 700 (no group/other access).",
            path=str(store),
            mode=oct(dir_mode),
        )
    for child in sorted(store.rglob("*")):
        child_mode = stat.S_IMODE(child.stat().st_mode)
        if child.is_dir():
            if child_mode & 0o077:
                return _finding(
                    "HIGH",
                    "ccr-store-permissions",
                    f"CCR store subdirectory {child} has mode {oct(child_mode)}; require 700.",
                    path=str(child),
                    mode=oct(child_mode),
                )
        elif child_mode & 0o077:
            return _finding(
                "HIGH",
                "ccr-store-file-permissions",
                f"CCR original {child} has mode {oct(child_mode)}; require 600 (no group/other access).",
                path=str(child),
                mode=oct(child_mode),
            )
    return None


def check_headroom_import_boundary(
    root: pathlib.Path,
    allowed_module: pathlib.Path,
) -> list[dict]:
    """ADR-0014: headroom imports only in the designated default-provider module."""
    root = pathlib.Path(root)
    allowed = pathlib.Path(allowed_module).resolve()
    findings: list[dict] = []
    for py in sorted(root.rglob("*.py")):
        if py.resolve() == allowed:
            continue
        if _HEADROOM_IMPORT_RE.search(py.read_text(encoding="utf-8", errors="ignore")):
            findings.append(
                _finding(
                    "HIGH",
                    "headroom-import-boundary",
                    f"headroom imported outside the default-provider module: {py}",
                    file=str(py),
                )
            )
    return findings


def check_headroom_pin(
    installed_version: str | None,
    installed_hash: str | None,
    pinned_version: str,
    pinned_hash: str,
) -> dict | None:
    """ADR-0014: installed headroom must match the pinned version + hash."""
    if installed_version is None:
        return _finding(
            "HIGH",
            "headroom-not-installed",
            f"compression enabled but headroom is not installed (pinned {pinned_version}).",
        )
    if installed_version != pinned_version or installed_hash != pinned_hash:
        return _finding(
            "HIGH",
            "headroom-pin-mismatch",
            f"installed headroom {installed_version}/{installed_hash} != pinned {pinned_version}/{pinned_hash}.",
        )
    return None


def check_no_full_payload_logging(logging_config: dict) -> dict | None:
    """ADR-0014 / Security: full-payload/debug body logging must be disabled."""
    for key in _FULL_PAYLOAD_LOG_KEYS:
        if logging_config.get(key):
            return _finding(
                "HIGH",
                "full-payload-logging",
                f"full-payload logging flag '{key}' is enabled; prohibited for the compression proxy.",
                key=key,
            )
    return None


DEFAULT_CCR_STORE = pathlib.Path.home() / ".arpinine" / "ccr-store"
DEFAULT_PINNED_VERSION = "0.27.0"
DEFAULT_PINNED_HASH = "<pinned-sha256>"


def run_checks(
    repo_root: pathlib.Path | str,
    *,
    store_path: pathlib.Path | str | None = None,
    provider_root: pathlib.Path | str | None = None,
    logging_config: dict | None = None,
    headroom: dict | None = None,
    home: pathlib.Path | None = None,
) -> dict:
    """
    Toggle-gated aggregate that actually invokes every enforced check.

    When compression is disabled, returns ok with no findings. When enabled,
    runs: CCR store path safety + permissions, headroom import-boundary scan,
    full-payload logging, and headroom pin.

    Inputs default to ADR-0018 conventions so the security controls run even
    before the headroom provider config lands:
      - store_path defaults to ~/.arpinine/ccr-store
      - provider_root defaults to <repo>/compression (scanned only if present)
      - logging_config defaults to {} (clean)
      - headroom: {version, hash, pinned_version, pinned_hash}; None => not
        installed, which is itself a HIGH finding while enabled.
    """
    repo = pathlib.Path(repo_root)
    enabled = bool(read_compression_enabled and read_compression_enabled(repo))
    if not enabled:
        return {"status": "ok", "compression_enabled": False, "findings": []}

    home = pathlib.Path(home) if home else pathlib.Path.home()
    store = pathlib.Path(store_path) if store_path else DEFAULT_CCR_STORE
    proot = pathlib.Path(provider_root) if provider_root else (repo / "context_compression")

    findings: list[dict] = []

    findings.append(check_ccr_store_path(store, repo, home))
    findings.append(check_store_permissions(store))

    if proot.exists():
        findings.extend(
            check_headroom_import_boundary(proot, proot / "headroom_provider.py")
        )

    findings.append(check_no_full_payload_logging(logging_config or {}))

    if headroom is None:
        findings.append(
            check_headroom_pin(
                installed_version=None,
                installed_hash=None,
                pinned_version=DEFAULT_PINNED_VERSION,
                pinned_hash=DEFAULT_PINNED_HASH,
            )
        )
    else:
        findings.append(
            check_headroom_pin(
                installed_version=headroom.get("version"),
                installed_hash=headroom.get("hash"),
                pinned_version=headroom.get("pinned_version", DEFAULT_PINNED_VERSION),
                pinned_hash=headroom.get("pinned_hash", DEFAULT_PINNED_HASH),
            )
        )

    findings = [f for f in findings if f]
    status = "high" if any(f["severity"] == "HIGH" for f in findings) else "ok"
    return {"status": status, "compression_enabled": True, "findings": findings}


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check compression setup.")
    parser.add_argument("--repo", default=".", help="project root")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    report = run_checks(pathlib.Path(args.repo))
    if args.json:
        print(json.dumps(report))
    else:
        print(f"compression_enabled={report['compression_enabled']} status={report['status']}")
        for f in report["findings"]:
            print(f"  [{f['severity']}] {f['code']}: {f['message']}")
    # Block (non-zero) on any HIGH finding.
    return 1 if report["status"] == "high" else 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
