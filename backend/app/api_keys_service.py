from datetime import datetime
import hashlib
import secrets
from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import ApiKey, Organization, User

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def create_api_key(
    db: Session,
    organization: Organization,
    actor: User,
    name: str,
    scopes: str = "invoices:write",
) -> tuple[ApiKey, str]:
    raw_key = f"fg_{secrets.token_urlsafe(32)}"
    key_prefix = raw_key[:12]

    api_key = ApiKey(
        organization_id=organization.id,
        created_by_user_id=actor.id,
        name=name.strip() or "API key",
        key_prefix=key_prefix,
        key_hash=hash_api_key(raw_key),
        scopes=scopes,
        status="active",
    )
    db.add(api_key)
    db.flush()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="api_key.created",
        entity_type="api_key",
        entity_id=api_key.id,
        message=f"API key creat: {api_key.name}.",
    )

    return api_key, raw_key

def list_api_keys(db: Session, organization: Organization) -> list[ApiKey]:
    return (
        db.query(ApiKey)
        .filter(ApiKey.organization_id == organization.id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )

def revoke_api_key(db: Session, organization: Organization, actor: User, api_key_id: int) -> ApiKey:
    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.id == api_key_id, ApiKey.organization_id == organization.id)
        .first()
    )
    if not api_key:
        raise ValueError("API key nu există.")

    api_key.status = "revoked"
    db.flush()

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action="api_key.revoked",
        entity_type="api_key",
        entity_id=api_key.id,
        message=f"API key revocat: {api_key.name}.",
    )

    return api_key

def authenticate_api_key(db: Session, raw_key: str, required_scope: str) -> ApiKey:
    if not raw_key:
        raise PermissionError("API key lipsă.")

    key_prefix = raw_key[:12]
    key_hash = hash_api_key(raw_key)

    api_key = (
        db.query(ApiKey)
        .filter(ApiKey.key_prefix == key_prefix, ApiKey.key_hash == key_hash)
        .first()
    )

    if not api_key or api_key.status != "active":
        raise PermissionError("API key invalid sau revocat.")

    scopes = {scope.strip() for scope in api_key.scopes.split(",") if scope.strip()}
    if required_scope not in scopes and "*" not in scopes:
        raise PermissionError("API key nu are scope-ul necesar.")

    api_key.last_used_at = datetime.utcnow()
    db.flush()
    return api_key
