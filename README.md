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
