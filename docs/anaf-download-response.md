# ANAF Download Response Draft

FacturaGuard v3.10 adds a draft flow for ANAF `/descarcare`.

## Endpoint

```txt
POST /organizations/{org_id}/invoices/{invoice_id}/anaf-download-response
```

Optional query:

```txt
?message_id=123456
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

1. uses `invoice.anaf_download_id` or manual `message_id`
2. checks OAuth token
3. calls `RealAnafClient.download_message`
4. stores ZIP in document storage as `anaf_response`
5. updates invoice response metadata
6. writes audit log

## New invoice metadata

```txt
anaf_download_id
anaf_response_document_id
anaf_last_checked_at
anaf_submission_environment
```

## Frontend

The `/ubl` page now supports:

- optional manual message id
- `Descarcă răspuns ANAF`
- result card with stored document ID

## Production warning

The ZIP content is stored as received. Production parsing of the ZIP/XML response still needs a dedicated parser.
