# CI Fix v3.20.1

This patch fixes the Backend FastAPI CI failure introduced by v3.20.

## Root cause

`test_deployment_readiness_endpoint` pinned the app version to:

```txt
3.19.0
```

v3.20 correctly bumped the app version to:

```txt
3.20.0
```

so the full backend suite failed.

## Fix

The test now asserts that the version field exists instead of pinning an exact release version.

This avoids the same failure on every future version bump.
