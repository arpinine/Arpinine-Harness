#!/usr/bin/env python3
"""Shared specification-provider contract for Arpinine Harness."""

from __future__ import annotations

import copy
import json
import pathlib
import shutil
from typing import Any


PROVIDER_CONFIG_PATH = pathlib.Path(".specify/specification-provider.json")
# The provider layer currently supports one execution contract only.
# Adding another kind is a harness change, not a configuration change.
SUPPORTED_ACTION_KINDS = {"assistant-command"}


DEFAULT_PROVIDER: dict[str, Any] = {
    "provider": "spec-kit",
    "description": "Default provider built on the specify CLI.",
    "dependencies": [
        {"label": "spec-kit CLI", "command": "specify", "required": True},
        {"label": "uv/uvx", "command": "uvx", "required": False},
    ],
    "actions": {
        "constitution": {"kind": "assistant-command", "command": "/speckit.constitution"},
        "new_spec": {"kind": "assistant-command", "command": "/speckit.specify"},
        "plan": {"kind": "assistant-command", "command": "/speckit.plan"},
        "tasks": {"kind": "assistant-command", "command": "/speckit.tasks"},
        "implement": {"kind": "assistant-command", "command": "/speckit.implement"},
    },
}


def find_project_root(start: pathlib.Path) -> pathlib.Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".specify").exists() or (candidate / "Makefile").exists() or (candidate / ".git").exists():
            return candidate
    return None


def normalize_provider_name(name: str) -> str:
    normalized = name.strip().lower().replace("_", "-")
    if normalized == "speckit":
        return "spec-kit"
    return normalized


def _validate_action(action_name: str, action_value: dict[str, Any], provider_name: str) -> dict[str, Any]:
    kind = str(action_value.get("kind", "")).strip()
    command = str(action_value.get("command", "")).strip()
    if not kind:
        raise ValueError(f"provider {provider_name!r} action {action_name!r} is missing required field 'kind'")
    if kind not in SUPPORTED_ACTION_KINDS:
        allowed = ", ".join(sorted(SUPPORTED_ACTION_KINDS))
        raise ValueError(
            f"provider {provider_name!r} action {action_name!r} uses unsupported kind {kind!r}; supported kinds: {allowed}"
        )
    if not command:
        raise ValueError(f"provider {provider_name!r} action {action_name!r} is missing required field 'command'")
    return {"kind": kind, "command": command}


def _merge_action_defaults(provider_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized_name = normalize_provider_name(provider_name)
    if normalized_name == "spec-kit":
        merged = copy.deepcopy(DEFAULT_PROVIDER)
    else:
        merged = {
            "provider": provider_name,
            "description": "",
            "dependencies": [],
            "actions": {},
        }

    for key, value in payload.items():
        if key == "actions" and isinstance(value, dict):
            merged.setdefault("actions", {})
            for action_name, action_value in value.items():
                if isinstance(action_value, dict):
                    merged["actions"][action_name] = {
                        **merged["actions"].get(action_name, {}),
                        **action_value,
                    }
                else:
                    merged["actions"][action_name] = action_value
        else:
            merged[key] = value

    merged["provider"] = normalized_name
    merged.setdefault("description", "")
    merged.setdefault("dependencies", [])
    merged.setdefault("actions", {})
    validated_actions: dict[str, dict[str, Any]] = {}
    for action_name, action_value in merged["actions"].items():
        if not isinstance(action_value, dict):
            raise ValueError(
                f"provider {normalized_name!r} action {action_name!r} must be a JSON object with 'kind' and 'command'"
            )
        validated_actions[action_name] = _validate_action(action_name, action_value, normalized_name)
    merged["actions"] = validated_actions
    return merged


def provider_config_path(repo: pathlib.Path) -> pathlib.Path:
    return repo / PROVIDER_CONFIG_PATH


def load_provider_config(repo: pathlib.Path) -> dict[str, Any]:
    path = provider_config_path(repo)
    if not path.exists():
        payload = copy.deepcopy(DEFAULT_PROVIDER)
        payload["source"] = "default"
        payload["config_path"] = str(path.relative_to(repo))
        return payload

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid specification provider config: {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"invalid specification provider config: {path}: expected a JSON object")

    provider_name = str(raw.get("provider") or "spec-kit")
    payload = _merge_action_defaults(provider_name, raw)
    payload["source"] = str(path.relative_to(repo))
    payload["config_path"] = str(path.relative_to(repo))
    return payload


def provider_action(provider: dict[str, Any], action: str) -> dict[str, Any]:
    actions = provider.get("actions", {})
    value = actions.get(action, {})
    return value if isinstance(value, dict) else {}


def require_provider_action(provider: dict[str, Any], action: str) -> dict[str, Any]:
    action_payload = provider_action(provider, action)
    provider_name = str(provider.get("provider", "unknown"))
    if not action_payload:
        raise ValueError(f"Provider {provider_name} has no action {action!r} configured")
    return _validate_action(action, action_payload, provider_name)


def provider_command(provider: dict[str, Any], action: str) -> str:
    action_payload = require_provider_action(provider, action)
    command = action_payload.get("command", "")
    return str(command).strip()


def provider_dependency_checks(provider: dict[str, Any]) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    for item in provider.get("dependencies", []):
        command = str(item.get("command", "")).strip()
        if not command:
            continue
        checks.append(
            {
                "label": str(item.get("label", command)),
                "command": command,
                "required": bool(item.get("required", False)),
                "available": shutil.which(command) is not None,
            }
        )
    return checks
