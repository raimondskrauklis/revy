# backend/tests/unit/test_github_tasks_autostart.py
"""GitHub webhook autostart — R8."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubIndexJobTriggerSource
from app.models.github_webhook_delivery import GitHubWebhookDeliveryORM
from app.services.github_pull_requests import IssueCommentPipelineIntent, PullRequestWebhookResult
from app.workers import github_tasks


def _delivery(*, event_type: str) -> GitHubWebhookDeliveryORM:
    return GitHubWebhookDeliveryORM(
        delivery_id="d-auto",
        event_type=event_type,
        installation_id=42,
        payload_json={"action": "opened"},
    )


def _db_context(session: AsyncMock) -> MagicMock:
    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)
    return db_context


def test_process_github_event_enqueues_pipeline_after_pull_request_opened():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    job_id = uuid.uuid4()
    delivery = _delivery(event_type="pull_request")
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    result = PullRequestWebhookResult(
        workspace_id=workspace_id,
        revision_id=revision_id,
        new_revision=True,
        action="opened",
    )

    with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
        with patch(
            "app.workers.github_tasks.apply_pull_request_webhook_event",
            AsyncMock(return_value=result),
        ):
            with patch(
                "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                AsyncMock(return_value=job_id),
            ) as pipeline_mock:
                with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                    github_tasks.process_github_event.run("d-auto")

    pipeline_mock.assert_awaited_once()
    assert pipeline_mock.await_args.kwargs["trigger"] == GitHubIndexJobTriggerSource.autostart
    enqueue_mock.assert_called_once_with(job_id)


def test_process_github_event_enqueues_pipeline_for_issue_comment_command():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    job_id = uuid.uuid4()
    delivery = _delivery(event_type="issue_comment")
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    intent = IssueCommentPipelineIntent(workspace_id=workspace_id, revision_id=revision_id)

    with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
        with patch(
            "app.workers.github_tasks.apply_issue_comment_webhook_event",
            AsyncMock(return_value=intent),
        ):
            with patch(
                "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                AsyncMock(return_value=job_id),
            ) as pipeline_mock:
                with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                    github_tasks.process_github_event.run("d-auto")

    assert pipeline_mock.await_args.kwargs["trigger"] == GitHubIndexJobTriggerSource.command
    enqueue_mock.assert_called_once_with(job_id)


def test_process_github_event_skips_enqueue_when_no_new_revision():
    delivery = _delivery(event_type="pull_request")
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
        with patch(
            "app.workers.github_tasks.apply_pull_request_webhook_event",
            AsyncMock(return_value=None),
        ):
            with patch("app.workers.github_tasks.maybe_enqueue_pipeline_for_revision", AsyncMock()) as pipeline_mock:
                with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                    github_tasks.process_github_event.run("d-auto")

    pipeline_mock.assert_not_awaited()
    enqueue_mock.assert_not_called()
