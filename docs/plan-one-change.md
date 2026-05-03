# Plan One

FacturaGuard v3.15 renames the old `free` plan to `one`.

## New plan details

```txt
Code: one
Name: One
Price: 5 EUR/lună
Organizations: 1
Invoices/month: 50
Documents: 50
```

## Migration

The migration:

```txt
0015_rename_free_plan_to_one.py
```

updates existing rows:

```sql
UPDATE organization_subscriptions SET plan_code = 'one' WHERE plan_code = 'free';
UPDATE payment_transactions SET plan_code = 'one' WHERE plan_code = 'free';
```

## Compatibility

`get_plan("free")` still resolves to the `one` plan internally as a temporary legacy alias, but `/billing/plans` only returns `one`, `starter`, `pro`, and `agency`.
