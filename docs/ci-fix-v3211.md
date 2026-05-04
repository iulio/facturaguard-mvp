# CI Fix v3.21.1

This patch fixes the Backend FastAPI CI failure introduced after v3.21.

## Root cause

`test_public_status_endpoint_is_public_and_sanitized` still pinned the public status version to:

```txt
3.20.0
```

v3.21 correctly bumped the app version, so the backend test failed.

## Fix

The test now checks that the `version` field exists instead of checking an exact release number.

This prevents the same CI failure on future version bumps.
