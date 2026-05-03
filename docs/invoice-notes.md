# Invoice Notes

FacturaGuard v2.7 adds notes on invoices.

## Page

```txt
/invoice-notes
```

## Endpoints

```txt
GET  /organizations/{org_id}/invoices/{invoice_id}/notes
POST /organizations/{org_id}/invoices/{invoice_id}/notes
```

## Use cases

- accountant leaves explanation for rejected invoice
- client operator confirms correction
- internal note records why an alert was resolved
- collaboration around problematic invoices

## Fields

- body
- is_internal
- author_user_id
- created_at
