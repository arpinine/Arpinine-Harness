# Arpinine Harness and The Two-Axis Framework

## Summary

The `two_axis_framework.pdf` document frames the space on two independent dimensions:

- **Axis 1**: AI Engineering Process Maturity
- **Axis 2**: Product AI-Nativeness


Arpinine Harness already operationalizes a high-maturity AI engineering process:

- a governed delivery loop: define, review, plan, decide, evaluate, implement, audit
- specialist roles instead of one generic assistant
- explicit artifact governance through `spec.md`, `plan.md`, ADRs, evals, observations, and coordination artifacts
- harness boundary design and runtime isolation
- multi-team operating model across assistants such as Claude and Codex
- measured evaluation and benchmark governance through benchmark sessions, baselines, dataset manifests, and observation history

This places Arpinine Harness solidly in **EP Level 4: Systematic Governance**, with meaningful elements of **EP Level 5: Operating Model Design**.

## Mapping To Axis 1: AI Engineering Process Maturity

### EP Level 1: Ad-Hoc Interaction

Arpinine Harness is clearly beyond this level. It is not a prompt bundle or a loose chat workflow.

### EP Level 2: Contextual Direction

Arpinine Harness includes this level, but goes further. It does not just improve prompts or provide advice. It structures the work through governed commands and artifacts.

### EP Level 3: Formal Planning

Arpinine Harness fully implements this level through:

- governed `spec.md`
- governed `plan.md`
- task sequencing
- ADR creation
- explicit evaluation planning

### EP Level 4: Systematic Governance

This is the strongest fit today. Arpinine Harness implements:

- always-on and scoped agent roles
- architecture and harness governance
- eval planning and review
- runtime observation
- drift detection
- benchmarked evaluation with history, baseline comparison, and fail-closed regression checks

### EP Level 5: Operating Model Design

Arpinine Harness has meaningful EP5 characteristics because it defines a reusable cross-assistant operating model:

- shared core workflow
- assistant-specific overlays instead of assistant-specific process divergence
- shared artifacts across implementations
- shared coordination model for concurrent assistant work

It is not just a project aid. It is becoming an organizational operating model for AI-assisted delivery.

## Mapping To Axis 2: Product AI-Nativeness

Arpinine Harness is not itself a product AI-nativeness framework. It is a governance layer that can support products at different AIN levels.

### AIN Level 1: AI-Free or Invisible

Arpinine Harness can still be used here as a delivery governance model, even if the product itself does not expose AI behavior.

### AIN Level 2: AI as Feature Layer

Arpinine Harness supports this well through scoped activation of the `ai-engineer`, eval planning, and AI-specific review when a feature uses AI or LLMs.

### AIN Level 3: AI-Callable Architecture

Arpinine Harness supports this through:

- harness strategy
- runtime boundary definition
- tool, memory, and permission model planning
- architecture and ADR governance

### AIN Level 4: Composable With Feedback

Arpinine Harness now partially supports this through:

- observation artifacts
- eval history
- benchmark sessions
- dataset manifests
- baselines
- regression comparison

This is a real capability, but still mainly as governance infrastructure rather than a full product runtime substrate.

### AIN Level 5: Self-Improving System

Arpinine Harness does not fully implement this level today.

It supports parts of the learning loop, but it is not yet a complete closed-loop self-improvement system with:

- strong cross-session trend reporting
- organization-wide experiment comparison
- first-class long-horizon learning analytics
- automated promotion of learned patterns into broadly measured operating controls

## Practical Positioning

The cleanest way to position the plugin is:

> Arpinine Harness operationalizes the process axis of the Two-Axis Framework.

More concretely:

- it turns AI engineering governance into commands, artifacts, agent responsibilities, and executable checks
- it helps teams move from ad hoc AI-assisted coding to a governed operating model
- it works regardless of whether the product is lightly AI-enabled or deeply AI-native

And the right qualifier is:

> It does not determine the product's AI-nativeness. It governs how teams build products across that spectrum.
