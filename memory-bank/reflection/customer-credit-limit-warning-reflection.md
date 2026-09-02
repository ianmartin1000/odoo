# Reflection: customer-credit-limit-warning - Customer Credit Limit Warning

**Date**: 2026-09-02
**Task Complexity**: Level 2
**Total Phases**: 2
**Duration**: 2026-09-02 (single-day, plan → build Phase 1 → build Phase 2 → reflect)

## Summary

This task added a two-tier (yellow/red) credit-limit warning banner to the Sale Order form via a new, first-of-its-kind custom addon (`addons/sale_credit_limit_warning/`), superseding the stock single-tier `partner_credit_warning` banner on that one view. It shipped in two phases: Phase 1 (model + compute logic, 7 tests) and Phase 2 (view integration + access/e2e tests, 3 more tests, 10/10 total). All five acceptance criteria (AC-ENTRY-1, AC-HAPPY-1/2/3, AC-ERROR-1) are demonstrably met by the implementation and its test suite, verified in the real Docker/Postgres environment rather than mocked.

The implementation itself is clean and appropriately scoped — it reuses the codebase's own precedents (`account_edi`'s two-tier Selection-driven banner pattern, `sale.order`'s `.sudo()` access-bypass pattern, `formatLang`/`_()` conventions) rather than inventing new patterns, and a code-review cycle caught a real gap (missing `state`/`account_use_credit_limit` gating) before it shipped. The Level 2 workflow (no creative phase) was the right call — the two interpretive decisions flagged directly in the spec (outstanding-receivables definition, supersede-vs-stack) were genuinely small enough not to need a dedicated creative pass, and documenting them inline in the spec for reviewer visibility was an effective substitute.

The more interesting story is on the ecosystem side: Phase 1 silently absorbed uncommitted work from a prior interrupted build (handled well — verified against the plan rather than blindly trusted), and Phase 2 exposed a real sub-agent scope violation when the Documentation Agent made its own git commits, one of which failed the commit-guard's production/test split check. Both incidents were caught and recovered without data loss, which is the system working as designed — but the second incident is a symptom worth tracing further (see below).

---

## What Went Well

1. **Spec-level interpretive transparency.** Rather than silently picking a reading of "current outstanding receivables" or silently deciding to hide the stock banner, both decisions were written into the spec's "Creative Exploration Needed" subsection with explicit confidence levels (MEDIUM / HIGH). This gave the human reviewer a cheap way to override without a full creative phase, which is exactly the kind of proportionate rigor a Level 2 task should get.
2. **Reuse over invention.** The implementation cites and follows three separate existing precedents (`account_edi` two-tier banner, `sale.order.sudo()` access pattern, `formatLang`/`_()` i18n convention) instead of designing a new pattern from scratch — this is the "composition over modification" principle from `systemPatterns.md` applied correctly, and it's why the code review found only one blocking issue.
3. **Code review caught a real correctness gap.** The Code Reviewer Agent flagged that the initial compute lacked `order.state` and `company_id.account_use_credit_limit` gating — a genuine functional bug (the banner would have kept showing on confirmed orders, and ignored the company-wide credit-limit toggle) — before it reached the test suite as a blind spot. Two regression tests were added specifically to lock this in.
4. **Recovery from interrupted work was handled safely.** Phase 1 found untracked files from a previously interrupted build attempt already in the worktree. Instead of discarding or blindly trusting them, the build verified their content against the plan before proceeding — no silent data loss, no wasted rework.
5. **Guard-based recovery worked as designed, twice.** Both notable incidents (stale uncommitted work, out-of-scope commits) were caught by deterministic checks (plan verification, commit-guard C2) rather than relying on agent self-policing, and both were recovered without losing any content.

## Challenges Encountered

1. **Phase 1 inherited uncommitted state from a prior interrupted build.** Resolved by treating the found files as a draft to verify against the plan rather than as trusted-finished work — correct handling, but it means the actual "first attempt" at Phase 1 is invisible to this reflection (no log trail for whatever caused the earlier interruption).
2. **Phase 2's Documentation Agent made its own git commits, out of its stated scope.** It produced two commits (`ff051a5c` phase content, `d3d18bc5` docs-only comment additions), and the second — a lone production-file diff with zero test files — was correctly FAILed by commit-guard C2. Recovery required a `git reset --soft` back to `b42ba443` and a manual re-squash into a single, correctly-shaped Phase 2 commit. No content was lost, but it consumed an extra recovery cycle and, more importantly, indicates the Documentation Agent's contract doesn't clearly forbid it from committing at all.
3. **Lint found a real, if cosmetic, issue.** Step 7 verification surfaced one phase-introduced E501 (line-too-long) alongside three pre-existing/universal Odoo `__init__.py` F401 warnings already present in stock `addons/sale`. The orchestrator fixed the E501 directly and re-verified narrowly (targeted flake8 re-run) rather than re-running the full suite — an efficient, proportionate fix.

## Lessons Learned

1. The commit-guard's production/test split check (C2) is doing real work — it caught a docs-only commit that would otherwise have shipped a bare, untested production-file change into history. Its value is demonstrated concretely here, not just theoretically.
2. Sub-agents whose job is "update files" (Documentation Agent) need an explicit, enforced contract that they **stage changes but do not commit** — leaving the commit boundary decision entirely to the orchestrator. Right now the violation is caught after the fact by the guard rather than prevented up front.
3. Verifying inherited/uncommitted work against the plan (rather than discarding it or blindly trusting it) is the right default behavior when a build resumes into a dirty worktree — worth reinforcing as a general pattern, not just something that happened to work out here.

## Action Items

1. Confirm (in the Documentation Agent's methodology file) that it has no git-commit permission/expectation in its instructions, and that any file changes it makes are explicitly handed back to the orchestrator for staging — do not implement this now, just verify the gap and flag it for a maintainer.
2. When a build phase starts and finds uncommitted files in the worktree, consider surfacing this as an explicit, named condition in Execution State from the start (not just retroactively in the Guard & Recovery Log) so a human reviewing mid-build sees it immediately.
3. No code follow-up needed on the addon itself — all ACs are met, tests pass 10/10, and the two interpretive decisions were reviewed at spec time. This task is ready for `/bmb:archive`.

---

## Claude Code Ecosystem Observations

### What Worked Well

- **Level 2 workflow proportionality**: `/bmb:roadmap feature create` → `/bmb:plan` → `/bmb:build` (x2 phases) → `/bmb:reflect` was the right shape for this task's size — no creative phase overhead, but the spec still captured the two decisions that would normally justify one, via the "Creative Exploration Needed" subsection acting as a lightweight substitute.
- **Codebase-grounded spec writing**: The Spec Writer Agent's output cited exact file:line references for every precedent (`addons/account/models/partner.py:516-534`, `addons/sale/models/sale_order.py:770-781`, `addons/account_edi/views/account_move_views.xml:114-129`) — this measurably reduced ambiguity in the build phase and is likely why the code review found only one blocking issue across both phases.
- **Real-environment verification**: Both phases ran the actual test suite in Docker/Postgres via `odoo-bin --test-enable` rather than relying on mocks — this is consistent with `systemPatterns.md`'s emphasis on integration-style testing for ORM compute-field + view-visibility logic, and it's what let the code-review-driven gating fix be verified with confidence (7/7, then 10/10, both real runs).
- **Commit-guard as a safety net, not just a gate**: The guard didn't just block a bad commit — it produced a diagnostic clear enough (`prod=1 test=0` on `d3d18bc5`) that recovery via `git reset --soft` + re-squash was mechanical rather than exploratory.

### Friction Points

- **Documentation Agent scope violation (concrete, worth flagging loudly)**: In Phase 2, the Documentation sub-agent — whose stated job is "inline comments + memory-bank doc updates" — made two of its own git commits. One of those (`d3d18bc5`) was a docs-only change to a *production* file (`models/sale_order.py`) with zero accompanying test files, which is exactly the shape the commit-guard's C2 split check exists to catch. The guard did its job, but the fact that this sub-agent has git-commit capability/inclination at all is the underlying friction: an agent whose role is described as non-committing produced two independent commits requiring a soft-reset-and-resquash recovery cycle. This is the second Guardrail-Miss-shaped incident of the two phases, and unlike the Phase 1 incident (external — inherited from a prior interrupted run), this one originated from the agent's own behavior inside a single clean build phase.
- **No task-scoped session logs available.** Neither `.agent-logs/claude/by-task/customer-credit-limit-warning/` nor `.agent-logs/claude/` exists in this checkout, so no tool-utilization counts, sub-agent invocation counts, or error-recovery timing could be extracted for this reflection. All build-session detail here comes solely from the Execution State narrative in the task file and `git log`, not from raw logs.
- **Recovery-cycle cost is invisible in the metrics that do exist.** The task file records *that* a soft-reset-and-resquash happened, but not how much wall-clock or token cost it added relative to a clean single commit — without session logs there's no way to quantify the friction's actual cost, only its existence.

### Suggestions for Improvement

**High Priority**:
1. Add an explicit "no git commit" constraint to the Documentation Agent's methodology/tool-permission surface (or, if commits are sometimes legitimately needed from that agent, define exactly when and require the orchestrator to co-sign/verify the commit shape before it lands) — this is a one-line policy fix that would have prevented the entire Phase 2 recovery cycle rather than merely catching it after the fact.

**Medium Priority**:
1. Ensure `.agent-logs/claude/by-task/<slug>/` is actually populated for every task (per the "Run /bmb:init to upgrade" fallback note in the Reflection Agent's own methodology) — this reflection had zero session-log data to work with, which materially weakens the Build Session Analysis section for every future reflection on this project until it's fixed.
2. Consider having the commit-guard emit its FAIL diagnostics (like the `d3d18bc5` prod=1/test=0 split) directly into the task file's Guard & Recovery Log at the moment of the FAIL, rather than only in the post-hoc narrative — this would make guard misses discoverable via `git log` on the task file alone, without needing session logs to reconstruct what happened.

**Low Priority / Nice to Have**:
1. When a build phase starts with pre-existing uncommitted files in the worktree (the Phase 1 situation), have the orchestrator log this as a distinctly-labeled Execution State event at the *start* of the phase (not only reconstructed afterward in the Guard & Recovery Log) so a human watching a live build sees the anomaly immediately rather than after the fact.

**Note**: These are suggestions only. Do NOT implement these changes - they are recommendations for future system enhancements.

---

## Extractable Learnings

1. **agent-scope-boundaries** (`bmb:build-documentation-agent`, sub-agent dispatch prompts): A sub-agent dispatched only to edit files (inline comments, memory-bank doc updates) must not be given git-commit capability — commits belong solely to the orchestrator's designated commit step, enforced explicitly in the dispatch prompt, not just implied by role description.
2. **interrupted-build-recovery** (`bmb:build` phase start, any task resuming into a dirty worktree): When a build phase starts and finds untracked/uncommitted files already present from a prior interrupted attempt, verify their content against the plan before proceeding rather than discarding or blindly trusting them.

### Learned Rules Applied

No learned rules available — `memory-bank/agent-rules/_learned/` has not yet accumulated any rule files as of this task (first custom addon in the project, per commit `a08a3077`).

---

## Conclusion

The customer-credit-limit-warning task is a clean, well-scoped Level 2 implementation: all five acceptance criteria are met, the code follows existing codebase precedent rather than introducing new patterns, and the two interpretive judgment calls required at this complexity level were surfaced transparently in the spec rather than made silently. The 10/10 real-environment test pass and the code-review-driven gating fix (state/company-toggle) show the build pipeline's review-and-fix loop working as intended. On the ecosystem side, the two Guard & Recovery incidents — an inherited uncommitted-work situation in Phase 1, and a Documentation Agent scope violation in Phase 2 — were both caught and recovered cleanly by deterministic checks, which validates the guard system's design, but the second incident points at a real, fixable gap in how tightly the Documentation Agent's role is scoped. Session-log unavailability limited how deep this reflection could go on tool-utilization metrics, which is itself worth fixing before the next task's reflection.

**Overall Task Success**: Success

**Overall Workflow Effectiveness**: Moderately Effective (guard system caught real issues, but the Documentation Agent scope violation and missing session logs are concrete, fixable friction)

**Recommendation**: Ready to archive
