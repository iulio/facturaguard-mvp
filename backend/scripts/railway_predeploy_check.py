"""Railway pre-deploy sanity checks.

This script intentionally avoids filesystem writes because Railway pre-deploy
commands run in a separate container and volumes are not mounted there.
"""
from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, text

def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)

def warn(message: str) -> None:
    print(f"[WARN] {message}")

def ok(message: str) -> None:
    print(f"[OK] {message}")

def main() -> None:
    environment = os.getenv("ENVIRONMENT", "development")
    database_url = os.getenv("DATABASE_URL")
    secret_key = os.getenv("SECRET_KEY")
    auto_create_tables = os.getenv("AUTO_CREATE_TABLES", "false").lower()
    storage_backend = os.getenv("FILE_STORAGE_BACKEND", "local").lower()
    storage_path = os.getenv("FILE_STORAGE_PATH", "/app/storage")
    anaf_mode = os.getenv("ANAF_CONNECTOR_MODE", "mock").lower()
    netopia_provider = os.getenv("NETOPIA_PROVIDER", "mock").lower()
    netopia_signature_mode = os.getenv("NETOPIA_IPN_SIGNATURE_MODE", "shared_secret").lower()
    netopia_require_signature = os.getenv("NETOPIA_IPN_REQUIRE_SIGNATURE", "false").lower() == "true"

    if not database_url:
        fail("DATABASE_URL is missing. Attach Railway PostgreSQL and reference ${{Postgres.DATABASE_URL}}.")

    if not secret_key or len(secret_key) < 32:
        fail("SECRET_KEY is missing or too short. Use a long random value.")

    if environment == "production" and auto_create_tables == "true":
        fail("AUTO_CREATE_TABLES must be false in production. Use Alembic migrations instead.")

    try:
        engine = create_engine(database_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        ok("Database connectivity works.")
    except Exception as exc:
        fail(f"Database connectivity failed: {exc}")

    if storage_backend == "local":
        if storage_path != "/app/storage":
            warn(f"FILE_STORAGE_PATH is {storage_path}. For Railway volume, recommended path is /app/storage.")
        warn("FILE_STORAGE_BACKEND=local requires a Railway Volume mounted at /app/storage.")
    elif storage_backend == "s3":
        missing_s3 = [
            key for key in [
                "S3_ENDPOINT_URL",
                "S3_BUCKET_NAME",
                "S3_ACCESS_KEY_ID",
                "S3_SECRET_ACCESS_KEY",
            ]
            if not os.getenv(key)
        ]
        if missing_s3:
            fail(f"FILE_STORAGE_BACKEND=s3 but missing variables: {', '.join(missing_s3)}.")
        ok("S3 storage variables are present.")
    else:
        fail(f"Unknown FILE_STORAGE_BACKEND={storage_backend}.")

    if netopia_provider == "v2":
        missing_netopia = [
            key for key in [
                "NETOPIA_API_KEY",
                "NETOPIA_POS_SIGNATURE",
                "NETOPIA_NOTIFY_URL",
                "NETOPIA_REDIRECT_URL",
            ]
            if not os.getenv(key)
        ]
        if missing_netopia:
            fail(f"NETOPIA_PROVIDER=v2 but missing variables: {', '.join(missing_netopia)}.")

        if netopia_signature_mode not in {"none", "shared_secret", "hmac_sha256", "hmac_sha512"}:
            fail(f"Invalid NETOPIA_IPN_SIGNATURE_MODE={netopia_signature_mode}.")

        if netopia_require_signature and not os.getenv("NETOPIA_IPN_SHARED_SECRET"):
            fail("NETOPIA_IPN_REQUIRE_SIGNATURE=true but NETOPIA_IPN_SHARED_SECRET is missing.")

    if anaf_mode == "real":
        missing_anaf = [
            key for key in [
                "ANAF_CLIENT_ID",
                "ANAF_CLIENT_SECRET",
                "ANAF_REDIRECT_URI",
                "FRONTEND_BASE_URL",
            ]
            if not os.getenv(key)
        ]
        if missing_anaf:
            fail(f"ANAF_CONNECTOR_MODE=real but missing variables: {', '.join(missing_anaf)}.")

        token_key = os.getenv("TOKEN_ENCRYPTION_KEY")
        if not token_key:
            warn("TOKEN_ENCRYPTION_KEY is missing. App will fall back to SECRET_KEY-derived encryption.")
        else:
            try:
                from cryptography.fernet import Fernet
                Fernet(token_key.encode("utf-8"))
                ok("TOKEN_ENCRYPTION_KEY is a valid Fernet key.")
            except Exception as exc:
                fail(f"TOKEN_ENCRYPTION_KEY is not a valid Fernet key: {exc}")

    cors = os.getenv("CORS_ORIGINS", "")
    trusted_hosts = os.getenv("TRUSTED_HOSTS", "*")
    if environment == "production" and ("localhost" in cors or not cors):
        warn("CORS_ORIGINS still contains localhost or is empty. Update after Railway frontend domain is generated.")

    if environment == "production" and trusted_hosts.strip() == "*":
        warn("TRUSTED_HOSTS is '*'. For production, set your Railway/custom backend domain.")

    ok("Railway pre-deploy sanity checks completed.")

if __name__ == "__main__":
    main()
