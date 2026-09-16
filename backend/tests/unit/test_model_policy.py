# backend/tests/unit/test_model_policy.py
"""Model policy resolver — MODEL_POLICY M0."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.model_policy import ModelRole
from app.core.config import Settings
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.services.model_policy import (
    ModelRef,
    resolve_model,
    review_profile_to_model_role,
)


def test_review_profile_to_model_role():
    assert review_profile_to_model_role("standard") == ModelRole.reviewer_standard
    assert review_profile_to_model_role("deep") == ModelRole.reviewer_deep
    assert review_profile_to_model_role("critical") == ModelRole.reviewer_critical


@pytest.mark.asyncio
async def test_resolve_platform_defaults():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    workspace_id = uuid.uuid4()
    with patch("app.services.model_policy.settings") as mock_settings:
        mock_settings.effective_reviewer_provider = "moonshot"
        mock_settings.moonshot_api_key = "key"
        mock_settings.revy_moonshot_model_standard = "kimi-k2.7-code"
        mock_settings.revy_moonshot_model_deep = "kimi-k3"
        mock_settings.revy_moonshot_model_critical = "kimi-k3"
        mock_settings.effective_judge_provider = "anthropic"
        mock_settings.anthropic_api_key = "key"
        mock_settings.anthropic_gateway_enabled = False
        mock_settings.effective_anthropic_gateway_judge_model = None
        mock_settings.revy_anthropic_model = "claude-sonnet-4-20250514"

        reviewer = await resolve_model(session, workspace_id, ModelRole.reviewer_standard)
        judge = await resolve_model(session, workspace_id, ModelRole.judge)

    assert reviewer == ModelRef(provider="moonshot", model_id="kimi-k2.7-code")
    assert judge == ModelRef(provider="anthropic", model_id="claude-sonnet-4-20250514")


@pytest.mark.asyncio
async def test_resolve_rtu_platform_defaults():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    workspace_id = uuid.uuid4()
    with patch("app.services.model_policy.settings") as mock_settings:
        mock_settings.effective_reviewer_provider = "rtu"
        mock_settings.effective_rtu_api_key = "rtu-key"
        mock_settings.revy_rtu_model_standard = "azure_ai/kimi-k2.7-code"
        mock_settings.revy_rtu_model_deep = "azure_ai/claude-fable-5-1"
        mock_settings.revy_rtu_model_critical = "azure_ai/claude-fable-5-1"
        mock_settings.effective_judge_provider = "rtu"
        mock_settings.revy_rtu_model_judge = "azure_ai/claude-opus-5"

        reviewer = await resolve_model(session, workspace_id, ModelRole.reviewer_standard)
        deep = await resolve_model(session, workspace_id, ModelRole.reviewer_deep)
        judge = await resolve_model(session, workspace_id, ModelRole.judge)

    assert reviewer == ModelRef(provider="rtu", model_id="azure_ai/kimi-k2.7-code")
    assert deep == ModelRef(provider="rtu", model_id="azure_ai/claude-fable-5-1")
    assert judge == ModelRef(provider="rtu", model_id="azure_ai/claude-opus-5")


@pytest.mark.asyncio
async def test_resolve_anthropic_judge_uses_direct_model():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.services.model_policy.settings") as mock_settings:
        mock_settings.effective_judge_provider = "anthropic"
        mock_settings.anthropic_direct_enabled = True
        mock_settings.revy_anthropic_model = "claude-sonnet-5"
        judge = await resolve_model(session, uuid.uuid4(), ModelRole.judge)
    assert judge == ModelRef(provider="anthropic", model_id="claude-sonnet-5")


@pytest.mark.asyncio
async def test_resolve_reviewer_missing_credentials_raises():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.services.model_policy.settings") as mock_settings:
        mock_settings.effective_reviewer_provider = "moonshot"
        mock_settings.moonshot_api_key = None
        with pytest.raises(ServiceUnavailableError) as exc:
            await resolve_model(session, uuid.uuid4(), ModelRole.reviewer_standard)
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_resolve_judge_missing_credentials_raises():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.services.model_policy.settings") as mock_settings:
        mock_settings.effective_judge_provider = "anthropic"
        mock_settings.anthropic_api_key = None
        mock_settings.anthropic_gateway_enabled = False
        mock_settings.anthropic_direct_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await resolve_model(session, uuid.uuid4(), ModelRole.judge)
    assert exc.value.error_code == "llm_disabled"


def _test_settings(**overrides) -> Settings:
    values = {
        "environment": "test",
        "database_url": "postgresql+asyncpg://localhost/revy",
        "redis_url": "redis://localhost",
        "secret_key": "x" * 32,
        "allowed_origins": "http://localhost",
        "keycloak_url": "http://localhost",
        "keycloak_realm": "revy",
        "keycloak_client_id": "revy-api",
        "keycloak_client_secret": "secret",
    }
    values.update(overrides)
    return Settings(**values)


def test_reviewer_llm_enabled_moonshot():
    settings = _test_settings(moonshot_api_key="key", revy_reviewer_provider="moonshot")
    assert settings.reviewer_llm_enabled() is True


def test_judge_llm_enabled_anthropic():
    settings = _test_settings(anthropic_api_key="key", revy_judge_provider="anthropic")
    assert settings.judge_llm_enabled() is True


def test_judge_llm_enabled_moonshot_is_false():
    settings = _test_settings(moonshot_api_key="key", revy_judge_provider="moonshot")
    assert settings.judge_llm_enabled() is False


@pytest.mark.asyncio
async def test_resolve_unsupported_judge_provider_falls_back_to_default():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.services.model_policy.settings") as mock_settings:
        mock_settings.effective_judge_provider = "moonshot"
        model_ref = await resolve_model(
            session,
            uuid.uuid4(),
            ModelRole.judge,
            require_credentials=False,
        )
    assert model_ref == ModelRef(provider="rtu", model_id="azure_ai/claude-opus-5")


def test_reviewer_llm_enabled_disabled_without_key():
    settings = _test_settings(moonshot_api_key=None, revy_reviewer_provider="moonshot")
    assert settings.reviewer_llm_enabled() is False


def test_moonshot_chat_completions_url_appends_path():
    settings = _test_settings(moonshot_api_base="https://api.moonshot.ai/v1")
    assert settings.moonshot_chat_completions_url == "https://api.moonshot.ai/v1/chat/completions"


def test_rtu_urls_normalize_origin_with_or_without_v1():
    for base in ("https://llm.ai.rtu.lv", "https://llm.ai.rtu.lv/v1"):
        settings = _test_settings(rtu_api_base=base)
        assert settings.rtu_chat_completions_url == "https://llm.ai.rtu.lv/v1/chat/completions"
        assert settings.rtu_messages_url == "https://llm.ai.rtu.lv/v1/messages"


def test_reviewer_llm_enabled_rtu_uses_rtu_key():
    settings = _test_settings(rtu_api_key="rtu-key", revy_reviewer_provider="rtu")
    assert settings.reviewer_llm_enabled() is True
    assert settings.effective_rtu_api_key == "rtu-key"


def test_rtu_does_not_read_anthropic_auth_token():
    settings = _test_settings(
        revy_reviewer_provider="rtu",
        revy_judge_provider="rtu",
        rtu_api_key="",
        anthropic_auth_token="anthropic-token",
        anthropic_api_key="",
    )
    assert settings.effective_rtu_api_key is None
    assert settings.reviewer_llm_enabled() is False
    assert settings.judge_llm_enabled() is False


def test_judge_llm_enabled_rtu_uses_rtu_key():
    settings = _test_settings(rtu_api_key="rtu-key", revy_judge_provider="rtu")
    assert settings.judge_llm_enabled() is True


def test_reviewer_llm_enabled_rtu_disabled_without_key():
    settings = _test_settings(
        revy_reviewer_provider="rtu",
        rtu_api_key="",
    )
    assert settings.reviewer_llm_enabled() is False


def test_platform_model_defaults_keep_moonshot_and_rtu_separate():
    fields = Settings.model_fields
    assert fields["revy_moonshot_model_standard"].default == "kimi-k2.7-code"
    assert fields["revy_moonshot_model_deep"].default == "kimi-k3"
    assert fields["revy_moonshot_model_critical"].default == "kimi-k3"
    assert fields["revy_rtu_model_standard"].default == "azure_ai/kimi-k2.7-code"
    assert fields["revy_rtu_model_deep"].default == "azure_ai/claude-fable-5-1"
    assert fields["revy_rtu_model_critical"].default == "azure_ai/claude-fable-5-1"
    assert fields["revy_rtu_model_judge"].default == "azure_ai/claude-opus-5"
    assert fields["revy_anthropic_gateway_model"].default is None
    assert fields["revy_judge_provider"].default == "rtu"
    assert fields["revy_llm_provider"].default == "rtu"


@pytest.mark.asyncio
async def test_dispatch_passes_model_id_to_moonshot():
    from app.integrations.llm_dispatch import call_review_llm

    client = AsyncMock()
    model_ref = ModelRef(provider="moonshot", model_id="kimi-k3")
    with patch(
        "app.integrations.llm_dispatch.moonshot_review.complete_review",
        AsyncMock(return_value="{}"),
    ) as complete_mock:
        await call_review_llm(
            client,
            model_ref=model_ref,
            profile="deep",
            user_prompt="prompt",
            timeout_seconds=30.0,
        )
    complete_mock.assert_awaited_once_with(
        client,
        profile="deep",
        user_prompt="prompt",
        model_id="kimi-k3",
        timeout_seconds=30.0,
        api_url=None,
        api_key=None,
    )


@pytest.mark.asyncio
async def test_dispatch_passes_rtu_url_and_key():
    from app.integrations.llm_dispatch import call_review_llm

    client = AsyncMock()
    model_ref = ModelRef(provider="rtu", model_id="azure_ai/kimi-k2.7-code")
    with patch("app.integrations.llm_dispatch.settings") as mock_settings:
        mock_settings.rtu_chat_completions_url = "https://llm.ai.rtu.lv/v1/chat/completions"
        mock_settings.effective_rtu_api_key = "rtu-key"
        with patch(
            "app.integrations.llm_dispatch.moonshot_review.complete_review",
            AsyncMock(return_value="{}"),
        ) as complete_mock:
            await call_review_llm(
                client,
                model_ref=model_ref,
                profile="standard",
                user_prompt="prompt",
                timeout_seconds=30.0,
            )
    complete_mock.assert_awaited_once_with(
        client,
        profile="standard",
        user_prompt="prompt",
        model_id="azure_ai/kimi-k2.7-code",
        timeout_seconds=30.0,
        api_url="https://llm.ai.rtu.lv/v1/chat/completions",
        api_key="rtu-key",
    )


@pytest.mark.asyncio
async def test_dispatch_passes_rtu_judge_url_and_key():
    from app.integrations.llm_dispatch import call_judge_llm

    client = AsyncMock()
    model_ref = ModelRef(provider="rtu", model_id="azure_ai/claude-opus-5")
    with patch("app.integrations.llm_dispatch.settings") as mock_settings:
        mock_settings.rtu_messages_url = "https://llm.ai.rtu.lv/v1/messages"
        mock_settings.effective_rtu_api_key = "rtu-key"
        with patch(
            "app.integrations.llm_dispatch.anthropic_review.judge_finding",
            AsyncMock(return_value={"outcome": "upheld"}),
        ) as judge_mock:
            await call_judge_llm(
                client,
                model_ref=model_ref,
                user_prompt="prompt",
                timeout_seconds=30.0,
            )
    judge_mock.assert_awaited_once_with(
        client,
        user_prompt="prompt",
        model_id="azure_ai/claude-opus-5",
        timeout_seconds=30.0,
        system_prompt=None,
        messages_url="https://llm.ai.rtu.lv/v1/messages",
        api_key="rtu-key",
    )


@pytest.mark.asyncio
async def test_dispatch_passes_model_id_to_anthropic_judge():
    from app.integrations.llm_dispatch import call_judge_llm

    client = AsyncMock()
    model_ref = ModelRef(provider="anthropic", model_id="claude-test")
    with patch(
        "app.integrations.llm_dispatch.anthropic_review.judge_finding",
        AsyncMock(return_value={"outcome": "upheld"}),
    ) as judge_mock:
        await call_judge_llm(
            client,
            model_ref=model_ref,
            user_prompt="prompt",
            timeout_seconds=30.0,
        )
    judge_mock.assert_awaited_once_with(
        client,
        user_prompt="prompt",
        model_id="claude-test",
        timeout_seconds=30.0,
        system_prompt=None,
    )


def test_bedrock_config_enabled():
    settings = _test_settings(
        aws_region="eu-central-1",
        revy_judge_provider="bedrock",
        revy_bedrock_judge_model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    )
    assert settings.bedrock_enabled() is True
    assert settings.judge_llm_enabled() is True


def test_bedrock_config_disabled_without_region():
    settings = _test_settings(
        revy_bedrock_judge_model_id="anthropic.claude-sonnet-4-20250514-v1:0",
    )
    assert settings.bedrock_enabled() is False


@pytest.mark.asyncio
async def test_resolve_bedrock_judge():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.services.model_policy.settings") as mock_settings:
        mock_settings.effective_judge_provider = "bedrock"
        mock_settings.aws_region = "eu-central-1"
        mock_settings.revy_bedrock_judge_model_id = "anthropic.claude-sonnet-4-20250514-v1:0"
        judge = await resolve_model(session, uuid.uuid4(), ModelRole.judge)
    assert judge == ModelRef(
        provider="bedrock",
        model_id="anthropic.claude-sonnet-4-20250514-v1:0",
        region="eu-central-1",
    )


@pytest.mark.asyncio
async def test_dispatch_bedrock_judge():
    from app.integrations.llm_dispatch import call_judge_llm

    client = AsyncMock()
    model_ref = ModelRef(
        provider="bedrock",
        model_id="anthropic.claude-sonnet-4-20250514-v1:0",
        region="eu-central-1",
    )
    with patch(
        "app.integrations.llm_dispatch.bedrock_review.judge_finding",
        AsyncMock(return_value={"outcome": "upheld"}),
    ) as judge_mock:
        await call_judge_llm(
            client,
            model_ref=model_ref,
            user_prompt="prompt",
            timeout_seconds=30.0,
        )
    judge_mock.assert_awaited_once_with(
        user_prompt="prompt",
        model_id="anthropic.claude-sonnet-4-20250514-v1:0",
        region="eu-central-1",
        timeout_seconds=30.0,
        system_prompt=None,
    )


@pytest.mark.asyncio
async def test_call_judge_llm_rejects_unsupported_provider():
    from app.integrations.llm_dispatch import call_judge_llm

    client = AsyncMock()
    model_ref = ModelRef(provider="moonshot", model_id="kimi-k3")
    with pytest.raises(ServiceUnavailableError) as exc_info:
        await call_judge_llm(
            client,
            model_ref=model_ref,
            user_prompt="prompt",
            timeout_seconds=30.0,
        )
    assert exc_info.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_resolve_workspace_override_rejects_moonshot_judge():
    from app.models.workspace_model_policy import WorkspaceModelPolicyORM

    session = AsyncMock()
    workspace_id = uuid.uuid4()
    row = WorkspaceModelPolicyORM(
        workspace_id=workspace_id,
        role=ModelRole.judge.value,
        provider="moonshot",
        model_id="kimi-k3",
        region=None,
    )
    session.scalar = AsyncMock(return_value=row)
    with (
        patch("app.services.model_policy.is_valid_catalog_entry", return_value=True),
        patch("app.services.model_policy.settings") as mock_settings,
        pytest.raises(ServiceUnavailableError),
    ):
        mock_settings.moonshot_api_key = "key"
        await resolve_model(session, workspace_id, ModelRole.judge)


@pytest.mark.asyncio
async def test_resolve_workspace_override():
    from app.models.workspace_model_policy import WorkspaceModelPolicyORM

    session = AsyncMock()
    workspace_id = uuid.uuid4()
    row = WorkspaceModelPolicyORM(
        workspace_id=workspace_id,
        role=ModelRole.judge.value,
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        region=None,
    )
    session.scalar = AsyncMock(return_value=row)
    with (
        patch("app.services.model_policy.is_valid_catalog_entry", return_value=True),
        patch("app.services.model_policy.settings") as mock_settings,
    ):
        mock_settings.anthropic_api_key = "key"
        model_ref = await resolve_model(session, workspace_id, ModelRole.judge)
    assert model_ref.provider == "anthropic"
    assert model_ref.model_id == "claude-sonnet-4-20250514"


@pytest.mark.asyncio
async def test_resolve_without_credentials_for_policy_display():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    with patch("app.services.model_policy.settings") as mock_settings:
        mock_settings.effective_reviewer_provider = "moonshot"
        mock_settings.reviewer_llm_enabled.return_value = False
        mock_settings.revy_moonshot_model_standard = "kimi-k2.7-code"
        reviewer = await resolve_model(
            session,
            uuid.uuid4(),
            ModelRole.reviewer_standard,
            require_credentials=False,
        )
    assert reviewer == ModelRef(provider="moonshot", model_id="kimi-k2.7-code")


@pytest.mark.asyncio
async def test_resolve_workspace_bedrock_override_checks_override_provider():
    from app.models.workspace_model_policy import WorkspaceModelPolicyORM

    session = AsyncMock()
    workspace_id = uuid.uuid4()
    row = WorkspaceModelPolicyORM(
        workspace_id=workspace_id,
        role=ModelRole.reviewer_standard.value,
        provider="bedrock",
        model_id="qwen.qwen3-coder-next",
        region="us-east-1",
    )
    session.scalar = AsyncMock(return_value=row)
    with (
        patch("app.services.model_policy.is_valid_catalog_entry", return_value=True),
        patch("app.services.model_policy.settings") as mock_settings,
    ):
        mock_settings.effective_reviewer_provider = "anthropic"
        mock_settings.reviewer_llm_enabled.return_value = False
        mock_settings.anthropic_api_key = None
        mock_settings.aws_region = "us-east-1"
        model_ref = await resolve_model(session, workspace_id, ModelRole.reviewer_standard)

    assert model_ref == ModelRef(
        provider="bedrock",
        model_id="qwen.qwen3-coder-next",
        region="us-east-1",
    )


@pytest.mark.asyncio
async def test_resolve_workspace_override_skips_catalog_when_display_only():
    from app.models.workspace_model_policy import WorkspaceModelPolicyORM

    session = AsyncMock()
    workspace_id = uuid.uuid4()
    row = WorkspaceModelPolicyORM(
        workspace_id=workspace_id,
        role=ModelRole.judge.value,
        provider="bedrock",
        model_id="qwen.qwen3-coder-next",
        region="us-east-1",
    )
    session.scalar = AsyncMock(return_value=row)
    with (
        patch("app.services.model_policy.is_valid_catalog_entry", return_value=False),
        patch("app.services.model_policy.settings") as mock_settings,
    ):
        mock_settings.aws_region = "us-east-1"
        model_ref = await resolve_model(
            session,
            workspace_id,
            ModelRole.judge,
            require_credentials=False,
        )

    assert model_ref == ModelRef(
        provider="bedrock",
        model_id="qwen.qwen3-coder-next",
        region="us-east-1",
    )


@pytest.mark.asyncio
async def test_resolve_workspace_override_invalid_rejected():
    from app.models.workspace_model_policy import WorkspaceModelPolicyORM

    session = AsyncMock()
    workspace_id = uuid.uuid4()
    row = WorkspaceModelPolicyORM(
        workspace_id=workspace_id,
        role=ModelRole.judge.value,
        provider="anthropic",
        model_id="removed-model",
        region=None,
    )
    session.scalar = AsyncMock(return_value=row)
    with (
        patch("app.services.model_policy.is_valid_catalog_entry", return_value=False),
        pytest.raises(ValidationError),
    ):
        await resolve_model(session, workspace_id, ModelRole.judge)
