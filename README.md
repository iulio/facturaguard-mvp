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
