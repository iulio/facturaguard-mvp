# CI Fix v3.18.2

This patch fixes the remaining Backend FastAPI CI failures.

## Fixed

1. ANAF response parser test no longer uploads an arbitrary ANAF response ZIP through `/invoices/upload`.
   - Added generic document upload endpoint:
     ```txt
     POST /organizations/{org_id}/documents/upload
     ```
   - The parser test now stores the ZIP as `document_type=anaf_response`.

2. NETOPIA IPN signature tests now work with env overrides after app import.
   - `verify_netopia_ipn_signature` reads IPN signature policy from live env values with cached settings fallback.

3. CI speed improvement.
   - Added:
     ```txt
     BCRYPT_ROUNDS
     ```
   - GitHub Actions sets:
     ```txt
     BCRYPT_ROUNDS=4
     ```
   - Production default remains `12`.

## New regression coverage

- `test_document_upload_endpoint`
- existing NETOPIA IPN strict-secret/HMAC tests now exercise live env overrides correctly
