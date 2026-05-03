# ANAF Response ZIP Parser Skeleton

FacturaGuard v3.11 adds a parser skeleton for ANAF response ZIP files.

## Endpoint

```txt
POST /organizations/{org_id}/invoices/{invoice_id}/anaf-parse-response
```

Optional query parameters:

```txt
document_id=123
apply_result=true
```

## Behavior

The endpoint:

1. finds the ANAF response document from `invoice.anaf_response_document_id` or `document_id`
2. reads the ZIP from document storage
3. extracts XML/text files
4. best-effort parses status and messages
5. optionally applies the result to the invoice
6. writes an audit log

## Frontend

The `/ubl` page now supports:

- optional `document_id` for parsing
- `Parsează răspuns`
- parsed file summary and raw extracted preview

## Current limitations

This is a robust-enough skeleton for testing, not a final production parser.

Before production, add parsers for official ANAF response XML structures and verify against real test responses.
