# Public Status Page

FacturaGuard v3.20 adds a public, sanitized status endpoint and frontend page.

## Backend endpoint

```txt
GET /public/status
```

No authentication required.

## Frontend page

```txt
/status
```

## Exposed data

The public status response includes only safe deployment-level information:

- app name
- version
- environment
- overall status
- database status
- provider modes:
  - ANAF
  - NETOPIA
  - email
  - storage
- timestamp

## Not exposed

The endpoint does not expose:

- secrets
- API keys
- tokens
- database URLs
- organization data
- user data
- internal provider credentials

## Use case

Use after Railway deploy to quickly check public availability without logging in.
