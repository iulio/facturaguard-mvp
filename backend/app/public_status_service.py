from __future__ import annotations

from datetime import datetime
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .settings import get_settings

def build_public_status(engine: Engine) -> dict:
    settings = get_settings()

    database_status = "unknown"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        database_status = "degraded"

    # Do not expose secrets, internal URLs, provider keys or organization data.
    providers = {
        "anaf": "mock" if settings.anaf_connector_mode == "mock" else "configured",
        "netopia": "mock" if settings.netopia_provider == "mock" else "configured",
        "email": "dry_run" if settings.fg_email_dry_run else "configured",
        "storage": settings.file_storage_backend,
    }

    overall_status = "operational" if database_status == "ok" else "degraded"

    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": overall_status,
        "database": database_status,
        "providers": providers,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    }
