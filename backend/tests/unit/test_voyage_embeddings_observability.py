# backend/tests/unit/test_voyage_embeddings_observability.py
"""Voyage embeddings attempt rows — MRC-P1 / PO-P1.4."""
import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations.voyage_embeddings import VoyageEmbedRecorderContext, embed_texts


@pytest.mark.asyncio
async def test_embed_texts_writes_index_embed_attempt_row():
    pipeline_run_id = uuid.uuid4()
    index_job_id = uuid.uuid4()
    recorder = VoyageEmbedRecorderContext(
        pipeline_run_id=pipeline_run_id,
        index_job_id=index_job_id,
        request_model="voyage-code-3.5",
    )
    response = httpx.Response(
        200,
        json={"data": [{"embedding": [0.1, 0.2]}]},
        request=httpx.Request("POST", "https://api.voyageai.com/v1/embeddings"),
    )
    client = AsyncMock()
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "test-key"
        mock_settings.revy_embedding_model = "voyage-code-3"
        mock_settings.revy_embedding_dimensions = 1024
        with patch(
            "app.integrations.voyage_embeddings.start_attempt",
            AsyncMock(return_value=uuid.uuid4()),
        ) as start_mock:
            with patch(
                "app.integrations.voyage_embeddings.complete_attempt",
                AsyncMock(),
            ) as complete_mock:
                vectors = await embed_texts(
                    client,
                    ["hello"],
                    request_model="voyage-code-3.5",
                    recorder=recorder,
                )

    assert vectors == [[0.1, 0.2]]
    start_mock.assert_awaited_once()
    context = start_mock.await_args.args[0]
    assert context.step_type.value == "index_embed"
    assert context.request_model == "voyage-code-3.5"
    assert context.batch_size == 1
    complete_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_embed_texts_threads_captured_output_dimension():
    pipeline_run_id = uuid.uuid4()
    index_job_id = uuid.uuid4()
    recorder = VoyageEmbedRecorderContext(
        pipeline_run_id=pipeline_run_id,
        index_job_id=index_job_id,
        request_model="voyage-code-3.5",
        output_dimension=512,
    )
    response = httpx.Response(
        200,
        json={"data": [{"embedding": [0.1]}]},
        request=httpx.Request("POST", "https://api.voyageai.com/v1/embeddings"),
    )
    client = AsyncMock()
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "test-key"
        mock_settings.revy_embedding_model = "voyage-code-3.5"
        mock_settings.revy_embedding_dimensions = 1024
        with patch("app.integrations.voyage_embeddings.start_attempt", AsyncMock(return_value=uuid.uuid4())):
            with patch("app.integrations.voyage_embeddings.complete_attempt", AsyncMock()):
                await embed_texts(client, ["hello"], recorder=recorder)

    body = client.post.await_args.kwargs["json"]
    assert body["output_dimension"] == 512


@pytest.mark.asyncio
async def test_embed_texts_skips_recorder_when_none():
    response = httpx.Response(
        200,
        json={"data": [{"embedding": [0.3]}]},
        request=httpx.Request("POST", "https://api.voyageai.com/v1/embeddings"),
    )
    client = AsyncMock()
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "test-key"
        mock_settings.revy_embedding_model = "voyage-code-3"
        mock_settings.revy_embedding_dimensions = 1024
        with patch(
            "app.integrations.voyage_embeddings.start_attempt",
            AsyncMock(),
        ) as start_mock:
            await embed_texts(client, ["hello"])

    start_mock.assert_not_awaited()
