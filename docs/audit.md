# Audit Log

FacturaGuard v2.1 adds a dedicated audit dashboard and CSV export.

## Page

```txt
/audit
```

## Endpoints

```txt
GET /organizations/{org_id}/audit-logs
GET /organizations/{org_id}/audit-logs?action=payment
GET /organizations/{org_id}/audit-logs?entity_type=invoice
GET /organizations/{org_id}/audit-logs/export.csv
GET /organizations/{org_id}/audit-summary
```

## Tracked examples

- organization created
- invoices uploaded
- document stored/downloaded
- invitation created/accepted
- ANAF mock sync
- alert resolved
- report exported
- subscription updated
- payment checkout/payment succeeded

## Purpose

The audit log is useful for:

- accountant traceability
- client disputes
- compliance review
- debugging operations
- demoing product seriousness
