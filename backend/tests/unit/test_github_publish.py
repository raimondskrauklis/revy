# backend/tests/unit/test_github_publish.py
"""GitHub publish service — R6.

Harness notes (GH-6):
- Autouse `_publish_formatter_defaults` mocks format, prior jobs, thread index, and resolve (unless `@pytest.mark.resolve_unmocked`).
- `resolve_unmocked` tests call real `_resolve_stale_inline_threads`; patch `github_api` GraphQL only.
- Prefer `_publish_job_context()` + targeted patches over ordered `session.scalars` side_effect chains.
- Build phase (`_build_publish_surface`) runs before flush; scalars order is groups → revision ids (×2) → inline findings → resolve queries.
- Inline posts persist partial `summary_json` via `session.flush` per comment (retry-safe); one `_checkpoint_publish_surface` after full flush.
"""
import uuid
from contextlib import nullcontext
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubAccountType,
    GitHubFindingGroupState,
    GitHubPublishJobStatus,
    GitHubPullRequestState,
    GitHubRepositoryStatus,
    GitHubReviewRunStatus,
    ResolutionStatus,
    ReviewProfile,
)
from app.core.exceptions import ServiceUnavailableError
from app.integrations import github_api
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_publish_job import GitHubPublishJobORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services import github_publish
from app.services.github_publish_formatter import PublishFormatResult


def _review_thread_index(
    mapping: dict[int, str] | None = None,
    *,
    outdated: frozenset[int] = frozenset(),
    resolved: frozenset[int] = frozenset(),
) -> github_api.ReviewThreadIndex:
    return github_api.ReviewThreadIndex(
        comment_to_thread_id=mapping or {},
        outdated_comment_ids=outdated,
        resolved_comment_ids=resolved,
    )


def _scalars_sequence(*items: object):
    """Scalars mock that returns fixed items then empty lists forever."""

    queue = list(items)

    def _next(*_args, **_kwargs):
        if queue:
            return queue.pop(0)
        return []

    return _next


@pytest.fixture(autouse=True)
def _publish_formatter_defaults(request):
    resolve_ctx = (
        patch(
            "app.services.github_publish._resolve_stale_inline_threads",
            AsyncMock(return_value=github_publish.empty_thread_resolve_skipped()),
        )
        if "resolve_unmocked" not in request.keywords
        else patch(
            "app.services.github_publish._resolve_stale_inline_threads",
            github_publish._resolve_stale_inline_threads,
        )
    )
    find_publish_ctx = (
        patch(
            "app.services.github_publish.find_publish_job_for_head_sha",
            AsyncMock(return_value=None),
        )
        if "find_publish_unmocked" not in request.keywords
        else nullcontext()
    )
    with find_publish_ctx:
        with patch(
            "app.services.github_publish.get_latest_completed_index_job",
            AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.github_publish.get_resolution_metrics_for_review_run",
                AsyncMock(return_value=None),
            ):
                with patch(
                    "app.services.github_publish._fetch_prior_completed_publish_jobs",
                    AsyncMock(return_value=[]),
                ):
                    with resolve_ctx:
                        with patch(
                            "app.services.github_publish.github_api.build_review_thread_index",
                            AsyncMock(return_value=_review_thread_index()),
                        ):
                            with patch(
                                "app.services.github_publish.build_publish_format_result_async",
                                AsyncMock(
                                    return_value=PublishFormatResult(
                                        check_summary="## Revy review\n\n**Confidence:** 5/5",
                                        issue_comment="## Revy code review\n\nfull narrative",
                                        confidence=5,
                                        summary_json={
                                            "confidence": 5,
                                            "active_count": 0,
                                            "resolution": {},
                                        },
                                    )
                                ),
                            ):
                                yield


def test_compute_check_conclusion_neutral_on_critical():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="x",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="bad",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    assert github_publish.compute_check_conclusion([group]) == "neutral"


def test_compute_check_conclusion_neutral_on_warnings_only():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="x",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Edge",
        message="note",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    assert github_publish.compute_check_conclusion([group]) == "neutral"


def test_build_summary_markdown_counts_active_findings_only():
    pull_request_id = uuid.uuid4()
    active = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="a",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="One",
        message="m",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    superseded = GitHubFindingGroupORM(
        workspace_id=active.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="b",
        state=GitHubFindingGroupState.superseded,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Old",
        message="m",
        file_path="b.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    markdown = github_publish.build_summary_markdown(
        pull_request_id=pull_request_id,
        groups=[active, superseded],
    )
    assert "of 1 findings" not in markdown
    assert "Old" not in markdown


def test_build_summary_markdown_escapes_pipe_in_cells():
    pull_request_id = uuid.uuid4()
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="pipe",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Bad | title",
        message="m",
        file_path="src/a|b.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    markdown = github_publish.build_summary_markdown(
        pull_request_id=pull_request_id,
        groups=[group],
    )
    assert "Bad \\| title" in markdown
    assert "src/a\\|b.py" in markdown
    assert "| Bad | title |" not in markdown


def test_inline_publish_findings_statement_filters_active_groups():
    review_run_id = uuid.uuid4()
    stmt = github_publish.inline_publish_findings_statement(review_run_id=review_run_id)
    sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "github_finding_groups" in sql
    assert GitHubFindingGroupState.active.value in sql


def test_inline_publish_findings_statement_includes_warning():
    review_run_id = uuid.uuid4()
    stmt = github_publish.inline_publish_findings_statement(review_run_id=review_run_id)
    sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert FindingSeverity.warning.value in sql
    assert FindingSeverity.info.value in sql


def test_compute_check_conclusion_success_when_no_active():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="x",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Old",
        message="fixed",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    assert github_publish.compute_check_conclusion([group]) == "success"


def test_load_inline_thread_map_keeps_latest_comment_id():
    older = MagicMock()
    older.summary_json = {"github_inline_threads": {"fp": 100}}
    newer = MagicMock()
    newer.summary_json = {"github_inline_threads": {"fp": 999}}
    assert github_publish._load_inline_thread_map([older, newer]) == {"fp": 999}


def test_deserialize_inline_thread_map_legacy_int():
    assert github_publish.deserialize_inline_thread_map({"fp": 100}) == {"fp": 100}


def test_deserialize_inline_thread_map_v2():
    raw = {"fp": {"comment_id": 200, "thread_id": "PRRT_x"}}
    assert github_publish.deserialize_inline_thread_map(raw) == {"fp": 200}


def test_serialize_inline_thread_map_emits_v2():
    result = github_publish.serialize_inline_thread_map({"fp": 100})
    assert result == {"fp": {"comment_id": 100}}


def test_serialize_inline_thread_map_preserves_thread_id_when_comment_unchanged():
    prior_v2 = {"fp": {"comment_id": 100, "thread_id": "PRRT_keep"}}
    result = github_publish.serialize_inline_thread_map({"fp": 100}, prior_v2=prior_v2)
    assert result == {"fp": {"comment_id": 100, "thread_id": "PRRT_keep"}}


def test_serialize_inline_thread_map_drops_stale_thread_id_when_comment_changes():
    prior_v2 = {"fp": {"comment_id": 99, "thread_id": "PRRT_stale"}}
    result = github_publish.serialize_inline_thread_map({"fp": 100}, prior_v2=prior_v2)
    assert result == {"fp": {"comment_id": 100}}


def test_load_inline_thread_map_reads_v2_entries():
    job = MagicMock()
    job.summary_json = {
        "github_inline_threads": {"fp": {"comment_id": 200, "thread_id": "PRRT_x"}},
    }
    assert github_publish._load_inline_thread_map([job]) == {"fp": 200}


@pytest.mark.asyncio
async def test_publishable_fingerprints_for_run():
    from app.models.github_finding import GitHubFindingORM

    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        id=group_id,
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-a",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Warn",
        message="fix",
        file_path="app/main.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        group_id=group_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Warn",
        message="fix",
        file_path="app/main.py",
        start_line=3,
    )

    session = AsyncMock()
    session.scalars = AsyncMock(side_effect=[[], [finding]])
    session.get = AsyncMock(return_value=group)

    result = await github_publish._publishable_fingerprints_for_run(
        session,
        review_run_id=review_run_id,
        pull_request_id=pull_request_id,
    )
    assert result == {"fp-a"}


def test_fingerprint_thread_ids_from_index():
    index = {100: "PRRT_a", 200: "PRRT_b"}
    comment_map = {"fp1": 100, "fp2": 300}
    assert github_publish._fingerprint_thread_ids_from_index(comment_map, index) == {
        "fp1": "PRRT_a",
    }


def test_serialize_inline_thread_map_with_thread_ids():
    result = github_publish.serialize_inline_thread_map(
        {"fp": 100},
        thread_ids={"fp": "PRRT_new"},
    )
    assert result == {"fp": {"comment_id": 100, "thread_id": "PRRT_new"}}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_uses_thread_index():
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    inline_threads = {"stale-fp": 1001}
    session = AsyncMock()
    session.scalars = AsyncMock(side_effect=[[], [], []])
    client = AsyncMock()
    list_mock = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.build_review_thread_index",
        list_mock,
    ):
        with patch(
            "app.services.github_publish.github_api.find_review_thread_id_for_comment",
            AsyncMock(),
        ) as find_mock:
            with patch(
                "app.services.github_publish.github_api.resolve_review_thread",
                AsyncMock(),
            ) as resolve_mock:
                await github_publish._resolve_stale_inline_threads(
                    client,
                    session=session,
                    review_run_id=review_run_id,
                    github_installation_id=12345,
                    owner="acme",
                    repo_name="demo",
                    pull_request_id=pull_request_id,
                    pull_number=7,
                    inline_threads=inline_threads,
                    auth_headers={"Authorization": "Bearer t"},
                    thread_index={1001: "PRRT_stale"},
                )
    list_mock.assert_not_awaited()
    find_mock.assert_not_awaited()
    resolve_mock.assert_awaited_once()
    assert inline_threads == {}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_falls_back_when_index_misses_comment():
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    inline_threads = {"stale-fp": 1001}
    session = AsyncMock()
    session.scalars = AsyncMock(side_effect=[[], [], []])
    client = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.find_review_thread_id_for_comment",
        AsyncMock(return_value="PRRT_stale"),
    ) as find_mock:
        with patch(
            "app.services.github_publish.github_api.resolve_review_thread",
            AsyncMock(),
        ) as resolve_mock:
            await github_publish._resolve_stale_inline_threads(
                client,
                session=session,
                review_run_id=review_run_id,
                github_installation_id=12345,
                owner="acme",
                repo_name="demo",
                pull_request_id=pull_request_id,
                pull_number=7,
                inline_threads=inline_threads,
                auth_headers={"Authorization": "Bearer t"},
                thread_index={9999: "PRRT_other"},
            )
    find_mock.assert_awaited_once()
    resolve_mock.assert_awaited_once()
    assert inline_threads == {}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_option_a():
    from app.models.github_finding import GitHubFindingORM

    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    inline_threads = {"stale-fp": 1001, "active-fp": 1002}
    group_id = uuid.uuid4()
    active_group = GitHubFindingGroupORM(
        id=group_id,
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="active-fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Active",
        message="still",
        file_path="app/main.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    active_finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        group_id=group_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Active",
        message="still",
        file_path="app/main.py",
        start_line=3,
    )
    session = AsyncMock()
    session.scalars = AsyncMock(side_effect=[[], [active_finding], [], []])
    session.get = AsyncMock(return_value=active_group)
    client = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.find_review_thread_id_for_comment",
        AsyncMock(return_value="PRRT_stale"),
    ) as find_mock:
        with patch(
            "app.services.github_publish.github_api.resolve_review_thread",
            AsyncMock(),
        ) as resolve_mock:
            await github_publish._resolve_stale_inline_threads(
                client,
                session=session,
                review_run_id=review_run_id,
                github_installation_id=12345,
                owner="acme",
                repo_name="demo",
                pull_request_id=pull_request_id,
                pull_number=7,
                inline_threads=inline_threads,
                auth_headers={"Authorization": "Bearer t"},
            )
    find_mock.assert_awaited_once_with(
        client,
        github_installation_id=12345,
        owner="acme",
        repo="demo",
        pull_number=7,
        comment_database_id=1001,
        auth_headers={"Authorization": "Bearer t"},
        thread_index=None,
    )
    resolve_mock.assert_awaited_once()
    assert inline_threads == {"active-fp": 1002}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_outdated_comment():
    from app.models.github_finding import GitHubFindingORM

    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    inline_threads = {"drift-fp": 1001, "active-fp": 1002}
    group_id = uuid.uuid4()
    active_group = GitHubFindingGroupORM(
        id=group_id,
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="active-fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Active",
        message="still",
        file_path="app/main.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    active_finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        group_id=group_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Active",
        message="still",
        file_path="app/main.py",
        start_line=3,
    )
    session = AsyncMock()
    session.scalars = AsyncMock(
        side_effect=[[], [active_finding], [], []],
    )
    session.get = AsyncMock(return_value=active_group)
    client = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.find_review_thread_id_for_comment",
        AsyncMock(return_value="PRRT_old"),
    ):
        with patch(
            "app.services.github_publish.github_api.resolve_review_thread",
            AsyncMock(),
        ) as resolve_mock:
            await github_publish._resolve_stale_inline_threads(
                client,
                session=session,
                review_run_id=review_run_id,
                github_installation_id=12345,
                owner="acme",
                repo_name="demo",
                pull_request_id=pull_request_id,
                pull_number=7,
                inline_threads=inline_threads,
                auth_headers={"Authorization": "Bearer t"},
                thread_index={1001: "PRRT_old"},
                outdated_comment_ids=frozenset({1001}),
            )
    resolve_mock.assert_awaited_once()
    assert inline_threads == {"active-fp": 1002}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_addressed_while_still_publishable():
    from app.models.github_finding import GitHubFindingORM

    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    inline_threads = {"addressed-fp": 1001}
    group_id = uuid.uuid4()
    addressed_group = GitHubFindingGroupORM(
        id=group_id,
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="addressed-fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Addressed",
        message="still reported",
        file_path="app/main.py",
        last_seen_revision_id=uuid.uuid4(),
        resolution_status=ResolutionStatus.addressed,
    )
    active_finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        group_id=group_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Addressed",
        message="still reported",
        file_path="app/main.py",
        start_line=3,
    )
    session = AsyncMock()
    session.scalars = AsyncMock(side_effect=[[], [active_finding], [addressed_group]])
    session.get = AsyncMock(return_value=addressed_group)
    client = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.find_review_thread_id_for_comment",
        AsyncMock(return_value="PRRT_addr"),
    ):
        with patch(
            "app.services.github_publish.github_api.resolve_review_thread",
            AsyncMock(),
        ) as resolve_mock:
            await github_publish._resolve_stale_inline_threads(
                client,
                session=session,
                review_run_id=review_run_id,
                github_installation_id=12345,
                owner="acme",
                repo_name="demo",
                pull_request_id=pull_request_id,
                pull_number=7,
                inline_threads=inline_threads,
                auth_headers={"Authorization": "Bearer t"},
            )
    resolve_mock.assert_awaited_once()
    assert inline_threads == {}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_pops_already_resolved_without_graphql():
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    inline_threads = {"done-fp": 1001}
    session = AsyncMock()
    session.scalars = AsyncMock(side_effect=[[], [], []])
    client = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.resolve_review_thread",
        AsyncMock(),
    ) as resolve_mock:
        await github_publish._resolve_stale_inline_threads(
            client,
            session=session,
            review_run_id=review_run_id,
            github_installation_id=12345,
            owner="acme",
            repo_name="demo",
            pull_request_id=pull_request_id,
            pull_number=7,
            inline_threads=inline_threads,
            auth_headers={"Authorization": "Bearer t"},
            resolved_comment_ids=frozenset({1001}),
        )
    resolve_mock.assert_not_awaited()
    assert inline_threads == {}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_counts_already_resolved():
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    inline_threads = {"done-fp": 1001}
    session = AsyncMock()
    session.scalars = AsyncMock(side_effect=[[], [], []])
    client = AsyncMock()

    skipped = await github_publish._resolve_stale_inline_threads(
        client,
        session=session,
        review_run_id=review_run_id,
        github_installation_id=12345,
        owner="acme",
        repo_name="demo",
        pull_request_id=pull_request_id,
        pull_number=7,
        inline_threads=inline_threads,
        auth_headers={"Authorization": "Bearer t"},
        resolved_comment_ids=frozenset({1001}),
    )

    assert skipped["already_resolved"] == 1
    assert inline_threads == {}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_counts_thread_id_not_found():
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    inline_threads = {"stale-fp": 1001}
    session = AsyncMock()
    stale_group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="stale-fp",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Stale",
        message="msg",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    session.scalars = AsyncMock(side_effect=[[stale_group], [], []])
    client = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.find_review_thread_id_for_comment",
        AsyncMock(return_value=None),
    ):
        skipped = await github_publish._resolve_stale_inline_threads(
            client,
            session=session,
            review_run_id=review_run_id,
            github_installation_id=12345,
            owner="acme",
            repo_name="demo",
            pull_request_id=pull_request_id,
            pull_number=7,
            inline_threads=inline_threads,
            auth_headers={"Authorization": "Bearer t"},
        )

    assert skipped["thread_id_not_found"] == 1
    assert inline_threads == {"stale-fp": 1001}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_retries_mutation_then_succeeds():
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    inline_threads = {"stale-fp": 1001}
    session = AsyncMock()
    stale_group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="stale-fp",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Stale",
        message="msg",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    session.scalars = AsyncMock(side_effect=[[stale_group], [], []])
    client = AsyncMock()
    resolve_mock = AsyncMock(
        side_effect=[ServiceUnavailableError(message="fail", error_code="github_api_error"), None],
    )
    with patch(
        "app.services.github_publish.github_api.resolve_review_thread",
        resolve_mock,
    ):
        skipped = await github_publish._resolve_stale_inline_threads(
            client,
            session=session,
            review_run_id=review_run_id,
            github_installation_id=12345,
            owner="acme",
            repo_name="demo",
            pull_request_id=pull_request_id,
            pull_number=7,
            inline_threads=inline_threads,
            auth_headers={"Authorization": "Bearer t"},
            thread_index={1001: "PRRT_stale"},
        )

    assert skipped["resolve_mutation_failed"] == 0
    assert resolve_mock.await_count == 2
    assert inline_threads == {}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_resolve_stale_inline_threads_counts_resolve_mutation_failed():
    review_run_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    inline_threads = {"stale-fp": 1001}
    session = AsyncMock()
    stale_group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="stale-fp",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Stale",
        message="msg",
        file_path="a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    session.scalars = AsyncMock(side_effect=[[stale_group], [], []])
    client = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.resolve_review_thread",
        AsyncMock(side_effect=ServiceUnavailableError(message="fail", error_code="github_api_error")),
    ):
        skipped = await github_publish._resolve_stale_inline_threads(
            client,
            session=session,
            review_run_id=review_run_id,
            github_installation_id=12345,
            owner="acme",
            repo_name="demo",
            pull_request_id=pull_request_id,
            pull_number=7,
            inline_threads=inline_threads,
            auth_headers={"Authorization": "Bearer t"},
            thread_index={1001: "PRRT_stale"},
        )

    assert skipped["resolve_mutation_failed"] == 1
    assert inline_threads == {"stale-fp": 1001}


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_run_publish_job_persists_thread_map_after_resolve_when_inline_skipped():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
        github_check_run_id=100,
        github_comment_id=200,
        inline_comments_posted=True,
    )
    job.id = publish_job_id
    job.summary_json = {
        "github_inline_threads": {"stale-fp": {"comment_id": 9001}},
    }

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    prior_job = MagicMock()
    prior_job.summary_json = {"github_inline_threads": {"stale-fp": {"comment_id": 9001}}}

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(side_effect=_scalars_sequence([], [revision_id], [], [], [], []))
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    with patch(
        "app.services.github_publish._fetch_prior_completed_publish_jobs",
        AsyncMock(return_value=[prior_job]),
    ):
        with patch(
            "app.services.github_publish.github_api.build_review_thread_index",
            AsyncMock(return_value=_review_thread_index({9001: "PRRT_stale"})),
        ):
            with patch(
                "app.services.github_publish.get_pipeline_run_for_review_run",
                AsyncMock(return_value=None),
            ):
                with patch(
                    "app.services.github_publish.github_api.installation_auth_headers",
                    AsyncMock(return_value={"Authorization": "Bearer t"}),
                ):
                    with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                        with patch(
                            "app.services.github_publish.github_api.update_issue_comment",
                            AsyncMock(),
                        ):
                            with patch(
                                "app.services.github_publish.github_api.resolve_review_thread",
                                AsyncMock(),
                            ):
                                result = await github_publish.run_publish_job(
                                    session,
                                    publish_job_id=publish_job_id,
                                    persist_github_surface=True,
                                )

    assert result.status == GitHubPublishJobStatus.completed
    assert result.summary_json is not None
    threads = result.summary_json.get("github_inline_threads")
    assert threads == {}
    assert "stale-fp" not in threads


@pytest.mark.asyncio
async def test_run_publish_job_creates_check_run():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(return_value=[])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=100)):
            with patch("app.services.github_publish.github_api.create_issue_comment", AsyncMock(return_value=200)):
                result = await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 100
    assert result.github_comment_id == 200


@pytest.mark.asyncio
async def test_run_publish_job_posts_formatted_issue_comment():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"
    formatted_comment = "## Revy code review\n\nfull narrative markdown"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(return_value=[])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    format_result = PublishFormatResult(
        check_summary="## Revy review\n\n**Confidence:** 5/5",
        issue_comment=formatted_comment,
        confidence=5,
        summary_json={"confidence": 5, "active_count": 0, "resolution": {}},
    )

    comment_mock = AsyncMock(return_value=200)
    with patch(
        "app.services.github_publish.build_publish_format_result_async",
        AsyncMock(return_value=format_result),
    ):
        with patch(
            "app.services.github_publish.github_api.installation_auth_headers",
            AsyncMock(return_value={"Authorization": "Bearer t"}),
        ):
            with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=100)):
                with patch(
                    "app.services.github_publish.github_api.create_issue_comment",
                    comment_mock,
                ):
                    await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    comment_mock.assert_awaited_once()
    assert comment_mock.await_args.kwargs["body"] == formatted_comment
    assert not comment_mock.await_args.kwargs["body"].startswith("{")


@pytest.mark.asyncio
async def test_run_publish_job_updates_linked_pipeline_check_run():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
        github_check_run_id=100,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(return_value=[])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    update_mock = AsyncMock()
    create_check_mock = AsyncMock()
    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch("app.services.github_publish.github_api.update_check_run", update_mock):
            with patch("app.services.github_publish.github_api.create_issue_comment", AsyncMock(return_value=200)):
                with patch("app.services.github_publish.github_api.create_check_run", create_check_mock):
                    result = await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 100
    update_mock.assert_awaited_once()
    assert update_mock.await_args.kwargs["check_run_id"] == 100
    create_check_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_publish_job_posts_inline_for_warning_finding():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
        github_check_run_id=100,
        github_comment_id=200,
        inline_comments_posted=False,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    finding = MagicMock()
    finding.file_path = "app/main.py"
    finding.start_line = 10
    finding.end_line = None
    finding.title = "Style"
    finding.message = "Prefer explicit return"
    finding.severity = FindingSeverity.warning
    finding.suggestion = "return True"
    finding.group_id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-warning",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Style",
        message="Prefer explicit return",
        file_path="app/main.py",
        last_seen_revision_id=revision_id,
    )
    group.id = finding.group_id

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation, group, group]
    )
    session.scalars = AsyncMock(side_effect=[[], [], [finding]])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    inline_mock = AsyncMock(return_value=9001)
    with patch(
        "app.services.github_publish._load_prior_inline_thread_map",
        AsyncMock(return_value={}),
    ):
        with patch(
            "app.services.github_publish._resolve_stale_inline_threads",
            AsyncMock(return_value=github_publish.empty_thread_resolve_skipped()),
        ):
            with patch(
                "app.services.github_publish.get_pipeline_run_for_review_run",
                AsyncMock(return_value=None),
            ):
                with patch(
                    "app.services.github_publish.github_api.installation_auth_headers",
                    AsyncMock(return_value={"Authorization": "Bearer t"}),
                ):
                    with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                        with patch("app.services.github_publish.github_api.update_issue_comment", AsyncMock()):
                            with patch(
                                "app.services.github_publish.github_api.create_pull_request_review_comment",
                                inline_mock,
                            ):
                                result = await github_publish.run_publish_job(
                                    session,
                                    publish_job_id=publish_job_id,
                                    persist_github_surface=True,
                                )

    assert result.status == GitHubPublishJobStatus.completed
    assert result.inline_comments_posted is True
    inline_mock.assert_awaited_once()
    body = inline_mock.await_args.kwargs["body"]
    assert "WARNING" in body
    assert "```suggestion" in body
    assert "return True" in body


@pytest.mark.asyncio
async def test_create_publish_job_for_review_run_reuses_pipeline_check_id():
    review_run_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=uuid.uuid4(),
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    pipeline_run = AsyncMock()
    pipeline_run.id = pipeline_run_id
    publish_job_id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[run, None])
    session.get = AsyncMock(return_value=revision)
    session.add = MagicMock(side_effect=lambda job: setattr(job, "id", publish_job_id))
    session.flush = AsyncMock()

    with patch(
        "app.services.github_publish.get_pipeline_run_for_review_run",
        AsyncMock(return_value=pipeline_run),
    ):
        with patch(
            "app.services.github_publish.link_publish_job_to_pipeline",
            AsyncMock(),
        ):
            with patch(
                "app.services.github_publish.resolve_pipeline_github_check_run_id",
                AsyncMock(return_value=42),
            ):
                job_id = await github_publish.create_publish_job_for_review_run(
                    session,
                    review_run_id=review_run_id,
                )

    assert job_id == publish_job_id
    added_job = session.add.call_args[0][0]
    assert added_job.github_check_run_id == 42


@pytest.mark.asyncio
async def test_run_publish_job_updates_existing_sha():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    existing = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.completed,
        github_check_run_id=50,
        github_comment_id=60,
        inline_comments_posted=True,
    )
    existing.id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(side_effect=_scalars_sequence([], []))
    session.scalar = AsyncMock(return_value=existing)
    session.flush = AsyncMock()

    update_mock = AsyncMock()
    comment_update_mock = AsyncMock()
    create_check_mock = AsyncMock()
    with patch(
        "app.services.github_publish.find_publish_job_for_head_sha",
        AsyncMock(return_value=existing),
    ):
        with patch(
            "app.services.github_publish.github_api.installation_auth_headers",
            AsyncMock(return_value={"Authorization": "Bearer t"}),
        ):
            with patch("app.services.github_publish.github_api.update_check_run", update_mock):
                with patch("app.services.github_publish.github_api.update_issue_comment", comment_update_mock):
                    with patch("app.services.github_publish.github_api.create_check_run", create_check_mock):
                        result = await github_publish.run_publish_job(session, publish_job_id=publish_job_id)

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 50
    update_mock.assert_awaited_once()
    create_check_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_publish_job_updates_prior_issue_comment_on_new_push():
    """R6-Q1: new head_sha reuses PR issue comment id from prior completed publish."""
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "def456"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
        github_check_run_id=100,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=2,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(return_value=[])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    comment_update_mock = AsyncMock()
    comment_create_mock = AsyncMock()
    with patch(
        "app.services.github_publish.find_prior_issue_comment_id_for_pull_request",
        AsyncMock(return_value=777),
    ):
        with patch(
            "app.services.github_publish.github_api.installation_auth_headers",
            AsyncMock(return_value={"Authorization": "Bearer t"}),
        ):
            with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                with patch(
                    "app.services.github_publish.github_api.update_issue_comment",
                    comment_update_mock,
                ):
                    with patch(
                        "app.services.github_publish.github_api.create_issue_comment",
                        comment_create_mock,
                    ):
                        result = await github_publish.run_publish_job(
                            session,
                            publish_job_id=publish_job_id,
                        )

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_comment_id == 777
    comment_update_mock.assert_awaited_once()
    assert comment_update_mock.await_args.kwargs["comment_id"] == 777
    comment_create_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_publish_job_posts_inline_when_prior_job_failed_before_inline():
    """R6-DEFER-01: Job B reuses Job A check run but posts inline when A never did."""
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    existing = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.failed,
        github_check_run_id=50,
        github_comment_id=60,
        inline_comments_posted=False,
    )
    existing.id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    finding = MagicMock()
    finding.file_path = "app/main.py"
    finding.start_line = 10
    finding.title = "Bug"
    finding.message = "Fix me"
    finding.severity = FindingSeverity.error
    finding.group_id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-error",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="Fix me",
        file_path="app/main.py",
        last_seen_revision_id=revision_id,
    )
    group.id = finding.group_id

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation, group, group]
    )
    session.scalars = AsyncMock(side_effect=_scalars_sequence([], [], [finding]))
    session.scalar = AsyncMock(side_effect=[uuid.uuid4(), None])
    session.flush = AsyncMock()

    inline_mock = AsyncMock(return_value=9002)
    create_check_mock = AsyncMock()
    with patch(
        "app.services.github_publish.find_prior_issue_comment_id_for_pull_request",
        AsyncMock(return_value=None),
    ):
        with patch(
            "app.services.github_publish.find_publish_job_for_head_sha",
            AsyncMock(return_value=existing),
        ):
            with patch(
                "app.services.github_publish.github_api.installation_auth_headers",
                AsyncMock(return_value={"Authorization": "Bearer t"}),
            ):
                with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                    with patch("app.services.github_publish.github_api.update_issue_comment", AsyncMock()):
                        with patch(
                            "app.services.github_publish.github_api.create_check_run",
                            create_check_mock,
                        ):
                            with patch(
                                "app.services.github_publish.github_api.create_pull_request_review_comment",
                                inline_mock,
                            ):
                                result = await github_publish.run_publish_job(
                                    session,
                                    publish_job_id=publish_job_id,
                                )

    create_check_mock.assert_not_awaited()

    assert result.status == GitHubPublishJobStatus.completed
    assert result.github_check_run_id == 50
    assert result.inline_comments_posted is True
    inline_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_publish_job_for_review_run_skips_when_pending_exists():
    review_run_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[run, uuid.uuid4()])

    result = await github_publish.create_publish_job_for_review_run(
        session,
        review_run_id=review_run_id,
    )

    assert result is None
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_publish_job_id_for_review_run_reuses_pending_job():
    review_run_id = uuid.uuid4()
    existing_job_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[run, uuid.uuid4(), existing_job_id])

    job_id, created = await github_publish.resolve_publish_job_id_for_review_run(
        session,
        review_run_id=review_run_id,
    )

    assert job_id == existing_job_id
    assert created is False
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_publish_job_returns_existing_pending_job():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    pending_job_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=uuid.uuid4(),
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    pending_job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha="abc",
        status=GitHubPublishJobStatus.pending,
    )
    pending_job.id = pending_job_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=pending_job_id)
    session.get = AsyncMock(side_effect=[run, revision, pending_job])

    with patch("app.services.github_publish.settings") as mock_settings:
        mock_settings.github_api_enabled = True
        with patch(
            "app.services.github_publish.ensure_revision_access",
            AsyncMock(),
        ):
            result = await github_publish.create_publish_job(
                session,
                workspace_id=workspace_id,
                repository_id=uuid.uuid4(),
                pull_request_id=uuid.uuid4(),
                revision_id=revision_id,
                review_run_id=review_run_id,
            )

    assert result.id == pending_job_id
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_run_publish_job_posts_inline_after_surface_checkpoint():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
        github_check_run_id=100,
        github_comment_id=200,
        inline_comments_posted=False,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    finding = MagicMock()
    finding.file_path = "app/main.py"
    finding.start_line = 10
    finding.title = "Bug"
    finding.message = "Fix me"
    finding.severity = FindingSeverity.error
    finding.group_id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-error-2",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="Fix me",
        file_path="app/main.py",
        last_seen_revision_id=revision_id,
    )
    group.id = finding.group_id

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation, group, group]
    )
    session.scalars = AsyncMock(side_effect=_scalars_sequence([finding], [], [], [finding]))
    session.scalar = AsyncMock(side_effect=[uuid.uuid4(), uuid.uuid4()])
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    inline_mock = AsyncMock(return_value=9003)
    with patch(
        "app.services.github_publish.find_publish_job_for_head_sha",
        AsyncMock(return_value=None),
    ):
        with patch(
            "app.services.github_publish.get_pipeline_run_for_review_run",
            AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.github_publish.github_api.installation_auth_headers",
                AsyncMock(return_value={"Authorization": "Bearer t"}),
            ):
                with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                    with patch("app.services.github_publish.github_api.update_issue_comment", AsyncMock()):
                        with patch(
                            "app.services.github_publish.github_api.create_pull_request_review_comment",
                            inline_mock,
                        ):
                            result = await github_publish.run_publish_job(
                                session,
                                publish_job_id=publish_job_id,
                                persist_github_surface=True,
                            )

    assert result.status == GitHubPublishJobStatus.completed
    assert result.inline_comments_posted is True
    inline_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_publish_job_resolves_superseded_threads_when_inline_already_posted():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
        github_check_run_id=100,
        github_comment_id=200,
        inline_comments_posted=True,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(return_value=[])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    resolve_mock = AsyncMock(return_value=github_publish.empty_thread_resolve_skipped())
    inline_mock = AsyncMock()
    with patch(
        "app.services.github_publish._resolve_stale_inline_threads",
        resolve_mock,
    ):
        with patch(
            "app.services.github_publish.get_pipeline_run_for_review_run",
            AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.github_publish.github_api.installation_auth_headers",
                AsyncMock(return_value={"Authorization": "Bearer t"}),
            ):
                with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                    with patch("app.services.github_publish.github_api.update_issue_comment", AsyncMock()):
                        with patch(
                            "app.services.github_publish.github_api.create_pull_request_review_comment",
                            inline_mock,
                        ):
                            result = await github_publish.run_publish_job(
                                session,
                                publish_job_id=publish_job_id,
                            )

    assert result.status == GitHubPublishJobStatus.completed
    resolve_mock.assert_awaited_once()
    inline_mock.assert_not_awaited()


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_run_publish_job_same_sha_re_publish_persists_thread_map():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "same-sha"

    existing_job = MagicMock()
    existing_job.id = uuid.uuid4()
    existing_job.github_check_run_id = 50
    existing_job.inline_comments_posted = True

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
        github_check_run_id=50,
        github_comment_id=200,
        inline_comments_posted=True,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )
    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )
    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )
    prior_job = MagicMock()
    prior_job.summary_json = {"github_inline_threads": {"gone-fp": {"comment_id": 7001}}}

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(side_effect=_scalars_sequence([], [revision_id], [], [], [], []))
    session.scalar = AsyncMock(return_value=existing_job)
    session.flush = AsyncMock()

    resolve_mock = AsyncMock()
    with patch(
        "app.services.github_publish._fetch_prior_completed_publish_jobs",
        AsyncMock(return_value=[prior_job]),
    ):
        with patch(
            "app.services.github_publish.github_api.build_review_thread_index",
            AsyncMock(return_value=_review_thread_index({7001: "PRRT_gone"})),
        ):
            with patch(
                "app.services.github_publish.github_api.resolve_review_thread",
                resolve_mock,
            ):
                with patch(
                    "app.services.github_publish.get_pipeline_run_for_review_run",
                    AsyncMock(return_value=None),
                ):
                    with patch(
                        "app.services.github_publish.github_api.installation_auth_headers",
                        AsyncMock(return_value={"Authorization": "Bearer t"}),
                    ):
                        with patch("app.services.github_publish.github_api.update_check_run", AsyncMock()):
                            with patch(
                                "app.services.github_publish.github_api.update_issue_comment",
                                AsyncMock(),
                            ):
                                result = await github_publish.run_publish_job(
                                    session,
                                    publish_job_id=publish_job_id,
                                    persist_github_surface=True,
                                )

    assert result.status == GitHubPublishJobStatus.completed
    assert result.summary_json["github_inline_threads"] == {}
    resolve_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_publish_job_inline_skipped_no_group(caplog):
    from app.models.github_finding import GitHubFindingORM

    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )
    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )
    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )
    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        group_id=None,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Orphan",
        message="no group",
        file_path="app/main.py",
        start_line=1,
    )
    finding.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation, None]
    )
    session.scalars = AsyncMock(side_effect=[[], [revision_id], [revision_id], [finding]])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    inline_mock = AsyncMock()
    with patch(
        "app.services.github_publish.get_pipeline_run_for_review_run",
        AsyncMock(return_value=None),
    ):
        with patch(
            "app.services.github_publish.github_api.installation_auth_headers",
            AsyncMock(return_value={"Authorization": "Bearer t"}),
        ):
            with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=1)):
                with patch("app.services.github_publish.github_api.create_issue_comment", AsyncMock(return_value=2)):
                    with patch(
                        "app.services.github_publish.github_api.create_pull_request_review_comment",
                        inline_mock,
                    ):
                        with caplog.at_level("WARNING"):
                            result = await github_publish.run_publish_job(
                                session,
                                publish_job_id=publish_job_id,
                            )

    assert result.status == GitHubPublishJobStatus.completed
    inline_mock.assert_not_awaited()
    assert "github_publish_inline_skipped_no_group" in caplog.text


@pytest.mark.resolve_unmocked
@pytest.mark.asyncio
async def test_run_publish_job_reactivates_inline_same_publish():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    group_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )
    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )
    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )
    group = GitHubFindingGroupORM(
        id=group_id,
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="return-fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Back",
        message="again",
        file_path="app/main.py",
        last_seen_revision_id=revision_id,
    )
    from app.models.github_finding import GitHubFindingORM

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        group_id=group_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Back",
        message="again",
        file_path="app/main.py",
        start_line=5,
    )

    prior_job = MagicMock()
    prior_job.summary_json = {"github_inline_threads": {"return-fp": {"comment_id": 8001}}}

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation, group, group, group]
    )
    session.scalars = AsyncMock(
        side_effect=[
            [],
            [revision_id],
            [revision_id],
            [finding],
            [],
            [finding],
            [],
        ]
    )
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    inline_mock = AsyncMock(return_value=8002)
    with patch(
        "app.services.github_publish._fetch_prior_completed_publish_jobs",
        AsyncMock(return_value=[prior_job]),
    ):
        with patch(
            "app.services.github_publish.github_api.build_review_thread_index",
            AsyncMock(return_value=_review_thread_index({8001: "PRRT_old"})),
        ):
            with patch(
                "app.services.github_publish.github_api.resolve_review_thread",
                AsyncMock(),
            ) as resolve_mock:
                with patch(
                    "app.services.github_publish._publishable_fingerprints_for_run",
                    AsyncMock(return_value={"return-fp"}),
                ):
                    with patch(
                        "app.services.github_publish.get_pipeline_run_for_review_run",
                        AsyncMock(return_value=None),
                    ):
                        with patch(
                            "app.services.github_publish.github_api.installation_auth_headers",
                            AsyncMock(return_value={"Authorization": "Bearer t"}),
                        ):
                            with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=1)):
                                with patch(
                                    "app.services.github_publish.github_api.create_issue_comment",
                                    AsyncMock(return_value=2),
                                ):
                                    with patch(
                                        "app.services.github_publish.github_api.create_pull_request_review_comment",
                                        inline_mock,
                                    ):
                                        result = await github_publish.run_publish_job(
                                            session,
                                            publish_job_id=publish_job_id,
                                        )

    assert result.status == GitHubPublishJobStatus.completed
    resolve_mock.assert_not_awaited()
    inline_mock.assert_awaited_once()
    threads = result.summary_json["github_inline_threads"]
    assert threads["return-fp"]["comment_id"] == 8002
    assert "thread_id" not in threads["return-fp"]


def _publish_job_context():
    publish_job_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    head_sha = "abc123"

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    job.id = publish_job_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha=head_sha,
    )

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[job, run, revision, pull_request, repository, installation]
    )
    session.scalars = AsyncMock(return_value=[])
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()

    return publish_job_id, session, job


@pytest.mark.asyncio
async def test_run_publish_job_marks_failed_on_permanent_error_when_persisting():
    publish_job_id, session, job = _publish_job_context()
    request = httpx.Request("POST", "https://api.github.com/check-runs")
    response = httpx.Response(400, request=request)
    error = httpx.HTTPStatusError("bad request", request=request, response=response)

    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch(
            "app.services.github_publish.github_api.create_check_run",
            AsyncMock(side_effect=error),
        ):
            result = await github_publish.run_publish_job(
                session,
                publish_job_id=publish_job_id,
                persist_github_surface=True,
            )

    assert result is job
    assert result.status == GitHubPublishJobStatus.failed
    assert result.error_message == "bad request"


@pytest.mark.asyncio
async def test_run_publish_job_raises_retryable_error_when_persisting():
    publish_job_id, session, job = _publish_job_context()
    request = httpx.Request("POST", "https://api.github.com/check-runs")
    response = httpx.Response(503, request=request)
    error = httpx.HTTPStatusError("unavailable", request=request, response=response)

    with patch(
        "app.services.github_publish.github_api.installation_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with patch(
            "app.services.github_publish.github_api.create_check_run",
            AsyncMock(side_effect=error),
        ):
            with pytest.raises(github_publish.PublishJobRetryableError):
                await github_publish.run_publish_job(
                    session,
                    publish_job_id=publish_job_id,
                    persist_github_surface=True,
                )

    assert job.status == GitHubPublishJobStatus.processing


@pytest.mark.asyncio
async def test_run_publish_job_head_gate_skipped_not_head():
    publish_job_id, session, job = _publish_job_context()
    job.head_sha = "old-sha"
    run = GitHubReviewRunORM(
        revision_id=job.revision_id,
        workspace_id=job.workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=uuid.uuid4(),
        revision_number=1,
        head_sha="old-sha",
    )
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha="new-sha",
        head_ref="feature",
        base_ref="main",
        revision_count=2,
    )
    session.get = AsyncMock(side_effect=[job, run, revision, pull_request])

    pipeline_run = MagicMock()
    pipeline_run.id = uuid.uuid4()

    with patch(
        "app.services.github_publish.get_pipeline_run_for_review_run",
        AsyncMock(return_value=pipeline_run),
    ):
        with patch(
            "app.services.github_publish.finalize_pipeline_github_check_neutral",
            AsyncMock(),
        ) as neutral_mock:
            with patch(
                "app.services.github_publish.github_api.create_pull_request_review_comment",
                AsyncMock(),
            ) as inline_mock:
                result = await github_publish.run_publish_job(
                    session,
                    publish_job_id=publish_job_id,
                )

    assert result.status == GitHubPublishJobStatus.skipped_not_head
    assert result.status != GitHubPublishJobStatus.processing
    inline_mock.assert_not_awaited()
    neutral_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_publish_job_skipped_superseded():
    publish_job_id, session, job = _publish_job_context()
    run = GitHubReviewRunORM(
        revision_id=job.revision_id,
        workspace_id=job.workspace_id,
        status=GitHubReviewRunStatus.superseded,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=uuid.uuid4(),
        revision_number=1,
        head_sha=job.head_sha,
    )
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=job.head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    session.get = AsyncMock(side_effect=[job, run, revision, pull_request])

    pipeline_run = MagicMock()
    pipeline_run.id = uuid.uuid4()

    with patch(
        "app.services.github_publish.get_pipeline_run_for_review_run",
        AsyncMock(return_value=pipeline_run),
    ):
        with patch(
            "app.services.github_publish.finalize_pipeline_github_check_neutral",
            AsyncMock(),
        ) as neutral_mock:
            result = await github_publish.run_publish_job(
                session,
                publish_job_id=publish_job_id,
            )

    assert result.status == GitHubPublishJobStatus.skipped_superseded
    neutral_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_publish_job_surface_flush_call_order():
    from app.models.github_finding import GitHubFindingORM

    publish_job_id, session, job = _publish_job_context()
    workspace_id = job.workspace_id
    review_run_id = job.review_run_id
    revision_id = job.revision_id
    pull_request_id = uuid.uuid4()
    group_id = uuid.uuid4()
    base_gets = [job, *list(session.get.side_effect)[1:]]

    group = GitHubFindingGroupORM(
        id=group_id,
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp-inline",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Warn",
        message="fix",
        file_path="app/main.py",
        last_seen_revision_id=revision_id,
    )
    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        group_id=group_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Warn",
        message="fix",
        file_path="app/main.py",
        start_line=3,
    )
    finding.id = uuid.uuid4()

    session.get = AsyncMock(side_effect=[*base_gets, group])
    session.scalars = AsyncMock(
        side_effect=[
            [],
            [revision_id],
            [revision_id],
            [finding],
        ]
    )

    call_order: list[str] = []

    def _track(name: str, return_value):
        async def _fn(*args, **kwargs):
            call_order.append(name)
            return return_value

        return _fn

    prior_job = MagicMock()
    prior_job.summary_json = {"github_inline_threads": {"stale-fp": 9001}}

    with patch(
        "app.services.github_publish._fetch_prior_completed_publish_jobs",
        AsyncMock(return_value=[prior_job]),
    ):
        with patch(
            "app.services.github_publish.get_pipeline_run_for_review_run",
            AsyncMock(return_value=None),
        ):
            with patch(
                "app.services.github_publish.github_api.build_review_thread_index",
                _track("index", _review_thread_index()),
            ):
                with patch(
                    "app.services.github_publish._resolve_stale_inline_threads",
                    _track("resolve", github_publish.empty_thread_resolve_skipped()),
                ):
                    with patch(
                        "app.services.github_publish.github_api.installation_auth_headers",
                        AsyncMock(return_value={"Authorization": "Bearer t"}),
                    ):
                        with patch(
                            "app.services.github_publish.github_api.create_check_run",
                            _track("check", 100),
                        ):
                            with patch(
                                "app.services.github_publish.github_api.create_issue_comment",
                                _track("issue", 200),
                            ):
                                with patch(
                                    "app.services.github_publish.github_api.create_pull_request_review_comment",
                                    _track("inline", 300),
                                ):
                                    await github_publish.run_publish_job(
                                        session,
                                        publish_job_id=publish_job_id,
                                    )

    assert call_order == ["index", "resolve", "check", "issue", "inline"]


@pytest.mark.asyncio
async def test_run_publish_job_persists_inline_progress_between_posts():
    """Partial inline thread map flushed per post so Celery retry does not duplicate."""
    from app.models.github_finding import GitHubFindingORM

    publish_job_id, session, job = _publish_job_context()
    workspace_id = job.workspace_id
    review_run_id = job.review_run_id
    revision_id = job.revision_id
    pull_request_id = uuid.uuid4()
    base_gets = [job, *list(session.get.side_effect)[1:]]

    groups_and_findings = []
    for idx, line in enumerate((3, 7), start=1):
        group_id = uuid.uuid4()
        group = GitHubFindingGroupORM(
            id=group_id,
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            fingerprint=f"fp-{idx}",
            state=GitHubFindingGroupState.active,
            severity=FindingSeverity.warning,
            category=FindingCategory.bug,
            title=f"Warn {idx}",
            message="fix",
            file_path="app/main.py",
            last_seen_revision_id=revision_id,
        )
        finding = GitHubFindingORM(
            review_run_id=review_run_id,
            workspace_id=workspace_id,
            group_id=group_id,
            severity=FindingSeverity.warning,
            category=FindingCategory.bug,
            title=f"Warn {idx}",
            message="fix",
            file_path="app/main.py",
            start_line=line,
        )
        finding.id = uuid.uuid4()
        groups_and_findings.append((group, finding))

    session.get = AsyncMock(
        side_effect=[*base_gets, groups_and_findings[0][0], groups_and_findings[1][0]]
    )
    session.scalars = AsyncMock(
        side_effect=[
            [],
            [revision_id],
            [revision_id],
            [groups_and_findings[0][1], groups_and_findings[1][1]],
        ]
    )
    flush_mock = AsyncMock()
    session.flush = flush_mock

    inline_calls = 0

    async def inline_post(*args, **kwargs):
        nonlocal inline_calls
        inline_calls += 1
        return 300 + inline_calls

    checkpoint_mock = AsyncMock()
    with patch(
        "app.services.github_publish.get_pipeline_run_for_review_run",
        AsyncMock(return_value=None),
    ):
        with patch(
            "app.services.github_publish._checkpoint_publish_surface",
            checkpoint_mock,
        ):
            with patch(
                "app.services.github_publish.github_api.installation_auth_headers",
                AsyncMock(return_value={"Authorization": "Bearer t"}),
            ):
                with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=100)):
                    with patch(
                        "app.services.github_publish.github_api.create_issue_comment",
                        AsyncMock(return_value=200),
                    ):
                        with patch(
                            "app.services.github_publish.github_api.create_pull_request_review_comment",
                            inline_post,
                        ):
                            await github_publish.run_publish_job(
                                session,
                                publish_job_id=publish_job_id,
                                persist_github_surface=True,
                            )

    assert inline_calls == 2
    assert flush_mock.await_count >= 2
    commit_mock = session.commit
    assert commit_mock.await_count >= 2
    checkpoint_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_publish_job_head_gate_skipped_not_head_after_build():
    publish_job_id, session, job = _publish_job_context()
    base_gets = list(session.get.side_effect)
    run = GitHubReviewRunORM(
        revision_id=job.revision_id,
        workspace_id=job.workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=job.head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    session.get = AsyncMock(
        side_effect=[
            job,
            run,
            GitHubPullRequestRevisionORM(
                pull_request_id=pull_request.id,
                revision_number=1,
                head_sha=job.head_sha,
            ),
            pull_request,
            base_gets[4],
            base_gets[5],
        ]
    )

    minimal_build = github_publish.PublishSurfaceBuild(
        check_summary="ok",
        issue_comment="ok",
        conclusion="success",
        summary_json={"confidence": 5},
        inline_threads={},
        prior_v2_inline={},
        inline_posts=[],
        post_inline=False,
        is_update_from_other=False,
        existing_github_check_run_id=None,
        existing_github_comment_id=None,
        existing_inline_comments_posted=False,
        external_id="ext",
        owner="acme",
        repo_name="demo",
    )

    async def refresh_side_effect(obj):
        if obj is pull_request:
            pull_request.head_sha = "new-sha-after-build"

    session.refresh = AsyncMock(side_effect=refresh_side_effect)

    pipeline_run = MagicMock()
    pipeline_run.id = uuid.uuid4()
    flush_mock = AsyncMock()

    with patch(
        "app.services.github_publish._build_publish_surface",
        AsyncMock(return_value=minimal_build),
    ):
        with patch("app.services.github_publish._flush_publish_surface", flush_mock):
            with patch(
                "app.services.github_publish.get_pipeline_run_for_review_run",
                AsyncMock(return_value=pipeline_run),
            ):
                with patch(
                    "app.services.github_publish.finalize_pipeline_github_check_neutral",
                    AsyncMock(),
                ) as neutral_mock:
                    result = await github_publish.run_publish_job(
                        session,
                        publish_job_id=publish_job_id,
                    )

    assert result.status == GitHubPublishJobStatus.skipped_not_head
    flush_mock.assert_not_awaited()
    neutral_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_publish_job_skipped_superseded_mid_flush_before_inline():
    publish_job_id, session, job = _publish_job_context()
    base_gets = list(session.get.side_effect)
    run = GitHubReviewRunORM(
        revision_id=job.revision_id,
        workspace_id=job.workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=job.head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    session.get = AsyncMock(
        side_effect=[
            job,
            run,
            GitHubPullRequestRevisionORM(
                pull_request_id=pull_request.id,
                revision_number=1,
                head_sha=job.head_sha,
            ),
            pull_request,
            base_gets[4],
            base_gets[5],
        ]
    )

    minimal_build = github_publish.PublishSurfaceBuild(
        check_summary="ok",
        issue_comment="ok",
        conclusion="success",
        summary_json={"confidence": 5},
        inline_threads={},
        prior_v2_inline={},
        inline_posts=[
            github_publish.InlinePostSpec(
                finding_id=uuid.uuid4(),
                group_id=uuid.uuid4(),
                group_fingerprint="fp-inline",
                file_path="app/main.py",
                start_line=3,
                title="Warn",
                message="fix",
                severity="warning",
                suggestion=None,
            )
        ],
        post_inline=True,
        is_update_from_other=False,
        existing_github_check_run_id=None,
        existing_github_comment_id=None,
        existing_inline_comments_posted=False,
        external_id="ext",
        owner="acme",
        repo_name="demo",
    )

    refresh_calls = 0

    async def refresh_side_effect(obj):
        nonlocal refresh_calls
        refresh_calls += 1
        if obj is run and refresh_calls >= 2:
            run.status = GitHubReviewRunStatus.superseded

    session.refresh = AsyncMock(side_effect=refresh_side_effect)

    pipeline_run = MagicMock()
    pipeline_run.id = uuid.uuid4()
    inline_mock = AsyncMock()

    with patch(
        "app.services.github_publish._build_publish_surface",
        AsyncMock(return_value=minimal_build),
    ):
        with patch(
            "app.services.github_publish.get_pipeline_run_for_review_run",
            AsyncMock(return_value=pipeline_run),
        ):
            with patch(
                "app.services.github_publish.finalize_pipeline_github_check_neutral",
                AsyncMock(),
            ):
                with patch(
                    "app.services.github_publish.github_api.installation_auth_headers",
                    AsyncMock(return_value={"Authorization": "Bearer t"}),
                ):
                    with patch("app.services.github_publish.github_api.create_check_run", AsyncMock(return_value=100)) as check_mock:
                        with patch(
                            "app.services.github_publish.github_api.create_issue_comment",
                            AsyncMock(return_value=200),
                        ) as comment_mock:
                            with patch(
                                "app.services.github_publish.github_api.create_pull_request_review_comment",
                                inline_mock,
                            ):
                                result = await github_publish.run_publish_job(
                                    session,
                                    publish_job_id=publish_job_id,
                                )

    assert result.status == GitHubPublishJobStatus.skipped_superseded
    check_mock.assert_not_awaited()
    comment_mock.assert_not_awaited()
    inline_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_publish_job_neutralizes_check_when_skipped_after_surface_writes():
    publish_job_id, session, job = _publish_job_context()
    base_gets = list(session.get.side_effect)
    run = GitHubReviewRunORM(
        revision_id=job.revision_id,
        workspace_id=job.workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=job.head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    session.get = AsyncMock(
        side_effect=[
            job,
            run,
            GitHubPullRequestRevisionORM(
                pull_request_id=pull_request.id,
                revision_number=1,
                head_sha=job.head_sha,
            ),
            pull_request,
            base_gets[4],
            base_gets[5],
        ]
    )

    minimal_build = github_publish.PublishSurfaceBuild(
        check_summary="ok",
        issue_comment="ok",
        conclusion="success",
        summary_json={"confidence": 5},
        inline_threads={},
        prior_v2_inline={},
        inline_posts=[],
        post_inline=False,
        is_update_from_other=False,
        existing_github_check_run_id=None,
        existing_github_comment_id=None,
        existing_inline_comments_posted=False,
        external_id="ext",
        owner="acme",
        repo_name="demo",
    )

    refresh_calls = 0

    async def refresh_side_effect(obj):
        nonlocal refresh_calls
        if obj is run:
            refresh_calls += 1
            if refresh_calls >= 5:
                run.status = GitHubReviewRunStatus.superseded

    session.refresh = AsyncMock(side_effect=refresh_side_effect)

    pipeline_run = MagicMock()
    pipeline_run.id = uuid.uuid4()
    create_check_mock = AsyncMock(return_value=100)
    neutral_check_mock = AsyncMock()
    neutral_comment_mock = AsyncMock()

    with patch(
        "app.services.github_publish._build_publish_surface",
        AsyncMock(return_value=minimal_build),
    ):
        with patch(
            "app.services.github_publish.get_pipeline_run_for_review_run",
            AsyncMock(return_value=pipeline_run),
        ):
            with patch(
                "app.services.github_publish.finalize_pipeline_github_check_neutral",
                AsyncMock(),
            ):
                with patch(
                    "app.services.github_publish.github_api.installation_auth_headers",
                    AsyncMock(return_value={"Authorization": "Bearer t"}),
                ):
                    with patch(
                        "app.services.github_publish.github_api.create_check_run",
                        create_check_mock,
                    ):
                        with patch(
                            "app.services.github_publish.github_api.create_issue_comment",
                            AsyncMock(return_value=200),
                        ):
                            with patch(
                                "app.services.github_publish.github_api.update_check_run",
                                neutral_check_mock,
                            ):
                                with patch(
                                    "app.services.github_publish.github_api.update_issue_comment",
                                    neutral_comment_mock,
                                ):
                                    result = await github_publish.run_publish_job(
                                        session,
                                        publish_job_id=publish_job_id,
                                    )

    assert result.status == GitHubPublishJobStatus.skipped_superseded
    create_check_mock.assert_awaited_once()
    neutral_check_mock.assert_awaited_once()
    assert neutral_check_mock.await_args.kwargs["conclusion"] == "neutral"
    neutral_comment_mock.assert_awaited_once()
    assert neutral_comment_mock.await_args.kwargs["body"] == github_publish._SKIP_PUBLISH_NEUTRAL_SUMMARY


@pytest.mark.asyncio
async def test_run_publish_job_returns_skip_when_neutralize_fails():
    publish_job_id, session, job = _publish_job_context()
    base_gets = list(session.get.side_effect)
    run = GitHubReviewRunORM(
        revision_id=job.revision_id,
        workspace_id=job.workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha=job.head_sha,
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    session.get = AsyncMock(
        side_effect=[
            job,
            run,
            GitHubPullRequestRevisionORM(
                pull_request_id=pull_request.id,
                revision_number=1,
                head_sha=job.head_sha,
            ),
            pull_request,
            base_gets[4],
            base_gets[5],
        ]
    )

    minimal_build = github_publish.PublishSurfaceBuild(
        check_summary="ok",
        issue_comment="ok",
        conclusion="success",
        summary_json={"confidence": 5},
        inline_threads={},
        prior_v2_inline={},
        inline_posts=[],
        post_inline=False,
        is_update_from_other=False,
        existing_github_check_run_id=None,
        existing_github_comment_id=None,
        existing_inline_comments_posted=False,
        external_id="ext",
        owner="acme",
        repo_name="demo",
    )

    refresh_calls = 0

    async def refresh_side_effect(obj):
        nonlocal refresh_calls
        if obj is run:
            refresh_calls += 1
            if refresh_calls >= 5:
                run.status = GitHubReviewRunStatus.superseded

    session.refresh = AsyncMock(side_effect=refresh_side_effect)

    pipeline_run = MagicMock()
    pipeline_run.id = uuid.uuid4()
    create_check_mock = AsyncMock(return_value=100)
    neutral_check_mock = AsyncMock(side_effect=httpx.HTTPError("neutralize failed"))

    with patch(
        "app.services.github_publish._build_publish_surface",
        AsyncMock(return_value=minimal_build),
    ):
        with patch(
            "app.services.github_publish.get_pipeline_run_for_review_run",
            AsyncMock(return_value=pipeline_run),
        ):
            with patch(
                "app.services.github_publish.finalize_pipeline_github_check_neutral",
                AsyncMock(),
            ):
                with patch(
                    "app.services.github_publish.github_api.installation_auth_headers",
                    AsyncMock(return_value={"Authorization": "Bearer t"}),
                ):
                    with patch(
                        "app.services.github_publish.github_api.create_check_run",
                        create_check_mock,
                    ):
                        with patch(
                            "app.services.github_publish.github_api.create_issue_comment",
                            AsyncMock(return_value=200),
                        ):
                            with patch(
                                "app.services.github_publish.github_api.update_check_run",
                                neutral_check_mock,
                            ):
                                result = await github_publish.run_publish_job(
                                    session,
                                    publish_job_id=publish_job_id,
                                )

    assert result.status == GitHubPublishJobStatus.skipped_superseded
    create_check_mock.assert_awaited_once()
    neutral_check_mock.assert_awaited_once()


@pytest.mark.find_publish_unmocked
@pytest.mark.asyncio
async def test_find_publish_job_for_head_sha_completed_only():
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    skipped_job = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=revision_id,
        workspace_id=uuid.uuid4(),
        head_sha="abc123",
        status=GitHubPublishJobStatus.skipped_not_head,
        github_check_run_id=100,
    )
    completed_job = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=revision_id,
        workspace_id=uuid.uuid4(),
        head_sha="abc123",
        status=GitHubPublishJobStatus.completed,
        github_check_run_id=200,
    )
    session = AsyncMock()
    session.scalars = AsyncMock(return_value=[revision_id])
    session.scalar = AsyncMock(return_value=completed_job)

    result = await github_publish.find_publish_job_for_head_sha(
        session,
        pull_request_id=pull_request_id,
        head_sha="abc123",
    )

    assert result is completed_job
    assert result is not skipped_job


@pytest.mark.asyncio
async def test_create_publish_job_for_review_run_skips_non_completed_superseded():
    """Superseded runs are not completed — create_publish_job returns None via status gate."""
    review_run_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.superseded,
        profile=ReviewProfile.standard,
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=run)

    job_id = await github_publish.create_publish_job_for_review_run(
        session,
        review_run_id=review_run_id,
    )

    assert job_id is None


@pytest.mark.asyncio
async def test_create_publish_job_for_review_run_after_skipped_not_head():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
    )
    run.id = review_run_id
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=uuid.uuid4(),
        revision_number=1,
        head_sha="same-sha",
    )
    revision.id = revision_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[run, None])
    session.get = AsyncMock(return_value=revision)
    session.add = MagicMock()
    new_job_id = uuid.uuid4()

    async def _flush_assign_id() -> None:
        added = session.add.call_args.args[0]
        added.id = new_job_id

    session.flush = AsyncMock(side_effect=_flush_assign_id)

    with patch(
        "app.services.github_publish.get_pipeline_run_for_review_run",
        AsyncMock(return_value=None),
    ):
        job_id = await github_publish.create_publish_job_for_review_run(
            session,
            review_run_id=review_run_id,
        )

    assert job_id == new_job_id
