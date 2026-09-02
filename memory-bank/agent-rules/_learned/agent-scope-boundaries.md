---
name: Agent Scope Boundaries
globs: ["**/*"]
topics: ["sub-agent-dispatch", "git-commits", "documentation-agent"]
priority: low
auto_generated: true
derived_from: [customer-credit-limit-warning]
evidence_count: 1
last_validated: 2026-09-02
---

- A sub-agent dispatched only to edit files (e.g. inline comments, memory-bank doc updates) must not be given git-commit capability — commits belong solely to the orchestrator's designated commit step. Enforce this explicitly in the dispatch prompt, not just implied by the agent's role description.
  - Evidence: `customer-credit-limit-warning` Phase 2 — the Documentation Agent made two of its own commits, one of which (`d3d18bc5`, a docs-only production-file change with zero test files) failed the commit-guard's C2 split check, requiring a `git reset --soft` and manual re-squash to recover.
