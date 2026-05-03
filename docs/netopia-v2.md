# NETOPIA Payments API v2

FacturaGuard v3.16 adds a real NETOPIA Payments API v2 adapter while keeping the mock provider for local development.

## Official API model

NETOPIA API v2 uses JSON endpoints secured with API tokens. The recommended flow starts a card payment with:

```txt
POST /payment/card/start
```

then handles 3-D Secure if required, and receives final payment updates through the `notifyUrl` callback.

## Settings

```env
NETOPIA_PROVIDER=mock
NETOPIA_IS_LIVE=false
NETOPIA_API_KEY=
NETOPIA_POS_SIGNATURE=
NETOPIA_POS_SIGNATURE_SET=
NETOPIA_PUBLIC_KEY=
NETOPIA_ACTIVE_KEY=
NETOPIA_HASH_METHOD=sha512
NETOPIA_SANDBOX_BASE_URL=https://secure.sandbox.netopia-payments.com
NETOPIA_LIVE_BASE_URL=https://secure.mobilpay.ro/pay
NETOPIA_NOTIFY_URL=https://your-backend.up.railway.app/billing/netopia/ipn
NETOPIA_REDIRECT_URL=https://your-frontend.up.railway.app/billing/return
NETOPIA_CANCEL_URL=https://your-frontend.up.railway.app/billing/return
NETOPIA_CURRENCY=EUR
NETOPIA_LANGUAGE=ro
NETOPIA_IPN_SHARED_SECRET=
```

## New endpoints

```txt
GET  /billing/netopia/config-check
POST /organizations/{org_id}/billing/netopia/checkout
POST /billing/netopia/ipn
```

The old mock endpoints still exist:

```txt
POST /organizations/{org_id}/billing/netopia-mock/checkout
POST /billing/netopia-mock/webhook
```

## Railway flow

Start with:

```env
NETOPIA_PROVIDER=mock
```

After sandbox credentials are ready, switch to:

```env
NETOPIA_PROVIDER=v2
NETOPIA_IS_LIVE=false
```

Set:

```txt
NETOPIA_NOTIFY_URL=https://your-backend.up.railway.app/billing/netopia/ipn
NETOPIA_REDIRECT_URL=https://your-frontend.up.railway.app/billing/return
NETOPIA_CANCEL_URL=https://your-frontend.up.railway.app/billing/return
```

## Important production note

The IPN endpoint currently includes safe transaction matching and optional shared-secret checking. Before live money processing, confirm the exact IPN signature format from your NETOPIA account/docs and add strict cryptographic verification using the provided public key / active key.
