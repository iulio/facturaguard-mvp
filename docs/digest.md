# Daily Digest

FacturaGuard v2.3 adds daily digest email support.

## Purpose

Daily digest gives the accountant or organization owner a short operational summary:

- total invoices
- validated invoices
- rejected invoices
- overdue invoices
- near-deadline invoices
- unsent invoices
- recent open alerts

## Endpoints

```txt
GET  /organizations/{org_id}/digest/preview
POST /organizations/{org_id}/digest/send
```

## Scheduler

When scheduler is enabled, a digest job is registered for 08:00 UTC:

```txt
facturaguard_daily_digest
```

The job sends digest emails only for organizations with:

```txt
daily_digest_enabled=true
email_alerts_enabled=true
```

## Frontend

Digest controls are available in:

```txt
/settings
```
