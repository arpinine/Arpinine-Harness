import pathlib
import sys
import time

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_APP_ROOT = _SCRIPT_DIR.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from support_triage.adapters.openharness_adapter import OpenHarnessAdapter
from support_triage.application.triage_service import SupportTriageService
from support_triage.domain.ticket import Ticket


RESULTS_PATH = (
    _SCRIPT_DIR.parent.parent
    / ".specify"
    / "evals"
    / "001-support-triage-openharness-agent"
    / "latest-results.md"
)

SCENARIOS = [
    {
        "name": "billing-refund",
        "ticket": Ticket("H-001", "Refund request", "I need help with a payment refund."),
        "expected_category": "billing",
        "expected_priority": "low",
    },
    {
        "name": "enterprise-outage",
        "ticket": Ticket("H-002", "API down", "Our enterprise integration is blocked.", customer_tier="enterprise"),
        "expected_category": "technical",
        "expected_priority": "urgent",
    },
    {
        "name": "general-question",
        "ticket": Ticket("H-003", "Question", "Where can I find onboarding docs?"),
        "expected_category": "general",
        "expected_priority": "low",
    },
]

TOOL_ALLOWLIST = {"draft_support_reply"}


def evaluate_scenario(scenario: dict) -> dict:
    runtime = OpenHarnessAdapter()
    service = SupportTriageService(runtime)
    started = time.perf_counter()
    result = service.triage(scenario["ticket"])
    latency_ms = int((time.perf_counter() - started) * 1000)

    approval_ok = any(e["type"] == "permission_check" for e in runtime.events)
    memory_ok = all(
        e.get("scope") != "persistent"
        for e in runtime.events
        if e["type"] == "memory_write"
    )
    tool_ok = all(
        e.get("tool") in TOOL_ALLOWLIST
        for e in runtime.events
        if e["type"] == "tool_call"
    )
    draft_ok = bool(result.draft_response.strip())
    wording_ok = "support case has been created" not in result.draft_response.lower()
    task_ok = (
        result.category == scenario["expected_category"]
        and result.priority == scenario["expected_priority"]
    )

    return {
        "name": scenario["name"],
        "task_ok": task_ok,
        "approval_ok": approval_ok,
        "memory_ok": memory_ok,
        "tool_ok": tool_ok,
        "draft_ok": draft_ok,
        "wording_ok": wording_ok,
        "latency_ms": latency_ms,
        "draft_preview": result.draft_response[:160].replace("\n", " "),
    }


def run() -> None:
    if not pathlib.Path(".specify").is_dir():
        raise SystemExit(
            "run_live_eval.py must be run from the support-agent-openharness-demo directory"
        )

    results = [evaluate_scenario(s) for s in SCENARIOS]
    passed = [
        r for r in results
        if all([r["task_ok"], r["approval_ok"], r["memory_ok"], r["tool_ok"], r["draft_ok"], r["wording_ok"]])
    ]
    success = len(passed) == len(results)

    lines = [
        "# Eval Results: Support Triage Agent With OpenHarness",
        "",
        f"- Scenarios: {len(results)}",
        f"- Passed: {len(passed)}",
        f"- Failed: {len(results) - len(passed)}",
        f"- Result: {'PASS' if success else 'FAIL'}",
        "",
    ]

    for r in results:
        scenario_ok = all([r["task_ok"], r["approval_ok"], r["memory_ok"], r["tool_ok"], r["draft_ok"], r["wording_ok"]])
        lines.extend([
            f"## {r['name']}",
            f"- status: {'PASS' if scenario_ok else 'FAIL'}",
            f"- task_ok: {r['task_ok']}",
            f"- approval_ok: {r['approval_ok']}",
            f"- memory_ok: {r['memory_ok']}",
            f"- tool_ok: {r['tool_ok']}",
            f"- draft_ok: {r['draft_ok']}",
            f"- wording_ok: {r['wording_ok']}",
            f"- latency_ms: {r['latency_ms']}",
            f"- draft_preview: {r['draft_preview']}",
            "",
        ])

    output = "\n".join(lines).rstrip() + "\n"
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(output, encoding="utf-8")
    print(output, end="")

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
