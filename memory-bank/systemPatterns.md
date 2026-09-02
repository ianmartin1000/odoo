# System Patterns

## Guiding Principles

| Principle | Evidence |
|---|---|
| **Module isolation & explicit dependencies** | Every addon declares `depends` in `__manifest__.py`; a module cannot use another's models/views without listing it as a dependency, enforcing a controlled load graph (`odoo/modules/graph.py`, `loading.py`) |
| **Composition over modification** | Modules extend core behavior via `_inherit` (model extension) and controller subclassing (e.g. `CustomerPortal(payment_portal.PaymentPortal)`) rather than editing base code |
| **Security is mandatory, not optional** | Nearly every addon ships `security/ir.model.access.csv` + `ir_rules.xml`; access control is declarative and separated from business logic |
| **Declarative data/UI** | Views, demo data, and reports are defined in XML/QWeb, not hard-coded in Python |
| **ORM as the single data-access layer** | All persistence goes through `models.Model`/`fields.py`; raw SQL is reserved for performance-critical paths (`sql_db.py`/`osv`) |
| **Transactional test isolation** | `TransactionCase` rolls back each test's DB transaction, keeping tests independent and repeatable |
| **Route-level auth is explicit** | Every `@http.route` declares an `auth` policy (`user`, `public`, `bearer`, etc.) — no implicit default |
| **Versioned upgrade path** | `odoo/modules/migration.py` and `odoo/upgrade/` provide structured schema/data migration between versions |
| **Convention-based module scaffolding** | Directory names (`models/`, `views/`, `security/`, `controllers/`, `wizard/`, `report/`, `static/src/`) are a framework-wide convention (`odoo-bin scaffold` generates this shape) |

## Architecture Overview

Monolithic Odoo 18.0 source checkout. As of Phase 1 of customer-credit-limit-warning, the first custom addon module `addons/sale_credit_limit_warning/` has been introduced; previously the repository contained only stock upstream Odoo modules.

- `odoo/` — core framework/runtime, not itself an addon:
  - `odoo/models.py` — `BaseModel`, ORM core (CRUD, recordsets, `_inherit`/`_inherits`, SQL generation)
  - `odoo/fields.py` — field type descriptors (Char, Many2one, Selection, computed/related fields)
  - `odoo/api.py` — decorators (`@api.model`, `@api.depends`, `@api.constrains`, `@api.onchange`), `Environment`
  - `odoo/http.py` — Werkzeug-based HTTP layer, `Controller`, `@route`, `Request`/`Response`, sessions
  - `odoo/modules/` — module graph, loading order, migration, registry
  - `odoo/osv/` — legacy ORM helpers / domain expression evaluation
  - `odoo/tools/` — shared utilities (XML data loading, config, misc, mail, image, profiling)
  - `odoo/tests/` — test framework
  - `odoo/service/` — server/worker processes, DB connection pooling
  - `odoo/sql_db.py` — low-level PostgreSQL connection/cursor management
- `addons/` — 621 standard addon modules (`sale`, `account`, `crm`, `stock`, etc.), each self-contained.
- `odoo/addons/` — small set of framework-bootstrapping addons (`base`, `test_access_rights`, `test_apikeys`, …).
- `odoo-bin` — top-level entry point (`odoo.cli.main()`).

### Entry Points
- `odoo-bin` → `odoo.cli.main()`
- `odoo/cli/` — CLI command dispatch (server start, shell, scaffold, etc.)
- `odoo/__main__.py` — `python -m odoo`
- `odoo/service/` — WSGI server/workers (prefork, gevent, threaded modes)

### API Structure
- Controllers live in each addon's `controllers/`, subclassing `odoo.http.Controller`.
- Routes: `@http.route(route, type='http'|'json', auth='user'|'public'|'bearer'|..., methods=[...])`.
- `type='json'` routes serve internal RPC for the OWL web client; `type='http'` serves regular/portal pages.
- Controllers extend/inherit across addons (e.g. portal → payment → sale chains).
- Request context via `odoo.http.request` (thread/greenlet-local proxy exposing `request.env`).

### Data Layer
- Models: Python classes in each addon's `models/`, subclassing `models.Model`/`TransientModel`/`AbstractModel`, declared via `_name`/`_inherit`.
- Data/demo files: XML/CSV in `data/`/`demo/`, loaded by `odoo/tools/convert.py` per the manifest's `data` list.
- Security: `security/ir.model.access.csv` (model-level CRUD per group), `security/ir_rules.xml` (row-level), `security/res_groups.xml` — present in essentially every addon.
- Migrations: `odoo/modules/migration.py` + per-version scripts (typically under a `migrations/` folder), run during module upgrades.

### Shared Utilities
- `odoo/tools/` — cross-cutting helpers (dates/floats, misc, mail formatting, image processing, i18n, JS transpiling for assets, config parsing).
- Cross-addon shared logic exposed as `odoo.addons.<module>` importable packages and via mixins (`mail.thread`, `portal.mixin`) that other modules `_inherit`.

## Code Organization Patterns

- **Primary language**: Python (backend/ORM/controllers). JS/OWL (frontend). XML (views/templates/data/QWeb). SCSS/CSS (styling). CSV (access rights).

| Directory (per addon) | Dominant extension(s) | Purpose |
|---|---|---|
| `models/` | `.py` | ORM model definitions |
| `controllers/` | `.py` | HTTP/JSON route handlers |
| `views/` | `.xml` | Backend/website view definitions (form, list, kanban, QWeb templates) |
| `wizard/` | `.py` + `.xml` | Transient-model wizards (model + view) |
| `report/` | `.py` + `.xml` | QWeb PDF/HTML report definitions |
| `security/` | `.csv`, `.xml` | Access rights, record rules, groups |
| `data/` / `demo/` | `.xml`, `.csv` | Seed/demo data |
| `static/src/js` | `.js` | OWL components / frontend logic |
| `static/src/scss` | `.scss` | Styling |
| `static/src/xml` | `.xml` | OWL/QWeb JS templates |
| `i18n/` | `.po`/`.pot` | Translations |
| `tests/` | `.py` | Automated tests |

**New addon module shape** (canonical pattern, e.g. `addons/sale`):
```
my_module/
  __init__.py
  __manifest__.py      # name, version, depends, data, category, license
  models/
  controllers/
  views/
  wizard/
  report/
  security/ir.model.access.csv, ir_rules.xml, res_groups.xml
  data/
  static/src/{js,scss,xml}
  i18n/
  tests/
```
`__manifest__.py`'s `depends` list controls install/load order and inheritance availability; `data` lists XML/CSV files loaded on install, in order.

## Testing Patterns

- **Location**: `tests/` inside each addon module (e.g. `addons/sale/tests/`) — never mixed into `models/`.
- **Naming**: `test_*.py`; a shared `common.py` per module's tests folder defines reusable base classes/fixtures (e.g. `SaleCommon`).
- **Framework**: `unittest`-based via `odoo/tests/common.py` — `TransactionCase` (DB-transaction-per-test, rolled back) is the default base; `HttpCase` (subclass) adds a real HTTP client for browser/JS tour tests.
- **Tagging**: `@tagged(...)` controls install-relative execution (`'post_install'`, `'-at_install'`).
- **Scope emphasis**: integration-style tests exercising ORM business logic end-to-end within a transaction (constraints, computed fields, multi-step workflows), plus `HttpCase`-driven JS "tours" for UI testing, and dedicated access-rights/controller tests.

## Component Relationships

- Modules declare dependencies explicitly via `__manifest__.py: depends` — this is the module dependency graph banyan should respect when reasoning about "what does changing module X affect."
- Extension happens via `_inherit` (models) and subclassing (controllers), not by editing the depended-upon module directly — treat existing core/addon code as generally not-to-be-modified in place; new behavior belongs in a new or extending addon module.
