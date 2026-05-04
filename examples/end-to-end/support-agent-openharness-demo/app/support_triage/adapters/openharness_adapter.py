import asyncio
import concurrent.futures
import os
from typing import Callable

from pydantic import BaseModel, Field

from openharness.tools.base import BaseTool, ToolExecutionContext, ToolRegistry, ToolResult
from openharness.config.settings import PermissionSettings
from openharness.permissions.checker import PermissionChecker
from openharness.permissions.modes import PermissionMode
from openharness.engine.query_engine import QueryEngine
from openharness.engine.stream_events import AssistantTurnComplete, ToolExecutionStarted

from support_triage.application.triage_service import SupportAgentRuntime
from support_triage.domain.ticket import Ticket, TriageResult


SYSTEM_PROMPT = """You are a support triage drafting assistant.

When given a support ticket, call the draft_support_reply tool exactly once to produce a
professional first response. Use only the ticket content and the provided classification.
Do not say a support case has already been created.
Do not promise a resolution you cannot verify.
Do not mention internal tooling or model behavior.
"""


class DraftSupportReplyInput(BaseModel):
    ticket_id: str = Field(description="Ticket identifier")
    category: str = Field(description="Ticket category: billing, technical, or general")
    priority: str = Field(description="Ticket priority: urgent, normal, or low")
    subject: str = Field(description="Ticket subject line")
    body: str = Field(description="Ticket body text")
    customer_tier: str = Field(description="Customer tier: enterprise, standard, or free")


class DraftSupportReplyTool(BaseTool):
    """Single registered tool for drafting support replies.

    Marked read-only — OpenHarness auto-approves without a confirmation prompt.
    """

    name = "draft_support_reply"
    description = "Draft a professional first response for a support ticket."
    input_model = DraftSupportReplyInput

    def is_read_only(self, _arguments: BaseModel) -> bool:
        return True

    async def execute(self, arguments: DraftSupportReplyInput, _context: ToolExecutionContext) -> ToolResult:
        draft = (
            f"Thank you for contacting support. We have received your request regarding "
            f"'{arguments.subject}' and classified it as {arguments.category} with "
            f"{arguments.priority} priority. Our team will review it and follow up as soon "
            f"as possible. Please share any additional details that would help us resolve "
            f"this faster."
        )
        return ToolResult(output=draft)


def _build_engine(api_client, model: str) -> QueryEngine:
    registry = ToolRegistry()
    registry.register(DraftSupportReplyTool())

    settings = PermissionSettings(
        mode=PermissionMode.DEFAULT,
        allowed_tools=["draft_support_reply"],
    )
    checker = PermissionChecker(settings)

    return QueryEngine(
        api_client=api_client,
        tool_registry=registry,
        permission_checker=checker,
        cwd=".",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        max_turns=4,
    )


class OpenHarnessAdapter(SupportAgentRuntime):
    """OpenHarness-backed harness adapter.

    Only this file imports from openharness.*
    SupportTriageService depends on SupportAgentRuntime, not on this class.
    """

    def __init__(
        self,
        model: str | None = None,
        approval_callback: Callable[[Ticket, TriageResult], bool] | None = None,
    ):
        self._model = model or os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
        self._approval_callback = approval_callback or (lambda _ticket, _result: True)
        self.events: list[dict[str, object]] = []

        from openharness.api.client import AnthropicApiClient
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required.")
        self._engine = _build_engine(AnthropicApiClient(api_key=api_key), self._model)

    def draft_response(self, ticket: Ticket, category: str, priority: str) -> str:
        try:
            asyncio.get_running_loop()
            # Already inside a running event loop (web framework, async test suite).
            # Run the coroutine in a fresh thread so it gets its own loop.
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    asyncio.run, self._draft_async(ticket, category, priority)
                ).result()
        except RuntimeError:
            return asyncio.run(self._draft_async(ticket, category, priority))

    async def _draft_async(self, ticket: Ticket, category: str, priority: str) -> str:
        prompt = (
            f"Ticket ID: {ticket.ticket_id}\n"
            f"Customer tier: {ticket.customer_tier}\n"
            f"Category: {category}\n"
            f"Priority: {priority}\n"
            f"Subject: {ticket.subject}\n"
            f"Body: {ticket.body}\n\n"
            "Draft a support reply for this ticket using the draft_support_reply tool."
        )

        draft_text = ""
        async for event in self._engine.submit_message(prompt):
            if isinstance(event, ToolExecutionStarted):
                if event.tool_name == "draft_support_reply":
                    self.events.append({
                        "type": "tool_call",
                        "tool": "draft_support_reply",
                        "provider": "openharness",
                        "model": self._model,
                        "ticket_id": ticket.ticket_id,
                    })
            elif isinstance(event, AssistantTurnComplete):
                for block in event.message.content:
                    if hasattr(block, "text") and block.text:
                        draft_text = block.text
                        break

        # Reset session — enforces session-scoped memory per harness strategy
        self._engine.clear()
        return draft_text or "Draft response could not be generated."

    def request_case_creation_approval(self, ticket: Ticket, result: TriageResult) -> bool:
        # create_support_case is a product-level approval gate, not an OpenHarness tool.
        # OpenHarness governs tool execution; product code governs business actions.
        approved = bool(self._approval_callback(ticket, result))
        self.events.append({
            "type": "permission_check",
            "action": "create_support_case",
            "result": "approved" if approved else "denied",
            "ticket_id": ticket.ticket_id,
        })
        self.events.append({
            "type": "memory_write",
            "scope": "session",
            "key": f"triage:{ticket.ticket_id}",
        })
        return approved
