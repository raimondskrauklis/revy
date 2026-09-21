# Purge user / workspace data (Revy)

How to remove a user and their workspace + all downstream data from the staging DB. Run in pgAdmin connected to `revy-staging`.

**TL;DR:** Delete users → delete their workspaces (cascade all review data). Only super-admin survives.

---

## 1. Identify users and workspaces

```sql
SELECT id, email, full_name, platform_role FROM users;

SELECT w.id, w.slug, w.name, w.status,
       gi.github_installation_id, gi.account_login
FROM workspaces w
LEFT JOIN github_installations gi ON gi.workspace_id = w.id AND gi.status = 'active'
ORDER BY w.created_at;
```

Note the workspace IDs you want to delete and the super-admin ID (keep).

---

## 2. Remove users (FKs: workspace_memberships, workspace_invitations, api_audit)

`api_audit.actor_user_id` is `NOT NULL` — reassign to super-admin before deleting users.

```sql
-- 2a. Reassign audit log rows to super-admin
UPDATE api_audit
SET actor_user_id = (SELECT id FROM users WHERE platform_role = 'super_admin' LIMIT 1)
WHERE actor_user_id IN (
    SELECT id FROM users WHERE platform_role IS DISTINCT FROM 'super_admin'
);

UPDATE api_audit
SET impersonator_user_id = (SELECT id FROM users WHERE platform_role = 'super_admin' LIMIT 1)
WHERE impersonator_user_id IN (
    SELECT id FROM users WHERE platform_role IS DISTINCT FROM 'super_admin'
);

-- 2b. Delete invitations
DELETE FROM workspace_invitations
WHERE invited_by_user_id IN (
    SELECT id FROM users WHERE platform_role IS DISTINCT FROM 'super_admin'
);

-- 2c. Delete memberships
DELETE FROM workspace_memberships
WHERE user_id IN (
    SELECT id FROM users WHERE platform_role IS DISTINCT FROM 'super_admin'
);

-- 2d. Delete users
DELETE FROM users WHERE platform_role IS DISTINCT FROM 'super_admin';
```

---

## 3. Purge a workspace and all downstream data

**No CASCADE on FKs** — delete leaf tables first, working up to `workspaces`.

Replace `'<workspace_uuid>'` and `'<workspace_slug>'` with actual values from step 1.

```sql
BEGIN;

-- 3a. Pipeline / finding chain (leaf first)
DELETE FROM github_llm_call_attempts WHERE review_run_id IN (
    SELECT id FROM github_review_runs WHERE workspace_id = '<workspace_uuid>'
);
DELETE FROM github_pipeline_runs WHERE workspace_id = '<workspace_uuid>';
DELETE FROM github_publish_jobs WHERE workspace_id = '<workspace_uuid>';
DELETE FROM github_finding_judge_outcomes WHERE workspace_id = '<workspace_uuid>';
DELETE FROM github_findings WHERE workspace_id = '<workspace_uuid>';
DELETE FROM github_finding_groups WHERE workspace_id = '<workspace_uuid>';
DELETE FROM github_review_runs WHERE workspace_id = '<workspace_uuid>';

-- 3b. Code chunks → index jobs
DELETE FROM github_code_chunks WHERE index_job_id IN (
    SELECT id FROM github_index_jobs WHERE workspace_id = '<workspace_uuid>'
);
DELETE FROM github_index_jobs WHERE workspace_id = '<workspace_uuid>';

-- 3c. PR chain
DELETE FROM github_pull_request_revisions WHERE pull_request_id IN (
    SELECT id FROM github_pull_requests WHERE workspace_id = '<workspace_uuid>'
);
DELETE FROM github_pull_request_reviews WHERE pull_request_id IN (
    SELECT id FROM github_pull_requests WHERE workspace_id = '<workspace_uuid>'
);
DELETE FROM github_pull_requests WHERE workspace_id = '<workspace_uuid>';

-- 3d. Repos + installation
DELETE FROM github_repositories WHERE workspace_id = '<workspace_uuid>';
DELETE FROM github_installations WHERE workspace_id = '<workspace_uuid>';

-- 3e. Webhook deliveries (by installation_id from step 1)
DELETE FROM github_webhook_deliveries WHERE installation_id = <installation_id>;

-- 3f. Audit log + workspace
DELETE FROM api_audit WHERE workspace_id = '<workspace_uuid>';
DELETE FROM workspaces WHERE slug = '<workspace_slug>';

COMMIT;
```

---

## 4. Clean up empty duplicate workspaces (no members, no GitHub install)

```sql
DELETE FROM workspaces
WHERE id IN (
    SELECT w.id FROM workspaces w
    LEFT JOIN workspace_memberships wm ON wm.workspace_id = w.id
    LEFT JOIN github_installations gi ON gi.workspace_id = w.id
    WHERE wm.workspace_id IS NULL AND gi.workspace_id IS NULL
);
```

---

## 5. Keycloak

Delete the same users in the Keycloak admin console (`revy` realm) by email.