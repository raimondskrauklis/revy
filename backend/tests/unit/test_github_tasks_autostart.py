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


def test_process_github_event_command_supersedes_before_enqueue():
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
                "app.workers.github_tasks.supersede_active_generations_for_revision",
                AsyncMock(),
            ) as supersede_mock:
                with patch(
                    "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                    AsyncMock(return_value=job_id),
                ) as pipeline_mock:
                    with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                        github_tasks.process_github_event.run("d-auto")

    supersede_mock.assert_awaited_once()
    assert supersede_mock.await_args.kwargs["revision_id"] == revision_id
    pipeline_mock.assert_awaited_once()
    enqueue_mock.assert_called_once_with(job_id)


def test_process_github_event_command_supersedes_in_flight_index_jobs():
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
                "app.services.github_generation_lifecycle.mark_active_index_jobs_superseded_for_revision",
                AsyncMock(return_value=[]),
            ) as index_supersede_mock:
                with patch(
                    "app.services.github_generation_lifecycle.mark_active_review_runs_superseded_for_revision",
                    AsyncMock(return_value=[]),
                ):
                    with patch(
                        "app.services.github_generation_lifecycle.finalize_pipeline_checks_for_superseded_review_runs",
                        AsyncMock(),
                    ):
                        with patch(
                            "app.services.github_generation_lifecycle.finalize_pipeline_checks_for_superseded_index_jobs",
                            AsyncMock(),
                        ):
                            with patch(
                                "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                                AsyncMock(return_value=job_id),
                            ):
                                with patch("app.workers.github_tasks.enqueue_index_job"):
                                    github_tasks.process_github_event.run("d-auto")

    index_supersede_mock.assert_awaited_once()
    assert index_supersede_mock.await_args.kwargs["revision_id"] == revision_id


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
                "app.workers.github_tasks.supersede_active_generations_for_revision",
                AsyncMock(),
            ):
                with patch(
                    "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                    AsyncMock(return_value=job_id),
                ) as pipeline_mock:
                    with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                        github_tasks.process_github_event.run("d-auto")

    assert pipeline_mock.await_args.kwargs["trigger"] == GitHubIndexJobTriggerSource.command
    enqueue_mock.assert_called_once_with(job_id)


def test_process_github_event_enqueues_pipeline_on_pull_request_synchronize():
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
        action="synchronize",
    )

    with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
        with patch(
            "app.workers.github_tasks.apply_pull_request_webhook_event",
            AsyncMock(return_value=result),
        ):
            with patch(
                "app.workers.github_tasks.apply_resolution_for_synchronize.delay",
            ) as resolution_mock:
                with patch(
                    "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                    AsyncMock(return_value=job_id),
                ) as pipeline_mock:
                    with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                        github_tasks.process_github_event.run("d-auto")

    resolution_mock.assert_called_once_with(str(revision_id))
    pipeline_mock.assert_awaited_once()
    assert pipeline_mock.await_args.kwargs["trigger"] == GitHubIndexJobTriggerSource.autostart
    enqueue_mock.assert_called_once_with(job_id)


def test_process_github_event_enqueues_on_same_sha_synchronize_retrigger():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    job_id = uuid.uuid4()
    delivery = _delivery(event_type="pull_request")
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    result = PullRequestWebhookResult(
        workspace_id=workspace_id,
        revision_id=revision_id,
        new_revision=False,
        action="synchronize",
        pipeline_retrigger=True,
    )

    with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
        with patch(
            "app.workers.github_tasks.apply_pull_request_webhook_event",
            AsyncMock(return_value=result),
        ):
            with patch(
                "app.workers.github_tasks.apply_resolution_for_synchronize.delay",
            ) as resolution_mock:
                with patch(
                    "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                    AsyncMock(return_value=job_id),
                ) as pipeline_mock:
                    with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                        github_tasks.process_github_event.run("d-auto")

    resolution_mock.assert_called_once_with(str(revision_id))
    pipeline_mock.assert_awaited_once()
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


def test_process_github_event_synchronize_coalesce_zero_enqueues_immediately():
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
        action="synchronize",
    )

    with patch("app.workers.github_tasks.settings.review_coalesce_seconds", 0):
        with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
            with patch(
                "app.workers.github_tasks.apply_pull_request_webhook_event",
                AsyncMock(return_value=result),
            ):
                with patch(
                    "app.workers.github_tasks.apply_resolution_for_synchronize.delay",
                ):
                    with patch(
                        "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                        AsyncMock(return_value=job_id),
                    ) as pipeline_mock:
                        with patch(
                            "app.workers.github_tasks.schedule_autostart_pipeline_for_revision.apply_async",
                        ) as schedule_mock:
                            with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                                github_tasks.process_github_event.run("d-auto")

    pipeline_mock.assert_awaited_once()
    schedule_mock.assert_not_called()
    enqueue_mock.assert_called_once_with(job_id)


def test_process_github_event_synchronize_coalesce_schedules_delayed_autostart():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    delivery = _delivery(event_type="pull_request")
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    result = PullRequestWebhookResult(
        workspace_id=workspace_id,
        revision_id=revision_id,
        new_revision=True,
        action="synchronize",
    )

    with patch("app.workers.github_tasks.settings.review_coalesce_seconds", 5):
        with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
            with patch(
                "app.workers.github_tasks.apply_pull_request_webhook_event",
                AsyncMock(return_value=result),
            ):
                with patch(
                    "app.workers.github_tasks.apply_resolution_for_synchronize.delay",
                ):
                    with patch(
                        "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                        AsyncMock(),
                    ) as pipeline_mock:
                        with patch(
                            "app.workers.github_tasks.schedule_autostart_pipeline_for_revision.apply_async",
                        ) as schedule_mock:
                            with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                                github_tasks.process_github_event.run("d-auto")

    pipeline_mock.assert_not_awaited()
    enqueue_mock.assert_not_called()
    schedule_mock.assert_called_once()
    assert schedule_mock.call_args.kwargs["countdown"] == 5
    assert schedule_mock.call_args.kwargs["kwargs"] == {
        "revision_id": str(revision_id),
        "workspace_id": str(workspace_id),
    }


def test_process_github_event_opened_bypasses_coalesce():
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

    with patch("app.workers.github_tasks.settings.review_coalesce_seconds", 5):
        with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
            with patch(
                "app.workers.github_tasks.apply_pull_request_webhook_event",
                AsyncMock(return_value=result),
            ):
                with patch(
                    "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                    AsyncMock(return_value=job_id),
                ) as pipeline_mock:
                    with patch(
                        "app.workers.github_tasks.schedule_autostart_pipeline_for_revision.apply_async",
                    ) as schedule_mock:
                        with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                            github_tasks.process_github_event.run("d-auto")

    pipeline_mock.assert_awaited_once()
    schedule_mock.assert_not_called()
    enqueue_mock.assert_called_once_with(job_id)


def test_process_github_event_command_bypasses_coalesce():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    job_id = uuid.uuid4()
    delivery = _delivery(event_type="issue_comment")
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    intent = IssueCommentPipelineIntent(workspace_id=workspace_id, revision_id=revision_id)

    with patch("app.workers.github_tasks.settings.review_coalesce_seconds", 5):
        with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
            with patch(
                "app.workers.github_tasks.apply_issue_comment_webhook_event",
                AsyncMock(return_value=intent),
            ):
                with patch(
                    "app.workers.github_tasks.supersede_active_generations_for_revision",
                    AsyncMock(),
                ):
                    with patch(
                        "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                        AsyncMock(return_value=job_id),
                    ) as pipeline_mock:
                        with patch(
                            "app.workers.github_tasks.schedule_autostart_pipeline_for_revision.apply_async",
                        ) as schedule_mock:
                            with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                                github_tasks.process_github_event.run("d-auto")

    pipeline_mock.assert_awaited_once()
    schedule_mock.assert_not_called()
    enqueue_mock.assert_called_once_with(job_id)


def test_schedule_autostart_pipeline_for_revision_skips_stale_revision():
    revision_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    session = AsyncMock()

    with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
        with patch(
            "app.workers.github_tasks.is_authoritative_for_pull_request_head",
            AsyncMock(return_value=False),
        ):
            with patch(
                "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                AsyncMock(),
            ) as pipeline_mock:
                with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                    github_tasks.schedule_autostart_pipeline_for_revision.run(
                        str(revision_id),
                        str(workspace_id),
                    )

    pipeline_mock.assert_not_awaited()
    enqueue_mock.assert_not_called()


def test_apply_resolution_for_synchronize_skips_stale_revision():
    revision_id = uuid.uuid4()
    session = AsyncMock()

    with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
        with patch(
            "app.workers.github_tasks.is_authoritative_for_pull_request_head",
            AsyncMock(return_value=False),
        ):
            with patch(
                "app.workers.github_tasks.apply_resolution_status_for_synchronize",
                AsyncMock(),
            ) as resolution_mock:
                github_tasks.apply_resolution_for_synchronize.run(str(revision_id))

    resolution_mock.assert_not_awaited()


def test_apply_resolution_for_synchronize_skips_retry_on_permanent_not_found():
    revision_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    task = github_tasks.apply_resolution_for_synchronize
    with patch.object(task, "retry", side_effect=AssertionError("retry should not be called")):
        with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
            with patch(
                "app.workers.github_tasks.is_authoritative_for_pull_request_head",
                AsyncMock(return_value=True),
            ):
                task.run(str(revision_id))


def test_schedule_autostart_pipeline_for_revision_enqueues_when_authoritative():
    revision_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    job_id = uuid.uuid4()
    session = AsyncMock()

    with patch("app.workers.github_tasks.get_db_context", return_value=_db_context(session)):
        with patch(
            "app.workers.github_tasks.is_authoritative_for_pull_request_head",
            AsyncMock(return_value=True),
        ):
            with patch(
                "app.workers.github_tasks.maybe_enqueue_pipeline_for_revision",
                AsyncMock(return_value=job_id),
            ) as pipeline_mock:
                with patch("app.workers.github_tasks.enqueue_index_job") as enqueue_mock:
                    github_tasks.schedule_autostart_pipeline_for_revision.run(
                        str(revision_id),
                        str(workspace_id),
                    )

    pipeline_mock.assert_awaited_once()
    enqueue_mock.assert_called_once_with(job_id)
