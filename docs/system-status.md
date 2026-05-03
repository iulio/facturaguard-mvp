# System Status

FacturaGuard v3.0 adds a system status and diagnostics page.

## Page

```txt
/system-status
```

## Endpoint

```txt
GET /system/status
```

## Shows

- app name/version
- environment
- database status
- scheduler enabled
- email dry-run
- storage backend
- ANAF connector mode
- NETOPIA mock status
- rate limiting
- total organizations
- total invoices
- total documents
- total open alerts

## Access

The endpoint requires authentication.
