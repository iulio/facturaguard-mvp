# Saved Views

FacturaGuard v2.5 adds saved views for the accountant portfolio.

## Purpose

Accountants can save frequently used dashboard filters, for example:

- high risk companies
- a specific client search
- low-risk companies
- medium-risk companies

## Endpoints

```txt
GET    /saved-views
POST   /saved-views
PUT    /saved-views/{saved_view_id}
DELETE /saved-views/{saved_view_id}
```

## Current implementation

Saved views are user-scoped and store filters as JSON.

Supported portfolio filters:

```json
{
  "search": "client name or CUI",
  "risk": "high"
}
```
