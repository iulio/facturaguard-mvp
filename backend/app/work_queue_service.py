from sqlalchemy.orm import Session

from .models import Invoice, Organization

WORK_STATUSES = {"rejected", "overdue", "near_deadline", "unsent", "pending"}

def build_work_queue(
    db: Session,
    organization: Organization,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    limit: int = 100,
) -> dict:
    query = db.query(Invoice).filter(Invoice.organization_id == organization.id)

    if status:
        query = query.filter(Invoice.internal_status == status)
    else:
        query = query.filter(Invoice.internal_status.in_(WORK_STATUSES))

    if priority:
        query = query.filter(Invoice.priority == priority)

    if tag:
        query = query.filter(Invoice.tags.ilike(f"%{tag}%"))

    limit = min(max(limit, 1), 500)

    priority_rank = {
        "urgent": 4,
        "high": 3,
        "normal": 2,
        "low": 1,
    }

    invoices = query.all()
    invoices.sort(
        key=lambda invoice: (
            -priority_rank.get(invoice.priority or "normal", 2),
            invoice.due_submission_date,
            invoice.issue_date,
        )
    )
    invoices = invoices[:limit]

    all_invoices = db.query(Invoice).filter(Invoice.organization_id == organization.id).all()

    return {
        "organization_id": organization.id,
        "total": len(invoices),
        "urgent": sum(1 for invoice in all_invoices if invoice.priority == "urgent"),
        "high": sum(1 for invoice in all_invoices if invoice.priority == "high"),
        "rejected": sum(1 for invoice in all_invoices if invoice.internal_status == "rejected"),
        "overdue": sum(1 for invoice in all_invoices if invoice.internal_status == "overdue"),
        "near_deadline": sum(1 for invoice in all_invoices if invoice.internal_status == "near_deadline"),
        "invoices": invoices,
    }
