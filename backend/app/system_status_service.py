from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import Alert, Invoice, Organization, OrganizationDocument
from .settings import get_settings

def build_system_status(db: Session) -> dict:
    settings = get_settings()

    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "error"

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "database": database,
        "scheduler_enabled": settings.fg_enable_scheduler,
        "email_dry_run": settings.fg_email_dry_run,
        "storage_backend": settings.file_storage_backend,
        "anaf_connector_mode": settings.anaf_connector_mode,
        "netopia_mock_enabled": settings.netopia_mock_enabled,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "total_organizations": db.query(Organization).count(),
        "total_invoices": db.query(Invoice).count(),
        "total_documents": db.query(OrganizationDocument).count(),
        "total_open_alerts": db.query(Alert).filter(Alert.status == "open").count(),
    }
