---
slug: customer-credit-limit-warning
legacy_id:
feature: customer-credit-limit-warning
status: BUILD_COMPLETE
---

# customer-credit-limit-warning: Customer Credit Limit Warning

**Complexity**: Level 2
**Status**: BUILD_COMPLETE
**Roadmap**: customer-credit-limit-warning
**Branch**: feature/customer-credit-limit-warning
**Worktree**: C:/Users/ian/odoo

## Task Description

Add a customer credit limit warning to the Sale Order form. The warning is a computed text message that appears as a banner when a customer is approaching or exceeding their credit limit. Yellow at 80% of limit, red over 100%. The message includes the credit limit, current outstanding receivables, and how much this order would add. Empty (no banner) when the customer has no credit limit set or is well within limit.

## Specification

**Feature Type**: End-User Feature
**Primary Persona**: Sales/CRM User (from `productBrief.md` § Key Personas — "manages leads, quotes, orders"; secondary: Accountant/Finance Staff, who owns the underlying `credit`/`credit_limit` data)
**Creative Exploration Needed**: No

**Codebase findings (context for the decisions below):** Stock Odoo 18 (`addons/sale`, `addons/account`) **already has a related but narrower feature** that this task extends rather than duplicates:

- `res.partner` (`addons/account/models/partner.py:516-534`) already exposes:
  - `credit` (Monetary, groups `account.group_account_invoice,account.group_account_readonly`) — "Total Receivable", i.e. already-invoiced unpaid amount.
  - `credit_to_invoice` (Monetary, same groups) — confirmed-but-not-yet-invoiced sale order amount (computed in `addons/sale/models/res_partner.py:80-107`, `_compute_credit_to_invoice`).
  - `credit_limit` (Float, `company_dependent=True`, same groups) — the limit itself; 0/unset means "no limit configured".
  - `res.company.account_use_credit_limit` (`addons/account/models/company.py:154`) — company-wide on/off switch for the whole credit-limit feature.
- `sale.order` already has a computed `partner_credit_warning` field (`addons/sale/models/sale_order.py:299-300, 770-781`) and a banner in the view (`addons/sale/views/sale_order_views.xml:301-305`):
  ```xml
  <div class="alert alert-warning" role="alert" invisible="partner_credit_warning == ''">
      <field name="partner_credit_warning"/>
  </div>
  ```
  but it (a) only fires once the customer is **at/over 100%** of the limit (`addons/account/models/account_move.py:1864`: `if not partner_id.credit_limit or total_credit <= partner_id.credit_limit: return ''`), (b) always renders `alert-warning` (yellow) — there is no red/danger tier, and (c) the message is a single combined "Total amount due" line, not three separately labeled figures.
- This task's requirements (80%-yellow / 100%-red two-tier banner, three explicit figures) are a genuine enhancement over stock behavior, not a re-implementation. **Decision**: replace/supersede the stock single-tier banner on the Sale Order form with the new two-tier one (see Scope Boundaries) rather than showing both, to avoid two overlapping/redundant banners once a customer is over limit.
- Precedent for a two-tier `alert-warning`/`alert-danger` pair driven by a Selection field's value, using `invisible="field != 'x'"` on sibling `<div>`s, exists in `addons/account_edi/views/account_move_views.xml:114-129` (driven by `edi_blocking_level` Selection `error`/`warning`). This is the pattern to follow.
- Precedent for computing such a message with `.sudo()` so non-Accounting users (e.g. a salesperson without `account.group_account_invoice`) still see the banner without an access error: `addons/sale/models/sale_order.py:778-779` (`order.sudo()`), and the existing regression test `addons/sale/tests/test_credit_limit.py::test_credit_limit_access` (`@users('notaccountman')`).
- Guiding principle from `systemPatterns.md`: "Composition over modification... new behavior belongs in a new or extending addon module," and `techContext.md`/`docker/odoo.conf` (`addons_path = /opt/odoo/addons,/opt/odoo/odoo/addons`) confirms new modules live as siblings under `addons/`. There is no existing custom-addons directory yet — this task creates the first one.

### Invocation Method
- **Location**: Sale Order form view, `sale.order`. New addon module `addons/sale_credit_limit_warning/` (new sibling module, `depends: ['sale']`), inheriting `sale.view_order_form` (`addons/sale/views/sale_order_views.xml`).
- **Element**: Two new `<div class="alert alert-warning">` / `<div class="alert alert-danger">` banners inserted via `<xpath expr="//div[hasclass('alert-warning')][field[@name='partner_credit_warning']]" position="after">`, mirroring the `account_edi` two-tier pattern. The stock `partner_credit_warning` banner is hidden on this view (`<xpath ... position="attributes"><attribute name="invisible">1</attribute></xpath>`) so only the new banner shows.
- **Visibility**: Passive/automatic — no button or menu; the banner is conditionally visible based on a new computed Selection field (`credit_limit_warning_level`: `none`/`warning`/`danger`), same visibility mechanism as the existing `partner_credit_warning` div (`invisible="credit_limit_warning_level != 'warning'"` / `!= 'danger'`).
- **Navigation**: Sales app → Orders → open/create a quotation → set a `partner_id` whose commercial partner has `credit_limit > 0` → banner appears immediately above the order lines, same position as today's stock banner (right after the `<header>` statusbar).
- **Confidence**: HIGH — exact insertion point, model, and field/view precedents all found in the codebase (cited above).

### Success Criteria
- **User sees**: A colored banner (`alert-warning` yellow at 80-99.99% of limit, `alert-danger` red at ≥100%) directly below the order's status bar, above the order lines, reading e.g. `"{partner name} is at {N}% of its credit limit of {credit_limit}.\nCurrent outstanding receivables: {credit + credit_to_invoice}.\nThis order would add: {amount_total}."` — see Scope Boundaries for the "current outstanding receivables" definition.
- **Verifiable at**: The Sale Order form (`sale.order`) in `draft`/`sent` state (matches stock's existing gating: `order.state in ('draft', 'sent')`, `addons/sale/models/sale_order.py:775`).
- **Data persisted**: None — `credit_limit_warning_level` and `credit_limit_warning_message` are non-stored computed fields (`compute=..., store=False`, the default), exactly like the existing `partner_credit_warning` field. No new table/column.
- **Observable within**: Immediate — the compute re-runs synchronously via `@api.depends('partner_id', 'order_line.price_total', 'amount_total', 'company_id')` whenever the dependent fields change in the form (same reactivity as the existing `partner_credit_warning`).

### Acceptance Criteria

#### AC-ENTRY-1: Salesperson sees the credit banner in the expected location on the Sale Order form
**Priority**: MUST
**Given** a user with Sales access opens or creates a quotation (`sale.order` in `draft` state) for a customer whose commercial partner has `credit_limit > 0`
**When** the customer's projected total exposure (`credit + credit_to_invoice + this order's amount_total`) reaches ≥ 80% of `credit_limit`
**Then** a banner appears immediately below the status bar and above the order lines — the same location the stock `partner_credit_warning` banner used to occupy

#### AC-HAPPY-1: Banner is yellow (alert-warning) when the customer is between 80% and 100% of their limit
**Priority**: MUST
**Given** a customer with `credit_limit` set, currently at `credit + credit_to_invoice` such that adding this order's `amount_total` brings total exposure to ≥80% and <100% of `credit_limit`
**When** the Sale Order form (re)computes `credit_limit_warning_level`
**Then** `credit_limit_warning_level == 'warning'`, the `alert-warning` div is visible, and its message states the credit limit, current outstanding receivables (`credit + credit_to_invoice`), and this order's contribution (`amount_total`) as three distinguishable figures

#### AC-HAPPY-2: Banner is red (alert-danger) when the customer is at or over 100% of their limit
**Priority**: MUST
**Given** the same setup as AC-HAPPY-1, but total projected exposure is ≥100% of `credit_limit`
**When** the form (re)computes `credit_limit_warning_level`
**Then** `credit_limit_warning_level == 'danger'`, the `alert-danger` div is visible (not the `alert-warning` one), and the message includes the same three figures

#### AC-HAPPY-3: No banner when there is no credit limit or the customer is well within it
**Priority**: MUST
**Given** either (a) the customer's `credit_limit` is 0/unset, or (b) total projected exposure is <80% of a configured `credit_limit`
**When** the form computes `credit_limit_warning_level`
**Then** `credit_limit_warning_level == 'none'`, `credit_limit_warning_message == ''`, and neither banner div is visible

#### AC-ERROR-1: Banner renders correctly for a salesperson without Accounting field access
**Priority**: MUST
**Given** a user who is a member of `sales_team.group_sale_salesman` but NOT `account.group_account_invoice`/`account.group_account_readonly` (mirrors `addons/sale/tests/test_credit_limit.py::test_credit_limit_access`, `@users('notaccountman')`)
**When** they open a Sale Order for a customer that is over their credit limit
**Then** the compute (using `.sudo()` on the partner/order, matching the existing `order.sudo()` pattern at `addons/sale/models/sale_order.py:779`) succeeds without an `AccessError`, and the correct-severity banner is shown — access-rights restrictions on `credit`/`credit_limit`/`credit_to_invoice` never surface as a traceback to the salesperson

### Scope Boundaries
- **In scope**:
  - New addon module `addons/sale_credit_limit_warning/` extending `sale.order` (model + view) only.
  - Two new non-stored computed fields on `sale.order`: `credit_limit_warning_level` (Selection: `none`/`warning`/`danger`) and `credit_limit_warning_message` (Text).
  - Threshold logic: ratio = `(partner.credit + partner.credit_to_invoice + order.amount_total/order.currency_rate) / partner.credit_limit` (company currency, mirroring the existing currency handling at `addons/sale/models/sale_order.py:780`); `danger` at ratio ≥ 1.0, `warning` at ratio ≥ 0.8, else `none`. No banner (`none`) when `credit_limit` is 0/falsy.
  - View change hides the stock `partner_credit_warning` div on the Sale Order form (via `invisible="1"` override) and inserts the two new divs in its place, so only one banner shows at a time.
- **Out of scope**:
  - Any change to `res.partner`, `account.move`, or the stock `partner_credit_warning` field/logic themselves — they are left intact (and still used elsewhere, e.g. customer invoices) and are only hidden on this one view.
  - Blocking order confirmation/validation — this is a passive informational banner only, not a hard stop (stock Odoo has no such block either; out of scope per task description, which only asks for a "computed text message").
  - Configuring/exposing the 80%/100% thresholds as user-editable settings — thresholds are fixed constants per the task description ("Yellow at 80% ... red over 100%").
  - Any change to POS, e-commerce, or invoice-flow credit warnings.
- **Dependencies**: `addons/sale` (for `sale.order`, `sale.view_order_form`) → transitively `addons/account` (for `credit`/`credit_limit`/`credit_to_invoice`/`account_use_credit_limit` on `res.partner`/`res.company`). New module manifest: `'depends': ['sale']`.
- **NFR implications**: None beyond what stock Odoo already does — same compute-field pattern, same field-level security groups inherited from `res.partner`, no new persisted data, no new external integration, no i18n concerns beyond wrapping user-facing strings in `_()` (existing convention throughout `addons/account/models/account_move.py:1866-1879`).

### Creative Exploration Needed
Specification is concrete — proceed to implementation planning. Two interpretive decisions were made directly (Level 2, no creative phase per the roadmap feature's complexity rationale) and are called out here for reviewer visibility rather than left implicit:
- **"Current outstanding receivables" = `credit + credit_to_invoice`, not `credit` alone.** Odoo's own stock credit-limit math (`_build_credit_warning_message`) treats `credit` (already invoiced) and `credit_to_invoice` (confirmed-not-yet-invoiced orders) as one combined exposure figure compared against `credit_limit`. Reusing that combined figure for "current outstanding receivables" keeps this feature's threshold math consistent with the field already named `credit_to_invoice` and with the pre-existing regression tests in `addons/sale/tests/test_credit_limit.py`. **Confidence: MEDIUM** — an alternate, narrower reading (`credit` only, i.e. strictly invoiced/unpaid) is defensible; flagging here so the human reviewer can override in the plan step if a stricter reading is intended.
- **Superseding, not stacking, the stock banner.** Showing both the old single-tier banner and the new two-tier banner simultaneously at ≥100% would be redundant/confusing on one form. Hiding the stock banner on this view only (leaving the field/model logic untouched for other consumers) was judged cleanest. **Confidence: HIGH.**

## User Journey Definition

**Feature Type**: End-User Feature
**Creative Phase Required**: No

### Invocation Method (End-User Features)
- **Location**: Sale Order form (`sale.order`), banner region directly below the status bar and above the order lines — see `## Specification` → Invocation Method for exact view/xpath.
- **Element**: Two conditionally-visible `<div class="alert alert-warning">` / `<div class="alert alert-danger">` blocks bound to the new `credit_limit_warning_level` field.
- **Visibility**: Automatic/computed — visible only when `credit_limit_warning_level` is `warning` or `danger`; no user action required to trigger it.
- **Navigation**: Sales app → Orders → open/create quotation → set customer → banner appears once the customer's projected exposure reaches ≥80% of their credit limit.

### Success Criteria (End-User Features)
- **User sees**: Yellow banner at 80-99.99% of limit, red banner at ≥100%, each stating the credit limit, current outstanding receivables (`credit + credit_to_invoice`), and this order's contribution (`amount_total`).
- **User can verify at**: The Sale Order form, in `draft`/`sent` state.
- **Data persisted**: None — non-stored computed fields only.
- **Observable within**: Immediate (synchronous compute on form field changes).

### NFR Verification (Infrastructure Features)
- **Test method**: N/A
- **Success metrics**: N/A
- **Observable at**: N/A

### Acceptance Criteria
- AC-ENTRY-1: Salesperson sees the credit banner in the expected location on the Sale Order form
- AC-HAPPY-1: Banner is yellow (alert-warning) when the customer is between 80% and 100% of their limit
- AC-HAPPY-2: Banner is red (alert-danger) when the customer is at or over 100% of their limit
- AC-HAPPY-3: No banner when there is no credit limit or the customer is well within it
- AC-ERROR-1: Banner renders correctly for a salesperson without Accounting field access

## Test Strategy

### Approach
- **Emphasis**: Integration (`TransactionCase`), matching `systemPatterns.md` § Testing Patterns — this is ORM compute-field + view-visibility logic, not isolated pure functions.
- **Target test count**: 8 across 2 phases (justified: 2 new computed fields with 3 threshold branches each to cover at their boundaries, plus one access-rights regression per `systemPatterns.md`'s existing precedent).

### File Organization
- **New test files**: `addons/sale_credit_limit_warning/tests/test_credit_limit_warning.py` (new module, new test file — nothing existing to extend).
- **Extend existing**: None. Reference (read-only, not modified) `addons/sale/tests/test_credit_limit.py` and `addons/sale/tests/common.py::SaleCommon` for setup patterns (creating a partner with `credit_limit` set, posting invoices to build up `credit`).

### What NOT to Test
- Odoo core's own `credit` / `credit_to_invoice` computation on `res.partner` — already covered by upstream Odoo test suites; this task only consumes those fields, it doesn't change how they're computed.
- Pixel-level CSS/rendering of `alert-warning`/`alert-danger` — out of scope; tests assert on the computed field values (`credit_limit_warning_level`, `credit_limit_warning_message`) and on view-arch visibility conditions, not rendered HTML.
- The stock `partner_credit_warning` field's own logic — untouched by this task, only hidden on one view.

### Per-Phase Test Guidance
- Phase 1: 5 tests — `credit_limit_warning_level`/`credit_limit_warning_message` compute correctness: (1) `none` when `credit_limit` unset/0, (2) `none` when projected exposure <80%, (3) `warning` at exactly 80% (boundary), (4) `warning` just under 100%, (5) `danger` at exactly 100% and above (boundary) — each also asserting the message contains all three figures (limit, `credit + credit_to_invoice`, `amount_total`).
- Phase 2: 3 tests — (1) `test_credit_limit_access`-style AC-ERROR-1 regression (salesperson without `account.group_account_invoice` can still read the computed fields via `.sudo()`, no `AccessError`), (2) view-arch assertion that the stock `partner_credit_warning` div is `invisible="1"` and the two new divs exist with correct `invisible` conditions on `sale.view_order_form` after this module installs, (3) end-to-end: create a real quotation via `SaleCommon` fixtures, add order lines until `amount_total` pushes exposure across the 80% boundary, assert the field flips from `none` to `warning` reactively.

## Implementation Roadmap

### New Source Files (pin path + extension)
- [x] `addons/sale_credit_limit_warning/__init__.py` — module init, imports `models`
- [x] `addons/sale_credit_limit_warning/__manifest__.py` — manifest: `depends: ['sale']`, `category`, `license: LGPL-3` (match repo license); `data: ['views/sale_order_views.xml']` to be added in Phase 2 when the view file exists
- [x] `addons/sale_credit_limit_warning/models/__init__.py` — imports `sale_order`
- [x] `addons/sale_credit_limit_warning/models/sale_order.py` — `_inherit = 'sale.order'`; adds `credit_limit_warning_level` (Selection, `store=False`) and `credit_limit_warning_message` (Text, `store=False`), `@api.depends('partner_id', 'order_line.price_total', 'amount_total', 'company_id', 'state')` compute method using `.sudo()`, gated on `state in ('draft', 'sent')` and `company_id.account_use_credit_limit` (added per code review, matching stock's own gating)
- [x] `addons/sale_credit_limit_warning/views/sale_order_views.xml` — `<record>` inheriting `sale.view_order_form`: xpath to `invisible=1` the stock `partner_credit_warning` div, xpath `position="after"` to insert the new `alert-warning`/`alert-danger` divs
- [x] `addons/sale_credit_limit_warning/tests/__init__.py` — imports `test_credit_limit_warning`
- [x] `addons/sale_credit_limit_warning/tests/test_credit_limit_warning.py` — `TransactionCase` (`SaleCommon`-based) tests per Test Strategy above; 10 tests (5 planned Phase 1 + 2 state/company-toggle regressions Phase 1 code-review + 3 Phase 2: access/view-arch/e2e-reactivity)

### Phases
- [x] Phase 1: Module scaffold + compute logic (`__init__.py`, `__manifest__.py`, `models/`, `tests/test_credit_limit_warning.py` compute tests) — delivers `credit_limit_warning_level`/`credit_limit_warning_message` on `sale.order`, verifiable via ORM/shell even without the view yet
- [x] Phase 2: View integration + access/e2e tests (`views/sale_order_views.xml`, remaining tests) — delivers the full entry-to-success flow: banner visible on the Sale Order form per AC-ENTRY-1/AC-HAPPY-1/2/3/AC-ERROR-1

### Observability Requirements
- **Applies**: No — no HTTP/GraphQL/gRPC handlers, background workers, or external service calls; this is a synchronous ORM compute field.

### API Requirements
- **REST API**: No
- **GraphQL API**: No

## Creative Phases

(none — Level 2, Creative Exploration Needed: No, per Specification)

---

## Execution State

**Build Status**: RUNNING
**Current Phase**: BUILD
**Phase Number**: 2 of 2
**Is Multi-Phase**: YES
**Build Started**: 2026-09-02
**Last Completed**: Step 1 (Phase 2 identified: View integration + access/e2e tests)
**Can Resume**: YES

### Current Build Step
**Step**: Step 3 - TDD Agent
**Status**: RUNNING
**Started**: 2026-09-02

### Active Sub-Agents
(none)

### Completed Steps
- Step 0.5 Git Setup: COMPLETE — single-worktree checkout at C:/Users/ian/odoo, already on feature/customer-credit-limit-warning (no separate worktree_root worktree in use for this repo)
- Step 1 Read Task Context: COMPLETE — Phase 1 of 2 identified (Module scaffold + compute logic)
- Step 3 TDD Agent: COMPLETE — 5 tests written (RED→GREEN) in addons/sale_credit_limit_warning/tests/test_credit_limit_warning.py against models/sale_order.py compute fields (work picked up from a prior interrupted build attempt's uncommitted files, verified against the plan)
- Step 6/7 Test Execution + Integration Verification: COMPLETE — module installed and full test run executed in the project's real Docker/Postgres environment (`docker compose build odoo` + `odoo-bin -i sale_credit_limit_warning --test-enable --test-tags /sale_credit_limit_warning --stop-after-init`); initial run: 5/5 tests passing, 0 failed, 0 errors
- Step 8 Code Reviewer Agent: COMPLETE — 1 BLOCKING issue found (compute missing `order.state`/`company_id.account_use_credit_limit` gating vs. the stock precedent the spec cites) + 3 non-blocking suggestions; security/dependency review PASS
- Fix + re-verify: COMPLETE — added state/company-toggle gating to `_compute_credit_limit_warning`, added 2 regression tests (confirmed-order gating, feature-disabled gating); re-ran full Docker test cycle — 7/7 tests passing, 0 failed, 0 errors
- Step 10 Update Memory Bank: COMPLETE — this file's Implementation Roadmap (file + phase checkboxes) and Execution State updated

### Guard & Recovery Log
- Phase 1: found untracked, uncommitted Phase 1 files already present in the worktree at build start (from a previously interrupted build for this same slug — the module scaffold, compute logic, and 5 of the 7 tests). Verified their content against the plan rather than re-writing from scratch, then ran them through the full review→fix→re-verify cycle before committing. No files were lost; commit-guard C1/C2/C3 all passed on the first commit attempt.
