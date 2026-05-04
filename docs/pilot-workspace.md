# Pilot Workspace

FacturaGuard v3.22 adds a pilot workspace for preparing a customer pilot.

## Endpoint

```txt
GET /organizations/{org_id}/pilot-workspace
```

Requires authentication and organization access.

## Frontend

```txt
/pilot
```

## Includes

- organization summary
- app version/environment
- invoice/document/payment counts
- onboarding progress
- deployment readiness summary
- ANAF mode
- NETOPIA provider
- next recommended actions

## Purpose

Use this page before and after Railway deploy to see what is missing for a real pilot.
