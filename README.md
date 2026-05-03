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
  - `free`
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
