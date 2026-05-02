# Onboarding

FacturaGuard v1.9 adds a first-run onboarding wizard.

## Page

```txt
/onboarding
```

## Goal

Guide a new user through the first working flow:

1. Create first organization.
2. Upload first CSV/XML/ZIP file.
3. Run Mock ANAF sync.
4. Review dashboard.

## Endpoint

```txt
GET /onboarding/status
```

## Status response

The endpoint returns:

- whether the user has an organization
- selected first organization
- invoice count
- whether sync has been run
- open alerts
- next recommended step
- completion status
