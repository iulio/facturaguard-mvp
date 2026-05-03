import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session

from .models import AuditLog

def filter_audit_logs(
    db: Session,
    organization_id: int,
    action: str | None = None,
    entity_type: str | None = None,
    actor_user_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 200,
) -> list[AuditLog]:
    query = db.query(AuditLog).filter(AuditLog.organization_id == organization_id)

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    if actor_user_id:
        query = query.filter(AuditLog.actor_user_id == actor_user_id)

    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)

    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    limit = min(max(limit, 1), 1000)

    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

def audit_logs_to_csv(logs: list[AuditLog]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id",
        "organization_id",
        "actor_user_id",
        "action",
        "entity_type",
        "entity_id",
        "message",
        "created_at",
    ])

    for log in logs:
        writer.writerow([
            log.id,
            log.organization_id,
            log.actor_user_id or "",
            log.action,
            log.entity_type or "",
            log.entity_id or "",
            log.message,
            log.created_at.isoformat(),
        ])

    return output.getvalue()
