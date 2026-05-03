# Developer API

FacturaGuard v3.2 adds a developer portal and API integration examples.

## Frontend page

```txt
/developer
```

## Public endpoint

```txt
POST /public-api/v1/invoices
```

## Authentication

Send the API key in the request header:

```txt
X-API-Key: fg_...
```

## Scope required

```txt
invoices:write
```

## Example cURL

```bash
curl -X POST http://localhost:8000/public-api/v1/invoices \
  -H "Content-Type: application/json" \
  -H "X-API-Key: fg_your_api_key_here" \
  -d '{
    "invoice_number": "ERP-1001",
    "issue_date": "2026-04-27",
    "customer_name": "Client ERP SRL",
    "customer_cui": "RO12345678",
    "total_amount": 1234.56,
    "currency": "RON",
    "anaf_status": "pending"
  }'
```

## Operational result

Created invoices appear in:

- dashboard
- work queue
- audit log
- reports
