from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "FacturaGuard MVP API"
    app_version: str = "1.0.0"
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
