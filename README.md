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
