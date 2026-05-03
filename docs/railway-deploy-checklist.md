# Railway Deploy Checklist

FacturaGuard v3.12 adds Railway deployment hardening.

## Railway services

Create three Railway services:

```txt
facturaguard-backend
facturaguard-frontend
PostgreSQL
```

## Backend service

Use the same GitHub repo.

Recommended settings:

```txt
Root Directory: /backend
Config File Path: /backend/railway.json
Volume Mount: /app/storage
```

The backend config file includes:

```txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Pre-deploy Command: sh scripts/railway_predeploy.sh
Healthcheck Path: /health
```

## Frontend service

Use the same GitHub repo.

Recommended settings:

```txt
Root Directory: /frontend
Config File Path: /frontend/railway.json
```

The frontend config file includes:

```txt
Build Command: npm run build
Start Command: npm run start -- -H 0.0.0.0 -p $PORT
Healthcheck Path: /
```

## Variables

Copy examples from:

```txt
deploy/railway/backend.env.example
deploy/railway/frontend.env.example
```

## Deploy order

1. Create PostgreSQL.
2. Create backend service.
3. Add backend variables.
4. Attach volume to backend at `/app/storage`, or switch to S3.
5. Deploy backend.
6. Generate backend Railway domain.
7. Create frontend service.
8. Add frontend variable `NEXT_PUBLIC_API_BASE`.
9. Deploy frontend.
10. Generate frontend Railway domain.
11. Update backend:
    ```txt
    CORS_ORIGINS
    FRONTEND_BASE_URL
    NETOPIA_MOCK_RETURN_URL
    ANAF_REDIRECT_URI
    ```
12. Redeploy backend.

## Pre-deploy script

The backend pre-deploy script runs:

```bash
alembic upgrade head
python scripts/railway_predeploy_check.py
```

The check validates:

- `DATABASE_URL`
- `SECRET_KEY`
- database connectivity
- `AUTO_CREATE_TABLES=false` in production
- storage configuration
- ANAF required variables when `ANAF_CONNECTOR_MODE=real`
- Fernet key validity when `TOKEN_ENCRYPTION_KEY` is provided

## First smoke tests

Backend:

```txt
https://your-backend.up.railway.app/health
https://your-backend.up.railway.app/ready
https://your-backend.up.railway.app/templates/invoices.csv
```

Frontend:

```txt
https://your-frontend.up.railway.app/
https://your-frontend.up.railway.app/landing
https://your-frontend.up.railway.app/templates
```

## ANAF real mode

Start with:

```txt
ANAF_CONNECTOR_MODE=mock
ANAF_ENV=test
```

Switch to:

```txt
ANAF_CONNECTOR_MODE=real
```

only after the ANAF OAuth application is configured and the Railway backend callback URL is registered in ANAF.
