#!/usr/bin/env python3
"""Scaffold a project directory structure from an archetype template."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys

from archetype_support import archetypes_dir as shared_archetypes_dir
from archetype_support import list_archetypes as shared_list_archetypes
from archetype_support import load_manifest as shared_load_manifest
from archetype_support import write_metadata


IGNORED_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".specify",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}
SOURCE_DIR_NAMES = {"src", "lib", "app", "pkg", "services", "backend", "frontend"}
MANIFEST_FILES = {
    "pyproject.toml",
    "package.json",
    "cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "requirements.txt",
}
SOURCE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java"}
TOP_LEVEL_ALLOWLIST = {
    "readme",
    "readme.md",
    "license",
    "license.md",
    "license.txt",
    ".gitignore",
    ".editorconfig",
    ".gitattributes",
    ".env.example",
    ".env.sample",
    ".python-version",
}


def _archetypes_dir(script_dir: pathlib.Path) -> pathlib.Path:
    return shared_archetypes_dir(script_dir)


def _list_archetypes(archetypes_dir: pathlib.Path) -> list[str]:
    return shared_list_archetypes(archetypes_dir)


def _load_manifest(archetype_dir: pathlib.Path) -> dict:
    try:
        return shared_load_manifest(archetype_dir.parent, archetype_dir.name)
    except FileNotFoundError:
        print(f"ERROR: Missing manifest.json in {archetype_dir}", file=sys.stderr)
        sys.exit(1)


def _iter_project_paths(target_dir: pathlib.Path) -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for path in target_dir.rglob("*"):
        rel_parts = path.relative_to(target_dir).parts
        if any(part in IGNORED_DIR_NAMES for part in rel_parts):
            continue
        paths.append(path)
    return paths


def project_looks_nonempty(target_dir: pathlib.Path) -> tuple[bool, str]:
    top_level_entries = [path for path in target_dir.iterdir() if path.name not in IGNORED_DIR_NAMES]
    for entry in top_level_entries:
        lower_name = entry.name.lower()
        if lower_name.startswith(".") and lower_name not in TOP_LEVEL_ALLOWLIST:
            return True, f"top-level file present: {entry.name}"
        if entry.is_dir() and entry.name not in {"docs", ".github", ".gitlab", ".vscode"}:
            return True, f"top-level directory present: {entry.name}/"
        if entry.is_file() and lower_name not in TOP_LEVEL_ALLOWLIST:
            return True, f"top-level file present: {entry.name}"

    for path in _iter_project_paths(target_dir):
        if path.is_dir() and path.name.lower() in SOURCE_DIR_NAMES:
            return True, f"source directory present: {path.relative_to(target_dir).as_posix()}/"
        if path.is_file() and path.name.lower() in MANIFEST_FILES:
            return True, f"manifest file present: {path.relative_to(target_dir).as_posix()}"
        if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS:
            return True, f"source file present: {path.relative_to(target_dir).as_posix()}"

    return False, ""


def scaffold(archetype_name: str, target_dir: pathlib.Path, archetypes_dir: pathlib.Path) -> int:
    archetype_dir = archetypes_dir / archetype_name
    if not archetype_dir.exists():
        available = _list_archetypes(archetypes_dir)
        print(f"ERROR: Archetype '{archetype_name}' not found.", file=sys.stderr)
        print(f"Available: {', '.join(available)}", file=sys.stderr)
        return 1

    manifest = _load_manifest(archetype_dir)
    created_dirs: list[str] = []
    created_files: list[str] = []
    skipped: list[str] = []

    for rel_dir in manifest.get("directories", []):
        dir_path = target_dir / rel_dir
        if dir_path.exists():
            skipped.append(rel_dir + "/")
            continue
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / ".gitkeep").touch()
        created_dirs.append(rel_dir)

    for rel_file in manifest.get("template_files", []):
        src_file = archetype_dir / rel_file
        dst_file = target_dir / rel_file
        if not src_file.exists():
            print(f"WARNING: Template file {rel_file} missing in archetype, skipping.", file=sys.stderr)
            continue
        if dst_file.exists():
            skipped.append(rel_file)
            continue
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        created_files.append(rel_file)

    print(f"Archetype:   {manifest['name']}")
    print(f"Description: {manifest.get('description', '')}")
    print(f"Target:      {target_dir}")
    if created_dirs:
        print(f"\nDirectories ({len(created_dirs)}):")
        for d in created_dirs:
            print(f"  + {d}/")
    if created_files:
        print(f"\nFiles ({len(created_files)}):")
        for f in created_files:
            print(f"  + {f}")
    if skipped:
        print(f"\nSkipped (already exist): {', '.join(skipped)}")
    metadata = write_metadata(target_dir, archetype_name)
    print(f"\nArchetype metadata: {metadata.relative_to(target_dir)}")
    return 0


def main() -> int:
    script_dir = pathlib.Path(__file__).parent
    archetypes_dir = _archetypes_dir(script_dir)

    parser = argparse.ArgumentParser(description="Scaffold project structure from archetype.")
    parser.add_argument("archetype", nargs="?", help="Archetype name (omit to list available)")
    parser.add_argument("--list", action="store_true", help="List available archetypes and exit")
    parser.add_argument("--target-dir", default=".", help="Target project directory (default: cwd)")
    parser.add_argument(
        "--skip-if-nonempty",
        action="store_true",
        help="Skip scaffolding when the target already looks like an existing project",
    )
    parser.add_argument("--force", action="store_true", help="Scaffold even when the target looks non-empty")
    args = parser.parse_args()

    if args.list or not args.archetype:
        available = _list_archetypes(archetypes_dir)
        if not available:
            print("No archetypes found.", file=sys.stderr)
            return 1
        print("Available archetypes:")
        for name in available:
            manifest_path = archetypes_dir / name / "manifest.json"
            desc = ""
            if manifest_path.exists():
                with open(manifest_path) as f:
                    desc = json.load(f).get("description", "")
            print(f"  {name:<22} {desc}")
        return 0

    target_dir = pathlib.Path(args.target_dir).resolve()
    nonempty, reason = project_looks_nonempty(target_dir)
    if nonempty and not args.force:
        if args.skip_if_nonempty:
            print(f"Skipping scaffold: target already looks non-empty ({reason}).")
            return 0
        print(
            "Refusing to scaffold into a non-empty target without --force "
            f"({reason}).",
            file=sys.stderr,
        )
        return 2

    return scaffold(args.archetype, target_dir, archetypes_dir)


if __name__ == "__main__":
    sys.exit(main())
