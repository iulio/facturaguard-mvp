# Onboarding Checklist

FacturaGuard v3.21 adds an organization-level onboarding checklist.

## Endpoint

```txt
GET /organizations/{org_id}/onboarding
```

Requires authentication and access to the organization.

## Frontend

```txt
/onboarding
```

## Checklist areas

- organization created
- invoice import
- document storage
- deployment readiness
- public status page
- billing / NETOPIA
- ANAF/SPV
- UBL XML
- API key

## Purpose

This makes pilot setup easier by showing the next practical action after deploy.
