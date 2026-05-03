from datetime import datetime
from sqlalchemy.orm import Session

from .models import Organization, OrganizationNotificationSettings, User

def get_or_create_notification_settings(
    db: Session,
    organization: Organization,
    default_email: str | None = None,
) -> OrganizationNotificationSettings:
    settings = (
        db.query(OrganizationNotificationSettings)
        .filter(OrganizationNotificationSettings.organization_id == organization.id)
        .first()
    )

    if settings:
        return settings

    settings = OrganizationNotificationSettings(
        organization_id=organization.id,
        alert_email=default_email,
    )
    db.add(settings)
    db.flush()
    return settings

def update_notification_settings(
    settings: OrganizationNotificationSettings,
    payload: dict,
) -> OrganizationNotificationSettings:
    allowed_fields = {
        "email_alerts_enabled",
        "alert_email",
        "send_rejected_alerts",
        "send_overdue_alerts",
        "send_near_deadline_alerts",
        "near_deadline_days",
        "daily_digest_enabled",
    }

    for field, value in payload.items():
        if field in allowed_fields and value is not None:
            setattr(settings, field, value)

    if settings.near_deadline_days < 1:
        settings.near_deadline_days = 1

    if settings.near_deadline_days > 14:
        settings.near_deadline_days = 14

    settings.updated_at = datetime.utcnow()
    return settings

def should_send_alert_email(
    settings: OrganizationNotificationSettings | None,
    alert_type: str,
) -> bool:
    if not settings:
        return True

    if not settings.email_alerts_enabled:
        return False

    if alert_type == "invoice_rejected":
        return settings.send_rejected_alerts

    if alert_type == "invoice_overdue":
        return settings.send_overdue_alerts

    if alert_type == "invoice_near_deadline":
        return settings.send_near_deadline_alerts

    return True

def get_alert_recipient(
    settings: OrganizationNotificationSettings | None,
    fallback_email: str | None,
) -> str | None:
    if settings and settings.alert_email:
        return settings.alert_email
    return fallback_email
