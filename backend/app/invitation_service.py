from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session

from .access import write_audit_log
from .models import Organization, OrganizationInvitation, OrganizationMember, User
from .notifier import send_email_notification

ALLOWED_INVITE_ROLES = {"client_viewer", "client_operator", "accountant_owner"}

def create_invitation(
    db: Session,
    organization: Organization,
    invited_email: str,
    role: str,
    invited_by: User,
) -> OrganizationInvitation:
    if role not in ALLOWED_INVITE_ROLES:
        raise ValueError(f"Rol invalid. Alege unul din: {', '.join(sorted(ALLOWED_INVITE_ROLES))}")

    existing = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.organization_id == organization.id,
            OrganizationInvitation.invited_email == invited_email,
            OrganizationInvitation.status == "pending",
        )
        .first()
    )

    if existing:
        existing.role = role
        existing.expires_at = datetime.utcnow() + timedelta(days=7)
        invitation = existing
    else:
        invitation = OrganizationInvitation(
            organization_id=organization.id,
            invited_email=invited_email,
            role=role,
            token=secrets.token_urlsafe(32),
            status="pending",
            invited_by_user_id=invited_by.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(invitation)
        db.flush()

    accept_url = f"http://localhost:3000/accept-invite?token={invitation.token}"
    send_email_notification(
        invited_email,
        f"Invitație FacturaGuard - {organization.name}",
        (
            f"Ai fost invitat în FacturaGuard pentru firma {organization.name}.\n\n"
            f"Rol: {role}\n"
            f"Acceptă invitația: {accept_url}\n\n"
            "În acest MVP, emailul este trimis în modul dry-run dacă SMTP nu este configurat."
        ),
    )

    write_audit_log(
        db,
        organization_id=organization.id,
        actor_user_id=invited_by.id,
        action="invitation.created",
        entity_type="organization_invitation",
        entity_id=invitation.id,
        message=f"Invitație trimisă către {invited_email} cu rolul {role}.",
    )

    return invitation

def accept_invitation(db: Session, token: str, user: User) -> tuple[OrganizationInvitation, OrganizationMember]:
    invitation = (
        db.query(OrganizationInvitation)
        .filter(OrganizationInvitation.token == token)
        .first()
    )

    if not invitation:
        raise ValueError("Invitația nu există.")

    if invitation.status != "pending":
        raise ValueError("Invitația nu mai este activă.")

    if invitation.expires_at < datetime.utcnow():
        invitation.status = "expired"
        db.flush()
        raise ValueError("Invitația a expirat.")

    if invitation.invited_email.lower() != user.email.lower():
        raise PermissionError("Invitația este pentru alt email.")

    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == invitation.organization_id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )

    if member:
        member.role = invitation.role
        member.status = "active"
    else:
        member = OrganizationMember(
            organization_id=invitation.organization_id,
            user_id=user.id,
            role=invitation.role,
            status="active",
        )
        db.add(member)
        db.flush()

    invitation.status = "accepted"
    invitation.accepted_by_user_id = user.id
    invitation.accepted_at = datetime.utcnow()

    write_audit_log(
        db,
        organization_id=invitation.organization_id,
        actor_user_id=user.id,
        action="invitation.accepted",
        entity_type="organization_invitation",
        entity_id=invitation.id,
        message=f"Invitația pentru {user.email} a fost acceptată.",
    )

    return invitation, member
