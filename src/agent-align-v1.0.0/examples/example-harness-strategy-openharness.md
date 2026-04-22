# Example Harness Strategy: OpenHarness

Use this example when the product feature depends on an embedded agent runtime and the team chooses OpenHarness as the implementation substrate.

| Concern | Decision |
|---------|----------|
| Why harness is needed | The feature requires multi-step tool use, controlled session state, approval-aware execution, and composable middleware that would be costly to rebuild directly in the product. |
| Harness/runtime class | Embedded agent runtime |
| Harness implementation | OpenHarness |
| Product abstraction boundary | `CustomerSupportAgentRuntime` interface with `OpenHarnessCustomerSupportAdapter` as the infrastructure implementation |
| Tool access model | Search knowledge base, draft response, create support ticket; no arbitrary shell or filesystem access in the product runtime |
| Memory/state model | Session-scoped context only; no cross-user persistent memory |
| Permission and safety model | Destructive or account-impacting actions require explicit approval through the harness permission callback |
| Evaluation implications | Evaluate task quality, tool misuse, approval correctness, and failure recovery in addition to standard task success |
| Swap strategy | Product code depends on `CustomerSupportAgentRuntime`; replacing OpenHarness should require changing the adapter only |

## Notes

- Keep OpenHarness imports in the adapter or infrastructure layer.
- Use OpenHarness tools and permissions through narrow, explicit registration.
- Avoid leaking OpenHarness event or message types into product domain code.
