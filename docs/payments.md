# Payments

FacturaGuard v1.7 includes a mock NETOPIA Payments provider.

This is not a real payment integration. It simulates the checkout and webhook flow so the SaaS billing architecture can be developed safely.

## Flow

1. User selects a plan.
2. Backend creates a payment transaction.
3. Frontend redirects to:
   ```txt
   /billing/mock-netopia?session_id=...
   ```
4. User clicks `Simulează plată reușită`.
5. Mock webhook is sent to backend.
6. Backend marks transaction as paid.
7. Backend activates the selected plan.

## Endpoints

```txt
POST /organizations/{org_id}/billing/netopia-mock/checkout
GET  /organizations/{org_id}/billing/transactions
POST /billing/netopia-mock/webhook
```

## Environment

```txt
NETOPIA_MOCK_ENABLED=true
NETOPIA_MOCK_RETURN_URL=http://localhost:3000/billing/return
NETOPIA_MOCK_WEBHOOK_SECRET=dev-netopia-webhook-secret
```

## Production NETOPIA TODO

To implement real NETOPIA Payments:

- create real merchant account
- generate payment request payload
- sign/encrypt request according to NETOPIA docs
- redirect user to NETOPIA payment URL
- expose secure IPN/webhook endpoint
- validate NETOPIA signature
- map payment statuses to internal transaction states
- activate subscription only after confirmed payment
- store provider transaction IDs and raw notification payload
