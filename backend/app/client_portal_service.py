from sqlalchemy.orm import Session

from .models import Alert, Invoice, Organization, OrganizationDocument, OrganizationMember, User

def get_client_portal_organizations(db: Session, user: User) -> list[dict]:
    memberships = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == "active",
        )
        .all()
    )

    rows = []

    for membership in memberships:
        org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
        if not org:
            continue

        invoices = db.query(Invoice).filter(Invoice.organization_id == org.id).all()
        open_alerts = (
            db.query(Alert)
            .filter(Alert.organization_id == org.id, Alert.status == "open")
            .count()
        )

        rows.append({
            "id": org.id,
            "name": org.name,
            "cui": org.cui,
            "role": membership.role,
            "total_invoices": len(invoices),
            "open_alerts": open_alerts,
            "rejected": sum(1 for invoice in invoices if invoice.internal_status == "rejected"),
            "overdue": sum(1 for invoice in invoices if invoice.internal_status == "overdue"),
            "near_deadline": sum(1 for invoice in invoices if invoice.internal_status == "near_deadline"),
        })

    return rows

def get_client_portal_detail(db: Session, user: User, organization_id: int) -> dict:
    organizations = get_client_portal_organizations(db, user)
    organization_row = next((row for row in organizations if row["id"] == organization_id), None)

    if not organization_row:
        raise PermissionError("Nu ai acces la această firmă în portalul client.")

    recent_invoices = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization_id)
        .order_by(Invoice.issue_date.desc())
        .limit(20)
        .all()
    )

    open_alerts = (
        db.query(Alert)
        .filter(Alert.organization_id == organization_id, Alert.status == "open")
        .order_by(Alert.created_at.desc())
        .limit(20)
        .all()
    )

    documents = (
        db.query(OrganizationDocument)
        .filter(OrganizationDocument.organization_id == organization_id)
        .order_by(OrganizationDocument.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "organization": organization_row,
        "recent_invoices": recent_invoices,
        "open_alerts": open_alerts,
        "documents": documents,
    }
