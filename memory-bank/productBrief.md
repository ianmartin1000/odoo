# Product Brief

> This document captures the **product and project context** for development teams.
> It ensures all agents understand the product's purpose, users, constraints, **and the project's foundation**.

## Project Foundation

- **Project Name**: `odoo` (fork of `github.com/odoo/odoo`, remote `origin` = `https://github.com/DaKaZ/odoo.git`)
- **Objectives**: Run Odoo 18.0 as a locally developable instance via Docker, with live-reload of `addons/` and `odoo/` source trees. History was squashed to a single commit ("local docker setup") — this is effectively a fresh personal working copy of upstream Odoo 18.0 Community plus a Docker/dev-environment layer, not a product with custom addons (none present yet).
- **Scope**: Full Odoo application server (core framework in `odoo/`, all 621 first-party business/technical modules in `addons/`) plus a Docker Compose dev environment (Postgres 16 + Odoo on port 8069). Community edition only — no Enterprise-only modules present. No custom business logic layered on yet.
- **Repository Structure**: Poly-repo, single Python application (not an npm/nx/turborepo mono-repo).
  - `odoo/` — core ORM/HTTP framework, CLI (`odoo-bin`), tests
  - `addons/` — 621 first-party modules (business apps + technical modules like `base`, `web`, `mail`)
  - `doc/` — technical/changelog documentation
  - `docker/`, `Dockerfile`, `docker-compose.yml` — local dev environment
  - `setup/`, `debian/` — packaging/install scripts
- **Key Stakeholders**: Upstream maintained by Odoo S.A.; this fork is maintained by a single developer for local development (workspace owner: ian.martin@simunix.com).

## Product Overview

- **Name**: Odoo (this repo: a personal Docker-based dev fork of Odoo Community)
- **Value Proposition**: A single, integrated suite of open-source business applications (CRM, accounting, inventory, manufacturing, e-commerce, HR, project management, POS, etc.), adoptable app-by-app or combined into a full ERP.
- **Product Type**: Web-based ERP/business-application platform and framework (Python/PostgreSQL backend, OWL-based web client, XML-RPC/JSON-RPC APIs), extensible via a modular add-on architecture.
- **Stage**: Mature upstream (Odoo 18.0, Production/Stable). This fork/checkout is at "environment bootstrap" stage locally — no custom product work yet.

## Key Functionality

- Finance/Accounting (`account` + ~20 modules: e-invoicing/UBL/CII/Peppol, SEPA, payments)
- Sales & CRM (`sale`, `crm`, livechat, SMS, loyalty)
- Inventory/Warehouse & Manufacturing (`stock`, `mrp`, `purchase`)
- eCommerce & Website (`website` + ~50 modules: blog, forum, events, e-learning, mass mailing)
- Point of Sale (`point_of_sale`)
- Human Resources (`hr` + ~20 modules: attendance, contracts, expenses, recruitment, time off)
- Project & Field Service (`project`, `repair`, `fleet`, `maintenance`, timesheets)
- Marketing (`marketing_card`, `social_media`, `sms`, mass mailing)
- Authentication/Security (`auth_oauth`, `auth_ldap`, `auth_totp`, `auth_passkey`, `auth_password_policy`)
- 228 `l10n_*` country-specific localization modules (tax/fiscal/accounting rules)

## Markets Serviced

- **Primary Market**: Small-to-mid-market businesses needing an integrated ERP
- **Secondary Markets**: Retail/eCommerce, manufacturing, professional services, POS/hospitality-adjacent, HR/recruitment, events
- **Geographic Focus**: Global — 228 country-specific localization modules; EU e-invoicing standards (UBL/CII, Peppol) present
- **Market Size**: [Not discoverable from code]

## Competitive Landscape

- [Not discoverable from code]. (Publicly, Odoo competes with SAP Business One, Microsoft Dynamics, NetSuite, ERPNext — external knowledge, not sourced from the repo.)

## Key Personas

### Primary Users

| Persona | Role | Goals | Pain Points | Success Metrics |
|---------|------|-------|-------------|-----------------|
| Business Owner/Operations Manager | Runs day-to-day operations | Single system across sales, inventory, purchasing | Fragmented tools, manual reconciliation | Time saved, fewer errors |
| Accountant/Finance Staff | Manages books, invoicing, tax compliance | Accurate localized financial reporting/e-invoicing | Jurisdiction-specific tax complexity | Audit-ready books, on-time filings |
| Sales/CRM User | Manages leads, quotes, orders | Track pipeline, convert leads | Disconnected CRM and order systems | Win rate, quote turnaround |
| Warehouse/Manufacturing Staff | Manage stock, production, deliveries | Accurate inventory, on-time fulfillment | Stockouts, manual tracking | Fulfillment rate, inventory accuracy |
| Retail/POS Cashier | Process in-store sales | Fast, reliable checkout | POS/inventory sync issues | Transaction speed, uptime |

### Secondary Users

| Persona | Role | Goals |
|---------|------|-------|
| HR/Recruiter | Manage employees, hiring, time off | Streamlined HR processes |
| Marketing Staff | Run campaigns, manage website/e-commerce content | Lead generation, online sales |
| End Customer (Portal) | Self-service via customer portal/website | View orders, invoices, make payments |

### Administrators/Operators

| Persona | Role | Responsibilities |
|---------|------|------------------|
| Odoo Administrator | Configures company, users, modules | App installation, access rights, multi-company setup |
| Developer/Integrator (this fork's user) | Extends Odoo via custom addons | Module development, Docker-based local dev, deployment |

## User Flows

- **Primary Flow**: Install/enable needed "Apps" (modules), configure company/users, then operate day-to-day business processes.
- **Onboarding**: Module-based guided setup wizards per app (`base_setup`, `*_onboarding_data.xml`).
- **Key Workflows**:
  - Procure-to-pay (purchase → receipt → vendor bill)
  - Order-to-cash (CRM lead → quote → sales order → delivery → invoice → payment)
  - Manufacturing (BOM → production order → subcontracting → stock)
  - eCommerce (website_sale → order → fulfillment)
  - HR lifecycle (recruitment → onboarding → time off/attendance)

## Success Metrics & KPIs

[Not discoverable from code — no analytics/telemetry definitions or business KPI targets found in repo]

## Non-Functional Requirements

### Security
- **Authentication**: password (+ policy module), OAuth, LDAP, TOTP 2FA, Passkeys/WebAuthn, self-signup
- **Authorization**: Group-based RBAC (`res.groups`) + row-level security (`ir.rule`), declared per-module in `security/`
- **Compliance**: No explicit SOC2/HIPAA claims in repo; `SECURITY.md` documents responsible-disclosure for versions 16.0–18.0
- **Data Classification**: Not formally documented
- **Multi-tenancy**: Multi-company (`res_company`) within a database, plus standard Odoo multi-database architecture

### Scalability & Availability
- Traditional Python WSGI/HTTP server + PostgreSQL backend. This repo's Docker Compose is a **single-instance dev configuration**, not production-scale.

### Internationalization (i18n)
- **Supported Languages**: Extensive `.po` translation files across nearly all 621 modules (`.weblate.json` translation management config present)
- **Localization Needs**: Currency/date/number formatting and country-specific fiscal/tax logic are core built-in capabilities (`l10n_*` modules)

### Accessibility / Browser Support
- [Not discoverable from code in this pass]

## Integration Points

### External Systems

| System | Purpose | Protocol/Module | Direction |
|--------|---------|------------------|-----------|
| Stripe, PayPal, Adyen, Mollie, Razorpay, Authorize.net, Buckaroo, Worldline, Xendit, Nuvei, AsiaPay, Flutterwave, Mercado Pago | Payment processing | `payment_*` addons | Outbound |
| Twilio | SMS delivery | `sms_twilio` | Outbound |
| Google (Calendar, Gmail, reCAPTCHA, Account) | Calendar sync, email, spam protection | `google_*` addons | Bidirectional |
| Peppol / UBL / CII networks | E-invoicing | `account_edi_ubl_cii`, `account_peppol*` | Bidirectional |
| Azure, Google Cloud Storage | Attachment/file storage offload | `cloud_storage_azure`, `cloud_storage_google` | Outbound |
| LDAP directories | Enterprise authentication | `auth_ldap` | Inbound |
| OAuth providers | SSO login | `auth_oauth` | Inbound |
| Mondial Relay | Shipping/delivery | `delivery_mondialrelay` | Outbound |
| Jitsi | Video conferencing | `website_event_jitsi`, `website_jitsi` | Outbound |

### APIs Provided
- XML-RPC and JSON-RPC interfaces for external client/system integration.

## Constraints & Assumptions

### Technical Constraints
- Requires PostgreSQL (16 in this Docker setup) and Python >= 3.10
- LGPL-3 licensed — Community edition, no Enterprise-only modules present
- This fork's Docker setup targets local development (bind-mounted live reload), not production hardening

### Assumptions
- This checkout represents a developer's local environment for exploring/building on Odoo 18.0, not yet a distinct commercial product
- No custom business logic or branding added beyond Docker dev tooling — the "product" is currently stock Odoo Community

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Squashed git history (single commit) obscures provenance vs. upstream Odoo | Medium | Low-Medium | Track upstream Odoo release notes separately; preserve fuller history if long-term customization is planned |
| Docker Compose setup is dev-only (default `odoo`/`odoo` DB credentials) | High if deployed as-is | High | Never use this compose file as-is in production; introduce secrets management first |
| Community edition lacks Enterprise-only features | Medium | Medium | Confirm licensing requirements before assuming feature parity with Odoo Enterprise |

## Open Questions

- [ ] What is the intended purpose of this fork — custom addon development base, internal deployment, or evaluation only?
- [ ] Will custom addons be added, and in what namespace/location?
- [ ] Is production deployment planned (current docker-compose.yml is dev-only)?

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-08-27 | /bmb:init (brownfield explorer agents) | Initial creation |

## Last Refreshed

2026-08-27
