# Import Templates

FacturaGuard v3.5 adds public import templates for CSV/XML upload.

## Page

```txt
/templates
```

## Download endpoints

```txt
GET /templates/invoices.csv
GET /templates/invoices.xml
GET /templates/facturaguard-import-templates.zip
```

## Required CSV columns

- invoice_number
- issue_date
- customer_name
- customer_cui
- total_amount

## Optional CSV columns

- currency
- anaf_status
- anaf_message

## Usage

Use these templates during onboarding, demos or ERP mapping discussions.
