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
