# FacturaGuard Deployment Notes

## Minimum production services

- Backend: FastAPI container
- Frontend: Next.js container
- Database: PostgreSQL 16+
- Optional: S3-compatible object storage for XML/PDF files
- Optional: SMTP provider for real email alerts

## Required production environment variables

```txt
ENVIRONMENT=production
SECRET_KEY=<long-random-secret>
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:5432/<db>
AUTO_CREATE_TABLES=false
CORS_ORIGINS=https://your-frontend-domain.com
FG_EMAIL_DRY_RUN=false
FG_SMTP_HOST=<smtp-host>
FG_SMTP_USERNAME=<smtp-user>
FG_SMTP_PASSWORD=<smtp-password>
FG_EMAIL_FROM=alerts@your-domain.com
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=120
```

## Database migrations

Run before starting the API:

```bash
cd backend
alembic upgrade head
```

## Health checks

```txt
GET /health
GET /ready
```

- `/health` checks app availability.
- `/ready` checks database connectivity.

## Security checklist before public launch

- Replace `SECRET_KEY`.
- Use HTTPS only.
- Restrict `CORS_ORIGINS`.
- Disable `AUTO_CREATE_TABLES`.
- Run Alembic migrations.
- Use PostgreSQL, not SQLite.
- Configure real email credentials.
- Review rate limits.
- Add backup policy for PostgreSQL.
- Add object storage for uploaded XML/ZIP/PDF files.
