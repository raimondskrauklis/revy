"""truncate all non-super-admin data — reset for fresh start."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "2026_09_20_2017_0036_truncate_all_non_super_admin_data"
down_revision = "2026_09_19_2200_0035_finding_group_claim_slot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Child tables (FKs to github_installations / workspaces / users)
    op.execute(
        sa.text(
            """
            TRUNCATE TABLE
                api_audit,
                impersonation_sessions,
                data_export_jobs,
                workspace_invitations,
                workspace_memberships,
                github_finding_judge_outcomes,
                github_code_chunks,
                github_findings,
                github_finding_groups,
                github_publish_jobs,
                github_index_jobs,
                github_llm_call_attempts,
                github_webhook_deliveries,
                github_pipeline_runs,
                github_pipeline_steps,
                github_pipeline_artifacts,
                github_review_runs,
                github_pull_requests,
                github_pull_request_revisions,
                github_pull_request_reviews,
                github_repositories,
                github_installations,
                workspace_model_policies,
                stripe_webhook_events,
                keycloak_webhook_deliveries,
                items,
                workspaces
            CASCADE
            """
        )
    )
    # Delete all non-super-admin users
    op.execute(
        sa.text(
            "DELETE FROM users WHERE platform_role IS DISTINCT FROM 'super_admin'"
        )
    )


def downgrade() -> None:
    """No downgrade — data cannot be restored."""
    pass