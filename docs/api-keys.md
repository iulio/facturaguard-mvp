# API Keys

FacturaGuard v3.1 adds organization API keys for external integrations.

## Page

```txt
/api-keys
```

## Management endpoints

```txt
GET  /organizations/{org_id}/api-keys
POST /organizations/{org_id}/api-keys
POST /organizations/{org_id}/api-keys/{api_key_id}/revoke
```

## Public API endpoint

```txt
POST /public-api/v1/invoices
```

Header:

```txt
X-API-Key: fg_...
```

## Scope

Initial supported scope:

```txt
invoices:write
```

## Security notes

- API keys are shown only once.
- Only a SHA-256 hash is stored.
- Keys can be revoked.
- Public API use is audited.
