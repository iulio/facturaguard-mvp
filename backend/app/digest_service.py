from datetime import date
from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import Alert, Invoice, Organization, OrganizationNotificationSettings, User
from .notification_settings_service import get_alert_recipient, get_or_create_notification_settings
from .notifier import send_email_notification

def build_daily_digest(
    db: Session,
    organization: Organization,
    recipient: str | None,
) -> dict:
    today = date.today()

    invoices = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization.id)
        .all()
    )

    open_alerts = (
        db.query(Alert)
        .filter(Alert.organization_id == organization.id, Alert.status == "open")
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )

    total = len(invoices)
    validated = sum(1 for invoice in invoices if invoice.internal_status == "validated")
    rejected = sum(1 for invoice in invoices if invoice.internal_status == "rejected")
    overdue = sum(1 for invoice in invoices if invoice.internal_status == "overdue")
    near_deadline = sum(1 for invoice in invoices if invoice.internal_status == "near_deadline")
    unsent = sum(1 for invoice in invoices if invoice.internal_status == "unsent")

    subject = f"FacturaGuard daily digest - {organization.name} - {today.isoformat()}"

    lines = [
        f"FacturaGuard daily digest pentru {organization.name}",
        f"Data: {today.isoformat()}",
        "",
        "Sumar facturi:",
        f"- Total facturi: {total}",
        f"- Validate: {validated}",
        f"- Respinse: {rejected}",
        f"- Depășite: {overdue}",
        f"- Aproape de termen: {near_deadline}",
        f"- Netrimise: {unsent}",
        f"- Alerte deschise: {len(open_alerts)}",
        "",
        "Alerte recente:",
    ]

    if not open_alerts:
        lines.append("- Nu există alerte deschise.")
    else:
        for alert in open_alerts:
            lines.append(f"- [{alert.severity}] {alert.title}: {alert.message}")

    lines.extend([
        "",
        "Acesta este un digest automat FacturaGuard.",
    ])

    return {
        "organization_id": organization.id,
        "recipient": recipient,
        "subject": subject,
        "body": "\n".join(lines),
        "would_send": bool(recipient),
    }

def send_daily_digest(
    db: Session,
    organization: Organization,
    actor: User | None = None,
    force: bool = False,
) -> dict:
    settings = get_or_create_notification_settings(
        db,
        organization,
        default_email=actor.email if actor else None,
    )

    recipient = get_alert_recipient(settings, actor.email if actor else None)
    digest = build_daily_digest(db, organization, recipient)

    if not force and not settings.daily_digest_enabled:
        return {
            "organization_id": organization.id,
            "sent": False,
            "recipient": recipient,
            "message": "Daily digest este dezactivat pentru această firmă.",
        }

    if not settings.email_alerts_enabled:
        return {
            "organization_id": organization.id,
            "sent": False,
            "recipient": recipient,
            "message": "Email alerts sunt dezactivate pentru această firmă.",
        }

    if not recipient:
        return {
            "organization_id": organization.id,
            "sent": False,
            "recipient": None,
            "message": "Nu există email destinatar pentru digest.",
        }

    send_email_notification(recipient, digest["subject"], digest["body"])

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id if actor else None,
        action="digest.email_sent",
        entity_type="organization",
        entity_id=organization.id,
        message=f"Daily digest trimis către {recipient}.",
    )

    db.flush()

    return {
        "organization_id": organization.id,
        "sent": True,
        "recipient": recipient,
        "message": "Daily digest trimis.",
    }

def send_due_digests_for_all_organizations(db: Session) -> list[dict]:
    organizations = db.query(Organization).all()
    results = []

    for organization in organizations:
        settings = (
            db.query(OrganizationNotificationSettings)
            .filter(OrganizationNotificationSettings.organization_id == organization.id)
            .first()
        )
        if not settings or not settings.daily_digest_enabled:
            continue

        results.append(send_daily_digest(db, organization, actor=None, force=False))

    return results
