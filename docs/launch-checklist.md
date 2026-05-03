# FacturaGuard Launch Checklist

Use this checklist before showing FacturaGuard to a real pilot user.

## Code and CI

- `main` branch is green in GitHub Actions.
- Latest commit is deployed to Railway backend.
- Latest commit is deployed to Railway frontend.
- Alembic migrations ran successfully.
- Backend health check is green.
- Frontend health check is green.

## Railway services

- PostgreSQL service exists.
- Backend service uses:
  ```txt
  Root Directory: /backend
  Config File Path: /backend/railway.json
  ```
- Frontend service uses:
  ```txt
  Root Directory: /frontend
  Config File Path: /frontend/railway.json
  ```
- Backend volume is mounted at:
  ```txt
  /app/storage
  ```
  or S3 variables are configured.

## Backend variables

- `ENVIRONMENT=production`
- `AUTO_CREATE_TABLES=false`
- `SECRET_KEY` is long and random.
- `TRUSTED_HOSTS` contains the backend Railway/custom domain.
- `SECURITY_HEADERS_ENABLED=true`.
- `DATABASE_URL` references Railway PostgreSQL.
- `CORS_ORIGINS` contains the frontend Railway/custom domain.
- `FRONTEND_BASE_URL` contains the frontend Railway/custom domain.
- `FILE_STORAGE_BACKEND` is correct.
- `NETOPIA_MOCK_RETURN_URL` points to the frontend.
- `ANAF_CONNECTOR_MODE=mock` until OAuth is configured.
- `FG_EMAIL_DRY_RUN=true` until SMTP is configured.

## Frontend variables

- `NEXT_PUBLIC_API_BASE` points to the backend Railway/custom domain.

## Smoke tests

Run:

```bash
python scripts/railway_smoke_test.py \
  --backend https://your-backend.up.railway.app \
  --frontend https://your-frontend.up.railway.app \
  --include-auth-flow
```

## Manual checks

- Register user.
- Login.
- Create organization.
- Upload CSV template.
- Open dashboard.
- Open work queue.
- Open UBL page.
- Generate XML preview.
- Open audit log.
- Open system status.
- Open help/ROI/templates pages.

## Pilot caveats

Explain clearly:

- ANAF connector is not production-valid until XML CIUS-RO validation and live OAuth testing are finished.
- NETOPIA is mock.
- Email is dry-run unless SMTP is configured.
- Storage is local Railway volume unless S3 is configured.
