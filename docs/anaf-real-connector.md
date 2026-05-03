# Real ANAF/SPV Connector Skeleton

FacturaGuard v3.6 adds the first real ANAF/SPV integration layer.

## What this version includes

- ANAF OAuth config variables
- encrypted token storage model
- Alembic migration:
  ```txt
  0013_anaf_authorizations.py
  ```
- OAuth connect endpoint
- OAuth callback endpoint
- config-check endpoint
- authorization listing endpoint
- disconnect endpoint
- frontend page:
  ```txt
  /integrations
  ```
- RealAnafClient skeleton with methods for:
  - upload
  - stareMesaj
  - listaMesajeFactura
  - descarcare

## Before Railway deploy

Add these backend variables:

```env
ANAF_CONNECTOR_MODE=real
ANAF_ENV=test
ANAF_CLIENT_ID=
ANAF_CLIENT_SECRET=
ANAF_REDIRECT_URI=https://api.facturaguard.ro/integrations/anaf/oauth/callback
ANAF_AUTH_BASE=https://logincert.anaf.ro/anaf-oauth2/v1
ANAF_API_TEST_BASE=https://webserviceapl.anaf.ro/test/FCTEL/rest
ANAF_API_PROD_BASE=https://webserviceapl.anaf.ro/prod/FCTEL/rest
ANAF_TOKEN_CONTENT_TYPE=jwt
FRONTEND_BASE_URL=https://app.facturaguard.ro
TOKEN_ENCRYPTION_KEY=
```

Generate the encryption key with:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## ANAF portal setup

The ANAF OAuth application callback URL must exactly match:

```txt
ANAF_REDIRECT_URI
```

Example:

```txt
https://api.facturaguard.ro/integrations/anaf/oauth/callback
```

## Current limitations

This is a skeleton. It prepares OAuth/token storage and HTTP client methods, but full production use still requires:

- XML UBL generation from invoice data
- XML validation
- robust ANAF XML response parsers
- upload flow wired to invoices
- scheduler wired to real `stareMesaj`
- response ZIP storage and parsing
- legal/accounting validation
