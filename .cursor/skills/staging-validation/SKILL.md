---
name: staging-validation
description: >-
  Create or update staging validation memos: deploy boundaries, dogfood push
  tables, pass criteria, sign-off — filled from real evidence (metrics scripts,
  staging DB, GitHub). Use when user asks to update validation, fill staging
  sign-off, create validation stub, or document dogfood results while tuning
  Revy or similar staging workflows.
---

# Staging validation

**When:** user asks to create/update/fill staging validation memo, record deploy boundary, sign off wave, or document dogfood push results.

**Config:** `.agent/manifest.json` → `validation` (scripts, memo paths, index doc).

**Templates (Revy):** `docs/review-pipeline/staging-validation/TEMPLATE_STAGING_VALIDATION.md` · index: [README.md](docs/review-pipeline/staging-validation/README.md).

**Pack (other repos):** `internal-docs/agent-workflow-pack/patterns/staging-validation/` + `overlays/revy/staging-validation.md` when `integrations.revy: true`.

**Rule:** Connect **real evidence** — never mark PASS without script output, SQL row, `head_sha`, or GitHub URL in Evidence column.

---

## 1. Locate or create memo

1. Read active program from `.agent/review-context.json` or user input.
2. Resolve memo path:
   - `manifest.validation.memo_pattern` with `{program_folder}`, `{PROGRAM}` substituted, or
   - `{docs_root}/{program_slug}/{PROGRAM_SLUG}_STAGING_VALIDATION.md`, or
   - user-provided path.
3. **Create stub** if missing — copy from `TEMPLATE_STAGING_VALIDATION.md`; link from program `README.md` and optional `validation.index_doc`.

---

## 2. Update on user demand (default action)

User says *update validation*, *fill table*, *record push N*, *sign off*:

### A. Deploy boundary (if new deploy)

1. Get deploy job completion ISO (`gh run list` / Actions / user paste).
2. Add row to **Deploy boundaries** table — do not replace prior rows.
3. Use this ISO for all `--since` flags in this pass.

### B. Run metrics scripts first

From `manifest.validation.metrics_scripts[]` — append `since_flag` and `json_flag` when present:

```bash
# example — adapt per manifest
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since <ISO> --json
```

Parse JSON stdout; cite values in Evidence column.

### C. GitHub / PR evidence

- `gh pr view <n> --json headRefOid,url,commits`
- Issue comment URLs for Revy publish output
- Check run conclusion

### D. Staging DB (when user has access)

Run SQL from runbook or execution doc; record `group_id`, `review_run_id`, `head_sha`, counts.

**Do not** run DB commands without user/env access — ask for paste or runbook output.

### E. Fill tables

| Table | Status values |
|-------|----------------|
| Pass criteria | `pending` \| `PASS` \| `FAIL` \| `PARTIAL` \| `skipped` |
| Dogfood pushes | `pending` \| `done` |
| Sign-off | `PASS` \| `FAIL` \| `pending` |

**Evidence column:** always — script line, SQL id, comment URL, or operator date note.

### F. Append, don't erase

- New wave / deploy → new subsection (e.g. `## Wave D`, `### Push 2`) or new pass table.
- Keep failed attempts (attempt 1, 2, …) for tuning history.

---

## 3. Root cause + next (on FAIL)

When sign-off is FAIL:

- Short **Root cause** table or bullets (hypothesis \| likelihood \| notes).
- **Next** options table (ID \| option \| verdict) when operator must choose path — see Revy FR-CS4 pattern.
- Link implementer handoff doc if execution plan defines one.

---

## 4. Index doc (optional)

Update `validation.index_doc` — active dogfood PR row, link to program memo.

---

## 5. Not in scope (unless asked)

- Opening dogfood PR (use `ship-changes`)
- Greptile babysit (off — do not invoke `babysit-pr`)
- Changing product code to fix validation failure (user directs separately)
- Inventing metrics without running script or user-provided output

---

## Verify before done

```text
[ ] Every PASS/FAIL row has Evidence
[ ] Deploy boundary ISO recorded for this pass
[ ] No pre-deploy runs counted as sign-off (if deploy boundary applies)
[ ] Program README links validation memo
[ ] Historical pass sections preserved
```

**Output:** summary of rows updated, commands run, gaps still pending.

---

## Create stub only

User says *create validation stub*:

1. Template → memo path
2. Wire findings + program links
3. Placeholder deploy boundary if known
4. Stop — do not fill PASS without evidence

---

## Integration

| Skill | When |
|-------|------|
| `create-execution-plan` | P0.1 subphase may create stub |
| `phase-execution` | Human gate may block until sign-off row PASS |
| `post-finish-gap-pass` | Compare memo sign-off vs shipped scope |
