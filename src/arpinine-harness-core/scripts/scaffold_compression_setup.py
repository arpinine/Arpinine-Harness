#!/usr/bin/env python3
"""
scaffold_compression_setup.py — idempotent scaffolder for the context-compression
provider layer.

Copies the provider templates into `<target>/compression/`:
  - context-compression-provider-template.py  -> context_compression_provider.py  (interface, always)
  - noop-context-compression-provider-template.py -> noop_provider.py              (noop, always)
  - headroom-context-compression-provider-template.py -> headroom_provider.py      (default, only if the template exists — lands in TASK-002)

Idempotent: existing destination files are skipped and never overwritten.

Governs: specs/011-context-compression-governance (TASK-005).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

_TEMPLATES_DIR = pathlib.Path(__file__).resolve().parents[1] / "templates"

# (template filename, destination filename, required)
_PROVIDERS = (
    ("context-compression-provider-template.py", "context_compression_provider.py", True),
    ("compression-security-template.py", "security.py", True),
    ("host-wiring-template.py", "host_wiring.py", True),
    ("noop-context-compression-provider-template.py", "noop_provider.py", True),
    # headroom default provider imports the headroom SDK at module top, so it is
    # NOT imported by __init__ (kept lazy); the disabled/noop path stays import-safe
    # without headroom installed.
    ("headroom-context-compression-provider-template.py", "headroom_provider.py", False),
)

# Replaces the dev-only path-loader block in the noop template with a package
# import so the scaffolded provider set shares one interface module identity,
# independent of import order (a file-path loader cannot guarantee that).
_SCAFFOLD_REPLACE_RE = re.compile(
    r"# === arpinine:scaffold-replace-start.*?# === arpinine:scaffold-replace-end ===",
    re.DOTALL,
)
_PACKAGE_IMPORT = (
    "from .context_compression_provider import CompressionEndpoint"
)
_HOST_WIRING_REPLACE_RE = re.compile(
    r"# === arpinine:host-wiring-replace-start.*?# === arpinine:host-wiring-replace-end ===",
    re.DOTALL,
)
_HOST_WIRING_PACKAGE_IMPORT = (
    "from .context_compression_provider import CompressionError"
)

_INIT_CONTENTS = (
    '"""Context-compression provider package (scaffolded).\n\n'
    "Consume providers through this package (e.g. `from context_compression.noop_provider\n"
    "import NoopContextCompressionProvider`). Do not load the modules by file path;\n"
    "package imports keep a single ContextCompressionProvider interface identity.\n\n"
    "Package name is `context_compression` (NOT `compression`) to avoid shadowing\n"
    "the Python 3.14+ stdlib `compression` package.\n"
    '"""\n'
    "from .context_compression_provider import (\n"
    "    CompressionEndpoint,\n"
    "    CompressionError,\n"
    "    ContextCompressionProvider,\n"
    ")\n"
    "from .noop_provider import NoopContextCompressionProvider\n"
    "from .host_wiring import (\n"
    "    PASSTHROUGH_FALLBACK_EVENT,\n"
    "    compression_session,\n"
    "    emit_passthrough_fallback,\n"
    "    host_env,\n"
    "    supported_hosts,\n"
    ")\n\n"
    '__all__ = [\n'
    '    "CompressionEndpoint",\n'
    '    "CompressionError",\n'
    '    "ContextCompressionProvider",\n'
    '    "NoopContextCompressionProvider",\n'
    '    "PASSTHROUGH_FALLBACK_EVENT",\n'
    '    "compression_session",\n'
    '    "emit_passthrough_fallback",\n'
    '    "host_env",\n'
    '    "supported_hosts",\n'
    "]\n"
)


def _render_dest(template_name: str, src_text: str) -> str:
    """Transform template text into its scaffolded form."""
    if template_name == "noop-context-compression-provider-template.py":
        return _SCAFFOLD_REPLACE_RE.sub(_PACKAGE_IMPORT, src_text)
    if template_name == "host-wiring-template.py":
        return _HOST_WIRING_REPLACE_RE.sub(_HOST_WIRING_PACKAGE_IMPORT, src_text)
    return src_text


# Package name deliberately NOT "compression" — that shadows the Python 3.14+
# stdlib `compression` package. "context_compression" matches the domain term.
PACKAGE_NAME = "context_compression"


def scaffold(target: pathlib.Path | str, templates_dir: pathlib.Path | None = None) -> dict:
    target = pathlib.Path(target)
    templates = pathlib.Path(templates_dir) if templates_dir else _TEMPLATES_DIR
    comp = target / PACKAGE_NAME
    comp.mkdir(parents=True, exist_ok=True)

    scaffolded: list[str] = []
    skipped: list[str] = []
    missing_templates: list[str] = []

    for template_name, dest_name, required in _PROVIDERS:
        src = templates / template_name
        if not src.exists():
            if required:
                missing_templates.append(template_name)
            continue
        dest = comp / dest_name
        if dest.exists():
            skipped.append(str(dest))
            continue
        dest.write_text(_render_dest(template_name, src.read_text()))
        scaffolded.append(str(dest))

    # Make the provider set an importable package so consumers use the import
    # system (single interface identity) rather than ad-hoc file-path loading.
    init_path = comp / "__init__.py"
    if init_path.exists():
        skipped.append(str(init_path))
    else:
        init_path.write_text(_INIT_CONTENTS)
        scaffolded.append(str(init_path))

    status = "error" if missing_templates else "ok"
    return {
        "status": status,
        "target": str(comp),
        "scaffolded": scaffolded,
        "skipped": skipped,
        "missing_templates": missing_templates,
    }


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Scaffold the compression provider layer.")
    parser.add_argument("--target-dir", default=".", help="directory to scaffold into")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    report = scaffold(pathlib.Path(args.target_dir))
    if args.json:
        print(json.dumps(report))
    else:
        print(f"status={report['status']} target={report['target']}")
        for p in report["scaffolded"]:
            print(f"  scaffolded {p}")
        for p in report["skipped"]:
            print(f"  skipped (exists) {p}")
        for t in report["missing_templates"]:
            print(f"  MISSING TEMPLATE {t}")
    return 1 if report["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
