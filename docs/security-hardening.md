# Production Security Hardening

FacturaGuard v3.14 adds basic production security hardening.

## Backend settings

```env
SECURITY_HEADERS_ENABLED=true
TRUSTED_HOSTS=api.facturaguard.ro,*.up.railway.app
```

## Security headers

When enabled, the API adds:

```txt
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cross-Origin-Opener-Policy: same-origin
Content-Security-Policy: default-src 'self'; frame-ancestors 'none'
```

## Trusted hosts

`TRUSTED_HOSTS` protects the backend from Host header abuse.

For Railway temporary domains, use:

```env
TRUSTED_HOSTS=your-backend.up.railway.app,*.up.railway.app
```

For custom domains, use:

```env
TRUSTED_HOSTS=api.facturaguard.ro
```

During local development you can keep:

```env
TRUSTED_HOSTS=*
```

## Railway note

After Railway generates the backend domain, update:

```txt
TRUSTED_HOSTS
CORS_ORIGINS
FRONTEND_BASE_URL
NETOPIA_MOCK_RETURN_URL
ANAF_REDIRECT_URI
```

Then redeploy the backend.
