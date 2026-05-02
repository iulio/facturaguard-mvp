from datetime import datetime
from sqlalchemy.orm import Session

from .access import write_audit_log
from .anaf_client import get_anaf_client
from .models import Invoice, Organization, OrganizationIntegration, User
from .services import compute_internal_status, create_alert_for_invoice, explain_anaf_error

def get_or_create_anaf_integration(db: Session, organization_id: int) -> OrganizationIntegration:
    integration = (
        db.query(OrganizationIntegration)
        .filter(
            OrganizationIntegration.organization_id == organization_id,
            OrganizationIntegration.provider == "anaf",
        )
        .first()
    )
    if integration:
        return integration

    integration = OrganizationIntegration(
        organization_id=organization_id,
        provider="anaf",
        mode="mock",
        status="not_configured",
        config_json='{"note": "mock connector; no real ANAF credentials stored"}',
    )
    db.add(integration)
    db.flush()
    return integration

def test_anaf_connection(db: Session, organization: Organization, actor: User | None = None) -> OrganizationIntegration:
    integration = get_or_create_anaf_integration(db, organization.id)
    client = get_anaf_client(integration)
    status, message = client.test_connection()

    integration.status = status
    integration.last_checked_at = datetime.utcnow()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id if actor else None,
        action="anaf.connection_tested",
        entity_type="organization_integration",
        entity_id=integration.id,
        message=message,
    )

    db.flush()
    return integration

def sync_invoice_status(
    db: Session,
    organization: Organization,
    invoice: Invoice,
    actor: User | None = None,
) -> dict:
    integration = get_or_create_anaf_integration(db, organization.id)
    client = get_anaf_client(integration)

    old_status = invoice.internal_status
    result = client.fetch_invoice_status(invoice)

    invoice.anaf_status = result.status
    invoice.anaf_message = result.message
    invoice.anaf_upload_id = result.upload_id
    invoice.plain_explanation = explain_anaf_error(result.message)
    invoice.internal_status, invoice.due_submission_date = compute_internal_status(
        invoice.issue_date,
        invoice.anaf_status,
    )
    invoice.last_synced_at = datetime.utcnow()
    invoice.updated_at = datetime.utcnow()

    create_alert_for_invoice(
        db,
        organization,
        invoice,
        notify_email=actor.email if actor else None,
    )

    changed = old_status != invoice.internal_status

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id if actor else None,
        action="invoice.status_synced",
        entity_type="invoice",
        entity_id=invoice.id,
        message=f"Factura {invoice.invoice_number}: {old_status} -> {invoice.internal_status}.",
    )

    db.flush()

    return {
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "old_status": old_status,
        "new_status": invoice.internal_status,
        "changed": changed,
        "message": result.message,
    }

def sync_organization_invoices(
    db: Session,
    organization: Organization,
    actor: User | None = None,
    only_open: bool = True,
) -> dict:
    query = db.query(Invoice).filter(Invoice.organization_id == organization.id)

    if only_open:
        query = query.filter(Invoice.internal_status != "validated")

    invoices = query.order_by(Invoice.issue_date.desc()).all()
    results = [
        sync_invoice_status(db, organization, invoice, actor=actor)
        for invoice in invoices
    ]

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id if actor else None,
        action="organization.status_sync_completed",
        entity_type="organization",
        entity_id=organization.id,
        message=f"Sincronizare statusuri finalizată pentru {len(results)} facturi.",
    )

    return {
        "organization_id": organization.id,
        "checked": len(results),
        "changed": sum(1 for item in results if item["changed"]),
        "results": results,
    }
