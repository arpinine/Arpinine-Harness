import json
import os
import pathlib
import sys


_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_APP_ROOT = _SCRIPT_DIR.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

from support_triage.adapters.fake_harness import FakeHarnessRuntime
from support_triage.application.triage_service import SupportTriageService
from support_triage.domain.ticket import Ticket


RESULTS_PATH = _SCRIPT_DIR.parent.parent / ".specify" / "evals" / "001-support-triage-agent" / "latest-results.md"

SCENARIOS = [
    {
        "name": "billing-refund",
        "ticket": Ticket("E-001", "Refund request", "I need help with a payment refund."),
        "category": "billing",
        "priority": "low",
    },
    {
        "name": "enterprise-outage",
        "ticket": Ticket("E-002", "API down", "Our enterprise integration is blocked."),
        "category": "technical",
        "priority": "urgent",
    },
    {
        "name": "general-question",
        "ticket": Ticket("E-003", "Question", "Where can I find onboarding docs?"),
        "category": "general",
        "priority": "low",
    },
]


def scenario_by_id(scenario_id: str) -> dict:
    for scenario in SCENARIOS:
        if scenario["name"] == scenario_id:
            return scenario
    raise KeyError(f"Unknown scenario_id: {scenario_id}")


def evaluate_scenario(scenario: dict) -> tuple[dict, dict]:
    runtime = FakeHarnessRuntime()
    service = SupportTriageService(runtime)
    result = service.triage(scenario["ticket"])
    approval_ok = any(event["type"] == "permission_check" for event in runtime.events)
    memory_ok = all(
        event.get("scope") != "persistent"
        for event in runtime.events
        if event["type"] == "memory_write"
    )
    success = (
        result.category == scenario["category"]
        and result.priority == scenario["priority"]
        and result.requires_approval
        and approval_ok
        and memory_ok
    )
    latency_map = {
        "billing-refund": 120,
        "enterprise-outage": 240,
        "general-question": 180,
    }
    token_input_map = {
        "billing-refund": 18,
        "enterprise-outage": 24,
        "general-question": 20,
    }
    token_output_map = {
        "billing-refund": 12,
        "enterprise-outage": 16,
        "general-question": 14,
    }
    cost_map = {
        "billing-refund": 0.010,
        "enterprise-outage": 0.018,
        "general-question": 0.012,
    }
    eval_result = {
        "run_id": f"{scenario['name']}-benchmark-run",
        "result": "PASS" if success else "FAIL",
        "variant_id": "support-triage-demo",
        "model_name": "fake-harness-runtime",
        "model_version": "demo-v1",
        "latency_ms": latency_map[scenario["name"]],
        "token_count_input": token_input_map[scenario["name"]],
        "token_count_output": token_output_map[scenario["name"]],
        "cost_usd": cost_map[scenario["name"]],
        "passed": 1 if success else 0,
        "failed": 0 if success else 1,
        "approval_check_present": approval_ok,
        "memory_scope_ok": memory_ok,
    }
    observation = {
        "run_id": f"{scenario['name']}-observation-run",
        "runtime_class": "embedded-agent-runtime",
        "runtime_implementation": "fake-harness-adapter",
        "latency_ms": eval_result["latency_ms"],
        "token_count_input": eval_result["token_count_input"],
        "token_count_output": eval_result["token_count_output"],
        "cost_usd": eval_result["cost_usd"],
        "turn_count": 1,
        "tool_call_count": 1,
        "error_count": 0 if success else 1,
        "final_outcome": "PASS" if success else "FAIL",
        "events": runtime.events,
    }
    return eval_result, observation


def write_benchmark_outputs() -> None:
    scenario_id = os.environ.get("ARPININE_HARNESS_SCENARIO_ID")
    result_path = os.environ.get("ARPININE_HARNESS_RESULT_PATH")
    observation_path = os.environ.get("ARPININE_HARNESS_OBSERVATION_PATH")
    if not scenario_id or not result_path:
        raise SystemExit("Missing benchmark scenario context")

    scenario = scenario_by_id(scenario_id)
    eval_result, observation = evaluate_scenario(scenario)
    pathlib.Path(result_path).write_text(json.dumps(eval_result) + "\n", encoding="utf-8")
    if observation_path:
        pathlib.Path(observation_path).write_text(json.dumps(observation) + "\n", encoding="utf-8")


def run() -> None:
    if not pathlib.Path(".specify").is_dir():
        raise SystemExit("run_eval.py must be run from the support-agent-demo directory")

    if os.environ.get("ARPININE_HARNESS_RESULT_PATH"):
        write_benchmark_outputs()
        return

    if not SCENARIOS:
        raise SystemExit("No scenarios defined in SCENARIOS list")

    passed = 0
    failures = []
    events_per_scenario = {}

    for scenario in SCENARIOS:
        eval_result, observation = evaluate_scenario(scenario)
        events_per_scenario[scenario["name"]] = observation["events"]
        if eval_result["result"] == "PASS":
            passed += 1
        else:
            failures.append(scenario["name"])

    total = len(SCENARIOS)
    approval_ok = all(
        any(event["type"] == "permission_check" for event in events_per_scenario[scenario["name"]])
        for scenario in SCENARIOS
    )
    memory_ok = all(
        all(
            event.get("scope") != "persistent"
            for event in events_per_scenario[scenario["name"]]
            if event["type"] == "memory_write"
        )
        for scenario in SCENARIOS
    )
    success = not failures and approval_ok and memory_ok

    lines = [
        "# Eval Results: Support Triage Agent",
        "",
        f"- Scenarios: {total}",
        f"- Passed: {passed}",
        f"- Failed: {len(failures)}",
        f"- Task success: {passed / total:.2f}",
        f"- Approval checks: {'PASS' if approval_ok else 'FAIL'}",
        f"- Memory scope: {'PASS' if memory_ok else 'FAIL'}",
        "",
    ]
    if failures:
        lines.append("Failed scenarios:")
        for failure in failures:
            lines.append(f"- {failure}")
    if not approval_ok:
        lines.append("- Approval failure: at least one scenario missed the permission check")
    if not memory_ok:
        lines.append("- Memory failure: persistent memory was written in at least one scenario")

    lines.append(f"Result: {'PASS' if success else 'FAIL'}")
    output = "\n".join(lines) + "\n"
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(output, encoding="utf-8")
    print(output, end="")

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
