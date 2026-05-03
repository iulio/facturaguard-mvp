# Bulk Invoice Actions

FacturaGuard v2.6 adds bulk actions for invoices.

## Endpoint

```txt
POST /organizations/{org_id}/invoices/bulk-action
```

## Payload

```json
{
  "invoice_ids": [1, 2, 3],
  "action": "sync_status"
}
```

## Supported actions

- `sync_status`
- `mark_unsent`
- `mark_pending`
- `resolve_related_alerts`

## Frontend

Bulk controls are available above the invoice table in the main dashboard.
