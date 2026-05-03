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


## CI migration note

In migration `0011_invoice_metadata.py`, `assignee_user_id` is added without an inline FK constraint for SQLite compatibility in CI. Production PostgreSQL can enforce this later with a dedicated migration if needed.
