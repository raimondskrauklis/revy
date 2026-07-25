# backend/app/core/config.py
"""Application settings — fail-fast on missing required env (no URL defaults in code)."""
import json

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required — set in backend/.env (see .env.example)
    environment: str
    database_url: str
    test_database_url: str | None = None
    redis_url: str
    secret_key: str
    allowed_origins: str

    keycloak_url: str
    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: str
    # JWT `iss` when it differs from KEYCLOAK_URL (e.g. public auth host vs docker `keycloak:8080`)
    keycloak_issuer: str | None = None

    # One-time first deploy — remove from .env after super admin first login
    bootstrap_super_admin_email: str | None = None

    # Registration — USER_REGISTRATION.md (open SaaS default)
    registration_require_admin_approval: bool = False
    registration_require_profile_form: bool = False

    # Security — comma-separated hosts for TrustedHostMiddleware (production)
    trusted_hosts: str = "localhost,127.0.0.1"

    # Optional overrides (default to redis_url when unset)
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    # Operational — safe non-secret defaults
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"
    app_name: str = "Revy"
    app_version: str = "1.0.0"
    app_public_url: str | None = None
    keycloak_frontend_client_id: str = "revy-web"

    # Pagination
    default_page_limit: int = 50
    max_page_limit: int = 100

    # Sentry — optional
    sentry_dsn: str | None = None
    sentry_enable_in_test: bool = False
    sentry_send_default_pii: bool = False
    sentry_traces_sample_rate_debug: float = 1.0
    sentry_traces_sample_rate_prod: float = 0.1

    # Email — console local, mailgun production
    email_provider: str = "console"
    email_from: str | None = None
    email_from_name: str | None = None
    mailgun_api_key: str | None = None
    mailgun_domain: str | None = None
    mailgun_region: str = "eu"
    mailgun_webhook_signing_key: str | None = None

    # GitHub App
    github_app_id: str | None = None
    github_app_private_key_path: str | None = None
    github_webhook_secret: str | None = None
    revy_bot_login: str = "revy[bot]"

    # Model providers
    moonshot_api_key: str | None = None
    anthropic_api_key: str | None = None
    voyage_api_key: str | None = None

    # Revy runtime paths (outside repo — see .env.example)
    revy_repos_root: str | None = None
    revy_worktrees_root: str | None = None
    revy_hf_cache_path: str | None = None

    # Stripe billing — disabled by default; set STRIPE_ENABLED=true with keys in production
    stripe_enabled: bool = False
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_pro: str | None = None
    stripe_checkout_success_url: str | None = None
    stripe_checkout_cancel_url: str | None = None

    # Review policy
    revy_default_review_profile: str = "standard"
    revy_revision_timeout_standard_seconds: int = 900
    revy_revision_timeout_deep_seconds: int = 1500
    revy_revision_timeout_critical_seconds: int = 1800

    @property
    def keycloak_token_issuer(self) -> str:
        """OIDC issuer (`iss`) for JWT validation — public URL when KEYCLOAK_URL is internal."""
        if self.keycloak_issuer:
            return self.keycloak_issuer.rstrip("/")
        base = self.keycloak_url.rstrip("/")
        return f"{base}/realms/{self.keycloak_realm}"

    @property
    def cors_origins(self) -> list[str]:
        raw = self.allowed_origins.strip()
        if raw.startswith("["):
            return json.loads(raw)
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


settings = Settings()
