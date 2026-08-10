# backend/tests/unit/test_review_timeout_config.py
"""Review Celery vs LLM HTTP timeout alignment."""
from app.core.config import Settings


def test_revy_revision_llm_http_timeout_is_below_celery_soft_limit():
    settings = Settings(
        revy_revision_timeout_standard_seconds=900,
        revy_revision_celery_timeout_buffer_seconds=60,
    )
    assert settings.revy_revision_llm_http_timeout_seconds("standard") == 840
    assert (
        settings.revy_revision_llm_http_timeout_seconds("standard")
        < settings.revy_revision_timeout_seconds("standard")
    )


def test_revy_revision_llm_http_timeout_respects_profile_and_floor():
    settings = Settings(
        revy_revision_timeout_deep_seconds=1500,
        revy_revision_timeout_critical_seconds=1800,
        revy_revision_celery_timeout_buffer_seconds=60,
    )
    assert settings.revy_revision_llm_http_timeout_seconds("deep") == 1440
    assert settings.revy_revision_llm_http_timeout_seconds("critical") == 1740

    tiny = Settings(
        revy_revision_timeout_standard_seconds=90,
        revy_revision_celery_timeout_buffer_seconds=60,
    )
    assert tiny.revy_revision_llm_http_timeout_seconds("standard") == 60
