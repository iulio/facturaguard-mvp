# FacturaGuard MVP

B2B SaaS MVP pentru monitorizarea conformării RO e-Factura.

## Include

- FastAPI backend
- SQLite local
- JWT auth
- upload CSV/XML/ZIP
- parsare XML UBL basic
- alerte automate
- email dry-run
- joburi programate cu APScheduler
- raport lunar JSON
- Next.js frontend
- Docker Compose
- GitHub Actions CI
- basic role/membership layer
- audit log
- backend API tests

## Local backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Local frontend

```bash
cd frontend
npm install
npm run dev
```

## Docker

```bash
docker compose up --build
```

## GitHub Actions

Pipeline inclus:

```txt
.github/workflows/ci.yml
```

Verifică:
- instalare backend
- import FastAPI app
- instalare frontend
- build Next.js

## Samples

```txt
backend/samples/invoices.csv
backend/samples/invoice.xml
backend/samples/ubl_invoice.xml
backend/samples/xml_batch.zip
```


---

## v0.5 additions

This version adds:

- `organization_members` table
- `audit_logs` table
- organization-level access helper
- mock invite endpoint for existing users
- audit log endpoint
- audit events for organization creation, invoice upload, alert resolution and status checks
- backend tests with `pytest`

### Run backend tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

### New endpoints

```txt
POST /organizations/{org_id}/members
GET  /organizations/{org_id}/audit-logs
```

`POST /organizations/{org_id}/members` expects:

```json
{
  "email": "client@example.com",
  "role": "client_viewer"
}
```

For this MVP, the user must already exist.


---

## v0.6 additions

This version adds a production-style database layer:

- PostgreSQL service in `docker-compose.yml`
- `DATABASE_URL` configuration
- `AUTO_CREATE_TABLES` flag
- Alembic migrations
- initial migration: `0001_initial_schema`
- CI migration check
- `Makefile` shortcuts

### Run with PostgreSQL

```bash
docker compose up --build
```

The backend runs:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Run migrations manually

```bash
cd backend
alembic upgrade head
```

### Create a new migration

```bash
cd backend
alembic revision --autogenerate -m "describe change"
```

### Local SQLite fallback

If `DATABASE_URL` is not set, the backend falls back to:

```txt
sqlite:///./facturaguard.db
```

For production, use PostgreSQL.


---

## v0.7 additions

This version introduces a connector abstraction for RO e-Factura/ANAF:

- `OrganizationIntegration` model
- mock ANAF connector
- deterministic status simulation for local development
- invoice fields:
  - `anaf_upload_id`
  - `last_synced_at`
- single invoice status sync endpoint
- bulk organization invoice status sync endpoint
- ANAF connection test endpoint
- Alembic migration `0002_anaf_integration`
- frontend button: `Mock ANAF sync`

### New endpoints

```txt
GET  /organizations/{org_id}/integrations/anaf
POST /organizations/{org_id}/integrations/anaf/test
POST /organizations/{org_id}/invoices/{invoice_id}/sync-status
POST /organizations/{org_id}/invoices/sync-statuses
```

### Important

The ANAF connector in v0.7 is a mock connector. It does not call ANAF/SPV.
It exists to stabilize the product architecture before implementing the live connector.


---

## v0.8 additions

This version adds exportable accountant-facing reports:

- monthly PDF report generated with ReportLab
- invoice CSV export
- audit events for PDF and CSV exports
- backend tests for CSV/PDF export
- frontend buttons:
  - `Export CSV`
  - `Raport PDF`

### New endpoints

```txt
GET /organizations/{org_id}/reports/monthly.pdf?year=2026&month=4
GET /organizations/{org_id}/invoices/export.csv
```

The PDF report includes:

- company identification
- monthly compliance summary
- top recurring errors
- recommendations
- problematic invoices table


---

## v0.9 additions

This version improves the accountant-facing dashboard:

- portfolio endpoint for all accessible organizations
- risk score per company
- risk labels: `high`, `medium`, `low`
- search by company name/CUI
- filter by risk level
- frontend portfolio table
- click a company row to select it in the operational dashboard

### New endpoint

```txt
GET /portfolio
GET /portfolio?risk=high
GET /portfolio?search=construct
```

The risk score is based on:

- rejected invoices
- overdue invoices
- near-deadline invoices
- unsent invoices
- open alerts
- issue ratio relative to total invoices


---

## v1.0 hardening additions

This version hardens the MVP foundation:

- central settings with `pydantic-settings`
- `.env` support
- configurable `DATABASE_URL`
- configurable CORS
- configurable JWT `SECRET_KEY`
- health endpoint:
  ```txt
  GET /health
  ```
- readiness endpoint with DB check:
  ```txt
  GET /ready
  ```
- basic in-memory rate limiting
- request timing header:
  ```txt
  X-Process-Time-Ms
  ```
- deployment notes in:
  ```txt
  docs/deployment.md
  ```

### Important production settings

Set these before deploying publicly:

```txt
ENVIRONMENT=production
SECRET_KEY=<long-random-secret>
AUTO_CREATE_TABLES=false
CORS_ORIGINS=https://your-domain.com
FG_EMAIL_DRY_RUN=false
RATE_LIMIT_ENABLED=true
```


---

## v1.1 additions

This version adds onboarding and invitations:

- `organization_invitations` table
- invitation tokens
- invitation expiry
- invite existing users by email
- accept invitation endpoint
- dry-run email notification for invitations
- frontend invitation panel
- audit logs:
  - `invitation.created`
  - `invitation.accepted`

### New endpoints

```txt
POST /organizations/{org_id}/invitations
GET  /organizations/{org_id}/invitations
POST /invitations/accept
```

### MVP limitation

For now, the invited user must already have an account.
The next production step is a public invitation acceptance page that supports account creation.


---

## v1.2 additions

This version improves invitation onboarding:

- public invitation details endpoint
- accept invitation and create account in one flow
- frontend page:
  ```txt
  /accept-invite?token=<token>
  ```
- automatic login after accepting invitation
- backend tests for public invitation acceptance

### New endpoints

```txt
GET  /invitations/public/{token}
POST /invitations/accept-with-account
```

### Flow

1. Accountant sends invitation.
2. Email contains `/accept-invite?token=...`.
3. Invited user opens link.
4. User creates password and accepts invite.
5. User is logged in automatically.


---

## v1.3 additions

This version adds password recovery and password change:

- password reset token table
- password reset request endpoint
- password reset confirmation endpoint
- authenticated password change endpoint
- dry-run reset email
- frontend page:
  ```txt
  /reset-password?token=<token>
  ```
- reset request UI on login screen
- backend tests for password reset and password change

### New endpoints

```txt
POST /auth/password-reset/request
POST /auth/password-reset/confirm
POST /auth/password-change
```


---

## v1.4 additions

This version adds original file storage for audit and compliance:

- local file storage service
- `organization_documents` table
- stores uploaded CSV/XML/ZIP files
- document metadata:
  - original filename
  - stored filename
  - content type
  - file size
  - uploaded user
- secure document listing by organization access
- secure document download endpoint
- audit logs:
  - `document.stored`
  - `document.downloaded`
- Docker volume for file storage
- frontend document table and download action

### New endpoints

```txt
GET /organizations/{org_id}/documents
GET /organizations/{org_id}/documents/{document_id}/download
```

### Storage setting

```txt
FILE_STORAGE_PATH=./storage
```

For production, replace local storage with S3-compatible object storage.


---

## v1.5 additions

This version introduces a storage abstraction:

- `StorageBackend` interface
- `LocalStorageBackend`
- `S3StorageBackend`
- S3-compatible storage support via `boto3`
- configurable storage backend:
  ```txt
  FILE_STORAGE_BACKEND=local
  ```
  or:
  ```txt
  FILE_STORAGE_BACKEND=s3
  ```
- storage documentation:
  ```txt
  docs/storage.md
  ```

### S3-compatible environment variables

```txt
S3_ENDPOINT_URL=
S3_REGION_NAME=eu-central-1
S3_BUCKET_NAME=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
```

Local storage remains the default for development.


---

## v1.6 additions

This version adds a SaaS billing/subscription skeleton:

- static pricing plans:
  - `one`
  - `starter`
  - `pro`
  - `agency`
- `organization_subscriptions` table
- organization subscription endpoint
- organization usage endpoint
- plan limits for:
  - max organizations
  - invoices per month
  - stored documents
- audit log for subscription updates
- frontend billing/usage panel
- backend tests for plans, subscription and usage

### New endpoints

```txt
GET  /billing/plans
GET  /organizations/{org_id}/subscription
POST /organizations/{org_id}/subscription
GET  /organizations/{org_id}/usage
```

### Notes

This is not connected to a real payment provider yet.
It prepares the domain model for Stripe, Netopia, SmartBill payments or manual invoicing.


---

## v1.7 additions

This version adds a NETOPIA mock payment provider:

- payment transaction table
- checkout session endpoint
- mock checkout page
- mock webhook endpoint
- automatic plan activation after simulated successful payment
- transaction listing endpoint
- audit logs:
  - `payment.checkout_created`
  - `payment.succeeded`
  - `subscription.activated_from_payment`
- frontend plan purchase now redirects to NETOPIA mock checkout
- backend tests for checkout + webhook + plan activation
- payment docs:
  ```txt
  docs/payments.md
  ```

### New endpoints

```txt
POST /organizations/{org_id}/billing/netopia-mock/checkout
GET  /organizations/{org_id}/billing/transactions
POST /billing/netopia-mock/webhook
```

This is a mock integration. It does not process real money.


---

## v1.8 additions

This version adds SaaS presentation pages:

- landing page:
  ```txt
  /landing
  ```
- pricing page:
  ```txt
  /pricing
  ```
- pricing page uses:
  ```txt
  GET /billing/plans
  ```
- marketing CSS and responsive layout
- marketing documentation:
  ```txt
  docs/marketing.md
  ```

The product can now be shown as a SaaS concept, not only as an internal dashboard.


---

## v1.9 additions

This version adds first-run onboarding:

- onboarding status endpoint:
  ```txt
  GET /onboarding/status
  ```
- onboarding wizard page:
  ```txt
  /onboarding
  ```
- guided steps:
  1. create first organization
  2. upload first CSV/XML/ZIP
  3. run Mock ANAF sync
  4. review dashboard
- dashboard links to onboarding
- backend tests for onboarding progression
- documentation:
  ```txt
  docs/onboarding.md
  ```


---

## v2.0 release polish

This version adds release-readiness tooling and documentation:

- demo seed script:
  ```bash
  make seed-demo
  ```
- smoke test:
  ```bash
  make smoke
  ```
- backend compile check in CI
- QA checklist:
  ```txt
  docs/qa-checklist.md
  ```
- release notes:
  ```txt
  docs/release-notes.md
  ```

### Demo login after seeding

```txt
demo@facturaguard.local
DemoPassword123!
```


---

## v2.1 audit dashboard

This version adds audit visibility:

- audit dashboard page:
  ```txt
  /audit
  ```
- audit filters by action/entity type
- audit CSV export
- audit summary endpoint
- audit documentation:
  ```txt
  docs/audit.md
  ```

### New endpoints

```txt
GET /organizations/{org_id}/audit-summary
GET /organizations/{org_id}/audit-logs/export.csv
```


---

## v2.2 notification preferences

This version adds per-organization notification settings:

- settings page:
  ```txt
  /settings
  ```
- configurable alert email
- enable/disable email alerts
- enable/disable alert categories
- near-deadline threshold
- daily digest flag for future digest feature
- audit log when settings change
- tests for notification settings

### New endpoints

```txt
GET /organizations/{org_id}/notification-settings
PUT /organizations/{org_id}/notification-settings
```


---

## v2.3 daily digest

This version adds daily digest email support:

- daily digest preview endpoint
- send digest now endpoint
- scheduler job for digest emails
- settings page buttons:
  - preview digest
  - send digest now
- audit event:
  ```txt
  digest.email_sent
  ```
- tests for digest preview/send
- documentation:
  ```txt
  docs/digest.md
  ```

### New endpoints

```txt
GET  /organizations/{org_id}/digest/preview
POST /organizations/{org_id}/digest/send
```


---

## v2.4 client portal

This version adds a read-only client portal:

- frontend page:
  ```txt
  /client-portal
  ```
- client portal summary endpoint
- client portal organization detail endpoint
- client users can view:
  - invoices
  - alerts
  - documents
- tests for read-only client access
- documentation:
  ```txt
  docs/client-portal.md
  ```

### New endpoints

```txt
GET /client-portal
GET /client-portal/organizations/{org_id}
```


---

## v2.5 saved views

This version adds saved views for the portfolio dashboard:

- save current portfolio filters
- apply saved portfolio views
- delete saved views
- user-scoped saved view table
- tests for saved view CRUD
- documentation:
  ```txt
  docs/saved-views.md
  ```

### New endpoints

```txt
GET    /saved-views
POST   /saved-views
PUT    /saved-views/{saved_view_id}
DELETE /saved-views/{saved_view_id}
```


---

## v2.6 bulk invoice actions

This version adds bulk actions for invoices:

- select invoices in the dashboard table
- apply bulk action:
  - `sync_status`
  - `mark_unsent`
  - `mark_pending`
  - `resolve_related_alerts`
- audit event:
  ```txt
  bulk_invoice_action.executed
  ```
- tests for bulk actions
- documentation:
  ```txt
  docs/bulk-actions.md
  ```

### New endpoint

```txt
POST /organizations/{org_id}/invoices/bulk-action
```


---

## v2.7 invoice notes

This version adds collaboration notes on invoices:

- invoice notes table
- add/list notes API
- frontend page:
  ```txt
  /invoice-notes
  ```
- internal/client-visible note flag
- audit event:
  ```txt
  invoice_note.created
  ```
- tests for invoice notes
- documentation:
  ```txt
  docs/invoice-notes.md
  ```

### New endpoints

```txt
GET  /organizations/{org_id}/invoices/{invoice_id}/notes
POST /organizations/{org_id}/invoices/{invoice_id}/notes
```


---

## v2.8 invoice tags and priority

This version adds operational invoice metadata:

- tags
- priority
- optional assignee user id
- frontend page:
  ```txt
  /invoice-metadata
  ```
- audit event:
  ```txt
  invoice.metadata_updated
  ```
- tests for metadata updates
- documentation:
  ```txt
  docs/invoice-metadata.md
  ```

### New endpoint

```txt
PUT /organizations/{org_id}/invoices/{invoice_id}/metadata
```


---

## v2.8.1 CI fix

Fixes SQLite-compatible Alembic migration for invoice metadata.

The migration `0011_invoice_metadata.py` now adds `assignee_user_id` as a nullable integer column without an inline foreign-key constraint, because SQLite cannot add FK constraints through `ALTER TABLE` in the CI migration check.

The SQLAlchemy model still keeps the application-level field.


---

## v2.9 work queue

This version adds an operational invoice work queue:

- frontend page:
  ```txt
  /work-queue
  ```
- filter by:
  - status
  - priority
  - tag
- queue summary metrics
- tests for work queue filters
- documentation:
  ```txt
  docs/work-queue.md
  ```

### New endpoint

```txt
GET /organizations/{org_id}/work-queue
```


---

## v3.0 system status

This version adds system diagnostics:

- app version bumped to `3.0.0`
- system status endpoint:
  ```txt
  GET /system/status
  ```
- frontend page:
  ```txt
  /system-status
  ```
- shows API/DB/config counters
- tests for system status endpoint
- documentation:
  ```txt
  docs/system-status.md
  ```


---

## v3.1 API keys

This version adds API keys for external integrations:

- API key table
- key creation/list/revoke
- public invoice creation API
- frontend page:
  ```txt
  /api-keys
  ```
- audit events:
  - `api_key.created`
  - `api_key.revoked`
  - `public_api.invoice_created`
- tests for API key flow
- documentation:
  ```txt
  docs/api-keys.md
  ```

### New endpoints

```txt
GET  /organizations/{org_id}/api-keys
POST /organizations/{org_id}/api-keys
POST /organizations/{org_id}/api-keys/{api_key_id}/revoke
POST /public-api/v1/invoices
```


---

## v3.2 developer portal

This version adds public API developer documentation:

- frontend page:
  ```txt
  /developer
  ```
- cURL, JavaScript and Python examples
- Postman collection:
  ```txt
  examples/public-api/facturaguard-public-api.postman_collection.json
  ```
- example scripts:
  ```txt
  examples/public-api/create_invoice.py
  examples/public-api/create_invoice.js
  ```
- documentation:
  ```txt
  docs/developer-api.md
  ```

No database migration is included in this version.


---

## v3.3 ROI calculator

This version adds a commercial ROI calculator:

- public page:
  ```txt
  /roi
  ```
- links from landing/pricing/login
- estimates:
  - monthly invoices
  - manual hours
  - saved hours
  - saved cost
  - net monthly value
  - annual value
  - ROI
- documentation:
  ```txt
  docs/roi-calculator.md
  ```

No database migration is included in this version.


---

## v3.4 help center

This version adds a public help center and demo script:

- public page:
  ```txt
  /help
  ```
- FAQ
- demo sales script
- positioning for accountants and SMEs
- documentation:
  ```txt
  docs/help-center.md
  docs/demo-script.md
  ```

No database migration is included in this version.


---

## v3.5 import templates

This version adds public import templates:

- frontend page:
  ```txt
  /templates
  ```
- CSV template download
- XML template download
- ZIP package download
- tests for template endpoints
- documentation:
  ```txt
  docs/import-templates.md
  ```

### New endpoints

```txt
GET /templates/invoices.csv
GET /templates/invoices.xml
GET /templates/facturaguard-import-templates.zip
```

No database migration is included in this version.


---

## v3.6 real ANAF connector skeleton

This version prepares the real ANAF/SPV integration:

- encrypted ANAF OAuth token storage
- ANAF config variables
- OAuth connect/callback endpoints
- authorization list/disconnect endpoints
- frontend page:
  ```txt
  /integrations
  ```
- RealAnafClient skeleton for:
  - upload
  - stareMesaj
  - listaMesajeFactura
  - descarcare
- documentation:
  ```txt
  docs/anaf-real-connector.md
  ```

### New endpoints

```txt
GET  /organizations/{org_id}/integrations/anaf/config-check
GET  /organizations/{org_id}/integrations/anaf/connect
GET  /organizations/{org_id}/integrations/anaf/authorizations
POST /organizations/{org_id}/integrations/anaf/disconnect
GET  /integrations/anaf/oauth/callback
```


---

## v3.7 UBL XML generator

This version adds a basic UBL XML generator skeleton:

- frontend page:
  ```txt
  /ubl
  ```
- XML preview endpoint
- XML download endpoint
- audit event:
  ```txt
  invoice.ubl_exported
  ```
- tests for preview/download
- documentation:
  ```txt
  docs/ubl-generator.md
  ```

### New endpoints

```txt
GET /organizations/{org_id}/invoices/{invoice_id}/ubl-preview
GET /organizations/{org_id}/invoices/{invoice_id}/ubl.xml
```

This is not production-valid CIUS-RO yet. Validate and complete the XML before real ANAF upload.


---

## v3.8 ANAF upload draft flow

This version adds a draft ANAF upload flow:

- backend upload-draft endpoint
- dry-run mode
- RealAnafClient upload wiring
- frontend buttons in:
  ```txt
  /ubl
  ```
- audit events:
  - `anaf.upload_dry_run`
  - `anaf.upload_submitted`
  - `anaf.upload_failed`
- test for mock-mode safety behavior
- documentation:
  ```txt
  docs/anaf-upload-draft.md
  ```

### New endpoint

```txt
POST /organizations/{org_id}/invoices/{invoice_id}/anaf-upload-draft
```

The XML generator is still a skeleton. Validate CIUS-RO before production upload.


---

## v3.9 ANAF status check draft

This version adds a draft ANAF `stareMesaj` check:

- backend status-check endpoint
- RealAnafClient status wiring
- best-effort parser for ANAF status response
- frontend button in:
  ```txt
  /ubl
  ```
- audit events:
  - `anaf.status_checked`
  - `anaf.status_check_failed`
- test for mock-mode safety behavior
- documentation:
  ```txt
  docs/anaf-status-check.md
  ```

### New endpoint

```txt
POST /organizations/{org_id}/invoices/{invoice_id}/anaf-status-check
```

The parser is still a draft. Validate with real ANAF test responses before production.


---

## v3.10 ANAF download response draft

This version adds a draft ANAF response download flow:

- invoice response metadata columns
- backend download-response endpoint
- RealAnafClient `/descarcare` wiring
- ZIP saved into document storage as:
  ```txt
  anaf_response
  ```
- frontend controls in:
  ```txt
  /ubl
  ```
- audit events:
  - `anaf.response_downloaded`
  - `anaf.response_download_failed`
- test for mock-mode safety behavior
- documentation:
  ```txt
  docs/anaf-download-response.md
  ```

### New endpoint

```txt
POST /organizations/{org_id}/invoices/{invoice_id}/anaf-download-response
```


---

## v3.11 ANAF response parser skeleton

This version adds a parser skeleton for ANAF response ZIP files:

- backend parser service:
  ```txt
  backend/app/anaf_response_parser.py
  ```
- parser endpoint
- ZIP/XML/text extraction
- best-effort status/message extraction
- optional invoice update
- frontend controls in:
  ```txt
  /ubl
  ```
- audit event:
  ```txt
  anaf.response_parsed
  ```
- tests for parsing uploaded ZIP document
- documentation:
  ```txt
  docs/anaf-response-parser.md
  ```

### New endpoint

```txt
POST /organizations/{org_id}/invoices/{invoice_id}/anaf-parse-response
```


---

## v3.12 Railway pre-deploy hardening

This version adds Railway deployment preparation:

- backend Railway config:
  ```txt
  backend/railway.json
  ```
- frontend Railway config:
  ```txt
  frontend/railway.json
  ```
- backend pre-deploy script:
  ```txt
  backend/scripts/railway_predeploy.sh
  backend/scripts/railway_predeploy_check.py
  ```
- Railway env examples:
  ```txt
  deploy/railway/backend.env.example
  deploy/railway/frontend.env.example
  ```
- deploy checklist:
  ```txt
  docs/railway-deploy-checklist.md
  ```

The backend pre-deploy command runs Alembic migrations and sanity checks before the service starts.


---

## v3.13 Railway smoke tests

This version adds post-deploy verification tooling:

- smoke test script:
  ```txt
  scripts/railway_smoke_test.py
  ```
- shell wrapper:
  ```txt
  scripts/railway_smoke_test.sh
  ```
- post-deploy docs:
  ```txt
  docs/railway-post-deploy-smoke.md
  ```
- launch checklist:
  ```txt
  docs/launch-checklist.md
  ```

Basic usage:

```bash
python scripts/railway_smoke_test.py \
  --backend https://your-backend.up.railway.app \
  --frontend https://your-frontend.up.railway.app
```

Deep smoke test with data creation:

```bash
python scripts/railway_smoke_test.py \
  --backend https://your-backend.up.railway.app \
  --frontend https://your-frontend.up.railway.app \
  --include-auth-flow
```


---

## v3.14 production security hardening

This version adds basic backend security hardening:

- security headers middleware
- trusted host middleware support
- new settings:
  ```txt
  SECURITY_HEADERS_ENABLED
  TRUSTED_HOSTS
  ```
- Railway env examples updated
- pre-deploy warning for wildcard trusted hosts
- tests for security headers
- documentation:
  ```txt
  docs/security-hardening.md
  ```

Recommended production values:

```env
SECURITY_HEADERS_ENABLED=true
TRUSTED_HOSTS=api.facturaguard.ro,*.up.railway.app
```


---

## v3.15 plan One

This version renames the previous `free` plan to `one`:

- `free` removed from public plan list
- new plan:
  ```txt
  code: one
  name: One
  price: 5 EUR/lună
  max invoices/month: 50
  ```
- default subscription is now `one`
- existing `free` subscriptions migrate to `one`
- temporary legacy alias maps `free` to `one`
- documentation:
  ```txt
  docs/plan-one-change.md
  ```


---

## v3.16 NETOPIA Payments API v2

This version adds real NETOPIA Payments API v2 integration:

- unified checkout endpoint:
  ```txt
  POST /organizations/{org_id}/billing/netopia/checkout
  ```
- config-check endpoint:
  ```txt
  GET /billing/netopia/config-check
  ```
- IPN endpoint:
  ```txt
  POST /billing/netopia/ipn
  ```
- frontend now calls the unified NETOPIA checkout endpoint
- return page:
  ```txt
  /billing/return
  ```
- new payment transaction metadata:
  ```txt
  provider_order_id
  provider_payment_id
  provider_status
  ```
- migration:
  ```txt
  0016_netopia_v2_metadata.py
  ```
- Railway env examples updated
- documentation:
  ```txt
  docs/netopia-v2.md
  ```


---

## v3.17 NETOPIA IPN signature hardening

This version hardens NETOPIA IPN handling:

- configurable IPN verification modes:
  ```txt
  none
  shared_secret
  hmac_sha256
  hmac_sha512
  ```
- new settings:
  ```txt
  NETOPIA_IPN_SIGNATURE_MODE
  NETOPIA_IPN_REQUIRE_SIGNATURE
  ```
- raw body HMAC verification support
- idempotent paid IPN handling
- Railway pre-deploy validation for strict IPN settings
- tests for invalid/valid shared secret and HMAC
- documentation:
  ```txt
  docs/netopia-ipn-signature.md
  ```


---

## v3.18 NETOPIA status reconciliation

This version adds manual NETOPIA payment reconciliation:

- transaction list endpoint:
  ```txt
  GET /organizations/{org_id}/billing/transactions
  ```
- status-check endpoint:
  ```txt
  POST /organizations/{org_id}/billing/transactions/{transaction_id}/status-check
  ```
- frontend page:
  ```txt
  /billing
  ```
- manual `/operation/status` integration for NETOPIA v2
- mock-mode safe behavior
- tests for transaction listing and mock status check
- documentation:
  ```txt
  docs/netopia-status-reconciliation.md
  ```


---

## v3.18.1 CI fix

This patch fixes the v3.18 backend CI issue:

- removes duplicate route:
  ```txt
  GET /organizations/{org_id}/billing/transactions
  ```
- adds regression test for route uniqueness
- hardens NETOPIA provider status extraction
- removes duplicate response key in status reconciliation
- documentation:
  ```txt
  docs/ci-fix-v3181.md
  ```


---

## v3.18.2 CI fix

This patch fixes the remaining Backend FastAPI CI failures:

- adds generic document upload endpoint:
  ```txt
  POST /organizations/{org_id}/documents/upload
  ```
- fixes ANAF parser test to upload response ZIP as a document, not as invoice import
- fixes NETOPIA IPN signature verification to respect live env overrides
- adds configurable bcrypt rounds:
  ```txt
  BCRYPT_ROUNDS
  ```
- GitHub Actions uses `BCRYPT_ROUNDS=4` for faster backend tests
- production default remains `12`
- documentation:
  ```txt
  docs/ci-fix-v3182.md
  ```


---

## v3.19 deployment readiness dashboard

This version adds a runtime deployment checklist:

- backend service:
  ```txt
  backend/app/deployment_readiness_service.py
  ```
- authenticated endpoint:
  ```txt
  GET /deployment/readiness
  ```
- frontend page:
  ```txt
  /deployment
  ```
- dashboard link:
  ```txt
  Deployment
  ```
- checks for DB, storage, CORS, trusted hosts, security headers, scheduler, email dry-run, ANAF and NETOPIA
- test coverage:
  ```txt
  test_deployment_readiness_endpoint
  ```
- documentation:
  ```txt
  docs/deployment-readiness.md
  ```


---

## v3.20 public status page

This version adds a sanitized public deployment status page:

- backend service:
  ```txt
  backend/app/public_status_service.py
  ```
- public endpoint:
  ```txt
  GET /public/status
  ```
- frontend page:
  ```txt
  /status
  ```
- links from landing/help pages
- test coverage:
  ```txt
  test_public_status_endpoint_is_public_and_sanitized
  ```
- documentation:
  ```txt
  docs/public-status.md
  ```


---

## v3.20.1 CI fix

This patch fixes the backend CI failure from v3.20:

- updates `test_deployment_readiness_endpoint`
- removes exact app-version pinning from the test
- keeps v3.20 app behavior unchanged
- documentation:
  ```txt
  docs/ci-fix-v3201.md
  ```


---

## v3.21 onboarding checklist

This version adds an organization onboarding flow:

- backend service:
  ```txt
  backend/app/onboarding_service.py
  ```
- endpoint:
  ```txt
  GET /organizations/{org_id}/onboarding
  ```
- frontend page:
  ```txt
  /onboarding
  ```
- dashboard link:
  ```txt
  Onboarding
  ```
- checks for invoice import, document storage, deployment readiness, public status, billing, ANAF, UBL and API keys
- test coverage:
  ```txt
  test_onboarding_checklist_endpoint
  ```
- documentation:
  ```txt
  docs/onboarding-checklist.md
  ```


---

## v3.21.1 CI fix

This patch fixes the backend CI failure after v3.21:

- removes exact app-version pinning from:
  ```txt
  test_public_status_endpoint_is_public_and_sanitized
  ```
- bumps app patch version to:
  ```txt
  3.21.1
  ```
- documentation:
  ```txt
  docs/ci-fix-v3211.md
  ```


---

## v3.21.2 CI fix

This patch fixes the backend import failure after adding onboarding checklist:

- imports:
  ```txt
  OnboardingChecklistOut
  ```
  in `backend/app/main.py`
- adds regression test:
  ```txt
  test_onboarding_checklist_schema_import_is_registered
  ```
- bumps app version:
  ```txt
  3.21.2
  ```
- documentation:
  ```txt
  docs/ci-fix-v3212.md
  ```
