# Tech Context

## Technology Stack

**Repository**: Odoo 18.0 (Community), `odoo/release.py`: `version_info = (18, 0, 0, FINAL, 0, '')`, LGPL-3.

### Languages
- **Python 3.10+** — server/ORM/business logic (`odoo/`, `addons/*/models`, `addons/*/wizard`). `requirements.txt` pins deps conditionally for Python 3.10–3.14. Docker image uses `python:3.12-slim`.
- **JavaScript (ES6+)** — web client, built on Odoo's own **OWL** (Odoo Web Library, vendored at `addons/web/static/lib/owl`), not React/Vue/Angular.
- **XML** — views, QWeb templates, data/demo files, manifest-declared report templates.
- **SQL** — raw SQL alongside the ORM in `odoo/osv`, `odoo/sql_db.py` (Postgres-specific).
- **SCSS/Less** — styling (Bootstrap-based), compiled via `node-less`/`libsass`.

### Frameworks
- **Odoo ORM** (`odoo/models.py`, `odoo/fields.py`, `odoo/api.py`) — maps Python model classes to Postgres tables; the foundation of the addon ecosystem.
- **HTTP layer**: custom, built on **Werkzeug** (`odoo/http.py`) — no Flask/Django.
- **OWL** — reactive JS component framework for the web client (post-v17).
- **QWeb** — XML templating engine, server-side (reports/emails) and client-side (compiled to JS for OWL).
- **RPC**: XML-RPC and JSON-RPC for external API access.
- **Testing**: Python — Odoo's own framework on `unittest` (`odoo/tests/`, `TransactionCase`/`HttpCase`, browser "tours"). JS — **Hoot** (`addons/web/static/lib/hoot`) plus legacy **QUnit**.
- **Concurrency**: gevent/greenlet-based worker model (`odoo/service`).

### Key Dependencies (requirements.txt / setup.py)
psycopg2 (Postgres driver) · lxml, MarkupSafe, Jinja2, docutils · Werkzeug · Pillow · reportlab, PyPDF2/PyPDF (+ external `wkhtmltopdf` binary) · openpyxl, XlsxWriter, xlrd/xlwt · babel, num2words, python-stdnum (i18n) · passlib, cryptography, pyopenssl (auth/crypto) · cbor2, qrcode (payment QR) · python-ldap · zeep (SOAP) · vobject (iCal/vCard) · geoip2 · libsass, rjsmin (asset pipeline; `rtlcss` via npm in Dockerfile) · gevent, greenlet.
Frontend JS libs (jQuery, Bootstrap, Luxon, Chart.js, PDF.js, DOMPurify, FullCalendar, etc.) are **vendored** under `addons/web/static/lib` — there is no npm-managed frontend dependency tree (no `package.json` in the repo).

### Build Tools / Package Managers
- pip + `requirements.txt` / `setup.py` (setuptools).
- No npm/yarn-managed JS project — JS deps are vendored; `npm` only used transiently in the Dockerfile to install `rtlcss`.
- Odoo's own asset-bundling system (QWeb `ir.asset` / `web.assets_*` bundles) replaces Webpack/Vite/Rollup.
- `MANIFEST.in`, `debian/` — source distribution / Debian packaging.

### Database / Storage
- **PostgreSQL** only (`postgres:16` in `docker-compose.yml`) — ORM uses Postgres-specific SQL features.
- **Filesystem filestore** for binary attachments (`odoo-filestore` volume, `/var/lib/odoo`); DB stores metadata only.

### Infrastructure
- `Dockerfile` (`python:3.12-slim`; system libs for lxml/ldap/ssl/jpeg/postgres; `node-less`, wkhtmltopdf-adjacent fonts, `rtlcss`).
- `docker-compose.yml` — `db` (postgres:16) + `odoo` (built from Dockerfile), `develop.watch` live-reload (`sync+restart` on `addons/`/`odoo/`, `rebuild` on `requirements.txt` changes).
- `docker/odoo.conf` mounted read-only for server config.
- No Kubernetes/Helm/Terraform in this repo.

### CI/CD
- **None checked into this repo** — `.github/` only has `ISSUE_TEMPLATE/` and `PULL_REQUEST_TEMPLATE.md`. Upstream Odoo's real CI/CD runs on Odoo's internal Runbot infrastructure, not represented here.

## Component Structure

- `odoo/` — core framework/runtime: ORM (`models.py` ~7.6k lines, `fields.py` ~5.4k lines, `api.py` ~1.6k lines), HTTP layer (`http.py`), module graph/loading/migration (`odoo/modules/`), shared utilities (`odoo/tools/`), test framework (`odoo/tests/`), service/worker layer (`odoo/service/`), low-level DB access (`sql_db.py`).
- `addons/` — 621 first-party stock modules (business apps + technical modules like `base`, `web`, `mail`) + custom addon modules (e.g., `sale_credit_limit_warning`).
- `odoo/addons/` — small set of framework-bootstrapping addons (`base`, `test_access_rights`, etc.).
- `odoo-bin` — entry point (`python odoo-bin -c <config> [options]`); `odoo/cli/` dispatches CLI commands; `odoo/__main__.py` allows `python -m odoo`.

Not a workspace/mono-repo tool (no Nx/Turborepo/Lerna/pnpm-workspaces/Cargo-workspace) — Odoo's own manifest-driven module system (`__manifest__.py` per addon, declaring `depends`) is its internal package/dependency manager.

## Development Commands

### Local Dev (Docker — this fork's setup, added in the "local docker setup" commit)
```
docker compose up            # or: docker compose watch   (live sync+restart on addons/ and odoo/ changes)
```
- Config: `docker/odoo.conf` (`db_host=db`, `db_user`/`db_password=odoo`, `admin_passwd=admin`, `dev_mode = reload`)
- Odoo served on `localhost:8069`
- `PYTHONDONTWRITEBYTECODE=1` set for dev

### Running the server directly
```
python odoo-bin -c <config.conf> [options]
```
Key CLI flags (`odoo/tools/config.py`): `-c/--config`, `-d/--database`, `-i/--init <modules>` (with `-d`), `-u/--update <modules>`, `--stop-after-init`.

### Testing
Built into `odoo-bin` (no separate pytest/unittest runner):
- `--test-enable` — run tests during install/update
- `--test-tags <spec>` — e.g. `:TestClass.test_func,/test_module,external`, or `/web.test_js[mail]` for JS/Hoot tests
- `--test-file <path>` — run a specific test file

Example:
```
python odoo-bin -c docker/odoo.conf -d <db> -i <module> --test-enable --stop-after-init
```

### Linting / Formatting
- `setup.cfg` — `[flake8]` with `extend-select = RST` (flake8-rst-docstrings), `extend-exclude = .git, .tx, debian, doc, setup`.
- No pre-commit, black, ruff, or ESLint config present.

### Environment Configuration
- INI-style `odoo.conf` (`[options]` section) — not `.env`. Two samples in-repo: `docker/odoo.conf` (Docker setup) and `debian/odoo.conf` (packaging sample).
- `requirements.txt` — pinned per Python-version markers (targets Ubuntu 24.04 / Debian 12/13 system packages).

### Coding Conventions
- LGPL-3 license. `CONTRIBUTING.md` points to the external Odoo wiki for contribution guidelines — no in-repo style guide beyond the flake8 config above.

## Test Strategy

- **Location**: `tests/` subdirectory inside each addon module (never mixed into `models/`); shared fixtures/base classes in a `common.py` per module (e.g. `SaleCommon` in `addons/sale/tests/common.py`).
- **Naming**: `test_*.py`.
- **Framework**: `odoo/tests/common.py` — `TransactionCase` (wraps each test in a rolled-back DB transaction) is the base for most tests; `HttpCase` (subclass) adds a real HTTP client for browser/JS "tour" tests.
- **Tagging**: `@tagged(...)` controls when tests run relative to module install (e.g. `'post_install'`, `'-at_install'`).
- **Scope emphasis**: mostly integration-style tests exercising ORM business logic end-to-end within a transaction (constraints, computed fields, order→invoice-type workflows), plus `HttpCase`-driven JS tours for UI testing and dedicated access-rights/controller tests.
