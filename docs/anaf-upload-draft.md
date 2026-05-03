# ANAF Upload Draft Flow

FacturaGuard v3.8 adds a draft upload flow for ANAF.

## Endpoint

```txt
POST /organizations/{org_id}/invoices/{invoice_id}/anaf-upload-draft
```

Optional query:

```txt
?dry_run=true
```

## Behavior

### Mock mode

If:

```txt
ANAF_CONNECTOR_MODE=mock
```

the endpoint does not call ANAF and returns a clear message.

### Real mode, dry-run

If:

```txt
ANAF_CONNECTOR_MODE=real
```

and:

```txt
dry_run=true
```

the endpoint generates XML and returns a preview without calling ANAF.

### Real mode, actual attempt

If:

```txt
ANAF_CONNECTOR_MODE=real
dry_run=false
```

the endpoint:

1. checks OAuth token
2. refreshes token if needed
3. generates XML
4. calls `RealAnafClient.upload_invoice_xml`
5. stores `anaf_upload_id` when it can extract it
6. writes audit log

## Frontend

The `/ubl` page now has buttons for:

- Dry-run ANAF
- Trimite către ANAF test
- Descarcă XML

## Production warning

The generated XML is still a skeleton. Do not use for production upload until CIUS-RO validation is completed.
