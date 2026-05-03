# NETOPIA IPN Signature Hardening

FacturaGuard v3.17 adds configurable IPN signature verification.

## Settings

```env
NETOPIA_IPN_SHARED_SECRET=
NETOPIA_IPN_SIGNATURE_MODE=shared_secret
NETOPIA_IPN_REQUIRE_SIGNATURE=false
```

Supported modes:

```txt
none
shared_secret
hmac_sha256
hmac_sha512
```

## Recommended sandbox setup

Start with:

```env
NETOPIA_IPN_SIGNATURE_MODE=shared_secret
NETOPIA_IPN_REQUIRE_SIGNATURE=false
```

This allows you to inspect the exact NETOPIA sandbox callback payload and headers without blocking integration tests.

## Recommended production setup

Use strict verification:

```env
NETOPIA_IPN_SHARED_SECRET=<long-random-secret>
NETOPIA_IPN_SIGNATURE_MODE=hmac_sha256
NETOPIA_IPN_REQUIRE_SIGNATURE=true
```

or keep `shared_secret` if the production callback is routed through a secure webhook/proxy that injects `X-NETOPIA-Secret`.

## Headers

The IPN endpoint accepts:

```txt
X-NETOPIA-Signature
X-NETOPIA-Secret
```

## Endpoint

```txt
POST /billing/netopia/ipn
```

## Idempotency

If the same successful payment IPN is received multiple times, the transaction remains paid and the subscription activation is not repeated.
