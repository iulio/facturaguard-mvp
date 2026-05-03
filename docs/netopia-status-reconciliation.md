# NETOPIA Status Reconciliation

FacturaGuard v3.18 adds manual NETOPIA payment status reconciliation.

## Why

IPN/webhook is the source of truth, but in real deployments callbacks may be delayed or blocked. The reconciliation endpoint lets an owner manually check the payment status from FacturaGuard.

## NETOPIA v2 reference

NETOPIA's v2 quick start describes the payment flow as:

1. start payment with `/payment/card/start`
2. handle 3-D Secure if needed
3. wait for callback through `notifyUrl`
4. optionally use `/operation/status` and other operation endpoints for further operations

## New endpoints

```txt
GET  /organizations/{org_id}/billing/transactions
POST /organizations/{org_id}/billing/transactions/{transaction_id}/status-check
```

## Frontend

```txt
/billing
```

The page shows:

- NETOPIA config status
- payment transactions
- order/payment IDs
- local status
- manual status check button

## Behavior

### Mock mode

Returns a safe message and does not call NETOPIA.

### NETOPIA v2 mode

Calls:

```txt
POST {NETOPIA_BASE_URL}/operation/status
```

with:

```json
{
  "posSignature": "...",
  "orderID": "...",
  "ntpID": "..."
}
```

Then it normalizes the result to:

```txt
paid
pending
failed
cancelled
```

and updates the local transaction/subscription when needed.
