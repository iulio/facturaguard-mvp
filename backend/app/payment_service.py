from datetime import datetime
import secrets
from sqlalchemy.orm import Session

from .access import write_audit_log
from .billing import get_plan, update_subscription_plan
from .models import Organization, PaymentTransaction, User
from .settings import get_settings

def create_netopia_mock_checkout(
    db: Session,
    organization: Organization,
    plan_code: str,
    actor: User,
) -> PaymentTransaction:
    settings = get_settings()

    if not settings.netopia_mock_enabled:
        raise RuntimeError("Netopia mock provider este dezactivat.")

    plan = get_plan(plan_code)
    session_id = f"NETOPIA-MOCK-{secrets.token_urlsafe(18)}"

    # In a real Netopia integration, this would be the Netopia payment page.
    checkout_url = f"http://localhost:3000/billing/mock-netopia?session_id={session_id}"

    transaction = PaymentTransaction(
        organization_id=organization.id,
        provider="netopia_mock",
        provider_session_id=session_id,
        plan_code=plan.code,
        amount_eur=plan.monthly_price_eur,
        currency="EUR",
        status="pending",
        checkout_url=checkout_url,
    )
    db.add(transaction)
    db.flush()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="payment.checkout_created",
        entity_type="payment_transaction",
        entity_id=transaction.id,
        message=f"Checkout Netopia mock creat pentru planul {plan.code}.",
    )

    return transaction

def process_netopia_mock_webhook(
    db: Session,
    session_id: str,
    status: str,
    secret: str,
) -> PaymentTransaction:
    settings = get_settings()

    if secret != settings.netopia_mock_webhook_secret:
        raise PermissionError("Secret webhook invalid.")

    transaction = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.provider_session_id == session_id)
        .first()
    )
    if not transaction:
        raise ValueError("Tranzacția nu există.")

    if transaction.status == "paid":
        return transaction

    allowed_statuses = {"paid", "failed", "cancelled"}
    if status not in allowed_statuses:
        raise ValueError(f"Status invalid. Alege unul din: {', '.join(sorted(allowed_statuses))}")

    transaction.status = status
    transaction.raw_payload = f'{{"session_id": "{session_id}", "status": "{status}", "provider": "netopia_mock"}}'

    organization = db.query(Organization).filter(Organization.id == transaction.organization_id).first()

    if status == "paid":
        transaction.paid_at = datetime.utcnow()
        if organization:
            subscription = update_subscription_plan(db, organization, transaction.plan_code)
            write_audit_log(
                db,
                organization_id=organization.id,
                actor_user_id=None,
                action="payment.succeeded",
                entity_type="payment_transaction",
                entity_id=transaction.id,
                message=f"Plată Netopia mock reușită. Plan activat: {transaction.plan_code}.",
            )
            write_audit_log(
                db,
                organization_id=organization.id,
                actor_user_id=None,
                action="subscription.activated_from_payment",
                entity_type="organization_subscription",
                entity_id=subscription.id,
                message=f"Planul {transaction.plan_code} a fost activat automat după plată.",
            )
    elif organization:
        write_audit_log(
            db,
            organization_id=organization.id,
            actor_user_id=None,
            action=f"payment.{status}",
            entity_type="payment_transaction",
            entity_id=transaction.id,
            message=f"Plată Netopia mock cu status: {status}.",
        )

    db.flush()
    return transaction
