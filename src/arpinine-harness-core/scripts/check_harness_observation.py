#!/usr/bin/env python3
"""Validate harness observation traces against governed runtime assertions."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any


REPO = pathlib.Path.cwd()
SPEC_ROOT = REPO / ".specify" / "specs"
EVAL_ROOT = REPO / ".specify" / "evals"
OBS_ROOT = REPO / ".specify" / "observations"

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$")
LIST_ITEM_RE = re.compile(r"^-\s+([^:]+):\s*(.+)$")
TOKEN_RE = re.compile(r"`([^`]+)`|'([^']+)'|\"([^\"]+)\"")
IDENT_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def _extract_section(text: str, title: str) -> str:
    matches = list(SECTION_RE.finditer(text))
    for index, match in enumerate(matches):
        if match.group(1).strip().lower() == title.lower():
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            return text[start:end].strip()
    return ""


def _parse_harness_strategy(plan_text: str) -> dict[str, str]:
    section = _extract_section(plan_text, "Harness Strategy")
    if not section or section.lstrip().startswith("N/A"):
        return {}

    strategy: dict[str, str] = {}
    for line in section.splitlines():
        match = ROW_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        if key == "concern" or key.startswith("---"):
            continue
        strategy[key] = value
    return strategy


def _parse_runtime_contract(eval_text: str) -> dict[str, str]:
    section = _extract_section(eval_text, "Runtime Contract Assertions")
    contract: dict[str, str] = {}
    for line in section.splitlines():
        match = LIST_ITEM_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1).strip().lower()
        contract[key] = match.group(2).strip()
    return contract


def _parse_replay(eval_text: str) -> dict[str, str]:
    section = _extract_section(eval_text, "Deterministic Replay")
    replay: dict[str, str] = {}
    for line in section.splitlines():
        match = LIST_ITEM_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1).strip().lower()
        replay[key] = match.group(2).strip()
    return replay


def _extract_values(text: str) -> list[str]:
    values = [group for match in TOKEN_RE.finditer(text) for group in match.groups() if group]
    if values:
        return values
    lowered = text.strip().lower()
    if lowered in {"none", "n/a", "no"}:
        return []
    return IDENT_RE.findall(text)


def _event_type(event: dict[str, Any]) -> str:
    return str(event.get("type", ""))


def _event_action(event: dict[str, Any]) -> str:
    return str(event.get("action") or event.get("tool") or event.get("result") or "")


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_slug(explicit_slug: str | None) -> str:
    if explicit_slug:
        return explicit_slug
    specs = sorted(SPEC_ROOT.glob("*/spec.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not specs:
        raise FileNotFoundError("No spec found under .specify/specs/")
    return specs[0].parent.name


def evaluate_slug(slug: str) -> dict[str, Any]:
    plan_path = SPEC_ROOT / slug / "plan.md"
    eval_path = EVAL_ROOT / slug / "eval-plan.md"
    trace_path = OBS_ROOT / slug / "trace.json"

    if not plan_path.exists():
        raise FileNotFoundError(f"Missing plan.md for slug {slug}")
    if not eval_path.exists():
        raise FileNotFoundError(f"Missing eval-plan.md for slug {slug}")
    if not trace_path.exists():
        raise FileNotFoundError(f"Missing trace.json for slug {slug}")

    plan_text = plan_path.read_text(encoding="utf-8")
    strategy = _parse_harness_strategy(plan_text)
    if not strategy:
        return {"slug": slug, "harness_required": False, "verdict": "PASS", "checks": []}

    eval_text = eval_path.read_text(encoding="utf-8")
    contract = _parse_runtime_contract(eval_text)
    replay = _parse_replay(eval_text)
    trace = _load_json(trace_path)
    events = trace.get("events", [])

    checks: list[dict[str, str]] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append(
            {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}
        )

    record("trace_has_events", bool(events), "trace.json must include runtime events")

    required_events = _extract_values(contract.get("required event types", ""))
    observed_event_types = {_event_type(event) for event in events}
    missing_events = [event for event in required_events if event not in observed_event_types]
    record(
        "required_event_types_present",
        not missing_events,
        "missing event types: " + ", ".join(missing_events) if missing_events else "all required event types present",
    )

    allowed_tools = _extract_values(contract.get("allowed tools", strategy.get("tool access model", "")))
    observed_tools = sorted(
        {
            str(event.get("tool"))
            for event in events
            if _event_type(event) in {"tool_requested", "tool_executed", "tool_call"}
            and event.get("tool")
        }
    )
    unexpected_tools = [tool for tool in observed_tools if allowed_tools and tool not in allowed_tools]
    record(
        "allowed_tools_only",
        not unexpected_tools,
        "unexpected tools: " + ", ".join(unexpected_tools) if unexpected_tools else "all observed tools are allowed",
    )

    protected_actions = _extract_values(contract.get("protected actions requiring approval", ""))
    approval_failures: list[str] = []
    for protected in protected_actions:
        saw_protected_action = False
        saw_prior_approval = False
        for event in events:
            action = _event_action(event)
            if _event_type(event) == "permission_check" and action == protected:
                if event.get("approved") is True or str(event.get("result", "")).lower() == "approved":
                    saw_prior_approval = True
            elif action == protected and _event_type(event) != "permission_check":
                saw_protected_action = True
                if not saw_prior_approval:
                    approval_failures.append(protected)
                    break
        if not saw_protected_action and not saw_prior_approval:
            approval_failures.append(f"{protected} (no approval evidence)")
    record(
        "approval_before_protected_write",
        not approval_failures,
        "approval issues: " + ", ".join(approval_failures) if approval_failures else "approval evidence present for protected actions",
    )

    memory_invariant = contract.get("memory scope invariant", strategy.get("memory / state model", "")).lower()
    memory_violations: list[str] = []
    if "session" in memory_invariant:
        for event in events:
            if _event_type(event) == "memory_write" and str(event.get("scope", "")).lower() not in {"", "session"}:
                memory_violations.append(str(event.get("scope")))
    elif "none" in memory_invariant:
        for event in events:
            if _event_type(event) in {"memory_write", "memory_read"}:
                memory_violations.append(_event_type(event))
    record(
        "memory_scope_invariant",
        not memory_violations,
        "memory invariant violations: " + ", ".join(memory_violations) if memory_violations else "memory scope matches declared invariant",
    )

    required_reset = _extract_values(contract.get("session reset evidence", ""))
    reset_ok = True
    reset_detail = "no session reset evidence required"
    if required_reset:
        reset_ok = all(required in observed_event_types for required in required_reset)
        reset_detail = (
            "all required session reset events present"
            if reset_ok
            else "missing session reset evidence: " + ", ".join([required for required in required_reset if required not in observed_event_types])
        )
    record("session_reset_evidence", reset_ok, reset_detail)

    replay_required = replay.get("replay required", "").strip().lower() == "yes"
    replay_command = replay.get("replay command", "").strip()
    replay_strategy = replay.get("mock / fixture strategy", "").strip()
    replay_fixtures = replay.get("replay fixture path", "").strip()
    record(
        "deterministic_replay_defined",
        (not replay_required) or bool(replay_command and replay_strategy and replay_fixtures),
        "replay command, strategy, and fixture path are required when replay is marked Yes",
    )

    failures = [check for check in checks if check["status"] == "FAIL"]
    return {
        "slug": slug,
        "harness_required": True,
        "verdict": "FAIL" if failures else "PASS",
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", help="Spec slug under .specify/specs/")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text summary")
    args = parser.parse_args()

    try:
        result = evaluate_slug(_find_slug(args.slug))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Slug: {result['slug']}")
        print(f"Verdict: {result['verdict']}")
        for check in result["checks"]:
            print(f"- {check['status']}: {check['name']} — {check['detail']}")
    return 1 if result["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
