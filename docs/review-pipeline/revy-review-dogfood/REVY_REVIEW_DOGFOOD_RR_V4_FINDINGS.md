# RR-V4 — Thread resolve mutation failures (findings)

**Date:** 2026-07-31  
**Trigger:** RR-W1 R5 dogfood on [PR #80](https://github.com/raimondskrauklis/revy/pull/80) — `--rr-v-gate` blocked on `RR-V4_thread_resolve_taxonomy` until App permission fix  
**Status:** **verified fixed** 2026-07-31 — Contents **Read and write** + rev 7+ `resolve_mutation_failed=0`; rev 10 latest publish clean.
**Authority:** [REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md](./REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md) · [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md)  
**Deploy boundary:** `deda3c9` (RR-W1 R1–R4)

---

## Summary

**DB closure works. GitHub threads stay open because the GitHub App lacks `Contents: Write`.**

Revy publish calls GraphQL `resolveReviewThread` with the **installation token** after findings are addressed in DB. Thread lookup succeeds (`thread_id_not_found=0`). Mutations fail → `resolve_mutation_failed` in manifest.

**Root cause (locked):** Revy GitHub App was configured with **Contents: Read** only. GitHub gates `resolveReviewThread` behind **Contents: Read and write** — `pull-requests: write` alone is insufficient ([gh-aw#35726](https://github.com/github/gh-aw/issues/35726), [Asymptote action docs](https://github.com/marketplace/actions/asymptote-security-scan)). Greptile/Bugbot resolve threads with App tokens that include **contents write**.

**Fix:** Upgrade App permission + accept on installation. **No PAT workaround required.**

---

## Evidence (PR #80 staging)

### Publish manifest

| Rev | `head_sha` | `resolve_mutation_failed` | `thread_id_not_found` |
|-----|------------|---------------------------|------------------------|
| 1 | `8f7f5e0` | 0 | 0 |
| 2–4 | `ee4668c`…`38dd7b4` | **2** each | 0 |
| 5 | `8aec926` | **4** | 0 |
| 6 | `114aecd` | **6** | 0 |
| 7 | `0cc1db3` | **0** | 0 |
| 8 | `7b99148` | **0** (`already_resolved=11`) | 0 |
| 10 | `b8a589e` | **0** | 0 |

### GitHub UI

- 11 Revy `revybot` review threads on PR #80 — **all unresolved** before permission fix (rev 6)
- After Contents **Read and write** (rev 7+): 14+ threads resolved; only **new active findings** stay open
- Operator PAT (`gh api graphql resolveReviewThread`) **succeeds** on same `PRRT_*` id → confirms code path + thread id are correct; **token permission** was the gap

### Code path (working as designed)

```text
flush_publish_surfaces
  → build_review_thread_index          ✓
  → _resolve_stale_inline_threads      ✓ finds PRRT_* 
  → resolve_review_thread (GraphQL)    ✗ without contents:write
```

---

## Fix (operator — do this on staging + production apps)

| Step | Action |
|------|--------|
| 1 | GitHub → **Developer settings → GitHub Apps** → `revy-staging` (and `revy` prod when ready) |
| 2 | **Repository permissions → Contents** → **Read and write** → **Save** |
| 3 | **Install App** → **Configure** → **Review requested permissions** → accept for `raimondskrauklis/revy` (+ customer repos) |
| 4 | Re-verify on PR #80: push empty commit **or** wait for next publish after permission accept |
| 5 | `DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.revy_review_dogfood_staging_validation --pr-number 80 --since … --rr-v-gate` → `RR-V4` **PASS** |

**Docs updated:** [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md) — Contents **Read and write** (was Read only).

**Code:** `github_api.resolve_review_thread` now surfaces GraphQL `errors[].message` in logs/manifest skip `error=` field.

---

## Gap catalog

| ID | Gap | Severity | Status |
|----|-----|----------|--------|
| **RR-DG12** | App missing `contents:write` for `resolveReviewThread` | **high** | **verified fixed** — Contents Read and write on staging app |

Supersedes prior RR-DG12 hypothesis (“App cannot resolve at all”) — installation token **can** resolve when **Contents: Write** is granted (same as Greptile).

---

## Re-verification pass criteria

| Check | Pass |
|-------|------|
| App installation shows `contents: write` | GitHub installation settings |
| Publish manifest `resolve_mutation_failed=0` on addressed cohort | staging DB |
| GitHub `reviewThreads.isResolved=true` for addressed fingerprints | GraphQL |
| `--rr-v-gate` `RR-V4_thread_resolve_taxonomy` | **PASS** (rev 10 latest publish) |

---

## References

- [GITHUB_APP_SETUP.md](../../utils/GITHUB_APP_SETUP.md) § Contents Write — inline thread resolve
- [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) — Greptile auto-resolves inline threads (GH-1v2)
- TenderPro RR-DG1 (same root cause class on `contents: read` app)
