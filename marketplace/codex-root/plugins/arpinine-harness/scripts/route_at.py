#!/usr/bin/env python3
"""Deterministic router for the /at facade."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import inspect_state


HANDOFF_COMMANDS: frozenset[str] = frozenset({
    "/at-map",
    "/at-discover",
    "/at-bootstrap-from-code",
    "/at-implement",
})
READ_ONLY_RETURN_COMMANDS: frozenset[str] = frozenset({
    "/at-status",
    "/at-ask",
})

EXPLICIT_COMMANDS: dict[str, str] = {
    "at-map": "/at-map",
    "/at-map": "/at-map",
    "at-discover": "/at-discover",
    "/at-discover": "/at-discover",
    "at-new": "/at-new",
    "/at-new": "/at-new",
    "at-plan": "/at-plan",
    "/at-plan": "/at-plan",
    "at-review": "/at-review",
    "/at-review": "/at-review",
    "at-ask": "/at-ask",
    "/at-ask": "/at-ask",
    "at-implement": "/at-implement",
    "/at-implement": "/at-implement",
    "at-audit": "/at-audit",
    "/at-audit": "/at-audit",
    "at-eval": "/at-eval",
    "/at-eval": "/at-eval",
    "at-retro": "/at-retro",
    "/at-retro": "/at-retro",
    "at-adr": "/at-adr",
    "/at-adr": "/at-adr",
    "at-observe": "/at-observe",
    "/at-observe": "/at-observe",
    "at-status": "/at-status",
    "/at-status": "/at-status",
    "at-init": "/at-init",
    "/at-init": "/at-init",
    "at-bootstrap-from-code": "/at-bootstrap-from-code",
    "/at-bootstrap-from-code": "/at-bootstrap-from-code",
}

INTENT_VOCABULARY: dict[str, tuple[str, ...]] = {
    "/at-map": (
        "build a product",
        "broad goal",
        "initiative",
        "multiple features",
        "start from scratch",
        "product vision",
        "decompose",
        "feature backlog",
        "roadmap",
        "whole system",
    ),
    "/at-discover": (
        "add a feature",
        "one feature",
        "this idea",
        "user story",
        "workflow for",
        "i want users to be able to",
        "before i write a spec",
    ),
    "/at-new": (
        "create a spec",
        "write a spec",
        "new spec for",
        "specify",
        "document the feature",
    ),
    "/at-plan": (
        "plan the implementation",
        "how to build",
        "generate a plan",
        "implementation plan",
        "technical plan",
        "before i implement",
    ),
    "/at-review": (
        "review the spec",
        "tighten the spec",
        "refine scope",
        "spec is unclear",
        "improve the spec",
        "acceptance criteria",
    ),
    "/at-ask": (
        "ask the",
        "get a second opinion",
        "what does the architect think",
        "what would security say",
        "check with",
        "specialist",
    ),
    "/at-implement": (
        "implement",
        "code it",
        "build it",
        "write the code",
        "start development",
        "tdd",
        "make it work",
    ),
    "/at-audit": (
        "something drifted",
        "implementation diverged",
        "doesn't match the spec",
        "check drift",
        "audit",
        "misalignment",
    ),
    "/at-eval": (
        "run the eval",
        "evaluate",
        "measure",
        "thresholds",
        "check metrics",
        "does it meet criteria",
    ),
    "/at-retro": (
        "retrospective",
        "what did we learn",
        "after shipping",
        "post-mortem",
        "lessons learned",
    ),
    "/at-adr": (
        "decision record",
        "adr",
        "architectural decision",
        "document this choice",
    ),
    "/at-observe": (
        "record observation",
        "log runtime behavior",
        "what happened in prod",
        "observation",
    ),
    "/at-status": (
        "what should i do next",
        "what's the state",
        "show me the status",
        "what's left",
        "where are we",
    ),
    "/at-bootstrap-from-code": (
        "existing codebase",
        "bootstrap from code",
        "reverse engineer the specs",
        "already have code",
        "legacy system",
    ),
}

NO_SPEC_REDIRECTS: frozenset[str] = frozenset({
    "/at-review",
    "/at-implement",
    "/at-audit",
    "/at-eval",
    "/at-retro",
    "/at-observe",
})
ROUTE_PRIORITY: tuple[str, ...] = (
    "/at-plan",
    "/at-review",
    "/at-audit",
    "/at-eval",
    "/at-implement",
    "/at-retro",
    "/at-observe",
    "/at-ask",
    "/at-adr",
    "/at-new",
    "/at-discover",
    "/at-map",
    "/at-bootstrap-from-code",
    "/at-status",
)


def normalize_intent(intent: str | None) -> str:
    normalized = (intent or "").strip()
    return normalized if normalized else "what should I do next?"


def classify_command(command: str | None) -> str | None:
    if command is None:
        return None
    if command in HANDOFF_COMMANDS:
        return "handoff"
    return "return"


def make_result(
    *,
    state: dict[str, Any],
    intent: str,
    interpretation: str,
    route: str | None,
    confidence: str,
    reason: str,
    alternative: str | None = None,
    mode: str | None = None,
    question: str | None = None,
    options: list[dict[str, str]] | None = None,
    requires_confirmation: bool | None = None,
    session_slug: str | None = None,
) -> dict[str, Any]:
    command_class = classify_command(route)
    if mode is None:
        if confidence == "low":
            mode = "clarify"
        elif confidence == "medium" and (command_class == "handoff" or route not in READ_ONLY_RETURN_COMMANDS):
            mode = "confirm"
        else:
            mode = "execute"
    if requires_confirmation is None:
        requires_confirmation = mode == "confirm"
    return {
        "intent": intent,
        "interpretation": interpretation,
        "route": route,
        "confidence": confidence,
        "reason": reason,
        "alternative": alternative,
        "command_class": command_class,
        "mode": mode,
        "requires_confirmation": requires_confirmation,
        "question": question,
        "options": options or [],
        "session_slug": session_slug,
        "state": state,
    }


def find_explicit_command(intent_lower: str) -> str | None:
    for phrase, command in sorted(EXPLICIT_COMMANDS.items(), key=lambda item: -len(item[0])):
        if phrase in intent_lower:
            return command
    return None


def score_intents(intent_lower: str) -> dict[str, int]:
    scores: dict[str, int] = {route: 0 for route in INTENT_VOCABULARY}
    for route, phrases in INTENT_VOCABULARY.items():
        for phrase in phrases:
            if phrase in intent_lower:
                scores[route] += 1
    if re.search(r"\badd\b", intent_lower) and re.search(r"\b(feature|auth|login|billing|search)\b", intent_lower):
        scores["/at-discover"] += 1
    if re.search(r"\b(spec|specification)\b", intent_lower) and re.search(r"\b(review|refine|tighten|improve)\b", intent_lower):
        scores["/at-review"] += 1
    return scores


def pick_best_route(intent_lower: str) -> tuple[str | None, int]:
    scores = score_intents(intent_lower)
    best_score = max(scores.values(), default=0)
    if best_score == 0:
        return None, 0
    top_routes = [route for route, score in scores.items() if score == best_score]
    for route in ROUTE_PRIORITY:
        if route in top_routes:
            return route, best_score
    return top_routes[0], best_score


def broad_goal_signal(intent_lower: str) -> bool:
    return score_intents(intent_lower).get("/at-map", 0) > 0


def feature_signal(intent_lower: str) -> bool:
    return score_intents(intent_lower).get("/at-discover", 0) > 0


def is_status_or_vague(intent_lower: str, best_score: int) -> bool:
    return score_intents(intent_lower).get("/at-status", 0) > 0 or best_score == 0


def redirect_without_specs(intent_lower: str) -> str:
    if broad_goal_signal(intent_lower):
        return "/at-map"
    return "/at-discover"


def route(intent: str, state: dict[str, Any]) -> dict[str, Any]:
    normalized_intent = normalize_intent(intent)
    intent_lower = normalized_intent.lower()
    explicit_command = find_explicit_command(intent_lower)

    if state.get("repo_root") is None:
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="blocked",
            route=None,
            confidence="low",
            reason="No project root could be determined.",
            mode="error",
            question="Navigate to the project directory or pass --repo explicitly.",
        )

    if not state.get("governed") and state.get("has_existing_codebase"):
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="ungoverned existing codebase",
            route="/at-init",
            confidence="medium",
            reason="Governance is missing, but the repo already contains implementation that could be bootstrapped.",
            alternative="/at-bootstrap-from-code",
            question="Do you want to initialize governance first or bootstrap from the current codebase?",
        )

    if not state.get("governed"):
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="ungoverned repository",
            route="/at-init",
            confidence="high",
            reason="No .specify/ directory exists, so governance must be initialized first.",
        )

    if state.get("bootstrap_candidate"):
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="governed repo with code but no specs",
            route="/at-bootstrap-from-code",
            confidence="medium",
            reason="The repo has code but no governed specs yet.",
            alternative="/at-map",
            question="Do you want to bootstrap governance from the existing codebase or start from a new product goal?",
        )

    has_map = bool(state.get("active_map_sessions"))
    has_discovery = bool(state.get("active_discovery_sessions"))
    broad_signal = broad_goal_signal(intent_lower)
    feat_signal = feature_signal(intent_lower)
    if has_map and has_discovery and not broad_signal and not feat_signal:
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="unclear continuation target",
            route=None,
            confidence="low",
            reason="Both map and discovery sessions are active, but the intent does not identify which one to continue.",
            question="Which session are you continuing: the project map or the feature discovery?",
            options=[
                {"route": "/at-map", "reason": f"Resume map session {state['active_map_sessions'][0]}"},
                {"route": "/at-discover", "reason": f"Resume discovery session {state['active_discovery_sessions'][0]}"},
            ],
        )
    if has_map and broad_signal:
        session = state["active_map_sessions"][0]
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="broad-goal continuation",
            route="/at-map",
            confidence="high" if not state.get("incomplete_state") else "medium",
            reason=f"An active map session ({session}) already exists for project-level work.",
            alternative="/at-status",
            session_slug=session,
        )
    if has_discovery and feat_signal:
        session = state["active_discovery_sessions"][0]
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="feature discovery continuation",
            route="/at-discover",
            confidence="high" if not state.get("incomplete_state") else "medium",
            reason=f"An active discovery session ({session}) already exists for feature-level work.",
            alternative="/at-status",
            session_slug=session,
        )

    best_route, best_score = pick_best_route(intent_lower)
    if explicit_command:
        best_route = explicit_command
        best_score = 10

    if state.get("specs_with_open_drift") and is_status_or_vague(intent_lower, best_score):
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="status request with open drift",
            route="/at-status",
            confidence="medium",
            reason="The repo has open drift findings, so status should surface them as the next recommended action.",
            alternative="/at-audit",
        )

    if best_route is None:
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="unclear",
            route="/at-status",
            confidence="low",
            reason="The request does not map cleanly to one workflow command.",
            alternative="/at-discover",
            question="Do you want to decompose a broad goal, refine one feature idea, or just see the current workflow state?",
            options=[
                {"route": "/at-status", "reason": "Show current governed workflow state"},
                {"route": "/at-map", "reason": "Decompose a broad project goal"},
                {"route": "/at-discover", "reason": "Refine one feature-sized idea"},
            ],
        )

    if best_route == "/at-plan":
        if state.get("spec_count", 0) == 0:
            redirect = redirect_without_specs(intent_lower)
            return make_result(
                state=state,
                intent=normalized_intent,
                interpretation="planning intent without specs",
                route=redirect,
                confidence="medium",
                reason="Planning cannot start because no governed spec exists yet.",
                alternative="/at-status",
            )
        if state.get("specs_without_plan"):
            return make_result(
                state=state,
                intent=normalized_intent,
                interpretation="planning intent",
                route="/at-plan",
                confidence="high" if not state.get("incomplete_state") else "medium",
                reason=f"Planning is still missing for {', '.join(state['specs_without_plan'])}.",
            )
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="planning intent",
            route="/at-status",
            confidence="medium",
            reason="All current specs already have plans.",
            alternative="/at-review",
        )

    if best_route in NO_SPEC_REDIRECTS and state.get("spec_count", 0) == 0:
        redirect = redirect_without_specs(intent_lower)
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="late-stage intent without specs",
            route=redirect,
            confidence="medium",
            reason=f"{best_route} requires an existing governed spec, but none exist yet.",
            alternative="/at-status",
        )

    if best_route == "/at-eval":
        if state.get("eval_gaps"):
            return make_result(
                state=state,
                intent=normalized_intent,
                interpretation="evaluation intent",
                route="/at-eval",
                confidence="high" if not state.get("incomplete_state") else "medium",
                reason=f"Evaluation planning is still missing for {', '.join(state['eval_gaps'])}.",
            )
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="evaluation intent",
            route="/at-status",
            confidence="medium",
            reason="All current specs already have eval plans.",
            alternative="/at-observe",
        )

    route_reasons = {
        "/at-review": "The request is asking to tighten or review an existing spec.",
        "/at-implement": "The request is asking to start governed implementation work.",
        "/at-audit": "The request explicitly asks for drift detection or audit.",
        "/at-retro": "The request is asking for post-delivery learning or retrospective review.",
        "/at-observe": "The request is asking to record or review runtime observations.",
        "/at-adr": "The request explicitly asks to document an architectural decision.",
        "/at-ask": "The request is asking for a focused question to a named specialist.",
        "/at-new": "The request is asking to create a new governed spec directly.",
    }
    if best_route in route_reasons:
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation=best_route.replace("/at-", "").replace("-", " "),
            route=best_route,
            confidence="high" if not state.get("incomplete_state") else "medium",
            reason=route_reasons[best_route],
        )

    if best_route == "/at-init":
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="explicit initialization intent",
            route="/at-init",
            confidence="high" if not state.get("incomplete_state") else "medium",
            reason="The user explicitly requested governance initialization and no hard gate blocks it.",
        )

    if best_route == "/at-bootstrap-from-code":
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="explicit bootstrap intent",
            route="/at-bootstrap-from-code",
            confidence="high" if not state.get("incomplete_state") else "medium",
            reason="The user explicitly requested bootstrap-from-code and no hard gate blocks it.",
        )

    if best_route == "/at-map":
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="broad product goal",
            route="/at-map",
            confidence="high" if best_score > 1 and not state.get("incomplete_state") else "medium",
            reason="The request spans project-level decomposition rather than one feature spec.",
            alternative="/at-discover",
        )

    if best_route == "/at-discover":
        return make_result(
            state=state,
            intent=normalized_intent,
            interpretation="single feature idea",
            route="/at-discover",
            confidence="high" if best_score > 0 and not state.get("incomplete_state") else "medium",
            reason="The request is feature-sized and should be refined before spec creation.",
            alternative="/at-new",
        )

    return make_result(
        state=state,
        intent=normalized_intent,
        interpretation="status or fallback intent",
        route="/at-status",
        confidence="medium" if best_score > 0 else "low",
        reason="Status is the safest fallback when the request is vague or explicitly asks what to do next.",
        alternative="/at-discover" if state.get("spec_count", 0) == 0 else "/at-plan",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Route /at intent deterministically using inspected repository state.",
    )
    parser.add_argument(
        "--intent",
        default="what should I do next?",
        help="Raw user intent text for the /at facade.",
    )
    parser.add_argument(
        "--repo",
        type=pathlib.Path,
        default=None,
        help="Project root path (auto-detected from CWD if omitted).",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indent width; use 0 for compact output (default: 2)",
    )
    args = parser.parse_args()

    repo = args.repo.resolve() if args.repo else inspect_state.find_project_root(pathlib.Path.cwd())
    if repo is None:
        state = {
            "repo_root": None,
            "governed": False,
            "has_specs": False,
            "spec_count": 0,
            "active_map_sessions": [],
            "completed_map_sessions": [],
            "active_discovery_sessions": [],
            "completed_discovery_sessions": [],
            "specs_without_plan": [],
            "specs_with_plan": [],
            "specs_with_open_drift": [],
            "eval_gaps": [],
            "observation_gaps": [],
            "has_existing_codebase": False,
            "bootstrap_candidate": False,
            "incomplete_state": True,
            "warnings": ["Could not determine project root: no .specify/ or .git/ found."],
        }
    else:
        state = inspect_state.inspect(repo)

    print(json.dumps(route(args.intent, state), indent=args.indent or None))


if __name__ == "__main__":
    main()
