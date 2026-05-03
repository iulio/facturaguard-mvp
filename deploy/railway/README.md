# Railway deployment files

This folder contains deployment examples for Railway.

## Files

```txt
deploy/railway/backend.env.example
deploy/railway/frontend.env.example
```

## Config as code

Service-specific config files are stored in:

```txt
backend/railway.json
frontend/railway.json
```

In Railway, set:

```txt
Backend Config File Path: /backend/railway.json
Frontend Config File Path: /frontend/railway.json
```

because this repository is a monorepo.


## Post-deploy smoke test

After backend and frontend domains are generated, run:

```bash
python scripts/railway_smoke_test.py \
  --backend https://your-backend.up.railway.app \
  --frontend https://your-frontend.up.railway.app
```

For a deeper test that creates demo data:

```bash
python scripts/railway_smoke_test.py \
  --backend https://your-backend.up.railway.app \
  --frontend https://your-frontend.up.railway.app \
  --include-auth-flow
```
