# AgentAlign Presentation

## Slide 1 - Goal, Why, And What It Addresses

**AgentAlign** is a plugin for AI-assisted software delivery that helps teams ship the software they intended to build, not just whatever code the model produced fastest.

**Why it exists**
- AI coding moves fast, but specs drift, architecture gets decided by accident, and quality checks are often skipped.
- Teams need governance without slowing delivery down.

**What it addresses**
- unclear or drifting requirements
- accidental architecture decisions
- missing security, deployment, and evaluation thinking
- weak coordination when multiple assistants work in the same repo

**Core idea**
- one plugin
- one workflow
- a virtual delivery team behind it: product, architecture, TDD, security, evaluation, and drift detection

---

## Slide 2 - Process

**AgentAlign delivery loop**

1. **Define** the feature in `spec.md`
2. **Refine** the spec until it is measurable and implementable
3. **Plan** the architecture, tasks, boundaries, and test strategy
4. **Decide** important architecture choices in ADRs
5. **Evaluate** quality gates and success criteria
6. **Execute** implementation task by task with TDD and review
7. **Realign** by auditing drift between intent, decisions, code, and runtime behavior

**How it works**
- the user answers focused questions in chat
- the plugin updates the right artifact directly
- specialist roles activate at the right stage instead of one generic assistant doing everything

**Key benefit**
- fast AI-assisted delivery with traceability, ownership, and quality control

---

## Slide 3 - How To Use It

**Typical usage flow**

```bash
/agent-align:at-init
/agent-align:at-new "Feature request"
/agent-align:at-review .specify/specs/<slug>/spec.md
/agent-align:at-plan .specify/specs/<slug>/
/agent-align:at-adr new "Important decision"
/agent-align:at-eval plan .specify/specs/<slug>/
/agent-align:at-implement .specify/specs/<slug>/
/agent-align:at-audit .specify/specs/<slug>/
```

**What the user does**
- provide the feature request
- answer clarification questions
- review the generated artifacts
- approve or adjust decisions when needed

**What the plugin does**
- creates and updates `spec.md`, `plan.md`, ADRs, eval, and coordination artifacts
- coordinates specialist roles
- helps multiple assistant teams work safely in the same repository

**Closing message**
- AgentAlign turns AI coding from a fast code-generation session into a governed delivery workflow.
