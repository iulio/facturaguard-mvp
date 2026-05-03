from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "FacturaGuard MVP API"
    app_version: str = "2.0.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")

    database_url: str = Field(default="sqlite:///./facturaguard.db", alias="DATABASE_URL")
    auto_create_tables: bool = Field(default=True, alias="AUTO_CREATE_TABLES")

    secret_key: str = Field(default="change-this-secret-in-production", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )

    fg_enable_scheduler: bool = Field(default=True, alias="FG_ENABLE_SCHEDULER")
    fg_status_check_interval_minutes: int = Field(default=60, alias="FG_STATUS_CHECK_INTERVAL_MINUTES")

    fg_email_dry_run: bool = Field(default=True, alias="FG_EMAIL_DRY_RUN")
    fg_smtp_host: str | None = Field(default=None, alias="FG_SMTP_HOST")
    fg_smtp_port: int = Field(default=587, alias="FG_SMTP_PORT")
    fg_smtp_username: str | None = Field(default=None, alias="FG_SMTP_USERNAME")
    fg_smtp_password: str | None = Field(default=None, alias="FG_SMTP_PASSWORD")
    fg_email_from: str = Field(default="alerts@facturaguard.local", alias="FG_EMAIL_FROM")

    anaf_connector_mode: str = Field(default="mock", alias="ANAF_CONNECTOR_MODE")

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
