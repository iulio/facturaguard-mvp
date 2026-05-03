# Work Queue

FacturaGuard v2.9 adds an operational work queue for invoices.

## Page

```txt
/work-queue
```

## Endpoint

```txt
GET /organizations/{org_id}/work-queue
```

## Filters

```txt
status=rejected
priority=urgent
tag=client-important
```

## Default behavior

Without filters, the work queue returns invoices with operational statuses:

- rejected
- overdue
- near_deadline
- unsent
- pending

The queue is sorted in Python for SQLite/PostgreSQL compatibility by:

1. priority rank
2. due submission date
3. issue date
