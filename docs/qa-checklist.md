# FacturaGuard MVP QA Checklist

## Backend automated checks

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Expected result:

```txt
all tests passed
```

## Docker smoke test

```bash
docker compose up --build
```

Then open:

```txt
http://localhost:8000/health
http://localhost:8000/ready
http://localhost:3000
```

Run:

```bash
make smoke
```

## Demo seed

```bash
make seed-demo
```

Demo login:

```txt
demo@facturaguard.local
DemoPassword123!
```

## Manual functional checklist

### Auth

- Register user.
- Login.
- Request password reset.
- Reset password from dry-run link.
- Change password from account.

### Organization setup

- Create organization.
- Confirm it appears in portfolio.
- Confirm subscription defaults to `free`.

### Uploads

- Upload CSV.
- Upload XML.
- Upload ZIP with XML files.
- Confirm invoices appear.
- Confirm uploaded file appears in documents.
- Download stored document.

### Alerts and sync

- Run Mock ANAF sync.
- Confirm invoice status changes.
- Confirm alerts appear.
- Resolve an alert.
- Confirm audit log contains actions.

### Reports

- Export CSV.
- Generate PDF.
- Confirm audit log for export.

### Invitations

- Send invitation.
- Open `/accept-invite?token=...`.
- Create account from invite.
- Confirm invited user sees organization.

### Billing

- View pricing page.
- Choose plan.
- Go through mock NETOPIA checkout.
- Simulate paid webhook.
- Confirm subscription plan changes.

### Onboarding

- Open `/onboarding`.
- Complete create organization.
- Upload file.
- Run sync.
- Confirm setup completed.

## Known MVP limitations

- ANAF connector is mock only.
- NETOPIA provider is mock only.
- Local storage is default; S3 requires environment setup.
- In-memory rate limiting is not suitable for multi-instance production.
- `AUTO_CREATE_TABLES` should be disabled in production; use Alembic.
