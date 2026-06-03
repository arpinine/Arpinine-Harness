#!/usr/bin/env python3
"""Assess an existing codebase and recommend bootstrap governance artifacts."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone


CODE_ROOTS = ("src", "app", "lib", "services", "packages", "internal", "cmd", "server", "backend", "frontend")
CODE_EXTS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".swift": "swift",
}
MANIFESTS = {
    "package.json": "node-package",
    "pyproject.toml": "python-project",
    "requirements.txt": "python-requirements",
    "go.mod": "go-module",
    "Cargo.toml": "rust-crate",
    "pom.xml": "maven-project",
    "build.gradle": "gradle-project",
    "Dockerfile": "dockerfile",
    "docker-compose.yml": "docker-compose",
    "docker-compose.yaml": "docker-compose",
}
PRIMARY_MANIFESTS = {"package.json", "pyproject.toml", "go.mod", "Cargo.toml", "pom.xml", "build.gradle"}
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".specify",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".next",
    ".turbo",
    ".idea",
    ".vscode",
    # Ignore plugin packages by default to avoid scanning the harness/plugin implementation itself.
    "plugins",
}
MAX_COMPONENT_SAMPLES = 12
MAX_ENTRYPOINT_SAMPLES = 12
MAX_TEST_SAMPLES = 10
MAX_ENDPOINT_SAMPLES = 20
MAX_ADR_RECOMMENDATIONS = 5
MAX_RISKS = 5
MAX_OPEN_QUESTIONS = 5
SIGNAL_SCAN_MAX_FILES = 200
SIGNAL_SCAN_MAX_CHARS_PER_FILE = 4000
SIGNAL_SCAN_MAX_TOTAL_CHARS = 200_000
MAX_DOC_SAMPLES = 12
MAX_TEST_DESCRIPTIONS = 12
MONOREPO_MAX_DEPTH = 3
DOC_EXTS = {".md", ".rst", ".txt"}
ROUTE_PATTERNS = [
    re.compile(r"""@(get|post|put|delete|patch)\(\s*["']([^"']+)["']""", re.IGNORECASE),
    re.compile(r"""\b(?:app|router)\.(get|post|put|delete|patch)\(\s*["']([^"']+)["']""", re.IGNORECASE),
    re.compile(r"""@app\.route\(\s*["']([^"']+)["'][^)]*methods\s*=\s*\[([^\]]+)\]""", re.IGNORECASE),
]
OPENHARNESS_IMPORT_RE = re.compile(
    r"(@openharness/|from\s+openharness\b|import\s+openharness\b|require\([\"'][^\"']*openharness[^\"']*[\"']\))",
    re.IGNORECASE,
)
AGENTIC_HINT_RE = re.compile(r"\b(agent|assistant|llm|prompt|inference|retrieval|rag|harness|embedding|completion)\b", re.IGNORECASE)
AGENTIC_EXCLUSION_RE = re.compile(
    r"\b(django model|sqlalchemy model|view model|prompt for input|inference statistics|test harness|autocomplete|font embedding|binary embedding)\b",
    re.IGNORECASE,
)
TEST_NAME_PATTERNS = [
    re.compile(r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(", re.MULTILINE),
    re.compile(r"^\s*it\s*\(\s*[\"']([^\"']+)[\"']", re.MULTILINE),
    re.compile(r"^\s*test\s*\(\s*[\"']([^\"']+)[\"']", re.MULTILINE),
]
DOC_FILENAMES = {
    "README.md",
    "CHANGELOG.md",
    "CHANGELOG.txt",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "DESIGN.md",
    "OVERVIEW.md",
}
DATA_HINTS = {
    "postgres": re.compile(r"\b(postgres|postgresql|psycopg|sqlalchemy)\b", re.IGNORECASE),
    "mysql": re.compile(r"\b(mysql|pymysql)\b", re.IGNORECASE),
    "sqlite": re.compile(r"\b(sqlite)\b", re.IGNORECASE),
    "redis": re.compile(r"\b(redis)\b", re.IGNORECASE),
    "mongodb": re.compile(r"\b(mongo|mongodb)\b", re.IGNORECASE),
    "elasticsearch": re.compile(r"\b(elasticsearch)\b", re.IGNORECASE),
    "vector-store": re.compile(r"\b(pinecone|weaviate|chroma|faiss|vector)\b", re.IGNORECASE),
}
DEPLOY_HINTS = {
    "docker": re.compile(r"\b(docker|docker-compose)\b", re.IGNORECASE),
    "kubernetes": re.compile(r"\b(k8s|kubernetes|helm)\b", re.IGNORECASE),
    "terraform": re.compile(r"\b(terraform)\b", re.IGNORECASE),
    "github-actions": re.compile(r"\b(github/actions|workflow_dispatch|uses:\s*actions/)\b", re.IGNORECASE),
}


def find_project_root(start: pathlib.Path) -> pathlib.Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / ".specify").exists():
            return candidate
    for candidate in [current, *current.parents]:
        if (candidate / "Makefile").exists():
            return candidate
    return current


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return ""
    except Exception:
        return ""


def iter_files(root: pathlib.Path) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    try:
        children = sorted(root.iterdir(), key=lambda path: path.name)
    except Exception:
        return files
    for path in children:
        if path.name in IGNORE_DIRS:
            continue
        if path.is_symlink():
            continue
        if path.is_dir():
            files.extend(iter_files(path))
        elif path.is_file():
            files.append(path)
    return files


def next_spec_slug(repo: pathlib.Path) -> str:
    return next_spec_slug_for_target(repo, repo)


def next_spec_slug_for_target(repo: pathlib.Path, target: pathlib.Path) -> str:
    spec_root = repo / ".specify" / "specs"
    existing = [path.name for path in spec_root.iterdir()] if spec_root.is_dir() else []
    seq = len([name for name in existing if re.match(r"^\d{3}-", name)]) + 1
    if target == repo:
        slug_base = repo.name
    else:
        try:
            slug_base = "-".join(target.relative_to(repo).parts)
        except ValueError:
            slug_base = target.name
    slug_name = re.sub(r"[^a-z0-9]+", "-", slug_base.lower()).strip("-") or "existing-system"
    return f"{seq:03d}-{slug_name}-bootstrap"


def collect_languages(files: list[pathlib.Path], base: pathlib.Path) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for path in files:
        language = CODE_EXTS.get(path.suffix.lower())
        if language:
            counts[language] = counts.get(language, 0) + 1
    return [{"language": language, "file_count": counts[language]} for language in sorted(counts)]


def collect_manifests(files: list[pathlib.Path], base: pathlib.Path) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for path in files:
        kind = MANIFESTS.get(path.name)
        if kind:
            results.append({"path": path.relative_to(base).as_posix(), "kind": kind})
    return sorted(results, key=lambda item: item["path"])


def path_depth(path: pathlib.Path, base: pathlib.Path) -> int:
    return len(path.relative_to(base).parts)


def infer_components(files: list[pathlib.Path], base: pathlib.Path) -> list[str]:
    components: set[str] = set()
    for path in files:
        rel = path.relative_to(base)
        if not rel.parts:
            continue
        if rel.parts[0] in CODE_ROOTS and len(rel.parts) >= 2:
            if len(rel.parts) == 2:
                stem = path.stem.lower()
                for suffix in ("_service", "_handler", "_repo", "_model", "_controller", "_client"):
                    if stem.endswith(suffix):
                        components.add(f"{rel.parts[0]}/{stem[: -len(suffix)]}{suffix}")
                        break
                else:
                    components.add("/".join(rel.parts[:2]))
            else:
                components.add("/".join(rel.parts[:2]))
        elif len(rel.parts) == 1 and path.suffix.lower() in CODE_EXTS:
            components.add(rel.parts[0])
    return sorted(components)[:MAX_COMPONENT_SAMPLES]


def detect_tests(files: list[pathlib.Path], base: pathlib.Path) -> dict[str, object]:
    tests: list[str] = []
    descriptions: list[dict[str, str]] = []
    for path in files:
        rel = path.relative_to(base).as_posix()
        name = path.name.lower()
        if (
            "/tests/" in f"/{rel}"
            or name.startswith("test_")
            or name.endswith("_test.py")
            or name.endswith(".test.ts")
            or name.endswith(".spec.ts")
            or name.endswith(".test.js")
            or name.endswith(".spec.js")
            or name.endswith("_test.go")
        ):
            tests.append(rel)
            if len(descriptions) < MAX_TEST_DESCRIPTIONS:
                text = read_text(path)
                for pattern in TEST_NAME_PATTERNS:
                    for match in pattern.finditer(text):
                        descriptions.append({"path": rel, "name": match.group(1)})
                        if len(descriptions) >= MAX_TEST_DESCRIPTIONS:
                            break
                    if len(descriptions) >= MAX_TEST_DESCRIPTIONS:
                        break
    return {
        "present": bool(tests),
        "sample_paths": sorted(tests)[:MAX_TEST_SAMPLES],
        "descriptions": descriptions,
    }


def extract_endpoints(text: str) -> set[str]:
    endpoints: set[str] = set()
    for index, pattern in enumerate(ROUTE_PATTERNS):
        for match in pattern.finditer(text):
            if index < 2:
                method, route = match.groups()
                endpoints.add(f"{method.upper()} {route}")
            else:
                route, methods = match.groups()
                method_list = re.findall(r"['\"]([A-Z]+)['\"]", methods, re.IGNORECASE)
                for method in method_list:
                    endpoints.add(f"{method.upper()} {route}")
    return endpoints


def collect_endpoints(files: list[pathlib.Path], base: pathlib.Path) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    sample_result = iter_signal_texts(files, include=lambda path: path.suffix.lower() in CODE_EXTS, base=base)
    for rel_path, text in sample_result["samples"]:
        for endpoint in sorted(extract_endpoints(text)):
            results.append({"endpoint": endpoint, "path": rel_path})
            if len(results) >= MAX_ENDPOINT_SAMPLES:
                return results
    return results


def iter_signal_texts(
    files: list[pathlib.Path],
    include: callable,
    base: pathlib.Path,
) -> dict[str, object]:
    results: list[tuple[str, str]] = []
    total_chars = 0
    scanned_files = 0
    eligible_files = 0
    truncated = False
    for path in files:
        if not include(path):
            continue
        eligible_files += 1
        if scanned_files >= SIGNAL_SCAN_MAX_FILES or total_chars >= SIGNAL_SCAN_MAX_TOTAL_CHARS:
            truncated = True
            continue
        text = read_text(path)
        if not text:
            continue
        sample = text[:SIGNAL_SCAN_MAX_CHARS_PER_FILE]
        scanned_files += 1
        total_chars += len(sample)
        results.append((path.relative_to(base).as_posix(), sample))
    return {
        "samples": results,
        "eligible_files": eligible_files,
        "scanned_files": scanned_files,
        "total_chars": total_chars,
        "truncated": truncated,
    }


def detect_named_signals(patterns: dict[str, re.Pattern[str]], samples: list[tuple[str, str]]) -> list[str]:
    hits: list[str] = []
    for name, pattern in patterns.items():
        for rel_path, text in samples:
            if pattern.search(rel_path) or pattern.search(text):
                hits.append(name)
                break
    return sorted(hits)


def confidence_from_matches(high: bool, count: int) -> str:
    if high:
        return "high"
    if count >= 2:
        return "medium"
    if count == 1:
        return "low"
    return "none"


def agentic_keyword_matches(text: str) -> set[str]:
    matches: set[str] = set()
    for match in AGENTIC_HINT_RE.finditer(text):
        context = text[max(0, match.start() - 40) : match.end() + 40]
        if AGENTIC_EXCLUSION_RE.search(context):
            continue
        matches.add(match.group(0).lower())
    return matches


def detect_data_signals(files: list[pathlib.Path], base: pathlib.Path) -> list[str]:
    sample_result = iter_signal_texts(
        files,
        include=lambda path: path.suffix.lower() in CODE_EXTS or path.name in MANIFESTS,
        base=base,
    )
    return detect_named_signals(DATA_HINTS, sample_result["samples"])


def detect_deployment_signals(files: list[pathlib.Path], base: pathlib.Path) -> list[str]:
    sample_result = iter_signal_texts(
        files,
        include=lambda path: path.name in MANIFESTS or "workflow" in path.parts,
        base=base,
    )
    return detect_named_signals(DEPLOY_HINTS, sample_result["samples"])


def detect_agentic_signals(files: list[pathlib.Path], base: pathlib.Path) -> dict[str, object]:
    sample_result = iter_signal_texts(files, include=lambda path: path.suffix.lower() in CODE_EXTS, base=base)
    direct_openharness: list[str] = []
    hint_paths: list[str] = []
    keyword_hits = 0
    for rel, text in sample_result["samples"]:
        if OPENHARNESS_IMPORT_RE.search(text):
            direct_openharness.append(rel)
            continue
        if "/test" in f"/{rel}" or rel.endswith((".test.js", ".spec.js", ".test.ts", ".spec.ts", "_test.py", "_test.go")):
            continue
        matches = agentic_keyword_matches(text)
        if matches:
            hint_paths.append(rel)
            keyword_hits += len(matches)
    has_definitive_signal = bool(direct_openharness)
    present = has_definitive_signal or keyword_hits >= 2
    return {
        "present": present,
        "hint_paths": sorted(hint_paths)[:MAX_COMPONENT_SAMPLES],
        "openharness_paths": sorted(direct_openharness)[:MAX_COMPONENT_SAMPLES],
        "confidence": confidence_from_matches(has_definitive_signal, keyword_hits),
        "keyword_hit_count": keyword_hits,
        "scan": {
            "eligible_files": sample_result["eligible_files"],
            "scanned_files": sample_result["scanned_files"],
            "truncated": sample_result["truncated"],
        },
    }


def detect_entrypoints(files: list[pathlib.Path], base: pathlib.Path) -> list[str]:
    results: list[str] = []
    for path in files:
        rel = path.relative_to(base).as_posix()
        name = path.stem.lower()
        if name in {"main", "app", "server", "cli", "manage", "index"} and path.suffix.lower() in CODE_EXTS:
            results.append(rel)
        elif path.name in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
            results.append(rel)
    return sorted(dict.fromkeys(results))[:MAX_ENTRYPOINT_SAMPLES]


def infer_system_shape(endpoints: list[dict[str, str]], tests: dict[str, object], agentic: dict[str, object], manifests: list[dict[str, str]]) -> list[str]:
    shapes: list[str] = []
    manifest_kinds = {item["kind"] for item in manifests}
    if endpoints:
        shapes.append("api-service")
    if any(kind in {"node-package", "python-project", "go-module", "rust-crate", "maven-project", "gradle-project"} for kind in manifest_kinds):
        shapes.append("application-or-library")
    if agentic["present"]:
        shapes.append("agentic-or-ai-assisted-flow")
    if tests["present"]:
        shapes.append("tested-codebase")
    return shapes or ["general-codebase"]


def collect_doc_signals(files: list[pathlib.Path], base: pathlib.Path) -> list[dict[str, str]]:
    docs: list[dict[str, str]] = []
    for path in files:
        rel = path.relative_to(base)
        rel_posix = rel.as_posix()
        if path.name in DOC_FILENAMES or (rel.parts and rel.parts[0] == "docs" and path.suffix.lower() in DOC_EXTS):
            docs.append({"path": rel_posix, "kind": "doc"})
    return sorted(docs, key=lambda item: item["path"])[:MAX_DOC_SAMPLES]


def detect_monorepo_services(files: list[pathlib.Path], base: pathlib.Path) -> list[dict[str, str]]:
    services: list[dict[str, str]] = []
    for path in files:
        if path.name not in PRIMARY_MANIFESTS:
            continue
        depth = path_depth(path, base)
        if depth == 1 or depth > MONOREPO_MAX_DEPTH:
            continue
        services.append(
            {
                "path": path.relative_to(base).parent.as_posix() or ".",
                "manifest": path.name,
            }
        )
    return sorted(services, key=lambda item: item["path"])


def git_signals(target: pathlib.Path, enabled: bool) -> list[str]:
    if not enabled:
        return []
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-50"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except Exception:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()][:50]


def recommend_adrs(agentic: dict[str, object], endpoints: list[dict[str, str]], data_signals: list[str], deploy_signals: list[str], components: list[str]) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []
    if len(components) >= 3:
        recs.append(
            {
                "title": "Module boundary and dependency direction",
                "reason": "The codebase has multiple visible components and needs an explicit architectural seam map.",
            }
        )
    if endpoints:
        recs.append(
            {
                "title": "Public interface and API boundary contract",
                "reason": "HTTP routes were detected, so interface scope and versioning should be documented explicitly.",
            }
        )
    if data_signals:
        recs.append(
            {
                "title": "Data persistence and state ownership",
                "reason": f"Detected data/storage signals: {', '.join(data_signals)}.",
            }
        )
    if deploy_signals:
        recs.append(
            {
                "title": "Deployment topology and environment strategy",
                "reason": f"Detected deployment signals: {', '.join(deploy_signals)}.",
            }
        )
    if agentic["present"]:
        recs.append(
            {
                "title": "Harness boundary, tool permissions, and evaluation policy",
                "reason": "AI or agentic behavior was detected and needs a bounded runtime contract.",
            }
        )
    return recs[:MAX_ADR_RECOMMENDATIONS]


def collect_risks(tests: dict[str, object], agentic: dict[str, object], endpoints: list[dict[str, str]], data_signals: list[str]) -> list[str]:
    risks: list[str] = []
    if not tests["present"]:
        risks.append("No obvious automated test files were detected; reverse-engineered requirements may be hard to verify.")
    if agentic["openharness_paths"]:
        risks.append("OpenHarness imports were detected; confirm they are isolated behind an adapter before documenting the runtime contract.")
    if agentic["present"] and not endpoints:
        risks.append("Agentic behavior was detected without obvious external interfaces; clarify the user-visible workflow before writing the spec.")
    if len(data_signals) > 1:
        risks.append("Multiple persistence technologies were detected; confirm ownership boundaries before writing ADRs.")
    return risks[:MAX_RISKS]


def open_questions(agentic: dict[str, object], endpoints: list[dict[str, str]], tests: dict[str, object]) -> list[str]:
    questions = [
        "Which user-facing workflow or business capability should this bootstrap spec cover first?",
        "Which parts of the codebase are legacy, experimental, or explicitly out of scope for the first governed spec?",
    ]
    if endpoints:
        questions.append("Which routes or interfaces are considered public and release-bound versus internal-only?")
    if agentic["present"]:
        questions.append("Which AI or agent behaviors require human approval, bounded tools, or explicit evaluation gates?")
    if not tests["present"]:
        questions.append("What current evidence exists to validate behavior if automated tests are sparse or missing?")
    return questions[:MAX_OPEN_QUESTIONS]


def build_report(target: pathlib.Path, include_git_log: bool = False) -> dict[str, object]:
    repo = find_project_root(target)
    files = iter_files(target)
    code_files = [path for path in files if path.suffix.lower() in CODE_EXTS]
    languages = collect_languages(files, target)
    manifests = collect_manifests(files, target)
    components = infer_components(files, target)
    tests = detect_tests(files, target)
    docs = collect_doc_signals(files, target)
    endpoints = collect_endpoints(files, target)
    data_signals = detect_data_signals(files, target)
    deploy_signals = detect_deployment_signals(files, target)
    agentic = detect_agentic_signals(files, target)
    entrypoints = detect_entrypoints(files, target)
    monorepo_services = detect_monorepo_services(files, target)
    git_history = git_signals(target, include_git_log)
    adr_recommendations = recommend_adrs(agentic, endpoints, data_signals, deploy_signals, components)

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        assessed_path = target.relative_to(repo).as_posix() or "."
    except ValueError:
        assessed_path = target.name or "."

    return {
        "generated_at": generated_at,
        "repo_root": repo.as_posix(),
        "assessed_path": assessed_path,
        "summary": {
            "repo_name": target.name,
            "system_shape": infer_system_shape(endpoints, tests, agentic, manifests),
            "languages": [item["language"] for item in languages],
            "component_count": len(components),
            "endpoint_count": len(endpoints),
            "agentic": agentic["present"],
            "tests_present": tests["present"],
            "code_file_count": len(code_files),
            "monorepo": bool(monorepo_services),
        },
        "limits": {
            "component_samples": MAX_COMPONENT_SAMPLES,
            "entrypoint_samples": MAX_ENTRYPOINT_SAMPLES,
            "test_samples": MAX_TEST_SAMPLES,
            "endpoint_samples": MAX_ENDPOINT_SAMPLES,
            "adr_recommendations": MAX_ADR_RECOMMENDATIONS,
            "risk_samples": MAX_RISKS,
            "open_question_samples": MAX_OPEN_QUESTIONS,
            "signal_scan_max_files": SIGNAL_SCAN_MAX_FILES,
            "signal_scan_max_chars_per_file": SIGNAL_SCAN_MAX_CHARS_PER_FILE,
            "signal_scan_max_total_chars": SIGNAL_SCAN_MAX_TOTAL_CHARS,
            "scan_budget_scope": "per-detector",
        },
        "signals": {
            "languages": languages,
            "manifests": manifests,
            "components": components,
            "entrypoints": entrypoints,
            "tests": tests,
            "docs": docs,
            "endpoints": endpoints,
            "data_signals": data_signals,
            "deployment_signals": deploy_signals,
            "agentic": agentic,
            "monorepo_services": monorepo_services,
            "git_signals": git_history,
        },
        "artifact_recommendations": {
            "spec_slug": next_spec_slug_for_target(repo, target),
            "spec_title": f"{target.name.replace('-', ' ').replace('_', ' ').title()} bootstrap",
            "needs_eval_plan": bool(agentic["present"] or endpoints),
            "needs_harness_strategy": bool(agentic["present"]),
            "needs_deployment_strategy": bool(deploy_signals),
            "needs_data_pipeline_section": bool("vector-store" in data_signals or agentic["present"]),
            "recommended_adrs": adr_recommendations,
        },
        "risks": collect_risks(tests, agentic, endpoints, data_signals),
        "open_questions": open_questions(agentic, endpoints, tests),
    }


def render_markdown(report: dict[str, object]) -> str:
    summary = report["summary"]
    signals = report["signals"]
    recs = report["artifact_recommendations"]
    lines = [
        "# Bootstrap From Code Assessment",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Assessed path: `{report['assessed_path']}`",
        f"- Suggested spec slug: `{recs['spec_slug']}`",
        "",
        "## Summary",
        f"- Repo name: `{summary['repo_name']}`",
        f"- System shape: {', '.join(summary['system_shape'])}",
        f"- Languages: {', '.join(summary['languages']) or 'none detected'}",
        f"- Components detected: {summary['component_count']}",
        f"- Endpoints detected: {summary['endpoint_count']}",
        f"- Agentic signals detected: {'yes' if summary['agentic'] else 'no'}",
        f"- Tests detected: {'yes' if summary['tests_present'] else 'no'}",
        f"- Monorepo services detected: {'yes' if summary['monorepo'] else 'no'}",
        "",
        "## Structural Signals",
    ]

    if signals["components"]:
        lines.append(f"- Components: {', '.join(signals['components'])}")
    if signals["docs"]:
        lines.append(f"- Docs: {', '.join(item['path'] for item in signals['docs'])}")
    if signals["entrypoints"]:
        lines.append(f"- Entrypoints: {', '.join(signals['entrypoints'])}")
    if signals["data_signals"]:
        lines.append(f"- Data signals: {', '.join(signals['data_signals'])}")
    if signals["deployment_signals"]:
        lines.append(f"- Deployment signals: {', '.join(signals['deployment_signals'])}")
    if signals["tests"]["sample_paths"]:
        lines.append(f"- Test samples: {', '.join(signals['tests']['sample_paths'])}")
    if signals["tests"]["descriptions"]:
        lines.append(
            f"- Test behavior hints: {', '.join(item['name'] for item in signals['tests']['descriptions'][:6])}"
        )
    if signals["monorepo_services"]:
        lines.append(
            f"- Monorepo services: {', '.join(item['path'] for item in signals['monorepo_services'])}"
        )

    lines.extend(["", "## Interface Signals"])
    if signals["endpoints"]:
        for item in signals["endpoints"][:10]:
            lines.append(f"- `{item['endpoint']}` in `{item['path']}`")
    else:
        lines.append("- No HTTP endpoints were detected by the lightweight scan.")

    lines.extend(["", "## Recommended Artifacts"])
    lines.append(f"- Spec title seed: `{recs['spec_title']}`")
    lines.append(f"- Eval plan recommended: {'yes' if recs['needs_eval_plan'] else 'no'}")
    lines.append(f"- Harness strategy required: {'yes' if recs['needs_harness_strategy'] else 'no'}")
    lines.append(f"- Deployment strategy section required: {'yes' if recs['needs_deployment_strategy'] else 'no'}")
    lines.append(f"- Data pipeline section required: {'yes' if recs['needs_data_pipeline_section'] else 'no'}")
    lines.append(f"- Agentic confidence: `{signals['agentic']['confidence']}`")
    for adr in recs["recommended_adrs"]:
        lines.append(f"- ADR seed: `{adr['title']}` — {adr['reason']}")

    if signals["git_signals"]:
        lines.extend(["", "## Git Signals"])
        for item in signals["git_signals"][:10]:
            lines.append(f"- {item}")

    if report["risks"]:
        lines.extend(["", "## Risks"])
        for risk in report["risks"]:
            lines.append(f"- {risk}")

    if report["open_questions"]:
        lines.extend(["", "## Open Questions"])
        for question in report["open_questions"]:
            lines.append(f"- {question}")

    return "\n".join(lines) + "\n"


def write_report_artifacts(repo: pathlib.Path, report: dict[str, object]) -> dict[str, str]:
    out_dir = repo / ".specify" / "bootstrap"
    history_dir = out_dir / "history"
    out_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "latest-assessment.json"
    md_path = out_dir / "latest-assessment.md"
    generated_at = str(report["generated_at"]).replace("Z", "+00:00")
    timestamp = datetime.fromisoformat(generated_at).strftime("%Y%m%dT%H%M%SZ")
    history_json_path = history_dir / f"assessment-{timestamp}.json"
    history_md_path = history_dir / f"assessment-{timestamp}.md"
    json_payload = json.dumps(report, indent=2) + "\n"
    markdown_payload = render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(markdown_payload, encoding="utf-8")
    history_json_path.write_text(json_payload, encoding="utf-8")
    history_md_path.write_text(markdown_payload, encoding="utf-8")
    return {
        "json_path": json_path.relative_to(repo).as_posix(),
        "markdown_path": md_path.relative_to(repo).as_posix(),
        "history_json_path": history_json_path.relative_to(repo).as_posix(),
        "history_markdown_path": history_md_path.relative_to(repo).as_posix(),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".", help="Path to assess, relative to the current working directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    parser.add_argument("--write-artifacts", action="store_true", help="Write assessment artifacts under .specify/bootstrap/")
    parser.add_argument("--git-log", action="store_true", help="Include recent git log summaries as additional intent signals")
    args = parser.parse_args(argv)

    target = pathlib.Path(args.path).resolve()
    if not target.exists():
        print(f"Invalid path: {target}", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"Invalid path: {target} is not a directory", file=sys.stderr)
        return 2
    report = build_report(target, include_git_log=args.git_log)
    if report["summary"]["code_file_count"] == 0:
        print(f"No code files detected under: {target}", file=sys.stderr)
        return 3
    if args.write_artifacts:
        report["artifact_paths"] = write_report_artifacts(find_project_root(target), report)

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
