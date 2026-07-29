# Finding resolution dogfood — validation findings (operator)

**Date:** 2026-07-29  
**Purpose:** Locked operator decisions discovered during staging validation — not product code gaps (those stay in [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md)).

**Authority:** [STAGING_VALIDATION_FINDINGS.md](../staging-validation/STAGING_VALIDATION_FINDINGS.md) SV-Q* · [FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md](./FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md)

---

## FR-DG-VAL1 — Wave A merged in one PR (#64)

| Item | Locked decision |
|------|-----------------|
| **What happened** | P0–P2 code + P3 doc-sync shipped in single merge `f0b12d5` ([#64](https://github.com/raimondskrauklis/revy/pull/64)) |
| **Deploy boundary** | Workflow `30476822659` — deploy finished **`2026-07-29T17:50:43Z`** (post-P1 **and** post-P2 — same droplet image) |
| **Impact** | Dogfood pushes 2–3 continue on a **new open chore PR**; do not assume rev history from pre-merge #64 carries forward |
| **Metrics `--since`** | Use `2026-07-29T17:50:43Z` for FR-DG1/FR-DG2 windows (not PSA `11:38:12Z`) |

---

## FR-DG-VAL2 — FR-DG1 requires rev ≥ 2 on open dogfood PR

| Item | Locked decision |
|------|-----------------|
| **Symptom** | Push 1 on #64 rev 1: `resolution_pass=null`, `denominator_active_prior=0` — expected (no prior published revision on PR) |
| **Rule** | FR-DG1 manifest/sign-off applies on **fix push** where rev N−1 published with ≥1 active group |
| **Cadence** | **Push 2a** wire probe → rev 1 publish (active finding) → wait Revy → **Push 2b** fix → rev 2 publish (FR-DG1 PASS) |
| **Execution** | [P1.5](./waves/FINDING_RESOLUTION_DOGFOOD_P1.5_EXECUTION.md) — do not mark FR-DG1 PASS on wire-only rev 1 |

---

## FR-DG-VAL3 — Push 1 evidence (#64 rev 1)

| Field | Value |
|-------|-------|
| `head_sha` | `5bb55ea3060092066d8a02532f7f698d84c74bd3` |
| `review_run_id` | `019fae9b-afb0-7229-a827-992382310366` |
| Publish | `completed` |
| `gen` / `pr` | `0` / `0` (probe unused — by design) |
| Moonshot | 1 critical on `github_resolution_metrics.py` — **judge dismissed** (FP vs branch fix) |
| G9 | `1 finding dismissed by judge` — not FR-DG1 surface |
| **Push 1 verdict** | **PASS** (probe introduced; publish completed) |

---

## FR-DG-VAL4 — Post-merge deploy before dogfood push 2

| Check | Status |
|-------|--------|
| #64 merged | `2026-07-29T17:45:54Z` |
| Droplet deploy | **done** `2026-07-29T17:50:43Z` |
| Worker has P1+P2 code | **yes** (`f0b12d5`) |
| Safe to open push-2 chore PR | **yes** after deploy ISO recorded |

---

## FR-DG-VAL5 — `publish_summary` script usage

| Window | `--since` | Use |
|--------|-----------|-----|
| PSA history | `2026-07-29T11:38:12Z` | Reference only — mixes PSA #63 runs |
| Post-#64 deploy | `2026-07-29T17:50:43Z` | FR-DG1/FR-DG2 sign-off metrics |
| Single push | rev `created_at` ISO | Narrowest — preferred per push row |

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T17:50:43Z --json'
```

---

## FR-DG-VAL6 — Push 2a wire did not surface Moonshot finding

| Item | Locked decision |
|------|-----------------|
| **Evidence** | PR #65 rev 1 `cdea3cc` — `gen=0`, `pr=0`, 0 findings; G9 `n/a` |
| **Cause** | Test-fixture-only wire insufficient for Moonshot publishable finding |
| **Remediation** | Push **2b** doc/probe delta surfaced 3 findings on rev 2; push **2c** fixes → FR-DG1 |

---

## FR-DG-VAL7 — FR-DG2 partial on rev 4 (probe deletion)

| Item | Locked decision |
|------|-----------------|
| **Evidence** | PR #65 rev 4 `66d64e5` — `pr_active` 3→7; probe group `019faf29-9c6e` still `active`; `0` closures on rev 4 |
| **Mechanism proof** | 2 doc groups `absent_and_addressed` on rev 3 — Pass 2 works when Pass 1 stamps `addressed` |
| **Root cause** | Pass 1: deleted files excluded from `patches_by_file` → `still_open` — see [post-validation RC-1](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md#rc-1--pass-1-ignores-file-deletion-primary-code-gap) |
| **Follow-up** | **FR-DG2a** Track A code fix + clean repro PR (Track B) — not merge-as-sign-off |

---

## FR-DG-VAL8 — Dogfood metrics interpretation

| Item | Locked decision |
|------|-----------------|
| **Rule** | `pr_active_count` shrink is **insufficient alone** when push introduces new Moonshot findings |
| **Primary metric** | Per-group `state` + `resolution_method` on the target fingerprint cohort |
| **Protocol** | FR-DG2 repro: no program-doc edits in pushes 1–3; isolated probe file only |

---

## FR-DG-VAL9 — Post-#66 deploy (FR-DG2a on staging)

| Item | Locked decision |
|------|-----------------|
| **Merge** | [#66](https://github.com/raimondskrauklis/revy/pull/66) `111e851` — `2026-07-29T19:16:07Z` |
| **Deploy** | Workflow `30483659578` — droplet job finished **`2026-07-29T19:20:33Z`** |
| **Metrics `--since`** | Use `2026-07-29T19:20:33Z` for Track B FR-DG2 windows |
| **Track B PR** | `chore/fr-dg2-staging-dogfood` — push 1 introduce → push 2 fix → push 3 delete |

---

## FR-DG-VAL10 — Pass 1 pairing window on delete

| Item | Locked decision |
|------|-----------------|
| **Evidence** | #67 rev 3 — `019faf5b` (last_seen rev 2) `absent_and_addressed`; `019faf58` (last_seen rev 1) stayed `active` |
| **Cause** | Pass 1 stamps only `last_seen_revision_id ∈ pairing_revision_ids` (last published prior + gap); rev-1 cohort excluded on rev 3 |
| **Mechanism** | #66 file-deletion stamp **works** for in-window cohort |
| **Operator rule** | Delete file on **next publish** after finding introduced, or accept orphan until product fix |
| **Follow-up** | **[FR-CS1](../finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md)** — wave C hygiene Pass 1b (planned, not ad-hoc) |

---
