from sqlalchemy.orm import Session

from .models import Alert, Invoice, Organization, OrganizationMember, User

def calculate_risk_score(
    rejected: int,
    unsent: int,
    near_deadline: int,
    overdue: int,
    open_alerts: int,
    total_invoices: int,
) -> tuple[int, str]:
    score = 0
    score += rejected * 20
    score += overdue * 25
    score += near_deadline * 10
    score += unsent * 8
    score += open_alerts * 5

    if total_invoices > 0:
        issue_ratio = (rejected + overdue + near_deadline + unsent) / total_invoices
        score += int(issue_ratio * 40)

    score = min(score, 100)

    if score >= 60:
        return score, "high"
    if score >= 25:
        return score, "medium"
    return score, "low"

def get_accessible_organization_ids(db: Session, user: User) -> list[int]:
    owned_ids = [
        org.id
        for org in db.query(Organization)
        .filter(Organization.owner_user_id == user.id)
        .all()
    ]

    member_ids = [
        membership.organization_id
        for membership in db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.status == "active",
        )
        .all()
    ]

    return sorted(set(owned_ids + member_ids))

def build_portfolio_summary(
    db: Session,
    user: User,
    risk: str | None = None,
    search: str | None = None,
) -> dict:
    ids = get_accessible_organization_ids(db, user)
    if not ids:
        return {
            "total_organizations": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
            "total_open_alerts": 0,
            "organizations": [],
        }

    query = db.query(Organization).filter(Organization.id.in_(ids))

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Organization.name.ilike(search_pattern)) |
            (Organization.cui.ilike(search_pattern))
        )

    organizations = query.order_by(Organization.name.asc()).all()
    rows = []

    for organization in organizations:
        invoices = db.query(Invoice).filter(Invoice.organization_id == organization.id).all()
        open_alerts = (
            db.query(Alert)
            .filter(Alert.organization_id == organization.id, Alert.status == "open")
            .count()
        )

        total = len(invoices)
        validated = sum(1 for invoice in invoices if invoice.internal_status == "validated")
        rejected = sum(1 for invoice in invoices if invoice.internal_status == "rejected")
        unsent = sum(1 for invoice in invoices if invoice.internal_status == "unsent")
        near_deadline = sum(1 for invoice in invoices if invoice.internal_status == "near_deadline")
        overdue = sum(1 for invoice in invoices if invoice.internal_status == "overdue")

        risk_score, risk_label = calculate_risk_score(
            rejected=rejected,
            unsent=unsent,
            near_deadline=near_deadline,
            overdue=overdue,
            open_alerts=open_alerts,
            total_invoices=total,
        )

        row = {
            "organization_id": organization.id,
            "name": organization.name,
            "cui": organization.cui,
            "total_invoices": total,
            "validated": validated,
            "rejected": rejected,
            "unsent": unsent,
            "near_deadline": near_deadline,
            "overdue": overdue,
            "open_alerts": open_alerts,
            "risk_score": risk_score,
            "risk_label": risk_label,
        }

        if not risk or row["risk_label"] == risk:
            rows.append(row)

    rows.sort(key=lambda item: item["risk_score"], reverse=True)

    return {
        "total_organizations": len(rows),
        "high_risk": sum(1 for row in rows if row["risk_label"] == "high"),
        "medium_risk": sum(1 for row in rows if row["risk_label"] == "medium"),
        "low_risk": sum(1 for row in rows if row["risk_label"] == "low"),
        "total_open_alerts": sum(row["open_alerts"] for row in rows),
        "organizations": rows,
    }
