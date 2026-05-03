# Invoice Metadata

FacturaGuard v2.8 adds operational invoice metadata.

## Fields

- tags
- priority
- assignee_user_id

## Priorities

```txt
low
normal
high
urgent
```

## Endpoint

```txt
PUT /organizations/{org_id}/invoices/{invoice_id}/metadata
```

## Frontend

```txt
/invoice-metadata
```
