#!/usr/bin/env python3
"""Scaffold observability and evaluation provider layers from a governed plan."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import textwrap


SECTION_RE = re.compile(r"^\s*##\s+(.+?)\s*$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"\[(?:file path|e\.g\.|TBD|TODO|FIXME)", re.IGNORECASE)
OBS_ALT_PATTERNS = (
    r"\blangfuse\b",
    r"\blangsmith\b",
    r"\bphoenix\b",
    r"\barize\b",
    r"\bhoneyhive\b",
)
OTEL_PATTERNS = (
    r"\bopentelemetry\b",
    r"\botel\b",
)
LANGFUSE_PATTERNS = (
    r"\blangfuse\b",
)
EVAL_ALT_PATTERNS = (
    r"\bragas\b",
    r"\btruelens\b",
    r"\bconfluent\b",
    r"\bphoenix\b",
    r"\brageval\b",
    r"\bcustom\s+eval\b",
)


def section_body(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for idx, match in enumerate(matches):
        if match.group(1).strip().lower() == title.lower():
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""


def section_is_na(body: str) -> bool:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--") or set(stripped) <= {"|", "-", " "}:
            continue
        return bool(re.match(r"N/?A\b", stripped, re.IGNORECASE))
    return False


def parse_strategy_table(body: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.count("|") < 3:
            continue
        columns = [col.strip() for col in stripped.strip("|").split("|")]
        if len(columns) < 2:
            continue
        key, value = columns[0], columns[1]
        if key.lower() == "concern" or set(key) <= {"-", " "}:
            continue
        rows[key.lower()] = value
    return rows


def clean_path_value(value: str) -> str:
    cleaned = value.strip().strip("`")
    return "" if not cleaned or PLACEHOLDER_RE.search(cleaned) else cleaned


def plan_names_provider(body: str, patterns: tuple[str, ...] | list[str], default_name: str) -> tuple[bool, bool]:
    chose_default = bool(re.search(rf"\b{re.escape(default_name)}\b", body, re.IGNORECASE))
    chose_alternative = any(re.search(pattern, body, re.IGNORECASE) for pattern in patterns)
    return chose_default, chose_alternative


def choose_root(repo: pathlib.Path, obs_interface: str, eval_interface: str) -> str:
    for candidate in (obs_interface, eval_interface):
        if candidate:
            return pathlib.PurePosixPath(candidate).parts[0]
    for candidate in ("src", "app", "lib"):
        if (repo / candidate).is_dir():
            return candidate
    return "src"


def rewrite_template(template_path: pathlib.Path, root_name: str) -> str:
    text = template_path.read_text(encoding="utf-8")
    text = text.replace("from src.", f"from {root_name}.")
    text = text.replace("src/observability", f"{root_name}/observability")
    text = text.replace("src/evaluation", f"{root_name}/evaluation")
    return text


def render_noop_observation_provider(root_name: str) -> str:
    return textwrap.dedent(
        f"""\
        \"\"\"Noop observation provider for unit tests and local development.\"\"\"

        from __future__ import annotations

        from contextlib import contextmanager
        from typing import Any, Generator
        import uuid

        from {root_name}.observability.base import ObservationProvider, SpanContext, TraceContext


        class NoopObservationProvider:
            def trace(
                self,
                name: str,
                *,
                user_id: str | None = None,
                session_id: str | None = None,
                metadata: dict[str, Any] | None = None,
                tags: list[str] | None = None,
            ) -> TraceContext:
                return TraceContext(trace_id=uuid.uuid4().hex, name=name, metadata=metadata or {{}})

            def generation(
                self,
                trace: TraceContext,
                *,
                model: str,
                input: Any,
                output: Any,
                usage: Any = None,
                name: str | None = None,
                metadata: dict[str, Any] | None = None,
                latency_ms: float | None = None,
            ) -> None:
                return None

            @contextmanager
            def span(
                self,
                trace: TraceContext,
                name: str,
                *,
                input: Any = None,
                metadata: dict[str, Any] | None = None,
            ) -> Generator[SpanContext, None, None]:
                yield SpanContext(span_id=uuid.uuid4().hex, trace_id=trace.trace_id, name=name)

            def score(
                self,
                trace: TraceContext,
                *,
                name: str,
                value: float,
                comment: str | None = None,
            ) -> None:
                return None

            def flush(self) -> None:
                return None


        assert isinstance(NoopObservationProvider, type)
        _ = ObservationProvider
        """
    )


def render_noop_evaluation_provider(root_name: str) -> str:
    return textwrap.dedent(
        f"""\
        \"\"\"Noop evaluation provider for unit tests that do not run full eval suites.\"\"\"

        from __future__ import annotations

        from typing import Any

        from {root_name}.evaluation.base import EvalPolicy, EvalResult, EvaluationProvider, LLMTestCase


        class NoopEvaluationProvider:
            def evaluate(
                self,
                test_cases: list[LLMTestCase],
                metrics: list[Any],
                *,
                run_async: bool = False,
            ) -> list[EvalResult]:
                return [EvalResult(test_case=test_case, metric_results=[]) for test_case in test_cases]

            def assert_passes(
                self,
                results: list[EvalResult],
                policy: EvalPolicy | None = None,
            ) -> None:
                return None


        assert isinstance(NoopEvaluationProvider, type)
        _ = EvaluationProvider
        """
    )


def ensure_file(path: pathlib.Path, content: str) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def ensure_env_vars(
    repo: pathlib.Path,
    *,
    need_langfuse: bool,
    need_opentelemetry: bool,
    need_deepeval: bool,
) -> bool:
    if not need_langfuse and not need_opentelemetry and not need_deepeval:
        return False

    env_path = repo / ".env.example"
    existing = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    additions: list[str] = []

    if need_langfuse:
        for key, value in (
            ("LANGFUSE_PUBLIC_KEY", ""),
            ("LANGFUSE_SECRET_KEY", ""),
            ("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        ):
            if re.search(rf"^{re.escape(key)}=", existing, re.MULTILINE):
                continue
            additions.append(f"{key}={value}")

    if need_opentelemetry:
        for key, value in (
            ("OTEL_SERVICE_NAME", "agent-runtime"),
            ("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces"),
            ("OTEL_EXPORTER_OTLP_HEADERS", ""),
            ("OTEL_RESOURCE_ATTRIBUTES", "deployment.environment=development"),
        ):
            if re.search(rf"^{re.escape(key)}=", existing, re.MULTILINE):
                continue
            additions.append(f"{key}={value}")

    if need_deepeval and not re.search(r"^DEEPEVAL_API_KEY=", existing, re.MULTILINE):
        additions.append("DEEPEVAL_API_KEY=")

    if not additions:
        return False

    prefix = existing
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    block = "\n".join(additions) + "\n"
    env_path.write_text(prefix + block, encoding="utf-8")
    return True


def scaffold_for_plan(repo: pathlib.Path, plan_path: pathlib.Path) -> dict[str, object]:
    plan_text = plan_path.read_text(encoding="utf-8")
    body = section_body(plan_text, "Observability Strategy")
    harness_body = section_body(plan_text, "Harness Strategy")
    if not body:
        return {"status": "skip", "reason": "plan has no Observability Strategy", "slug": plan_path.parent.name}
    if section_is_na(body):
        return {"status": "skip", "reason": "Observability Strategy marked N/A", "slug": plan_path.parent.name}

    strategy = parse_strategy_table(body)
    obs_interface = clean_path_value(strategy.get("observationprovider interface", ""))
    eval_interface = clean_path_value(strategy.get("evaluationprovider interface", ""))
    root_name = choose_root(repo, obs_interface, eval_interface)

    obs_base_path = repo / (obs_interface or f"{root_name}/observability/base.py")
    eval_base_path = repo / (eval_interface or f"{root_name}/evaluation/base.py")
    obs_dir = obs_base_path.parent
    eval_dir = eval_base_path.parent

    script_dir = pathlib.Path(__file__).resolve().parent
    templates_dir = script_dir.parent / "templates"

    obs_default, obs_alternative = plan_names_provider(body, OBS_ALT_PATTERNS, "opentelemetry")
    obs_opentelemetry, _ = plan_names_provider(body, OTEL_PATTERNS, "opentelemetry")
    obs_langfuse, _ = plan_names_provider(body, LANGFUSE_PATTERNS, "langfuse")
    eval_default, eval_alternative = plan_names_provider(body, EVAL_ALT_PATTERNS, "deepeval")
    harness_required = bool(harness_body) and not section_is_na(harness_body)
    scaffold_opentelemetry = obs_opentelemetry or not obs_alternative
    scaffold_langfuse = obs_langfuse or harness_required
    scaffold_deepeval = eval_default or not eval_alternative or harness_required

    created: list[str] = []
    skipped: list[str] = []

    if ensure_file(obs_base_path, rewrite_template(templates_dir / "observation-provider-template.py", root_name)):
        created.append(str(obs_base_path.relative_to(repo)))
    else:
        skipped.append(str(obs_base_path.relative_to(repo)))

    if ensure_file(eval_base_path, rewrite_template(templates_dir / "evaluation-provider-template.py", root_name)):
        created.append(str(eval_base_path.relative_to(repo)))
    else:
        skipped.append(str(eval_base_path.relative_to(repo)))

    if scaffold_langfuse:
        obs_provider_path = obs_dir / "langfuse.py"
        if ensure_file(obs_provider_path, rewrite_template(templates_dir / "langfuse-observation-provider-template.py", root_name)):
            created.append(str(obs_provider_path.relative_to(repo)))
        else:
            skipped.append(str(obs_provider_path.relative_to(repo)))

    if scaffold_opentelemetry:
        obs_provider_path = obs_dir / "opentelemetry.py"
        if ensure_file(obs_provider_path, rewrite_template(templates_dir / "opentelemetry-observation-provider-template.py", root_name)):
            created.append(str(obs_provider_path.relative_to(repo)))
        else:
            skipped.append(str(obs_provider_path.relative_to(repo)))

    if scaffold_deepeval:
        eval_provider_path = eval_dir / "deepeval.py"
        if ensure_file(eval_provider_path, rewrite_template(templates_dir / "deepeval-evaluation-provider-template.py", root_name)):
            created.append(str(eval_provider_path.relative_to(repo)))
        else:
            skipped.append(str(eval_provider_path.relative_to(repo)))

    obs_noop_path = obs_dir / "noop.py"
    if ensure_file(obs_noop_path, render_noop_observation_provider(root_name)):
        created.append(str(obs_noop_path.relative_to(repo)))
    else:
        skipped.append(str(obs_noop_path.relative_to(repo)))

    eval_noop_path = eval_dir / "noop.py"
    if ensure_file(eval_noop_path, render_noop_evaluation_provider(root_name)):
        created.append(str(eval_noop_path.relative_to(repo)))
    else:
        skipped.append(str(eval_noop_path.relative_to(repo)))

    env_updated = ensure_env_vars(
        repo,
        need_langfuse=scaffold_langfuse,
        need_opentelemetry=scaffold_opentelemetry,
        need_deepeval=scaffold_deepeval,
    )
    if env_updated:
        created.append(".env.example")
    elif (repo / ".env.example").exists():
        skipped.append(".env.example")

    return {
        "status": "ok",
        "slug": plan_path.parent.name,
        "root": root_name,
        "created": created,
        "skipped": skipped,
        "scaffolded_defaults": {
            "langfuse": scaffold_langfuse,
            "opentelemetry": scaffold_opentelemetry,
            "deepeval": scaffold_deepeval,
            "harness_required": harness_required,
        },
    }


def locate_plans(repo: pathlib.Path, spec_slug: str) -> list[pathlib.Path]:
    specs_root = repo / ".specify" / "specs"
    if spec_slug:
        candidate = specs_root / spec_slug / "plan.md"
        return [candidate] if candidate.exists() else []
    if not specs_root.exists():
        return []
    return sorted(specs_root.glob("*/plan.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold observation/evaluation provider layers from plan.md.")
    parser.add_argument("--spec", default="", help="Spec slug to scaffold for (default: scan all plans)")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    repo = pathlib.Path(".").resolve()
    plans = locate_plans(repo, args.spec)
    if not plans:
        result = {"status": "skip", "reason": "no plan.md found — run /at-plan first"}
        print(json.dumps(result) if args.json else f"SKIP: {result['reason']}")
        return 0

    results = [scaffold_for_plan(repo, plan_path) for plan_path in plans]
    if args.json:
        print(json.dumps({"results": results}))
    else:
        for result in results:
            slug = result.get("slug", "unknown")
            status = result["status"]
            if status == "ok":
                print(f"[OK] {slug}: source root {result['root']}")
                created = result.get("created", [])
                skipped = result.get("skipped", [])
                if created:
                    print("  created:")
                    for item in created:
                        print(f"    - {item}")
                if skipped:
                    print("  skipped:")
                    for item in skipped:
                        print(f"    - {item}")
            else:
                print(f"[SKIP] {slug}: {result['reason']}")
        print("\nNext step: wire the provider instances at the composition root, then run check-observability-setup.sh.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
