---
name: at-report-costs
description: Report Arpinine Harness token consumption and cost in Claude Code using the shared at-report-costs workflow.
---

Follow `commands/at-report-costs.md` from the assembled Arpinine Harness plugin root.

When using this skill in Claude Code:
- execute the same cost-reporting workflow defined in `commands/at-report-costs.md`
- prefer the `report_costs.py` script output before adding narrative explanation
- never synthesize token or cost numbers the runtime did not record; report incomplete runs as incomplete

If the shared command file and this wrapper ever disagree, follow `commands/at-report-costs.md`.
