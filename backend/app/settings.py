from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "FacturaGuard MVP API"
    app_version: str = "3.21.2"
    environment: str = Field(default="development", alias="ENVIRONMENT")

    database_url: str = Field(default="sqlite:///./facturaguard.db", alias="DATABASE_URL")
    auto_create_tables: bool = Field(default=True, alias="AUTO_CREATE_TABLES")

    secret_key: str = Field(default="change-this-secret-in-production", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    bcrypt_rounds: int = Field(default=12, alias="BCRYPT_ROUNDS")

    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )
    trusted_hosts: str = Field(default="*", alias="TRUSTED_HOSTS")
    security_headers_enabled: bool = Field(default=True, alias="SECURITY_HEADERS_ENABLED")

    fg_enable_scheduler: bool = Field(default=True, alias="FG_ENABLE_SCHEDULER")
    fg_status_check_interval_minutes: int = Field(default=60, alias="FG_STATUS_CHECK_INTERVAL_MINUTES")

    fg_email_dry_run: bool = Field(default=True, alias="FG_EMAIL_DRY_RUN")
    fg_smtp_host: str | None = Field(default=None, alias="FG_SMTP_HOST")
    fg_smtp_port: int = Field(default=587, alias="FG_SMTP_PORT")
    fg_smtp_username: str | None = Field(default=None, alias="FG_SMTP_USERNAME")
    fg_smtp_password: str | None = Field(default=None, alias="FG_SMTP_PASSWORD")
    fg_email_from: str = Field(default="alerts@facturaguard.local", alias="FG_EMAIL_FROM")

    anaf_connector_mode: str = Field(default="mock", alias="ANAF_CONNECTOR_MODE")
    anaf_env: str = Field(default="test", alias="ANAF_ENV")
    anaf_client_id: str | None = Field(default=None, alias="ANAF_CLIENT_ID")
    anaf_client_secret: str | None = Field(default=None, alias="ANAF_CLIENT_SECRET")
    anaf_redirect_uri: str | None = Field(default=None, alias="ANAF_REDIRECT_URI")
    anaf_auth_base: str = Field(default="https://logincert.anaf.ro/anaf-oauth2/v1", alias="ANAF_AUTH_BASE")
    anaf_api_test_base: str = Field(default="https://webserviceapl.anaf.ro/test/FCTEL/rest", alias="ANAF_API_TEST_BASE")
    anaf_api_prod_base: str = Field(default="https://webserviceapl.anaf.ro/prod/FCTEL/rest", alias="ANAF_API_PROD_BASE")
    anaf_token_content_type: str = Field(default="jwt", alias="ANAF_TOKEN_CONTENT_TYPE")
    anaf_scope: str = Field(default="", alias="ANAF_SCOPE")
    frontend_base_url: str = Field(default="http://localhost:3000", alias="FRONTEND_BASE_URL")
    token_encryption_key: str | None = Field(default=None, alias="TOKEN_ENCRYPTION_KEY")

    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")

    file_storage_backend: str = Field(default="local", alias="FILE_STORAGE_BACKEND")
    file_storage_path: str = Field(default="./storage", alias="FILE_STORAGE_PATH")

    s3_endpoint_url: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_region_name: str = Field(default="eu-central-1", alias="S3_REGION_NAME")
    s3_bucket_name: str | None = Field(default=None, alias="S3_BUCKET_NAME")
    s3_access_key_id: str | None = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: str | None = Field(default=None, alias="S3_SECRET_ACCESS_KEY")

    netopia_mock_enabled: bool = Field(default=True, alias="NETOPIA_MOCK_ENABLED")
    netopia_mock_return_url: str = Field(default="http://localhost:3000/billing/return", alias="NETOPIA_MOCK_RETURN_URL")
    netopia_mock_webhook_secret: str = Field(default="dev-netopia-webhook-secret", alias="NETOPIA_MOCK_WEBHOOK_SECRET")

    # NETOPIA Payments API v2
    # Use "mock" for development and "v2" for real NETOPIA API.
    netopia_provider: str = Field(default="mock", alias="NETOPIA_PROVIDER")
    netopia_is_live: bool = Field(default=False, alias="NETOPIA_IS_LIVE")
    netopia_api_key: str | None = Field(default=None, alias="NETOPIA_API_KEY")
    netopia_pos_signature: str | None = Field(default=None, alias="NETOPIA_POS_SIGNATURE")
    netopia_pos_signature_set: str = Field(default="", alias="NETOPIA_POS_SIGNATURE_SET")
    netopia_public_key: str | None = Field(default=None, alias="NETOPIA_PUBLIC_KEY")
    netopia_active_key: str | None = Field(default=None, alias="NETOPIA_ACTIVE_KEY")
    netopia_hash_method: str = Field(default="sha512", alias="NETOPIA_HASH_METHOD")
    netopia_sandbox_base_url: str = Field(default="https://secure.sandbox.netopia-payments.com", alias="NETOPIA_SANDBOX_BASE_URL")
    netopia_live_base_url: str = Field(default="https://secure.mobilpay.ro/pay", alias="NETOPIA_LIVE_BASE_URL")
    netopia_notify_url: str | None = Field(default=None, alias="NETOPIA_NOTIFY_URL")
    netopia_redirect_url: str | None = Field(default=None, alias="NETOPIA_REDIRECT_URL")
    netopia_cancel_url: str | None = Field(default=None, alias="NETOPIA_CANCEL_URL")
    netopia_currency: str = Field(default="EUR", alias="NETOPIA_CURRENCY")
    netopia_language: str = Field(default="ro", alias="NETOPIA_LANGUAGE")
    netopia_ipn_shared_secret: str | None = Field(default=None, alias="NETOPIA_IPN_SHARED_SECRET")
    # IPN verification modes:
    # - none: no signature verification
    # - shared_secret: compare X-NETOPIA-Secret to NETOPIA_IPN_SHARED_SECRET
    # - hmac_sha256: compare X-NETOPIA-Signature to HMAC-SHA256(raw_body, NETOPIA_IPN_SHARED_SECRET)
    # - hmac_sha512: compare X-NETOPIA-Signature to HMAC-SHA512(raw_body, NETOPIA_IPN_SHARED_SECRET)
    netopia_ipn_signature_mode: str = Field(default="shared_secret", alias="NETOPIA_IPN_SIGNATURE_MODE")
    netopia_ipn_require_signature: bool = Field(default=False, alias="NETOPIA_IPN_REQUIRE_SIGNATURE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
