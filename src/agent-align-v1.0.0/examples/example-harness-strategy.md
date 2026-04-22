# Example Harness Strategy

Use this example when a product feature depends on an agent runtime but the team wants to keep the application decoupled from a specific harness implementation.

| Concern | Decision |
|---------|----------|
| Why harness is needed | The feature requires multi-step tool use, controlled memory, and approval-aware execution that would be expensive to rebuild from scratch. |
| Harness/runtime class | Embedded agent runtime |
| Product abstraction boundary | `CustomerSupportAgentRuntime` interface with one concrete adapter in the infrastructure layer |
| Tool access model | Search knowledge base, draft response, create support ticket; no arbitrary shell or filesystem access |
| Memory/state model | Session-scoped context only; no cross-user memory persistence |
| Permission and safety model | Ticket creation allowed automatically; account-impacting actions require explicit approval |
| Swap strategy | Only the adapter behind `CustomerSupportAgentRuntime` is runtime-specific; product logic depends on the interface only |

## Notes

- Product logic should call an internal runtime interface, not the harness SDK directly.
- Tool allowlists should be narrow and documented.
- Harness evaluation should test tool misuse, unsafe escalation, and failure recovery in addition to task success.
