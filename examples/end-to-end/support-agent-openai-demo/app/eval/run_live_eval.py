import pathlib
import sys
import time


_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_APP_ROOT = _SCRIPT_DIR.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from support_triage.adapters.openai_harness import OpenAIHarnessRuntime
from support_triage.application.triage_service import SupportTriageService
from support_triage.domain.ticket import Ticket


RESULTS_PATH = (
    _SCRIPT_DIR.parent.parent
    / ".specify"
    / "evals"
    / "001-support-triage-openai-agent"
    / "latest-results.md"
)

SCENARIOS = [
    {
        "name": "billing-refund",
        "ticket": Ticket("O-001", "Refund request", "I need help with a payment refund."),
        "category": "billing",
        "priority": "low",
    },
    {
        "name": "enterprise-outage",
        "ticket": Ticket("O-002", "API down", "Our enterprise integration is blocked."),
        "category": "technical",
        "priority": "urgent",
    },
    {
        "name": "general-question",
        "ticket": Ticket("O-003", "Question", "Where can I find onboarding docs?"),
        "category": "general",
        "priority": "low",
    },
]


def evaluate_scenario(scenario: dict) -> dict:
    runtime = OpenAIHarnessRuntime()
    service = SupportTriageService(runtime)
    started = time.perf_counter()
    result = service.triage(scenario["ticket"])
    latency_ms = int((time.perf_counter() - started) * 1000)

    approval_ok = any(event["type"] == "permission_check" for event in runtime.events)
    memory_ok = all(
        event.get("scope") != "persistent"
        for event in runtime.events
        if event["type"] == "memory_write"
    )
    draft_ok = bool(result.draft_response.strip())
    wording_ok = "support case has been created" not in result.draft_response.lower()
    task_ok = result.category == scenario["category"] and result.priority == scenario["priority"]

    return {
        "name": scenario["name"],
        "task_ok": task_ok,
        "approval_ok": approval_ok,
        "memory_ok": memory_ok,
        "draft_ok": draft_ok,
        "wording_ok": wording_ok,
        "latency_ms": latency_ms,
        "draft_preview": result.draft_response[:160].replace("\n", " "),
    }


def run() -> None:
    if not pathlib.Path(".specify").is_dir():
        raise SystemExit("run_live_eval.py must be run from the support-agent-openai-demo directory")

    results = [evaluate_scenario(scenario) for scenario in SCENARIOS]
    passed = [
        result
        for result in results
        if all(
            [
                result["task_ok"],
                result["approval_ok"],
                result["memory_ok"],
                result["draft_ok"],
                result["wording_ok"],
            ]
        )
    ]
    success = len(passed) == len(results)

    lines = [
        "# Eval Results: Support Triage Agent With OpenAI",
        "",
        f"- Scenarios: {len(results)}",
        f"- Passed: {len(passed)}",
        f"- Failed: {len(results) - len(passed)}",
        f"- Result: {'PASS' if success else 'FAIL'}",
        "",
    ]

    for result in results:
        scenario_ok = all(
            [
                result["task_ok"],
                result["approval_ok"],
                result["memory_ok"],
                result["draft_ok"],
                result["wording_ok"],
            ]
        )
        lines.extend(
            [
                f"## {result['name']}",
                f"- status: {'PASS' if scenario_ok else 'FAIL'}",
                f"- task_ok: {result['task_ok']}",
                f"- approval_ok: {result['approval_ok']}",
                f"- memory_ok: {result['memory_ok']}",
                f"- draft_ok: {result['draft_ok']}",
                f"- wording_ok: {result['wording_ok']}",
                f"- latency_ms: {result['latency_ms']}",
                f"- draft_preview: {result['draft_preview']}",
                "",
            ]
        )

    output = "\n".join(lines).rstrip() + "\n"
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(output, encoding="utf-8")
    print(output, end="")

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
