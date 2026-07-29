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

## FR-DG-VAL6 — Push 2a wire did not surface Moonshot finding

| Item | Locked decision |
|------|-----------------|
| **Evidence** | PR #65 rev 1 `cdea3cc` — `gen=0`, `pr=0`, 0 findings; G9 `n/a` |
| **Cause** | Test-fixture-only wire insufficient for Moonshot publishable finding |
| **Remediation** | Push **2b** adds PSA-class wrong-kwargs snippet in `probe_module.py`; push **2c** fixes → FR-DG1; push **3** removes probe |

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
