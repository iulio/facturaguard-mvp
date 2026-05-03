from base64 import urlsafe_b64encode
from datetime import datetime, timedelta
import hashlib
from urllib.parse import urlencode

from cryptography.fernet import Fernet
import httpx
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import AnafAuthorization, Organization, OrganizationIntegration, User
from .settings import get_settings

STATE_ALGORITHM = "HS256"

def get_anaf_api_base() -> str:
    settings = get_settings()
    return settings.anaf_api_prod_base if settings.anaf_env == "prod" else settings.anaf_api_test_base

def get_anaf_config_status() -> dict:
    settings = get_settings()
    required = {
        "ANAF_CLIENT_ID": settings.anaf_client_id,
        "ANAF_CLIENT_SECRET": settings.anaf_client_secret,
        "ANAF_REDIRECT_URI": settings.anaf_redirect_uri,
    }
    missing = [key for key, value in required.items() if not value]

    return {
        "mode": settings.anaf_connector_mode,
        "environment": settings.anaf_env,
        "auth_base": settings.anaf_auth_base,
        "api_base": get_anaf_api_base(),
        "redirect_uri": settings.anaf_redirect_uri,
        "configured": len(missing) == 0,
        "missing_variables": missing,
    }

def get_token_fernet() -> Fernet:
    settings = get_settings()

    if settings.token_encryption_key:
        return Fernet(settings.token_encryption_key.encode("utf-8"))

    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(urlsafe_b64encode(digest))

def encrypt_value(value: str | None) -> str | None:
    if value is None:
        return None
    return get_token_fernet().encrypt(value.encode("utf-8")).decode("utf-8")

def decrypt_value(value: str | None) -> str | None:
    if value is None:
        return None
    return get_token_fernet().decrypt(value.encode("utf-8")).decode("utf-8")

def create_signed_state(organization: Organization, actor: User) -> str:
    settings = get_settings()
    payload = {
        "org_id": organization.id,
        "user_id": actor.id,
        "cui": organization.cui,
        "iat": int(datetime.utcnow().timestamp()),
        "exp": int((datetime.utcnow() + timedelta(minutes=15)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=STATE_ALGORITHM)

def verify_signed_state(state: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(state, settings.secret_key, algorithms=[STATE_ALGORITHM])
    except JWTError as exc:
        raise ValueError("State OAuth invalid sau expirat.") from exc

def build_anaf_authorization_url(db: Session, organization: Organization, actor: User) -> dict:
    settings = get_settings()
    config = get_anaf_config_status()

    if not config["configured"]:
        raise RuntimeError(f"Lipsesc variabile ANAF: {', '.join(config['missing_variables'])}")

    state = create_signed_state(organization, actor)

    params = {
        "response_type": "code",
        "client_id": settings.anaf_client_id,
        "redirect_uri": settings.anaf_redirect_uri,
        "token_content_type": settings.anaf_token_content_type,
        "state": state,
    }

    if settings.anaf_scope:
        params["scope"] = settings.anaf_scope

    integration = get_or_create_real_anaf_integration(db, organization)
    integration.status = "pending_oauth"
    integration.last_checked_at = datetime.utcnow()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="anaf.oauth_started",
        entity_type="organization_integration",
        entity_id=integration.id,
        message="Flux OAuth ANAF pornit.",
    )

    db.flush()

    return {
        "authorization_url": f"{settings.anaf_auth_base}/authorize?{urlencode(params)}",
        "state": state,
        "mode": "real",
    }

def exchange_code_for_tokens(code: str) -> dict:
    settings = get_settings()
    config = get_anaf_config_status()

    if not config["configured"]:
        raise RuntimeError(f"Lipsesc variabile ANAF: {', '.join(config['missing_variables'])}")

    response = httpx.post(
        f"{settings.anaf_auth_base}/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.anaf_redirect_uri,
            "token_content_type": settings.anaf_token_content_type,
        },
        auth=(settings.anaf_client_id or "", settings.anaf_client_secret or ""),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

def refresh_anaf_tokens(db: Session, authorization: AnafAuthorization) -> AnafAuthorization:
    settings = get_settings()
    refresh_token = decrypt_value(authorization.refresh_token_encrypted)

    if not refresh_token:
        raise RuntimeError("Refresh token ANAF lipsă.")

    response = httpx.post(
        f"{settings.anaf_auth_base}/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "token_content_type": settings.anaf_token_content_type,
        },
        auth=(settings.anaf_client_id or "", settings.anaf_client_secret or ""),
        timeout=30,
    )
    response.raise_for_status()
    tokens = response.json()

    save_anaf_tokens(
        db,
        organization_id=authorization.organization_id,
        authorized_cif=authorization.authorized_cif,
        tokens=tokens,
        existing=authorization,
    )
    authorization.last_refresh_at = datetime.utcnow()
    db.flush()
    return authorization

def save_anaf_tokens(
    db: Session,
    organization_id: int,
    authorized_cif: str,
    tokens: dict,
    existing: AnafAuthorization | None = None,
) -> AnafAuthorization:
    now = datetime.utcnow()
    expires_in = int(tokens.get("expires_in") or 3600)
    expires_at = now + timedelta(seconds=expires_in)

    authorization = existing or (
        db.query(AnafAuthorization)
        .filter(AnafAuthorization.organization_id == organization_id)
        .first()
    )

    if not authorization:
        authorization = AnafAuthorization(
            organization_id=organization_id,
            authorized_cif=authorized_cif,
            access_token_encrypted=encrypt_value(tokens["access_token"]),
            refresh_token_encrypted=encrypt_value(tokens.get("refresh_token")),
            token_type=tokens.get("token_type", "Bearer"),
            expires_at=expires_at,
            scope=tokens.get("scope"),
            status="active",
        )
        db.add(authorization)
    else:
        authorization.authorized_cif = authorized_cif
        authorization.access_token_encrypted = encrypt_value(tokens["access_token"])
        if tokens.get("refresh_token"):
            authorization.refresh_token_encrypted = encrypt_value(tokens.get("refresh_token"))
        authorization.token_type = tokens.get("token_type", "Bearer")
        authorization.expires_at = expires_at
        authorization.scope = tokens.get("scope")
        authorization.status = "active"
        authorization.updated_at = now

    db.flush()
    return authorization

def handle_anaf_callback(db: Session, code: str, state: str) -> AnafAuthorization:
    payload = verify_signed_state(state)
    organization_id = int(payload["org_id"])
    authorized_cif = str(payload.get("cui") or "")

    tokens = exchange_code_for_tokens(code)

    authorization = save_anaf_tokens(
        db,
        organization_id=organization_id,
        authorized_cif=authorized_cif,
        tokens=tokens,
    )

    integration = (
        db.query(OrganizationIntegration)
        .filter(
            OrganizationIntegration.organization_id == organization_id,
            OrganizationIntegration.provider == "anaf",
        )
        .first()
    )

    if integration:
        integration.mode = "real"
        integration.status = "connected"
        integration.config_json = '{"connector": "real", "oauth": "connected"}'
        integration.last_checked_at = datetime.utcnow()

    write_audit_log(
        db,
        organization_id=organization_id,
        actor_user_id=int(payload.get("user_id")) if payload.get("user_id") else None,
        action="anaf.oauth_connected",
        entity_type="anaf_authorization",
        entity_id=authorization.id,
        message="Conectare OAuth ANAF finalizată.",
    )

    db.flush()
    return authorization

def get_or_create_real_anaf_integration(db: Session, organization: Organization) -> OrganizationIntegration:
    integration = (
        db.query(OrganizationIntegration)
        .filter(
            OrganizationIntegration.organization_id == organization.id,
            OrganizationIntegration.provider == "anaf",
        )
        .first()
    )
    if integration:
        integration.mode = "real"
        return integration

    integration = OrganizationIntegration(
        organization_id=organization.id,
        provider="anaf",
        mode="real",
        status="not_configured",
        config_json='{"connector": "real", "oauth": "not_connected"}',
    )
    db.add(integration)
    db.flush()
    return integration

def get_valid_access_token(db: Session, organization_id: int) -> str:
    authorization = (
        db.query(AnafAuthorization)
        .filter(AnafAuthorization.organization_id == organization_id, AnafAuthorization.status == "active")
        .first()
    )
    if not authorization:
        raise RuntimeError("Organizația nu este conectată la ANAF.")

    if authorization.expires_at and authorization.expires_at <= datetime.utcnow() + timedelta(minutes=5):
        authorization = refresh_anaf_tokens(db, authorization)

    token = decrypt_value(authorization.access_token_encrypted)
    if not token:
        raise RuntimeError("Access token ANAF invalid.")
    return token

def list_anaf_authorizations(db: Session, organization: Organization) -> list[AnafAuthorization]:
    return (
        db.query(AnafAuthorization)
        .filter(AnafAuthorization.organization_id == organization.id)
        .order_by(AnafAuthorization.created_at.desc())
        .all()
    )

def disconnect_anaf(db: Session, organization: Organization, actor: User) -> list[AnafAuthorization]:
    authorizations = list_anaf_authorizations(db, organization)

    for authorization in authorizations:
        authorization.status = "revoked"
        authorization.updated_at = datetime.utcnow()

    integration = get_or_create_real_anaf_integration(db, organization)
    integration.status = "disconnected"
    integration.last_checked_at = datetime.utcnow()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="anaf.oauth_disconnected",
        entity_type="organization_integration",
        entity_id=integration.id,
        message="Conectarea ANAF a fost dezactivată în FacturaGuard.",
    )

    db.flush()
    return authorizations
