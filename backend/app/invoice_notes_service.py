from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import Invoice, InvoiceNote, Organization, User

def list_invoice_notes(db: Session, organization: Organization, invoice: Invoice, include_internal: bool = True) -> list[InvoiceNote]:
    query = (
        db.query(InvoiceNote)
        .filter(
            InvoiceNote.organization_id == organization.id,
            InvoiceNote.invoice_id == invoice.id,
        )
    )

    if not include_internal:
        query = query.filter(InvoiceNote.is_internal == False)  # noqa: E712

    return query.order_by(InvoiceNote.created_at.desc()).all()

def create_invoice_note(
    db: Session,
    organization: Organization,
    invoice: Invoice,
    actor: User,
    body: str,
    is_internal: bool = False,
) -> InvoiceNote:
    cleaned = body.strip()
    if not cleaned:
        raise ValueError("Nota nu poate fi goală.")
    if len(cleaned) > 5000:
        raise ValueError("Nota este prea lungă. Maxim 5000 caractere.")

    note = InvoiceNote(
        organization_id=organization.id,
        invoice_id=invoice.id,
        author_user_id=actor.id,
        body=cleaned,
        is_internal=is_internal,
    )
    db.add(note)
    db.flush()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="invoice_note.created",
        entity_type="invoice",
        entity_id=invoice.id,
        message=f"Notă adăugată pe factura {invoice.invoice_number}.",
    )

    return note
