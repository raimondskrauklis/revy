# Review engineering context P5 — Staging validation & closeout (execution)

Phase **P5** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: findings § Validation metrics, RCX-G9. **P5 only.**

**Goal:** Human gate — staging metrics + doc sync; program sign-off after dogfood PR.

## Decisions locked for P5

- Sign-off requires: `engineering_context_injected` > 0 on scoped runs, diff truncated % < 5%, omitted `.md` runs = 0 (post-cap), judge path includes locks on escalation PR if triggered.
- Use `--since` = RCX deploy timestamp on staging (not full history).
- Manual **contradict locks %** — operator reviews published findings on dogfood PR; 0% target.
- Staging metrics script rename deferred to post-program parking lot (keep `judge_json_contract_staging_metrics.py` for P5).

## Out of scope for P5

- RC4 `workspace_review_policy` DB
- Disposition helpers (RCX-G7)

---

## P5.1 — Validation memo stub

**What:** Create `REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md` — deploy status, metrics tables (pre-filled baseline from findings), sign-off row, **dogfood trigger steps:**

1. Deploy `feat/review-engineering-context` to staging (alembic `0029`).
2. Open/merge dogfood PR with `backend/**` changes.
3. Trigger review: workspace autostart **or** PR comment `@revy review`.
4. Confirm `revy/review` check completes on latest `head_sha`.
5. Run metrics script with `--since <deploy-iso>`.

**Files:** `docs/review-pipeline/review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md`

**Deliverable:** Memo exists with baseline row from 2026-07-29, trigger steps, empty post-deploy columns.

---

## P5.2 — Deploy + dogfood PR (human gate)

**What:** Execute trigger steps in validation memo.

**Deliverable (human gate):** At least one completed review run in `--since` window with `context_stats` populated.

---

## P5.3 — Fill metrics tables

**What:** Run staging script; record `context_stats` aggregates + review-context block; update validation memo + judge validation § Review context.

**Files:** `docs/review-pipeline/review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md`, `docs/review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md`

**Deliverable (non-gate):**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics --since <deploy-iso> --json'
```

---

## P5.4 — Doc sync

**What:** Update program README execution table (Done + sha); recovery checklist Track M row; general plan status; findings status; PRODUCT_PATTERNS planning-doc row.

| Doc | Change |
|-----|--------|
| [README.md](../README.md) | All phases Done + commit shas |
| [waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_EXECUTION.md) | Status column |
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Status: shipped |
| [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md) | Status: done |
| [../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](../../REVIEW_PIPELINE_RECOVERY_CHECKLIST.md) | Track M — RCX shipped |
| [../../REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Planning-doc inject row → **shipped** dogfood |

**Deliverable:**

```bash
grep -l "review-engineering-context" docs/review-pipeline/README.md docs/review-pipeline/REVIEW_PIPELINE_RECOVERY_CHECKLIST.md docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_engineering_context_manifest.py tests/unit/test_engineering_context_pack.py tests/unit/test_github_review.py tests/unit/test_github_finding_judge.py -q
```

**Human gate:** P5.2 + P5.3 + **P5.5** complete — operator sign-off in validation memo.

**Next:** none — program complete.

---

## P5.5 — Greptile-shaped issue comment (RQ7 G3+)

**Goal:** Rich revybot PR issue comment before dogfood sign-off — Greptile Summary parity (narrative + rationale + structured sections), not a one-line table.

**Baseline:** PR #60 — Greptile posted narrative + confidence rationale + security `<details>` + important-files table; revybot posted a short table because Moonshot formatter prompt says **short narrative** (`moonshot_review.ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT`).

**Locked shape (issue comment only — check run stays compact):**

1. **Narrative** — 2–4 sentences: what changed, main risk theme, merge readiness hint.
2. **Confidence score** — `N/5` plus **one sentence rationale** (why not higher/lower).
3. **Since last push** — G9 resolution prose when present.
4. **Files needing attention** — bullet list with paths.
5. **Findings** — severity table (`Severity | Category | Title | File`).
6. **`<details>` Security review** — open when any security-category finding is active.
7. **`<details>` Important files changed** — short overview table for top changed files (path + one-line note); cap rows like Greptile.
8. **Review metadata** `<details>` — head_sha, revision, Revy link (existing footer).

**Out of scope:** mermaid; expanding check-run `output.summary`.

---

### P5.5.1 — Moonshot system prompt

**What:** Replace “short narrative” in `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` with locked section list above; allow ~400–800 words narrative budget; keep “no JSON wrapper” + 12000 char cap.

**Files:** `backend/app/integrations/moonshot_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_moonshot_review.py -q
```

---

### P5.5.2 — Deterministic fallback parity

**What:** Extend `build_pr_review_comment_fallback` — confidence rationale line (template from active finding severities); optional security `<details>` when category is security; **Important files changed** table from active finding file paths + titles.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -q
```

---

### P5.5.3 — LLM user prompt context

**What:** Enrich `build_pr_review_comment` user prompt — pass file-level change hints (paths, severities, titles) so Moonshot narrative can reference important files without inventing paths.

**Files:** `backend/app/services/github_publish_formatter.py`

---

### P5.5.4 — Dogfood verify (human)

**What:** After deploy, confirm revybot issue comment on dogfood PR matches Greptile section depth (narrative + rationale + details blocks).

**Deliverable:** One line in `REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md` § Publish surface.
