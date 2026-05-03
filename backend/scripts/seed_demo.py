"""Seed demo data for local FacturaGuard demos.

Usage:
    cd backend
    python scripts/seed_demo.py

Default login:
    demo@facturaguard.local / DemoPassword123!
"""
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.auth import hash_password
from app.billing import get_or_create_subscription, update_subscription_plan
from app.database import Base, SessionLocal, engine
from app.models import Invoice, Organization, OrganizationMember, User
from app.services import compute_internal_status, create_alert_for_invoice, explain_anaf_error

DEMO_EMAIL = "demo@facturaguard.local"
DEMO_PASSWORD = "DemoPassword123!"

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if not user:
            user = User(
                name="Demo Accountant",
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                role="accountant",
            )
            db.add(user)
            db.flush()

        organizations_payload = [
            {"name": "Demo Construct SRL", "cui": "RO10000001"},
            {"name": "Demo Retail SRL", "cui": "RO10000002"},
            {"name": "Demo Transport SRL", "cui": "RO10000003"},
        ]

        for payload in organizations_payload:
            org = db.query(Organization).filter(Organization.cui == payload["cui"]).first()
            if not org:
                org = Organization(
                    owner_user_id=user.id,
                    name=payload["name"],
                    cui=payload["cui"],
                )
                db.add(org)
                db.flush()

                db.add(OrganizationMember(
                    organization_id=org.id,
                    user_id=user.id,
                    role="accountant_owner",
                    status="active",
                ))
                get_or_create_subscription(db, org)
                update_subscription_plan(db, org, "pro")

            existing_count = db.query(Invoice).filter(Invoice.organization_id == org.id).count()
            if existing_count == 0:
                invoices = [
                    {
                        "invoice_number": f"{payload['cui']}-001",
                        "issue_date": date(2026, 4, 27),
                        "customer_name": "Client Valid SRL",
                        "customer_cui": "RO20000001",
                        "total_amount": 1200.0,
                        "anaf_status": "validated",
                        "anaf_message": None,
                    },
                    {
                        "invoice_number": f"{payload['cui']}-002",
                        "issue_date": date(2026, 4, 28),
                        "customer_name": "Client Problem SRL",
                        "customer_cui": "RO00000000",
                        "total_amount": 850.0,
                        "anaf_status": "rejected",
                        "anaf_message": "CUI invalid pentru client",
                    },
                    {
                        "invoice_number": f"{payload['cui']}-003",
                        "issue_date": date(2026, 4, 29),
                        "customer_name": "Client Pending SRL",
                        "customer_cui": "RO20000003",
                        "total_amount": 3400.0,
                        "anaf_status": "pending",
                        "anaf_message": None,
                    },
                ]

                for item in invoices:
                    internal_status, due_date = compute_internal_status(item["issue_date"], item["anaf_status"])
                    invoice = Invoice(
                        organization_id=org.id,
                        invoice_number=item["invoice_number"],
                        issue_date=item["issue_date"],
                        due_submission_date=due_date,
                        customer_name=item["customer_name"],
                        customer_cui=item["customer_cui"],
                        total_amount=item["total_amount"],
                        currency="RON",
                        source="demo_seed",
                        internal_status=internal_status,
                        anaf_status=item["anaf_status"],
                        anaf_message=item["anaf_message"],
                        plain_explanation=explain_anaf_error(item["anaf_message"]),
                    )
                    db.add(invoice)
                    db.flush()
                    create_alert_for_invoice(db, org, invoice, notify_email=None)

        db.commit()
        print("Demo data created.")
        print(f"Login: {DEMO_EMAIL}")
        print(f"Password: {DEMO_PASSWORD}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
