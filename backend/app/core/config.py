# backend/app/core/config.py
"""Application settings — fail-fast on missing required env (no URL defaults in code)."""
import json
import logging

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)
_revy_llm_provider_alias_logged = False


def reset_revy_llm_provider_alias_logged() -> None:
    """Test helper — avoid module-level deprecation flag bleed across tests."""
    global _revy_llm_provider_alias_logged
    _revy_llm_provider_alias_logged = False


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
    keycloak_webhook_secret: str | None = None
    revy_bot_login: str = "revy[bot]"

    # Model providers — MODEL_POLICY M0
    revy_reviewer_provider: str | None = None
    revy_judge_provider: str = "anthropic"
    revy_llm_provider: str = "moonshot"  # deprecated alias for revy_reviewer_provider
    revy_moonshot_model_standard: str = "kimi-k2.7-code"
    revy_moonshot_model_deep: str = "kimi-k3"
    revy_moonshot_model_critical: str = "kimi-k3"
    # Thinking models share reasoning_content + content under max_completion_tokens.
    # Moonshot API default when omitted is ~1024 — too low for K2/K3 (see staging dogfood).
    revy_moonshot_max_completion_tokens: int = 32768
    revy_anthropic_model: str = "claude-sonnet-5"
    revy_judge_structured_output: bool = False
    # Optional Anthropic-compatible gateway (e.g. RTU llm.ai.rtu.lv) — does not replace direct API
    anthropic_base_url: str | None = None
    revy_anthropic_gateway_model: str | None = None
    moonshot_api_key: str | None = None
    anthropic_api_key: str | None = None
    anthropic_auth_token: str | None = None
    voyage_api_key: str | None = None

    # AWS Bedrock — MODEL_POLICY M1
    aws_region: str | None = None
    revy_bedrock_judge_model_id: str | None = None
    revy_bedrock_reviewer_model_id: str | None = None
    revy_bedrock_inference_profile_arn: str | None = None

    # Revy runtime paths (outside repo — see .env.example)
    revy_repos_root: str | None = None
    revy_worktrees_root: str | None = None
    revy_hf_cache_path: str | None = None

    # Embeddings — R3 indexing (Voyage)
    revy_embedding_model: str = "voyage-code-3"
    revy_embedding_dimensions: int = 1024

    @field_validator("revy_embedding_model", mode="before")
    @classmethod
    def _strip_embedding_model(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    # Stripe billing — disabled by default; set STRIPE_ENABLED=true with keys in production
    stripe_enabled: bool = False
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_pro: str | None = None
    stripe_checkout_success_url: str | None = None
    stripe_checkout_cancel_url: str | None = None

    # Data export — ACCOUNT_LIFECYCLE.md
    export_storage_path: str = "/tmp/revy/exports"
    export_ttl_days: int = 7

    # Pipeline trace retention — review-quality O8
    pipeline_retention_days: int = 90

    # Generation lifecycle — autostart coalesce before pipeline enqueue (0 = off, max 10)
    review_coalesce_seconds: int = 0

    @field_validator("review_coalesce_seconds", mode="after")
    @classmethod
    def _clamp_review_coalesce_seconds(cls, value: int) -> int:
        clamped = max(0, min(10, value))
        if clamped != value:
            logger.warning(
                "review_coalesce_seconds=%s clamped to %s (allowed range 0-10)",
                value,
                clamped,
            )
        return clamped

    @field_validator("revy_moonshot_max_completion_tokens", mode="after")
    @classmethod
    def _clamp_moonshot_max_completion_tokens(cls, value: int) -> int:
        clamped = max(16_000, min(131_072, value))
        if clamped != value:
            logger.warning(
                "revy_moonshot_max_completion_tokens=%s clamped to %s (allowed range 16000-131072)",
                value,
                clamped,
            )
        return clamped

    # Review policy
    revy_default_review_profile: str = "standard"
    revy_revision_timeout_standard_seconds: int = 900
    revy_revision_timeout_deep_seconds: int = 1500
    revy_revision_timeout_critical_seconds: int = 1800
    # HTTP client timeout buffer — finish LLM calls before Celery soft_time_limit fires.
    revy_revision_celery_timeout_buffer_seconds: int = 60

    # Review prompt caps — RCX engineering context (wired in github_review P2)
    revy_diff_max_bytes: int = 524288
    revy_engineering_context_max_bytes: int = 32768
    revy_pr_body_max_bytes: int = 4096

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

    @property
    def github_webhooks_enabled(self) -> bool:
        return bool(self.github_webhook_secret and self.github_webhook_secret.strip())

    @property
    def keycloak_webhooks_enabled(self) -> bool:
        return bool(self.keycloak_webhook_secret and self.keycloak_webhook_secret.strip())

    @property
    def github_api_enabled(self) -> bool:
        return bool(
            self.github_app_id
            and self.github_app_id.strip()
            and self.github_app_private_key_path
            and self.github_app_private_key_path.strip()
        )

    @property
    def embeddings_enabled(self) -> bool:
        return bool(self.voyage_api_key and self.voyage_api_key.strip())

    @property
    def anthropic_direct_enabled(self) -> bool:
        return bool(self.anthropic_api_key and self.anthropic_api_key.strip())

    @property
    def anthropic_gateway_base_url(self) -> str | None:
        base = (self.anthropic_base_url or "").strip().rstrip("/")
        if not base or base == "https://api.anthropic.com":
            return None
        return base

    @property
    def anthropic_gateway_enabled(self) -> bool:
        return bool(
            self.anthropic_gateway_base_url
            and self.anthropic_auth_token
            and self.anthropic_auth_token.strip()
        )

    @property
    def anthropic_gateway_messages_url(self) -> str | None:
        base = self.anthropic_gateway_base_url
        if not base:
            return None
        return f"{base}/v1/messages"

    @property
    def effective_anthropic_gateway_judge_model(self) -> str | None:
        value = (self.revy_anthropic_gateway_model or "").strip()
        return value or None

    @property
    def effective_reviewer_provider(self) -> str:
        global _revy_llm_provider_alias_logged
        explicit = (self.revy_reviewer_provider or "").strip().lower()
        if explicit:
            return explicit
        if not _revy_llm_provider_alias_logged:
            logger.warning(
                "revy_llm_provider is deprecated; set REVY_REVIEWER_PROVIDER instead",
            )
            _revy_llm_provider_alias_logged = True
        return (self.revy_llm_provider or "moonshot").strip().lower()

    @property
    def effective_judge_provider(self) -> str:
        return (self.revy_judge_provider or "anthropic").strip().lower()

    def bedrock_enabled(self) -> bool:
        region = (self.aws_region or "").strip()
        if not region:
            return False
        judge_model = (self.revy_bedrock_judge_model_id or "").strip()
        reviewer_model = (self.revy_bedrock_reviewer_model_id or "").strip()
        return bool(judge_model or reviewer_model)

    def reviewer_llm_enabled(self) -> bool:
        provider = self.effective_reviewer_provider
        if provider == "moonshot":
            return bool(self.moonshot_api_key and self.moonshot_api_key.strip())
        if provider == "anthropic":
            return self.anthropic_direct_enabled
        if provider == "bedrock":
            return self.bedrock_enabled() and bool(
                (self.revy_bedrock_reviewer_model_id or "").strip()
            )
        return False

    def judge_llm_enabled(self) -> bool:
        provider = self.effective_judge_provider
        if provider == "anthropic":
            return self.anthropic_gateway_enabled or self.anthropic_direct_enabled
        if provider == "bedrock":
            return self.bedrock_enabled() and bool(
                (self.revy_bedrock_judge_model_id or "").strip()
            )
        return False

    @property
    def llm_enabled(self) -> bool:
        """Deprecated — use ``reviewer_llm_enabled()``."""
        return self.reviewer_llm_enabled()

    def revy_revision_timeout_seconds(self, profile: str) -> int:
        normalized = (profile or self.revy_default_review_profile).strip().lower()
        if normalized == "deep":
            return self.revy_revision_timeout_deep_seconds
        if normalized == "critical":
            return self.revy_revision_timeout_critical_seconds
        return self.revy_revision_timeout_standard_seconds

    def revy_revision_llm_http_timeout_seconds(self, profile: str) -> int:
        """LLM HTTP timeout — strictly below Celery soft_time_limit for the same profile."""
        task_timeout = self.revy_revision_timeout_seconds(profile)
        buffer_seconds = max(0, self.revy_revision_celery_timeout_buffer_seconds)
        return max(60, task_timeout - buffer_seconds)

    def revy_moonshot_model_for_profile(self, profile: str) -> str:
        normalized = (profile or self.revy_default_review_profile).strip().lower()
        if normalized == "deep":
            return self.revy_moonshot_model_deep
        if normalized == "critical":
            return self.revy_moonshot_model_critical
        return self.revy_moonshot_model_standard

    @property
    def revy_worktrees_path(self) -> str:
        return self.revy_worktrees_root or "/tmp/revy/worktrees"


settings = Settings()
