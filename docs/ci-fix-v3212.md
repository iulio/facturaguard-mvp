# CI Fix v3.21.2

This patch fixes the Backend FastAPI import failure from v3.21/v3.21.1.

## Root cause

The new endpoint:

```txt
GET /organizations/{org_id}/onboarding
```

used:

```python
response_model=OnboardingChecklistOut
```

but `OnboardingChecklistOut` was not imported in `backend/app/main.py`.

That breaks app import during backend tests.

## Fix

- imports `OnboardingChecklistOut` in `backend/app/main.py`
- adds a regression test that verifies the route is registered with the correct response model
- bumps app version to `3.21.2`
