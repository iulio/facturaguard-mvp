# ANAF Status Check Draft

FacturaGuard v3.9 adds a draft `stareMesaj` status check flow.

## Endpoint

```txt
POST /organizations/{org_id}/invoices/{invoice_id}/anaf-status-check
```

## Behavior

### Mock mode

If:

```txt
ANAF_CONNECTOR_MODE=mock
```

the endpoint does not call ANAF and returns a clear message.

### Real mode

If:

```txt
ANAF_CONNECTOR_MODE=real
```

the endpoint:

1. checks that the invoice has `anaf_upload_id`
2. checks OAuth token
3. calls `RealAnafClient.fetch_invoice_status`
4. best-effort parses the response
5. updates invoice status
6. creates alerts when needed
7. writes audit log

## Frontend

The `/ubl` page now has a button:

```txt
Verifică stareMesaj
```

## Current limitations

The parser is intentionally best-effort. Production use still requires robust parsing of official ANAF XML response variants.
