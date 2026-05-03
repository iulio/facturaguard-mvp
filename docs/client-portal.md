# Client Portal

FacturaGuard v2.4 adds a read-only client portal.

## Page

```txt
/client-portal
```

## Endpoints

```txt
GET /client-portal
GET /client-portal/organizations/{org_id}
```

## Purpose

Clients invited to an organization can view:

- organization summary
- recent invoices
- open alerts
- stored documents

The portal is designed for read-only visibility. Users with `client_viewer` cannot upload invoices or change operational data.

## Access

The portal uses existing organization memberships:

- `client_viewer`
- `client_operator`
- `accountant_owner`

Data is scoped to organizations the authenticated user belongs to.
