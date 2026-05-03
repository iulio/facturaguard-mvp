# Deployment Readiness Dashboard

FacturaGuard v3.19 adds an authenticated runtime checklist for Railway and production readiness.

## Endpoint

```txt
GET /deployment/readiness
```

Requires authentication.

## Frontend

```txt
/deployment
```

## Checks

The readiness dashboard checks:

- database connectivity
- `AUTO_CREATE_TABLES`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `TRUSTED_HOSTS`
- security headers
- storage backend
- email dry-run
- scheduler
- NETOPIA provider/config
- ANAF provider/config

## Statuses

```txt
pass
warn
fail
```

`warn` does not block deployment, but highlights mock providers or incomplete production settings.

## Recommended use

Run after Railway deploy and after every environment variable change.
