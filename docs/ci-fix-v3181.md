# CI Fix v3.18.1

This patch fixes the backend CI failure introduced by v3.18.

## Fixed

- removed duplicate route registration for:
  ```txt
  GET /organizations/{org_id}/billing/transactions
  ```
- added a regression test to ensure the route is registered once
- hardened NETOPIA provider status extraction
- removed duplicate `message` key in status reconciliation response

## Why

The v3.18 package accidentally added a new billing transaction list endpoint while an older endpoint with the same path already existed. This can produce FastAPI/OpenAPI duplicate-operation warnings and unstable backend checks.
