from datetime import datetime
import hashlib
import hmac
import json
import secrets
import httpx
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


# ---------------------------------------------------------------------------
# NETOPIA Payments API v2 integration
# ---------------------------------------------------------------------------

def get_netopia_v2_base_url() -> str:
    settings = get_settings()
    return settings.netopia_live_base_url.rstrip("/") if settings.netopia_is_live else settings.netopia_sandbox_base_url.rstrip("/")

def get_netopia_v2_config_status() -> dict:
    settings = get_settings()

    required = {
        "NETOPIA_API_KEY": settings.netopia_api_key,
        "NETOPIA_POS_SIGNATURE": settings.netopia_pos_signature,
        "NETOPIA_NOTIFY_URL": settings.netopia_notify_url,
        "NETOPIA_REDIRECT_URL": settings.netopia_redirect_url,
    }
    missing = [key for key, value in required.items() if not value]

    return {
        "provider": settings.netopia_provider,
        "mode": "live" if settings.netopia_is_live else "sandbox",
        "base_url": get_netopia_v2_base_url(),
        "configured": len(missing) == 0,
        "missing_variables": missing,
        "notify_url": settings.netopia_notify_url,
        "redirect_url": settings.netopia_redirect_url,
        "cancel_url": settings.netopia_cancel_url,
        "currency": settings.netopia_currency,
    }

def build_netopia_order_id(organization: Organization, plan_code: str) -> str:
    return f"FG-{organization.id}-{plan_code}-{secrets.token_hex(8)}"

def build_netopia_v2_start_payload(
    organization: Organization,
    plan_code: str,
    actor: User,
    order_id: str,
) -> dict:
    settings = get_settings()
    plan = get_plan(plan_code)

    # NETOPIA v2 request shape is JSON with config/payment/order sections.
    # We intentionally do not collect card data inside FacturaGuard. The
    # gateway/3DS URL returned by NETOPIA must be used for the customer step.
    return {
        "config": {
            "notifyUrl": settings.netopia_notify_url,
            "redirectUrl": settings.netopia_redirect_url,
            "cancelUrl": settings.netopia_cancel_url or settings.netopia_redirect_url,
            "language": settings.netopia_language,
            "emailTemplate": "default",
            "emailSubject": f"FacturaGuard - plan {plan.name}",
        },
        "payment": {
            "options": {
                "installments": 1,
                "bonus": 0,
            },
            "instrument": {
                "type": "card",
            },
        },
        "order": {
            "orderID": order_id,
            "amount": float(plan.monthly_price_eur),
            "currency": settings.netopia_currency,
            "description": f"FacturaGuard subscription - {plan.name}",
            "billing": {
                "email": actor.email,
                "firstName": actor.name or "FacturaGuard",
                "lastName": "User",
                "city": "Bucuresti",
                "country": 642,
                "state": "Bucuresti",
                "postalCode": "010000",
                "details": organization.address or organization.name,
                "phone": "0700000000",
            },
            "products": [
                {
                    "name": f"FacturaGuard {plan.name}",
                    "code": plan.code,
                    "category": "SaaS",
                    "price": float(plan.monthly_price_eur),
                    "vat": 0,
                }
            ],
        },
    }

def extract_netopia_checkout_url(response_payload: dict) -> str | None:
    candidates: list[str | None] = [
        response_payload.get("checkoutUrl"),
        response_payload.get("checkout_url"),
        response_payload.get("paymentUrl"),
        response_payload.get("payment_url"),
        response_payload.get("redirectUrl"),
        response_payload.get("redirect_url"),
        response_payload.get("authUrl"),
        response_payload.get("auth_url"),
    ]

    payment = response_payload.get("payment")
    if isinstance(payment, dict):
        candidates.extend([
            payment.get("checkoutUrl"),
            payment.get("paymentUrl"),
            payment.get("redirectUrl"),
            payment.get("authUrl"),
            payment.get("url"),
        ])

    data = response_payload.get("data")
    if isinstance(data, dict):
        candidates.extend([
            data.get("checkoutUrl"),
            data.get("paymentUrl"),
            data.get("redirectUrl"),
            data.get("authUrl"),
            data.get("url"),
        ])

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.startswith("http"):
            return candidate

    return None

def extract_netopia_payment_id(response_payload: dict) -> str | None:
    candidates = [
        response_payload.get("paymentID"),
        response_payload.get("paymentId"),
        response_payload.get("payment_id"),
        response_payload.get("ntpID"),
        response_payload.get("ntpId"),
    ]
    payment = response_payload.get("payment")
    if isinstance(payment, dict):
        candidates.extend([
            payment.get("paymentID"),
            payment.get("paymentId"),
            payment.get("payment_id"),
            payment.get("ntpID"),
            payment.get("ntpId"),
        ])
    for candidate in candidates:
        if candidate is not None:
            return str(candidate)
    return None

def create_netopia_checkout(
    db: Session,
    organization: Organization,
    plan_code: str,
    actor: User,
) -> PaymentTransaction:
    settings = get_settings()

    if settings.netopia_provider == "mock":
        return create_netopia_mock_checkout(db, organization, plan_code, actor)

    if settings.netopia_provider != "v2":
        raise RuntimeError("NETOPIA_PROVIDER trebuie să fie 'mock' sau 'v2'.")

    config = get_netopia_v2_config_status()
    if not config["configured"]:
        raise RuntimeError(f"Lipsesc variabile NETOPIA: {', '.join(config['missing_variables'])}")

    plan = get_plan(plan_code)
    order_id = build_netopia_order_id(organization, plan.code)
    payload = build_netopia_v2_start_payload(organization, plan.code, actor, order_id)

    base_url = get_netopia_v2_base_url()
    endpoint = f"{base_url}/payment/card/start"

    response = httpx.post(
        endpoint,
        json=payload,
        headers={
            "Authorization": settings.netopia_api_key or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=45,
    )

    raw_text = response.text
    try:
        response_payload = response.json()
    except Exception:
        response_payload = {"raw": raw_text}

    if response.status_code >= 400:
        raise RuntimeError(f"NETOPIA start payment a eșuat: HTTP {response.status_code} - {raw_text[:500]}")

    checkout_url = extract_netopia_checkout_url(response_payload)
    payment_id = extract_netopia_payment_id(response_payload)

    transaction = PaymentTransaction(
        organization_id=organization.id,
        provider="netopia_v2",
        provider_session_id=order_id,
        provider_order_id=order_id,
        provider_payment_id=payment_id,
        provider_status=str(response_payload.get("status") or response_payload.get("payment", {}).get("status") if isinstance(response_payload.get("payment"), dict) else "started"),
        plan_code=plan.code,
        amount_eur=plan.monthly_price_eur,
        currency=settings.netopia_currency,
        status="pending",
        checkout_url=checkout_url,
        raw_payload=json.dumps({"request": payload, "response": response_payload}, ensure_ascii=False),
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
        message=f"Checkout NETOPIA v2 creat pentru planul {plan.code}. order_id={order_id}.",
    )

    return transaction



def _clean_signature(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip()
    if "=" in value and value.lower().startswith(("sha256=", "sha512=", "hmac=")):
        return value.split("=", 1)[1].strip()
    return value

def verify_netopia_ipn_signature(
    raw_body: bytes,
    signature_header: str | None,
    shared_secret_header: str | None,
) -> None:
    """Verify NETOPIA IPN authenticity according to configured local policy.

    This supports a strict local shared-secret strategy immediately and HMAC
    verification for deployments that configure NETOPIA/proxy/webhook signing.
    Keep NETOPIA_IPN_REQUIRE_SIGNATURE=false during sandbox discovery if the
    exact provider signature format is not enabled yet.
    """
    settings = get_settings()
    mode = (settings.netopia_ipn_signature_mode or "none").lower()
    configured_secret = settings.netopia_ipn_shared_secret

    if mode == "none":
        return

    if not configured_secret:
        if settings.netopia_ipn_require_signature:
            raise PermissionError("NETOPIA_IPN_SHARED_SECRET lipsește.")
        return

    if mode == "shared_secret":
        if shared_secret_header == configured_secret:
            return
        if settings.netopia_ipn_require_signature:
            raise PermissionError("Secret IPN NETOPIA invalid.")
        return

    if mode in {"hmac_sha256", "hmac_sha512"}:
        if not signature_header:
            if settings.netopia_ipn_require_signature:
                raise PermissionError("Semnătură IPN NETOPIA lipsă.")
            return

        digestmod = hashlib.sha256 if mode == "hmac_sha256" else hashlib.sha512
        expected = hmac.new(
            configured_secret.encode("utf-8"),
            raw_body,
            digestmod,
        ).hexdigest()

        supplied = _clean_signature(signature_header)
        if hmac.compare_digest(expected.lower(), supplied.lower()):
            return

        if settings.netopia_ipn_require_signature:
            raise PermissionError("Semnătură IPN NETOPIA invalidă.")
        return

    raise PermissionError(f"NETOPIA_IPN_SIGNATURE_MODE invalid: {mode}.")

def normalize_netopia_status(payload: dict) -> str:
    raw_values = [
        payload.get("status"),
        payload.get("orderStatus"),
        payload.get("paymentStatus"),
        payload.get("statusText"),
    ]

    payment = payload.get("payment")
    if isinstance(payment, dict):
        raw_values.extend([
            payment.get("status"),
            payment.get("statusText"),
            payment.get("paymentStatus"),
        ])

    order = payload.get("order")
    if isinstance(order, dict):
        raw_values.extend([
            order.get("status"),
            order.get("orderStatus"),
        ])

    text = " ".join(str(value).lower() for value in raw_values if value is not None)

    if any(marker in text for marker in ["paid", "confirmed", "captured", "success", "approved", "3"]):
        return "paid"
    if any(marker in text for marker in ["cancel", "canceled", "cancelled"]):
        return "cancelled"
    if any(marker in text for marker in ["fail", "failed", "declined", "rejected", "error"]):
        return "failed"

    return "pending"

def extract_netopia_order_id(payload: dict) -> str | None:
    candidates = [
        payload.get("orderID"),
        payload.get("orderId"),
        payload.get("order_id"),
        payload.get("merchantOrderId"),
    ]
    order = payload.get("order")
    if isinstance(order, dict):
        candidates.extend([
            order.get("orderID"),
            order.get("orderId"),
            order.get("order_id"),
            order.get("merchantOrderId"),
        ])

    for candidate in candidates:
        if candidate:
            return str(candidate)
    return None

def process_netopia_v2_webhook(
    db: Session,
    payload: dict,
    signature_header: str | None = None,
    shared_secret: str | None = None,
    raw_body: bytes | None = None,
) -> PaymentTransaction | None:
    verify_netopia_ipn_signature(
        raw_body=raw_body or json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        signature_header=signature_header,
        shared_secret_header=shared_secret,
    )

    order_id = extract_netopia_order_id(payload)
    payment_id = extract_netopia_payment_id(payload)
    status = normalize_netopia_status(payload)

    query = db.query(PaymentTransaction).filter(PaymentTransaction.provider == "netopia_v2")

    transaction = None
    if order_id:
        transaction = query.filter(PaymentTransaction.provider_order_id == order_id).first()
    if not transaction and payment_id:
        transaction = query.filter(PaymentTransaction.provider_payment_id == payment_id).first()

    if not transaction:
        return None

    transaction.provider_status = str(payload.get("status") or status)
    transaction.raw_payload = json.dumps(payload, ensure_ascii=False)

    organization = db.query(Organization).filter(Organization.id == transaction.organization_id).first()

    if status == "paid":
        already_paid = transaction.status == "paid"
        transaction.status = "paid"
        if not transaction.paid_at:
            transaction.paid_at = datetime.utcnow()
        if organization and not already_paid:
            subscription = update_subscription_plan(db, organization, transaction.plan_code)
            subscription.billing_provider = "netopia_v2"
            subscription.billing_subscription_id = transaction.provider_order_id
            subscription.updated_at = datetime.utcnow()

            write_audit_log(
                db,
                organization_id=organization.id,
                actor_user_id=None,
                action="payment.succeeded",
                entity_type="payment_transaction",
                entity_id=transaction.id,
                message=f"Plată NETOPIA v2 reușită. Plan activat: {transaction.plan_code}.",
            )
            write_audit_log(
                db,
                organization_id=organization.id,
                actor_user_id=None,
                action="subscription.activated_from_payment",
                entity_type="organization_subscription",
                entity_id=subscription.id,
                message=f"Planul {transaction.plan_code} a fost activat automat după NETOPIA v2.",
            )
    elif status in {"failed", "cancelled"}:
        transaction.status = status
        if organization:
            write_audit_log(
                db,
                organization_id=organization.id,
                actor_user_id=None,
                action=f"payment.{status}",
                entity_type="payment_transaction",
                entity_id=transaction.id,
                message=f"Plată NETOPIA v2 cu status: {status}.",
            )
    else:
        transaction.status = "pending"

    db.flush()
    return transaction


# ---------------------------------------------------------------------------
# NETOPIA reconciliation / status check
# ---------------------------------------------------------------------------

def list_organization_payment_transactions(
    db: Session,
    organization: Organization,
    limit: int = 50,
) -> list[PaymentTransaction]:
    limit = min(max(limit, 1), 200)
    return (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.organization_id == organization.id)
        .order_by(PaymentTransaction.created_at.desc())
        .limit(limit)
        .all()
    )

def build_netopia_status_payload(transaction: PaymentTransaction) -> dict:
    settings = get_settings()
    payload = {
        "posSignature": settings.netopia_pos_signature,
        "orderID": transaction.provider_order_id or transaction.provider_session_id,
    }

    if transaction.provider_payment_id:
        payload["ntpID"] = transaction.provider_payment_id

    return payload

def check_netopia_transaction_status(
    db: Session,
    organization: Organization,
    transaction_id: int,
    actor: User,
) -> dict:
    settings = get_settings()
    transaction = (
        db.query(PaymentTransaction)
        .filter(
            PaymentTransaction.id == transaction_id,
            PaymentTransaction.organization_id == organization.id,
        )
        .first()
    )

    if not transaction:
        raise ValueError("Tranzacția nu există.")

    previous_status = transaction.status

    if transaction.provider == "netopia_mock" or settings.netopia_provider == "mock":
        return {
            "transaction_id": transaction.id,
            "organization_id": organization.id,
            "provider": transaction.provider,
            "provider_order_id": transaction.provider_order_id,
            "provider_payment_id": transaction.provider_payment_id,
            "previous_status": previous_status,
            "current_status": transaction.status,
            "provider_status": transaction.provider_status,
            "changed": False,
            "message": "Providerul este mock. Nu există status extern de verificat.",
            "raw_response": None,
        }

    if transaction.provider != "netopia_v2":
        raise ValueError(f"Providerul tranzacției nu este suportat pentru status check: {transaction.provider}")

    config = get_netopia_v2_config_status()
    if not config["configured"]:
        raise RuntimeError(f"Lipsesc variabile NETOPIA: {', '.join(config['missing_variables'])}")

    payload = build_netopia_status_payload(transaction)
    endpoint = f"{get_netopia_v2_base_url()}/operation/status"

    response = httpx.post(
        endpoint,
        json=payload,
        headers={
            "Authorization": settings.netopia_api_key or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        timeout=45,
    )

    raw_text = response.text
    try:
        response_payload = response.json()
    except Exception:
        response_payload = {"raw": raw_text}

    if response.status_code >= 400:
        raise RuntimeError(f"NETOPIA status check a eșuat: HTTP {response.status_code} - {raw_text[:500]}")

    normalized_status = normalize_netopia_status(response_payload)
    provider_status = str(
        response_payload.get("status")
        or response_payload.get("payment", {}).get("status") if isinstance(response_payload.get("payment"), dict) else normalized_status
    )

    transaction.provider_status = provider_status
    transaction.raw_payload = json.dumps(
        {
            "last_status_check_request": payload,
            "last_status_check_response": response_payload,
        },
        ensure_ascii=False,
    )

    if normalized_status == "paid":
        already_paid = transaction.status == "paid"
        transaction.status = "paid"
        if not transaction.paid_at:
            transaction.paid_at = datetime.utcnow()

        if not already_paid:
            subscription = update_subscription_plan(db, organization, transaction.plan_code)
            subscription.billing_provider = "netopia_v2"
            subscription.billing_subscription_id = transaction.provider_order_id
            subscription.updated_at = datetime.utcnow()

            write_audit_log(
                db,
                organization_id=organization.id,
                actor_user_id=actor.id,
                action="payment.status_reconciled_paid",
                entity_type="payment_transaction",
                entity_id=transaction.id,
                message=f"Status NETOPIA reconciliat ca paid. Plan activat: {transaction.plan_code}.",
            )
    elif normalized_status in {"failed", "cancelled"}:
        transaction.status = normalized_status
        write_audit_log(
            db,
            organization_id=organization.id,
            actor_user_id=actor.id,
            action=f"payment.status_reconciled_{normalized_status}",
            entity_type="payment_transaction",
            entity_id=transaction.id,
            message=f"Status NETOPIA reconciliat: {normalized_status}.",
        )
    else:
        transaction.status = "pending"
        write_audit_log(
            db,
            organization_id=organization.id,
            actor_user_id=actor.id,
            action="payment.status_reconciled_pending",
            entity_type="payment_transaction",
            entity_id=transaction.id,
            message="Status NETOPIA reconciliat: pending.",
        )

    db.flush()

    return {
        "transaction_id": transaction.id,
        "organization_id": organization.id,
        "provider": transaction.provider,
        "provider_order_id": transaction.provider_order_id,
        "provider_payment_id": transaction.provider_payment_id,
        "previous_status": previous_status,
        "current_status": transaction.status,
        "provider_status": transaction.provider_status,
        "changed": previous_status != transaction.status,
        "message": f"Status NETOPIA verificat: {transaction.status}.",
        "raw_response": response_payload,
    }
