# Archive: Customer Credit Limit Warning

## Metadata
- Task: customer-credit-limit-warning
- Complexity: Level 2
- Completed: 2026-09-02

## Summary

Added a two-tier (yellow/red) credit-limit warning banner to the Sale Order form via a new addon module, `addons/sale_credit_limit_warning/` — the first custom addon in this project. The banner supersedes the stock single-tier `partner_credit_warning` banner on the Sale Order form view only (that field/logic is left untouched everywhere else, e.g. customer invoices).

The banner shows yellow (`alert-warning`) when a customer's projected credit exposure (`credit + credit_to_invoice + this order's amount_total`) reaches 80-99.99% of their `credit_limit`, and red (`alert-danger`) at ≥100%. It states the credit limit, current outstanding receivables, and the order's own contribution as three distinguishable figures. No banner shows when the customer has no credit limit set or is well within it.

## Solution

- New non-stored computed fields on `sale.order`: `credit_limit_warning_level` (Selection: `none`/`warning`/`danger`) and `credit_limit_warning_message` (Text), computed via `.sudo()` so non-Accounting users see the banner without an `AccessError`.
- Compute is gated on `order.state in ('draft', 'sent')` and `company_id.account_use_credit_limit` (added during code review — the initial version was missing this gating).
- View change hides the stock `partner_credit_warning` div (`invisible="1"`) and inserts the two new alert divs in its place, following the existing two-tier Selection-driven pattern already used in `addons/account_edi/views/account_move_views.xml`.
- Delivered in two phases: Phase 1 (module scaffold + compute logic, commit `b42ba443`) and Phase 2 (view integration + access/e2e tests, commit `e476ea0b`).
- All 5 acceptance criteria met (AC-ENTRY-1, AC-HAPPY-1/2/3, AC-ERROR-1), verified by 10/10 tests passing in a real Docker/Postgres environment (`odoo-bin --test-enable`), not mocked.

## Files Changed

- `addons/sale_credit_limit_warning/__init__.py` — module init
- `addons/sale_credit_limit_warning/__manifest__.py` — manifest, `depends: ['sale']`
- `addons/sale_credit_limit_warning/models/__init__.py` — model import
- `addons/sale_credit_limit_warning/models/sale_order.py` — `credit_limit_warning_level`/`credit_limit_warning_message` compute fields on `sale.order`
- `addons/sale_credit_limit_warning/views/sale_order_views.xml` — hides stock banner, inserts two-tier alert-warning/alert-danger pair
- `addons/sale_credit_limit_warning/tests/__init__.py`, `tests/test_credit_limit_warning.py` — 10 tests (compute correctness at threshold boundaries, access-rights regression, view-arch assertion, e2e reactivity)
- `memory-bank/tasks/customer-credit-limit-warning.md` — full plan + execution state
- `memory-bank/reflection/customer-credit-limit-warning-reflection.md` — task + ecosystem reflection
- `memory-bank/agent-rules/_learned/agent-scope-boundaries.md`, `interrupted-build-recovery.md` — learnings extracted from this task's reflection

## Notes

- Two interpretive Level-2 decisions were made directly (no creative phase) and documented transparently in the task file's spec for reviewer visibility: (1) "current outstanding receivables" = `credit + credit_to_invoice`, matching Odoo's own combined-exposure convention; (2) the new banner supersedes rather than stacks alongside the stock banner on this one view.
- Guard & Recovery: Phase 1 safely absorbed uncommitted work inherited from a prior interrupted build (verified against the plan before proceeding). Phase 2's Documentation Agent made its own out-of-scope git commits, one of which correctly failed the commit-guard's production/test split check (C2); recovered via `git reset --soft` + re-squash with no content lost. See the reflection document for the full analysis and two extractable learnings derived from these incidents.
- As part of this archive, `memory-bank/projectConfig.md` was corrected: `metadata_branch`/`pr_target`/`protected_branches` pointed at a nonexistent `main` branch — this repo (an Odoo fork with version-named branches) actually uses `banyan` as its trunk, per the config's own Notes section. Fixed to `banyan` with `archive_strategy: push-and-pr` (required now that `banyan` is protected).
