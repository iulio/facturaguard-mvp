# Railway Post-Deploy Smoke Tests

FacturaGuard v3.13 adds a post-deploy smoke test script.

## Basic smoke test

After Railway gives you backend and frontend domains, run:

```bash
python scripts/railway_smoke_test.py \
  --backend https://your-backend.up.railway.app \
  --frontend https://your-frontend.up.railway.app
```

This checks:

- backend `/health`
- backend `/ready`
- backend template downloads
- backend `/docs`
- frontend `/`
- frontend `/landing`
- frontend `/pricing`
- frontend `/roi`
- frontend `/help`
- frontend `/templates`

## Deeper smoke test with data creation

Run this only when you are okay with creating a smoke user, organization and invoice:

```bash
python scripts/railway_smoke_test.py \
  --backend https://your-backend.up.railway.app \
  --frontend https://your-frontend.up.railway.app \
  --include-auth-flow
```

This additionally checks:

- register
- login
- create organization
- upload CSV invoice
- dashboard
- UBL preview
- system status

## Shell wrapper

```bash
sh scripts/railway_smoke_test.sh \
  https://your-backend.up.railway.app \
  https://your-frontend.up.railway.app \
  --include-auth-flow
```

## Important

The deeper test creates data in production. Use a clear smoke naming convention and delete it later if needed.
