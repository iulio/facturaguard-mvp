from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .settings import get_settings

def check_item(
    key: str,
    label: str,
    status: str,
    message: str,
    severity: str = "info",
    metadata: dict | None = None,
) -> dict:
    return {
        "key": key,
        "label": label,
        "status": status,
        "message": message,
        "severity": severity,
        "metadata": metadata or {},
    }

def build_deployment_readiness(engine: Engine) -> dict:
    settings = get_settings()
    checks: list[dict] = []

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks.append(check_item("database", "Database connectivity", "pass", "Database connection works.", "critical"))
    except Exception as exc:
        checks.append(check_item("database", "Database connectivity", "fail", f"Database connection failed: {exc}", "critical"))

    if settings.environment == "production" and settings.auto_create_tables:
        checks.append(check_item(
            "auto_create_tables",
            "AUTO_CREATE_TABLES",
            "fail",
            "AUTO_CREATE_TABLES must be false in production. Use Alembic migrations.",
            "critical",
        ))
    else:
        checks.append(check_item(
            "auto_create_tables",
            "AUTO_CREATE_TABLES",
            "pass",
            f"AUTO_CREATE_TABLES={settings.auto_create_tables}.",
            "critical",
        ))

    if len(settings.secret_key or "") >= 32:
        checks.append(check_item("secret_key", "SECRET_KEY", "pass", "SECRET_KEY length looks acceptable.", "critical"))
    else:
        checks.append(check_item("secret_key", "SECRET_KEY", "fail", "SECRET_KEY is missing or too short.", "critical"))

    cors_origins = settings.cors_origin_list
    if settings.environment == "production" and any("localhost" in origin for origin in cors_origins):
        checks.append(check_item("cors", "CORS_ORIGINS", "warn", "CORS_ORIGINS still contains localhost.", "warning", {"origins": cors_origins}))
    elif cors_origins:
        checks.append(check_item("cors", "CORS_ORIGINS", "pass", "CORS origins configured.", "warning", {"origins": cors_origins}))
    else:
        checks.append(check_item("cors", "CORS_ORIGINS", "warn", "No CORS origins configured.", "warning"))

    trusted_hosts = [host.strip() for host in settings.trusted_hosts.split(",") if host.strip()]
    if settings.environment == "production" and trusted_hosts == ["*"]:
        checks.append(check_item("trusted_hosts", "TRUSTED_HOSTS", "warn", "TRUSTED_HOSTS is wildcard in production.", "warning"))
    else:
        checks.append(check_item("trusted_hosts", "TRUSTED_HOSTS", "pass", "Trusted hosts configured.", "warning", {"trusted_hosts": trusted_hosts}))

    if settings.security_headers_enabled:
        checks.append(check_item("security_headers", "Security headers", "pass", "Security headers are enabled.", "warning"))
    else:
        checks.append(check_item("security_headers", "Security headers", "warn", "Security headers are disabled.", "warning"))

    storage_backend = settings.file_storage_backend.lower()
    if storage_backend == "local":
        storage_path = Path(settings.file_storage_path)
        exists = storage_path.exists()
        checks.append(check_item(
            "storage",
            "File storage",
            "pass" if exists else "warn",
            f"Local storage path: {storage_path}. {'Exists.' if exists else 'Does not exist yet; Railway volume should mount it.'}",
            "warning",
            {"backend": "local", "path": str(storage_path)},
        ))
    elif storage_backend == "s3":
        missing_s3 = [
            key for key, value in {
                "S3_ENDPOINT_URL": settings.s3_endpoint_url,
                "S3_BUCKET_NAME": settings.s3_bucket_name,
                "S3_ACCESS_KEY_ID": settings.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": settings.s3_secret_access_key,
            }.items()
            if not value
        ]
        checks.append(check_item(
            "storage",
            "File storage",
            "fail" if missing_s3 else "pass",
            "Missing S3 variables: " + ", ".join(missing_s3) if missing_s3 else "S3 variables are configured.",
            "critical",
            {"backend": "s3", "missing": missing_s3},
        ))
    else:
        checks.append(check_item("storage", "File storage", "fail", f"Unknown FILE_STORAGE_BACKEND={storage_backend}.", "critical"))

    if settings.fg_email_dry_run:
        checks.append(check_item("email", "Email delivery", "warn", "FG_EMAIL_DRY_RUN=true. Emails are not sent.", "info"))
    else:
        checks.append(check_item("email", "Email delivery", "pass", "Email dry-run disabled. Verify SMTP/provider externally.", "info"))

    checks.append(check_item(
        "scheduler",
        "Scheduler",
        "pass" if settings.fg_enable_scheduler else "warn",
        f"FG_ENABLE_SCHEDULER={settings.fg_enable_scheduler}.",
        "info",
    ))

    if settings.netopia_provider == "mock":
        checks.append(check_item("netopia", "NETOPIA", "warn", "NETOPIA_PROVIDER=mock. Real payments are disabled.", "warning"))
    elif settings.netopia_provider == "v2":
        missing_netopia = [
            key for key, value in {
                "NETOPIA_API_KEY": settings.netopia_api_key,
                "NETOPIA_POS_SIGNATURE": settings.netopia_pos_signature,
                "NETOPIA_NOTIFY_URL": settings.netopia_notify_url,
                "NETOPIA_REDIRECT_URL": settings.netopia_redirect_url,
            }.items()
            if not value
        ]
        checks.append(check_item(
            "netopia",
            "NETOPIA",
            "fail" if missing_netopia else "pass",
            "Missing NETOPIA variables: " + ", ".join(missing_netopia) if missing_netopia else "NETOPIA v2 configuration looks complete.",
            "critical",
            {"missing": missing_netopia, "mode": "live" if settings.netopia_is_live else "sandbox"},
        ))
    else:
        checks.append(check_item("netopia", "NETOPIA", "fail", f"Invalid NETOPIA_PROVIDER={settings.netopia_provider}.", "critical"))

    if settings.anaf_connector_mode == "mock":
        checks.append(check_item("anaf", "ANAF/SPV", "warn", "ANAF_CONNECTOR_MODE=mock. Real SPV calls are disabled.", "warning"))
    elif settings.anaf_connector_mode == "real":
        missing_anaf = [
            key for key, value in {
                "ANAF_CLIENT_ID": settings.anaf_client_id,
                "ANAF_CLIENT_SECRET": settings.anaf_client_secret,
                "ANAF_REDIRECT_URI": settings.anaf_redirect_uri,
                "FRONTEND_BASE_URL": settings.frontend_base_url,
            }.items()
            if not value
        ]
        checks.append(check_item(
            "anaf",
            "ANAF/SPV",
            "fail" if missing_anaf else "pass",
            "Missing ANAF variables: " + ", ".join(missing_anaf) if missing_anaf else "ANAF real connector variables are configured.",
            "critical",
            {"missing": missing_anaf, "environment": settings.anaf_env},
        ))
    else:
        checks.append(check_item("anaf", "ANAF/SPV", "fail", f"Invalid ANAF_CONNECTOR_MODE={settings.anaf_connector_mode}.", "critical"))

    total = len(checks)
    failed = sum(1 for check in checks if check["status"] == "fail")
    warnings = sum(1 for check in checks if check["status"] == "warn")
    passed = sum(1 for check in checks if check["status"] == "pass")

    overall_status = "fail" if failed else "warn" if warnings else "pass"

    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "overall_status": overall_status,
        "summary": {
            "total": total,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
        },
        "checks": checks,
    }
