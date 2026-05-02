from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Session

from .models import Invoice, Organization, OrganizationDocument, OrganizationSubscription, User

@dataclass(frozen=True)
class Plan:
    code: str
    name: str
    monthly_price_eur: float
    max_organizations: int
    max_invoices_per_month: int
    max_documents: int
    features: list[str]

PLANS: dict[str, Plan] = {
    "free": Plan(
        code="free",
        name="Free",
        monthly_price_eur=0,
        max_organizations=1,
        max_invoices_per_month=30,
        max_documents=50,
        features=["1 firmă", "30 facturi/lună", "CSV/XML upload", "alerte basic"],
    ),
    "starter": Plan(
        code="starter",
        name="Starter",
        monthly_price_eur=19,
        max_organizations=5,
        max_invoices_per_month=500,
        max_documents=1000,
        features=["5 firme", "500 facturi/lună", "raport PDF", "export CSV", "invitații client"],
    ),
    "pro": Plan(
        code="pro",
        name="Pro",
        monthly_price_eur=49,
        max_organizations=25,
        max_invoices_per_month=5000,
        max_documents=10000,
        features=["25 firme", "5000 facturi/lună", "portfolio dashboard", "mock ANAF sync", "audit log"],
    ),
    "agency": Plan(
        code="agency",
        name="Agency",
        monthly_price_eur=149,
        max_organizations=200,
        max_invoices_per_month=50000,
        max_documents=100000,
        features=["200 firme", "50k facturi/lună", "S3 storage", "prioritate suport", "pregătit multi-tenant"],
    ),
}

def list_plans() -> list[dict]:
    return [plan.__dict__ for plan in PLANS.values()]

def get_plan(plan_code: str) -> Plan:
    if plan_code not in PLANS:
        raise ValueError(f"Plan invalid: {plan_code}")
    return PLANS[plan_code]

def get_or_create_subscription(db: Session, organization: Organization) -> OrganizationSubscription:
    subscription = (
        db.query(OrganizationSubscription)
        .filter(OrganizationSubscription.organization_id == organization.id)
        .first()
    )
    if subscription:
        return subscription

    subscription = OrganizationSubscription(
        organization_id=organization.id,
        plan_code="free",
        status="active",
    )
    db.add(subscription)
    db.flush()
    return subscription

def update_subscription_plan(db: Session, organization: Organization, plan_code: str) -> OrganizationSubscription:
    get_plan(plan_code)
    subscription = get_or_create_subscription(db, organization)
    subscription.plan_code = plan_code
    subscription.updated_at = datetime.utcnow()
    db.flush()
    return subscription

def get_month_invoice_count(db: Session, organization_id: int, year: int, month: int) -> int:
    invoices = (
        db.query(Invoice)
        .filter(Invoice.organization_id == organization_id)
        .all()
    )
    return sum(1 for invoice in invoices if invoice.issue_date.year == year and invoice.issue_date.month == month)

def get_document_count(db: Session, organization_id: int) -> int:
    return (
        db.query(OrganizationDocument)
        .filter(OrganizationDocument.organization_id == organization_id)
        .count()
    )

def get_usage(db: Session, organization: Organization) -> dict:
    subscription = get_or_create_subscription(db, organization)
    plan = get_plan(subscription.plan_code)
    now = datetime.utcnow()

    return {
        "organization_id": organization.id,
        "plan_code": subscription.plan_code,
        "invoices_this_month": get_month_invoice_count(db, organization.id, now.year, now.month),
        "documents_total": get_document_count(db, organization.id),
        "max_invoices_per_month": plan.max_invoices_per_month,
        "max_documents": plan.max_documents,
    }

def assert_can_create_organization(db: Session, user: User) -> None:
    # MVP rule: organization count limit is based on the highest plan among user's owned orgs.
    owned_orgs = db.query(Organization).filter(Organization.owner_user_id == user.id).all()

    if not owned_orgs:
        return

    highest_limit = 1
    for org in owned_orgs:
        subscription = get_or_create_subscription(db, org)
        plan = get_plan(subscription.plan_code)
        highest_limit = max(highest_limit, plan.max_organizations)

    if len(owned_orgs) >= highest_limit:
        raise PermissionError(
            f"Limita de firme pentru planul curent este {highest_limit}. Fă upgrade pentru mai multe firme."
        )

def assert_can_import_invoices(db: Session, organization: Organization, incoming_count: int) -> None:
    subscription = get_or_create_subscription(db, organization)
    plan = get_plan(subscription.plan_code)
    now = datetime.utcnow()
    current_count = get_month_invoice_count(db, organization.id, now.year, now.month)

    if current_count + incoming_count > plan.max_invoices_per_month:
        raise PermissionError(
            f"Limita lunară de facturi pentru planul {plan.name} este {plan.max_invoices_per_month}."
        )

def assert_can_store_document(db: Session, organization: Organization) -> None:
    subscription = get_or_create_subscription(db, organization)
    plan = get_plan(subscription.plan_code)
    current_count = get_document_count(db, organization.id)

    if current_count + 1 > plan.max_documents:
        raise PermissionError(
            f"Limita de documente pentru planul {plan.name} este {plan.max_documents}."
        )
