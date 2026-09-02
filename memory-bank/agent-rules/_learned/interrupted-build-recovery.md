---
name: Interrupted Build Recovery
globs: ["**/*"]
topics: ["build-resumption", "dirty-worktree", "phase-start"]
priority: low
auto_generated: true
derived_from: [customer-credit-limit-warning]
evidence_count: 1
last_validated: 2026-09-02
---

- When a build phase starts and finds untracked/uncommitted files already present from a prior interrupted attempt, verify their content against the plan before proceeding — do not discard them and do not blindly trust them as finished work.
  - Evidence: `customer-credit-limit-warning` Phase 1 — inherited uncommitted module scaffold/compute logic/tests from a previously interrupted build; verifying against the plan before continuing avoided both data loss and wasted rework.
