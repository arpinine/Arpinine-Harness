import pathlib

from support_triage.adapters.fake_harness import FakeHarnessRuntime
from support_triage.application.triage_service import SupportTriageService
from support_triage.domain.ticket import Ticket


RESULTS_PATH = pathlib.Path(".specify/evals/001-support-triage-agent/latest-results.md")

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


def run():
    passed = 0
    failures = []
    events_per_scenario = {}

    for scenario in SCENARIOS:
        runtime = FakeHarnessRuntime()
        service = SupportTriageService(runtime)
        result = service.triage(scenario["ticket"])
        events_per_scenario[scenario["name"]] = runtime.events
        ok = (
            result.category == scenario["category"]
            and result.priority == scenario["priority"]
            and result.requires_approval
        )
        if ok:
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
    RESULTS_PATH.write_text(output)
    print(output, end="")

    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    run()
