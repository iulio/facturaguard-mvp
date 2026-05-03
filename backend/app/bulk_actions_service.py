from datetime import datetime
from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import Alert, Invoice, Organization, User
from .sync_service import sync_invoice_status

ALLOWED_BULK_ACTIONS = {
    "sync_status",
    "mark_unsent",
    "mark_pending",
    "resolve_related_alerts",
}

def run_bulk_invoice_action(
    db: Session,
    organization: Organization,
    actor: User,
    invoice_ids: list[int],
    action: str,
) -> dict:
    if action not in ALLOWED_BULK_ACTIONS:
        raise ValueError(f"Acțiune invalidă. Alege una din: {', '.join(sorted(ALLOWED_BULK_ACTIONS))}")

    unique_ids = sorted(set(invoice_ids))
    processed = 0
    skipped = 0

    invoices = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization.id, Invoice.id.in_(unique_ids))
        .all()
    )

    invoice_by_id = {invoice.id: invoice for invoice in invoices}

    for invoice_id in unique_ids:
        invoice = invoice_by_id.get(invoice_id)

        if not invoice:
            skipped += 1
            continue

        if action == "sync_status":
            sync_invoice_status(db, organization, invoice, actor=actor)
            processed += 1

        elif action == "mark_unsent":
            invoice.internal_status = "unsent"
            invoice.anaf_status = "pending"
            invoice.updated_at = datetime.utcnow()
            processed += 1

        elif action == "mark_pending":
            invoice.internal_status = "pending"
            invoice.anaf_status = "pending"
            invoice.updated_at = datetime.utcnow()
            processed += 1

        elif action == "resolve_related_alerts":
            alerts = (
                db.query(Alert)
                .filter(Alert.invoice_id == invoice.id, Alert.status == "open")
                .all()
            )
            for alert in alerts:
                alert.status = "resolved"
                alert.resolved_at = datetime.utcnow()
            processed += 1

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="bulk_invoice_action.executed",
        entity_type="invoice",
        message=f"Bulk action {action} executată pentru {processed} facturi. Skipped: {skipped}.",
    )

    db.flush()

    return {
        "organization_id": organization.id,
        "action": action,
        "requested": len(unique_ids),
        "processed": processed,
        "skipped": skipped,
        "message": f"Acțiunea {action} a fost aplicată pentru {processed} facturi.",
    }
