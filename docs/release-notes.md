# FacturaGuard MVP v2.0 Release Notes

## Summary

FacturaGuard v2.0 is a presentable MVP for Romanian B2B e-Factura monitoring. It includes authentication, organization management, invoice imports, mock ANAF sync, alerts, audit logs, reports, subscriptions, mock NETOPIA payments, onboarding and marketing pages.

## Main capabilities

- FastAPI backend
- Next.js frontend
- PostgreSQL + Alembic migrations
- JWT authentication
- password reset and password change
- organization roles and invitations
- CSV/XML/ZIP invoice upload
- original document storage
- S3-compatible storage abstraction
- mock ANAF/e-Factura connector
- alerts and deadline status calculation
- monthly PDF report
- invoice CSV export
- portfolio dashboard with risk scoring
- audit logs
- billing/subscription skeleton
- mock NETOPIA checkout and webhook
- landing page and pricing page
- onboarding wizard
- GitHub Actions CI

## Demo commands

```bash
docker compose up --build
make seed-demo
make smoke
```

Demo credentials:

```txt
demo@facturaguard.local
DemoPassword123!
```

## Release status

MVP: ready for internal demo and user interviews.

Not production-ready yet for real compliance processing because:

- ANAF/SPV integration is mock.
- NETOPIA integration is mock.
- production object storage and secrets need setup.
- legal/accounting validation is still required.
