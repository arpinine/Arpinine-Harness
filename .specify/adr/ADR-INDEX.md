# ADR Index

| Number | Title | Status | Governs | Covers |
|--------|-------|--------|---------|--------|
| ADR-0001 | Separate shared core from assistant-specific implementations | Accepted | specs/001-plugin-abstraction | decision:001-plugin-abstraction:core-impl-separation |
| ADR-0002 | Stable dist/plugins/ dir as local marketplace registration target | Accepted | specs/001-plugin-abstraction | decision:001-plugin-abstraction:local-marketplace-registration-path |
| ADR-0003 | assemble target as composition primitive for build and install | Accepted | specs/001-plugin-abstraction | decision:001-plugin-abstraction:assemble-as-build-primitive |
| ADR-0004 | Specialized role-based agent team | Accepted | specs/002-arpinine-harness-core-workflow | decision:002-arpinine-harness-core-workflow:agent-team-structure |
| ADR-0005 | Shared file-based task coordination for multi-team execution | Accepted | specs/007-multi-team-task-coordination | decision:007-multi-team-task-coordination:shared-file-based-task-coordination |
| ADR-0006 | Centralize cross-language style standards under a shared repository directory | Accepted | specs/008-cross-language-code-style-governance | decision:008-cross-language-code-style-governance:canonical-style-config-directory |
| ADR-0007 | Add operational measurement and benchmark governance artifacts | Accepted | specs/009-operational-measurement-and-benchmark-governance | decision:009-operational-measurement-and-benchmark-governance:benchmark-history-baseline-model |
| ADR-0008 | PreToolUse hooks as blocking enforcement gates | Accepted | specs/002-arpinine-harness-core-workflow | decision:002-arpinine-harness-core-workflow:hook-enforcement-as-hard-gate |
| ADR-0009 | Plain-text version-controlled artifact store under .specify/ | Accepted | specs/002-arpinine-harness-core-workflow | decision:002-arpinine-harness-core-workflow:plain-text-artifact-store |
| ADR-0010 | Machine-readable AIN fields in spec.md as the gating source of truth | Accepted | specs/004-ain-readiness-gates | decision:004-ain-readiness-gates:machine-readable-ain-source-of-truth |
| ADR-0011 | Shared JSON violation contract as the output format for rule execution | Accepted | specs/005-deterministic-rule-engine | decision:005-deterministic-rule-engine:shared-json-violation-contract |
| ADR-0012 | Semantic drift detection as opt-in LLM-judge at audit time | Accepted | specs/002-arpinine-harness-core-workflow | decision:002-arpinine-harness-core-workflow:semantic-drift-detection-mechanism |
| ADR-0013 | One shared ContextCompressionProvider abstraction with swappable implementations | Accepted | specs/011-context-compression-governance | decision:011-context-compression-governance:provider-abstraction |
| ADR-0014 | Consume headroom as the external default compression dependency | Accepted | specs/011-context-compression-governance | decision:011-context-compression-governance:headroom-dependency |
| ADR-0015 | Whole-payload compression via local proxy interception with passthrough fallback | Accepted | specs/011-context-compression-governance | decision:011-context-compression-governance:proxy-interception |
| ADR-0016 | Record the compression enable/disable toggle in the constitution at /at-init | Accepted | specs/011-context-compression-governance | decision:011-context-compression-governance:constitution-toggle |
| ADR-0017 | Deterministic golden-session replay benchmark as the evaluation framework | Accepted | specs/011-context-compression-governance | decision:011-context-compression-governance:eval-framework |
| ADR-0018 | CCR original store location, access policy, and no-sync invariant | Accepted | specs/011-context-compression-governance | decision:011-context-compression-governance:ccr-store-location |
| ADR-0019 | Compression proxy lifecycle — per-session activate/deactivate | Accepted | specs/011-context-compression-governance | decision:011-context-compression-governance:proxy-lifecycle-model |
| ADR-0020 | Out-of-host launcher as the runtime delivery mechanism for compression | Accepted | specs/011-context-compression-governance | decision:011-context-compression-governance:launcher-runtime-delivery |
