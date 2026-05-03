# Notification Settings

FacturaGuard v2.2 adds per-organization notification settings.

## Page

```txt
/settings
```

## Endpoints

```txt
GET /organizations/{org_id}/notification-settings
PUT /organizations/{org_id}/notification-settings
```

## Settings

- enable/disable email alerts
- custom alert email
- rejected invoice alerts
- overdue invoice alerts
- near-deadline invoice alerts
- near-deadline days threshold
- daily digest flag for future digest feature

## Notes

The current email system still supports dry-run mode. In production, configure SMTP and set:

```txt
FG_EMAIL_DRY_RUN=false
```
