"""Application configuration settings."""

from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="DB_")

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="procurement_copilot", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="postgres", description="Database password")
    echo: bool = Field(default=False, description="Enable SQLAlchemy echo")

    @property
    def url(self) -> str:
        """Get database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")

    @property
    def url(self) -> str:
        """Get Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class ScrapingSettings(BaseSettings):
    """Scraping configuration settings."""

    model_config = SettingsConfigDict(env_prefix="SCRAPING_")

    ted_api_url: str = Field(
        default="https://data.europa.eu/api/hub/search/datasets/",
        description="TED API base URL",
    )
    ted_dataset_id: str = Field(default="ted-csv", description="TED dataset ID")
    boamp_base_url: str = Field(
        default="https://www.boamp.fr", description="BOAMP base URL"
    )
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(
        default=1.0, description="Initial retry delay in seconds"
    )
    rate_limit_delay: float = Field(
        default=0.5, description="Delay between requests in seconds"
    )
    user_agent: str = Field(
        default="ProcurementCopilot/1.0 (https://procurement-copilot.com)",
        description="User agent for requests",
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env file
        populate_by_name=True,  # Allow both field names and aliases
    )

    # Connector configuration
    ENABLE_CONNECTORS: str = Field(
        default="TED", description="Comma-separated list of enabled connectors"
    )
    SHADOW_CONNECTORS: str = Field(
        default="", description="Comma-separated list of shadow connectors"
    )
    TZ: str = Field(default="Europe/Paris", description="Application timezone")

    # Application
    app_name: str = Field(default="TenderPulse", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT, description="Environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    timezone: str = Field(default="Europe/Paris", description="Application timezone")

    # API
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "https://*.vercel.app",
        ],
        description="CORS origins",
    )

    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens",
    )
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )

    # Scheduler
    scheduler_timezone: str = Field(
        default="Europe/Paris", description="Scheduler timezone"
    )
    ingest_interval_hours: int = Field(
        default=6, description="Ingest interval in hours"
    )

    # Database
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    # Redis
    redis: RedisSettings = Field(default_factory=RedisSettings)

    # Scraping
    scraping: ScrapingSettings = Field(default_factory=ScrapingSettings)

    # Email
    resend_api_key: Optional[str] = Field(
        default=None, description="Resend API key for sending emails"
    )
    sendgrid_api_key: Optional[str] = Field(
        default=None, description="SendGrid API key for sending emails"
    )

    # OpenAI
    openai_api_key: Optional[str] = Field(
        default=None, description="OpenAI API key for content generation"
    )

    # Stripe
    stripe_secret_key: Optional[str] = Field(
        default=None,
        description="Stripe secret key for payments",
        alias="STRIPE_SECRET_KEY",
    )
    stripe_webhook_secret: Optional[str] = Field(
        default=None,
        description="Stripe webhook secret for webhook verification",
        alias="STRIPE_WEBHOOK_SECRET",
    )

    # Frontend
    frontend_url: Optional[str] = Field(
        default="http://localhost:3000", description="Frontend URL for redirects"
    )

    # Outbound Pipeline
    outbound_enabled: bool = Field(
        default=True, description="Enable outbound pipeline"
    )
    outbound_schedule_cron: str = Field(
        default="30 8 * * *", description="Cron schedule for outbound pipeline (08:30 Europe/Paris)"
    )
    outbound_max_leads_per_day: int = Field(
        default=150, description="Maximum number of leads to process per day"
    )
    outbound_max_emails_per_day: int = Field(
        default=100, description="Maximum number of emails to send per day"
    )
    outbound_min_score: float = Field(
        default=0.55, description="Minimum fit score threshold for prospects"
    )
    outbound_sectors: Optional[str] = Field(
        default=None, description="Comma-separated list of sectors to focus on"
    )

    # Email Configuration
    email_from: str = Field(
        default="alerts@mail.tenderpulse.eu", description="From email address"
    )
    email_from_name: str = Field(
        default="TenderPulse", description="From name for emails"
    )
    list_unsub_base_url: str = Field(
        default="https://tenderpulse.eu/unsub", description="Base URL for unsubscribe links"
    )

    # Hunter.io Configuration
    hunter_api_key: Optional[str] = Field(
        default=None, description="Hunter.io API key"
    )
    hunter_daily_cap: int = Field(
        default=250, description="Daily API call limit for Hunter.io"
    )
    sender_domain: str = Field(
        default="mail.tenderpulse.eu", description="Sender domain for tracking"
    )

    # Apollo.io Configuration
    apollo_api_key: Optional[str] = Field(
        default=None, description="Apollo.io API key"
    )
    apollo_daily_cap: int = Field(
        default=50, description="Daily API call limit for Apollo.io"
    )


# Global settings instance
settings = Settings()
