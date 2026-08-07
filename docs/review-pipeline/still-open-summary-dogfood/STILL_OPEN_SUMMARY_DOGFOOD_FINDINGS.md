# Still-open summary vs inline collapse — findings

**Date:** 2026-08-07  
**Purpose:** Baseline for **block-2 / verdict drift** when all GitHub inline threads are collapsed but `### Still open on PR` still lists rows. **No execution steps.**

**Trigger:** kp-platform [#489](https://github.com/raimondskrauklis/kp-platform/pull/489) rev 12 — issue comment lists **7** still-open rows; footer `Thread resolve skipped: 18 (already_resolved: 18)`; all inline threads collapsed on GitHub. Same class as [#485](https://github.com/raimondskrauklis/kp-platform/pull/485).

**Evidence:** Staging DB (`revy-staging`) via `revy_review_dogfood_staging_validation.py`; [#489](https://github.com/raimondskrauklis/kp-platform/pull/489#issuecomment-5215109464) (pre-deploy repro); [#491](https://github.com/raimondskrauklis/kp-platform/pull/491#issuecomment-5222157966) (post-deploy validation). [PR #83](https://github.com/raimondskrauklis/revy/pull/83) merged `2026-08-07T21:09:35Z` (`a5bb273`).

---

## Build principles

1. **One honest story** — inline thread state, block 2, merge/confidence, and G9 must not contradict (PSA thesis).
2. **No ad-hoc table hacks** — fix the collapse → summary contract; do not fork markdown builders.
3. **Staging truth** — verify deploy SHA + `summary_json` fields on **post-#83** PRs; unit tests alone did not catch the original bug.
4. **Fix forward** — improve current `github_publish*` when dogfood proves drift; **no backfill** for PRs that published on pre-#83 workers.
5. **DB vs surface** — Option-A `still_open` rows may stay `active` in DB; summary alignment via `collapsed_inline_fingerprints` is acceptable; silent wrong rows on **new** publishes are not.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Block 2** | `### Still open on PR` table (`format_summary_comment`) |
| **Collapsed fingerprint** | Fingerprint whose inline thread was collapsed (GH-1v2) and should be omitted from block 2 when not generation-publishable |
| **`collapsed_inline_fingerprints`** | Persisted list on `github_publish_jobs.summary_json` — cross-revision memory of collapses |
| **`already_resolved` skip** | Pre-#83 path: thread already resolved on GitHub → increment skip counter, **do not** record collapse |
| **`closed_fingerprints`** | Post-#83 path: same GitHub state → treat as collapse for summary + persistence |

---

## Symptom (kp-platform #489 rev 12) — **historical / pre-deploy only**

> **Out of scope (SOS-D4):** #489 ran entirely before #83 deploy. Stale block 2 is expected; we do not backfill or re-publish to repair legacy PRs.

| Surface | Observed |
|---------|----------|
| GitHub inline threads | All collapsed (author sees no open review threads) |
| Issue comment block 2 | **7 rows** (falsy-threshold ×3, N06 import/cap, N01/N03 truncation ×2) |
| Narrative | “**7** findings remain open on PR #489” |
| G9 / resolution metrics | “1 issue fixed since last push” — 100% (1/1 prior active) |
| Footer | `Thread resolve skipped: 18 (already_resolved: 18)` |
| `summary_json` (staging) | `collapsed_inline_fingerprints`: **null**; `pr_active_count`: **7**; `generation_active_count`: **0** |

---

## DB evidence (staging, 2026-08-07)

Queried `revy-staging` for `raimondskrauklis/kp-platform` PR **489**.

### Finding groups

| Metric | Value |
|--------|-------|
| Total groups | 21 |
| `state=resolved` | 12 (mostly `judge_dismissed` / `absent_and_addressed`) |
| `state=active` | **7** — all `resolution_status=still_open` |
| Active ever in `github_inline_threads` | **7/7** |

Active fingerprints (all `still_open`, all had inline threads historically):

| Severity | File | Title (abbrev) |
|----------|------|----------------|
| warning | `_shared_official_overlap.py` | Falsy threshold |
| warning | `n01_ownership_overlap.py` | Falsy threshold |
| warning | `n03_shared_beneficial_owner.py` | Falsy threshold |
| warning | `n06_co_participation.py` | Runtime sqlalchemy import |
| info | `n06_co_participation.py` | Magic-number evidence cap |
| info | `n01_ownership_overlap.py` | Nondeterministic truncation |
| info | `n03_shared_beneficial_owner.py` | Nondeterministic truncation |

### Publish jobs (completed)

| Revision | `already_resolved` skips | `collapsed_inline_fingerprints` |
|----------|---------------------------|--------------------------------|
| 1 | 0 | 0 |
| 2 | 0 | 0 |
| 3 | 1 | 0 |
| 4 | 5 | 0 |
| 5 | 7 | 0 |
| 6 | 11 | 0 |
| 8–11 | 11 → 17 | 0 |
| **12** | **18** | **0** |

Latest publish: rev **12**, `head_sha` `06c7dfc5…`, `github_inline_threads` map **empty** (all fingerprints popped), `findings in rev12 run`: **0**.

### Reconcile (selected)

| Revision | `transitions_addressed` | `denominator_active_prior` |
|----------|-------------------------|----------------------------|
| 5 (falsy-threshold fix) | 3 | 3 |
| 10 (N06 import/cap fix) | 2 | 4 |
| 11 | 2 | 2 |
| 12 | 1 | 1 |

Despite multiple addressed transitions across the PR, **7 groups remain `active` + `still_open`** in DB at HEAD.

---

## Post-#83 validation — kp-platform #491 (2026-08-07)

**PR opened after deploy:** [#491](https://github.com/raimondskrauklis/kp-platform/pull/491) created `2026-08-07T21:20:12Z` (~11 min after #83 merge). Docs-only PR; rev 1–3 tracked below.

### Rev 1 → rev 2 lifecycle

| Surface | Rev 1 | Rev 2 (fix push) |
|---------|-------|------------------|
| Generation findings | 3 | 2 (new doc nits) |
| `resolution_pass` | — | 2 addressed / 3 prior active (66.7%) |
| `collapsed_inline_fingerprints` | **0** | **2** (fixed NETWORK plan fingerprints) |
| `already_resolved` skips | **0** | **0** |
| `thread_resolve_skipped` footer | absent | absent |
| Block 2 rows | 3 (all rev-1 findings) | **3** — 1 prior `still_open` + 2 new generation |
| Narrative “remain open” | — | **3** (matches block 2 + `pr_active_count`) |
| DB `state=resolved` | 0 | **2** (`absent_and_addressed`) |
| DB `active` | 3 | **3** (1 `still_open` + 2 new) |

### Alignment check (rev 2) — **PASS (forward path)**

| Check | Expected (post-#83) | Observed |
|-------|---------------------|----------|
| Fixed rev-1 items omitted from block 2 | 2 NETWORK plan rows gone | **PASS** — only `still_open` NETWORK row remains |
| `collapsed_inline_fingerprints` persisted | ≥ 2 after fix push | **PASS** — `35d7a39a…`, `84ca9ffc…` |
| `already_resolved` skip counter | 0 | **PASS** — both publishes |
| G9 / resolution metrics | 2 closed, 1 still open | **PASS** — matches reconcile manifest |
| Inline threads on GitHub | 2 open (new gen) + 2 collapsed (fixed) | **PASS** — 4 total comments; 2 rev-1 NETWORK threads collapsed; 2 rev-2 threads open |
| Block 2 vs open inline count | block 2 ≥ open inline (FR-Q7 double-block OK) | **PASS** — 3 block-2 rows vs 2 open inline (1 `still_open` has no open thread) |

**Verdict:** PR #83 **forward path works** on rev 1→2 fix push.

### Rev 3 — clean generation, all inline collapsed (2026-08-08 check)

**Push:** `63f09519` — fix duplicated markdown paths / stray backtick. **No new publishable findings.**

| Surface | Rev 3 observed |
|---------|----------------|
| `### This generation` | “No publishable findings this generation” |
| Block 2 | **1 row** — `bdcf4d58…` “Corpus sync prose…” on `NETWORK_CALCULATOR_GENERAL_PLAN.md` |
| GitHub inline | **4 comments, all threads collapsed** — none expanded |
| Open inline for block-2 row | **None** — `bdcf4d58` **never** in `github_inline_threads` on any rev |
| `collapsed_inline_fingerprints` | **4** — includes `f9e730db…` (INDICATOR; thread collapsed, hidden from block 2) |
| `pr_active_count` / `active_count` | **1** (filtered; 2 raw `active` in DB) |
| G9 | “1 issue fixed since last push; **1 still open from prior review**” |
| Resolution block | 50.0% (1/2 prior active); closed 1; still open 1 |
| Confidence | **4/5** — “some active findings remain” |
| `already_resolved` skips | **0** |

#### DB detail (rev 3 HEAD)

| Fingerprint | `state` | `resolution_status` | Inline ever? | In block 2? |
|-------------|---------|---------------------|--------------|-------------|
| `bdcf4d58…` | active | `still_open` | **No** — reported rev 1 only; `last_seen_rev=1` | **Yes** |
| `f9e730db…` | active | `still_open` | Yes — collapsed rev 3 | **No** (in `collapsed_inline_fingerprints`) |
| `33e4fe7b…` | resolved | `addressed` | Yes — collapsed | No |
| `35d7a39a…`, `84ca9ffc…` | resolved | `judge_dismissed` / addressed | Yes — collapsed rev 2 | No |

#### Metrics audit — **internally consistent**

| Metric | Source | Matches block 2 / UX? |
|--------|--------|------------------------|
| Reconcile `denominator_active_prior=2` | Pass 1 pairing on rev 3 | Prior actives at push: `f9e730db` + `33e4fe7b` (or pairing cohort) |
| `transitions_addressed=1` | CALCULATION-ENGINES `33e4fe7b` → `resolved` | G9 “1 fixed” ✓ |
| `still_open_count=1` | Reconcile manifest | G9 “1 still open” = `bdcf4d58` ✓ |
| `pr_active_count=1` | After `filter_pr_active_groups_for_summary` | Block 2 **1 row** ✓ |
| Confidence 4/5 | 1 filtered active warning | Narrative “1 finding remain open” ✓ |

**Metrics are not wrong** — they faithfully reflect DB + reconcile. The UX gap is **block 2 + metrics warn about a finding the author cannot see on the diff** (no inline anchor).

#### Verdict rev 3 — **SOS-5 (new P1 gap)**

| Check | Result |
|-------|--------|
| Collapse path for inlined findings | **PASS** — INDICATOR thread collapsed; omitted from block 2 |
| Clean generation | **PASS** |
| Orphan block-2 row | **FAIL (product)** — `still_open` + **never inlined** + all visible threads collapsed → author sees warning with no comment |
| Metrics vs visible threads | **Misleading UX** — numerically correct, experientially wrong |

---

### Open items on #491 (updated)

| Item | Notes |
|------|-------|
| **SOS-5** orphan block-2 row | `bdcf4d58` — rev 3; never inlined; `last_seen_rev=1`; block 2 + G9 still warn |
| `f9e730db` DB vs surface | `active`+`still_open` in DB but hidden from block 2 via collapse filter — Option-A + #83 working |
| Generation rows in both blocks | FR-Q7 by design (N/A on rev 3 clean gen) |

---

## Program scope (operator lock)

| In scope | Out of scope |
|----------|----------------|
| Post-#83 PRs (#491+) — fix push → collapse → block 2 | Pre-#83 PRs (#489) — no backfill, no reconstruction |
| Targeted code fixes when dogfood proves drift | Alembic / manual DB edits |
| Unit tests for each proven bug | Reconcile Pass 1 rule changes (→ finding-resolution) |

---

## What exists vs genuinely new

### Shipped (PR #83 — **deployed to staging** 2026-08-07)

| Capability | Location | Notes |
|------------|----------|-------|
| `filter_pr_active_groups_for_summary` | `github_publish_formatter.py:390–417` | Drops `addressed` + collapsed-not-publishable |
| `collapsed_inline_fingerprints` persistence | `github_publish.py:76`, `1914–1918` | Merge prior + flush collapses into `summary_json` |
| `already_resolved` → `closed_fingerprints` | `github_publish.py:891–893` | No skip counter; test `test_resolve_stale_inline_threads_syncs_already_resolved_without_skip` |
| Flush-time summary rebuild | `apply_publish_summary_thread_collapse` `github_publish_formatter.py:545–582` | Re-splices block 2 + verdict sections |
| Build uses `prior_collapsed` only | `_build_publish_surface` `github_publish.py:1398–1407` | Does not optimistically pre-collapse |

### Pre-#83 staging worker (verified via #489 `summary_json`)

| Behavior | Evidence |
|----------|----------|
| `already_resolved` **skip counter** increments | rev 3→12: 1→18; footer on issue comment |
| `collapsed_inline_fingerprints` **never written** | 0 on all 11 completed publishes |
| Block 2 uses raw `active` + `still_open` groups | 7 rows match DB exactly |

**Conclusion:** #489 = **pre-#83** worker only. Kept as root-cause evidence; not a repair target (SOS-D4).

### Post-#83 staging worker (verified via #491 `summary_json`)

| Behavior | Evidence |
|----------|----------|
| `collapsed_inline_fingerprints` **written on fix push** | rev 2: 2 fingerprints |
| `already_resolved` skip = **0** | rev 1 + rev 2 |
| Block 2 **drops fixed rows** after collapse | rev 2: 2 NETWORK plan rows gone; 1 `still_open` + 2 new remain |
| Flush rebuild + G9 | resolution manifest + narrative align |

### Active gaps (fix forward — post-#83 dogfood only)

| ID | Gap | Status | Notes |
|----|-----|--------|-------|
| **SOS-2** | Reconcile / DB `still_open` drift | **parallel** | [finding-resolution post-wave-C](../finding-resolution/FINDING_RESOLUTION_POST_WAVE_C_BACKLOG_FINDINGS.md) — not this program |
| **SOS-3** | Build vs flush verdict/`summary_json` sync | **open** | Only if post-#83 dogfood proves mismatch after flush rebuild |
| **SOS-5** | **Orphan block-2 row** — `still_open`, never inlined, not in generation | **code ready** | P1 — `ever_inlined_fingerprints` filter + display G9 alignment |
| **SOS-4** | Deploy #83 | **closed** | #491 validates |

### Out of scope / rejected

| ID | Item | Resolution |
|----|------|------------|
| **SOS-1** | Retroactive collapse backfill (#489) | **Rejected (SOS-D4)** — legacy PRs not repaired |

---

## Root-cause chain (verified)

```text
Fix pushes (rev 4–12)
  → GH-1v2 marks inline threads resolved on GitHub (cumulative 18)
  → Staging worker: already_resolved SKIP path (pre-#83)
       → inline_threads popped
       → collapsed_fingerprints NOT returned
       → collapsed_inline_fingerprints NOT persisted
  → Pass 1 stamps some addressed transitions per push
       → but 7 groups remain active + still_open (line-region / cohort limits)
  → Publish build: filter_pr_active_groups_for_summary(prior_collapsed=∅)
       → block 2 lists all 7 active groups
  → Flush: inline_threads already empty at rev 12
       → no new collapses detected
       → issue comment published with stale block 2
```

**Primary failure mode (pre-#83):** collapse memory never persisted — fixed by #83 on new publishes.

**Secondary failure mode (ongoing):** groups **fixed in code** but `still_open` in DB may remain in block 2 — reconcile scope (SOS-2), not collapse backfill.

---

## Edge cases

| Case | Post-#83 target (#491-class) | Notes |
|------|------------------------------|-------|
| Fix push collapses inline | Block 2 drops fixed rows same publish | **PASS** on #491 rev 2 |
| `collapsed_inline_fingerprints` on next rev | Carries forward from prior publish | Verify on multi-fix PRs |
| `already_resolved` on publish | 0 skips; fingerprint in collapsed set | **PASS** on #491 |
| `still_open` + no inline (never posted) | Row stays in block 2 | **SOS-5** — #491 rev 3 repro |
| `still_open` + inline collapsed | Hidden via `collapsed_inline_fingerprints` | **PASS** on #491 rev 3 (INDICATOR) |
| Pass 1 `addressed` | Row dropped via DB `resolved` or filter | SOS-2 if stamp misses |
| Pre-#83 PR (#489) | Stale block 2 acceptable | **Out of scope** |

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| SOS-Q1 | Is this a PSA formatter bug or GH-1v2 memory bug? | **locked** | **GH-1v2 → summary memory** — PSA filter exists; staging never persisted collapses |
| SOS-Q2 | Is #83 sufficient for new PRs? | **locked** | **Yes** — #491 PASS; monitor via dogfood |
| SOS-Q3 | Close DB groups on thread collapse? | **locked** | **Partial** — `should_close_absent_and_addressed` only; Option-A `still_open` stays active; summary via collapsed set (FR-Q7) |
| SOS-Q4 | Backfill legacy PRs (#489)? | **locked** | **Reject (SOS-D4)** — no reconstruction from history |
| SOS-Q5 | How to ship improvements? | **locked** | Findings row → minimal code fix + test on `main`; no ad-hoc without dogfood proof |
| SOS-Q6 | Hide never-inlined `still_open` from block 2? | **locked** | **Yes (SOS-D7)** — when not in generation and never in `ever_inlined_fingerprints` |

---

## Relation to prior work

| Artifact | Relevance |
|----------|-----------|
| [PR #83](https://github.com/raimondskrauklis/revy/pull/83) | Forward-path collapse memory + flush rebuild — **deployed**; validated on kp-platform #491 |
| kp-platform #491 | Post-deploy happy path — fix push collapses 2 threads, block 2 updates correctly |
| [PSA findings](../publish-summary-alignment/PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md) | `filter_pr_active_groups_for_summary` contract |
| [FR-Q7 / FR-Q16](../finding-resolution/FINDING_RESOLUTION_FINDINGS.md) | Block 2 definition + filter |
| [FR-DG2](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) | Stale group survives removal — related but different (file delete vs collapse memory) |
| kp-platform #485 | Same symptom; motivated #83 |
| kp-platform #489 | Pre-deploy repro — **out of scope** for repair |

---

## Experiment / verification (dogfood pass criteria)

| Check | Command / source | Pass |
|-------|------------------|------|
| Deploy includes #83 | merge `a5bb273` `2026-08-07T21:09:35Z` | **PASS** |
| `collapsed_inline_fingerprints` after fix push | #491 rev 2 `summary_json` | **PASS** (2) |
| `already_resolved` skip = 0 on new publishes | #491 rev 1–2 `thread_resolve_skipped` | **PASS** |
| Block 2 drops fixed rows | #491 rev 2 issue comment | **PASS** |
| Narrative count | #491 rev 2: “3 remain open” = block 2 rows | **PASS** |
| Rev 3 clean gen (#491) — SOS-5 | #491 rev 3 | **code ready** — re-dogfood after deploy |
| Legacy #489 repair | — | **N/A** (out of scope) |
| Unit regression | `test_resolve_stale_inline_threads_syncs_already_resolved_without_skip` | green on `main` |

---

## Parking lot

- **Pass 1 line-region misses** on refactor-only fixes (SOS-2) — track under finding-resolution post-wave-C, not block this program.
- **Hide `Thread resolve skipped` footer** when all skips are benign `already_resolved` on old worker — cosmetic.
- **Production** kp-platform — confirm same staging worker; not validated here.

---

## Devil's advocate

- Operators may still open stale #489 — document as pre-deploy; new PRs are the contract.
- **SOS-5 orphan block-2 row** — never-inlined `still_open` survives when all visible threads collapsed (#491 rev 3); fix via reconcile or summary filter (P1).
- Closing groups in DB on collapse may fight Pass 2 reconcile ordering — keep summary-only alignment unless FR-CS scope expands.

---

## References

- `backend/app/services/github_publish.py` — `_resolve_stale_inline_threads`, `_build_publish_surface`, `_flush_publish_surface`
- `backend/app/services/github_publish_formatter.py` — `filter_pr_active_groups_for_summary`, `apply_publish_summary_thread_collapse`
- `backend/scripts/revy_review_dogfood_staging_validation.py` — staging DB evidence
- `docs/utils/DATABASE_CONNECTION_GUIDE.md` — connection pattern

**Next:** [STILL_OPEN_SUMMARY_DOGFOOD_GENERAL_PLAN.md](./STILL_OPEN_SUMMARY_DOGFOOD_GENERAL_PLAN.md)
