from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import Invoice, Organization, User

ALLOWED_PRIORITIES = {"low", "normal", "high", "urgent"}

def update_invoice_metadata(
    db: Session,
    organization: Organization,
    invoice: Invoice,
    actor: User,
    tags: str | None = None,
    priority: str | None = None,
    assignee_user_id: int | None = None,
) -> Invoice:
    if priority is not None and priority not in ALLOWED_PRIORITIES:
        raise ValueError(f"Prioritate invalidă. Alege una din: {', '.join(sorted(ALLOWED_PRIORITIES))}")

    if tags is not None:
        cleaned_tags = ",".join([tag.strip() for tag in tags.split(",") if tag.strip()])
        if len(cleaned_tags) > 500:
            raise ValueError("Lista de taguri este prea lungă.")
        invoice.tags = cleaned_tags or None

    if priority is not None:
        invoice.priority = priority

    if assignee_user_id is not None:
        invoice.assignee_user_id = assignee_user_id

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="invoice.metadata_updated",
        entity_type="invoice",
        entity_id=invoice.id,
        message=f"Metadata actualizată pentru factura {invoice.invoice_number}.",
    )

    db.flush()
    return invoice
