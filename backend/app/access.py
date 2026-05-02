from fastapi import HTTPException
from sqlalchemy.orm import Session
from .models import AuditLog, Organization, OrganizationMember, User

OWNER_ROLES = {"accountant_owner"}
WRITE_ROLES = {"accountant_owner", "client_operator"}
READ_ROLES = {"accountant_owner", "client_operator", "client_viewer"}

def get_user_membership(db: Session, organization_id: int, user_id: int) -> OrganizationMember | None:
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.status == "active",
        )
        .first()
    )

def get_accessible_organization(
    db: Session,
    organization_id: int,
    current_user: User,
    require_write: bool = False,
    require_owner: bool = False,
) -> Organization:
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Firma nu a fost găsită.")

    membership = get_user_membership(db, organization_id, current_user.id)

    if not membership and organization.owner_user_id == current_user.id:
        membership = OrganizationMember(
            organization_id=organization_id,
            user_id=current_user.id,
            role="accountant_owner",
            status="active",
        )
        db.add(membership)
        db.flush()

    if not membership:
        raise HTTPException(status_code=404, detail="Firma nu a fost găsită.")

    if require_owner and membership.role not in OWNER_ROLES:
        raise HTTPException(status_code=403, detail="Ai nevoie de rol de owner pentru această acțiune.")

    if require_write and membership.role not in WRITE_ROLES:
        raise HTTPException(status_code=403, detail="Ai nevoie de drept de scriere pentru această acțiune.")

    if membership.role not in READ_ROLES:
        raise HTTPException(status_code=403, detail="Nu ai acces la această firmă.")

    return organization

def write_audit_log(
    db: Session,
    organization_id: int,
    actor_user_id: int | None,
    action: str,
    message: str,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
) -> AuditLog:
    log = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        message=message,
    )
    db.add(log)
    db.flush()
    return log
