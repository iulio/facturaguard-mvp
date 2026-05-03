# UBL XML Generator Skeleton

FacturaGuard v3.7 adds a basic UBL XML generator.

## Page

```txt
/ubl
```

## Endpoints

```txt
GET /organizations/{org_id}/invoices/{invoice_id}/ubl-preview
GET /organizations/{org_id}/invoices/{invoice_id}/ubl.xml
```

## What this version does

- creates a minimal UBL-like XML invoice from an existing FacturaGuard invoice
- allows preview in the frontend
- allows XML download
- writes audit event:
  ```txt
  invoice.ubl_exported
  ```

## Production warning

This is a skeleton, not a full Romanian CIUS-RO compliant generator.

Before real ANAF upload, complete and validate:

- supplier address
- customer address
- VAT category and subtotals
- product/service line details
- tax scheme rules
- payment means
- invoice allowances/charges, if needed
- CIUS-RO business rules
- official ANAF validator compatibility

## Next step

Wire this generated XML to RealAnafClient.upload_invoice_xml after adding validation and response parsers.
