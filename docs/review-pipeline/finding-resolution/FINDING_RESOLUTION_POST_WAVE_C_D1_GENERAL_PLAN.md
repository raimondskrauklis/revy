# Finding resolution — post–wave C D1 general plan (FR-CS4 dogfood)

**Baseline:** [FINDING_RESOLUTION_POST_WAVE_C_D1_FINDINGS.md](./FINDING_RESOLUTION_POST_WAVE_C_D1_FINDINGS.md)  
**Parent:** [post–wave C general plan](./FINDING_RESOLUTION_POST_WAVE_C_GENERAL_PLAN.md) § D1  
**Execution:** [D1 execution](./waves/FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md)

**Thesis:** Prove FR-CS4 on staging — structural in-file fix without line-region overlap closes via Pass 3 verification judge (`verification_dismissed`).

**Prerequisites (hard):** **D0** [#71](https://github.com/raimondskrauklis/revy/pull/71) deployed to staging; `judge_llm_enabled()` true on workers (pre-flight on `revy-worker` before D1.1).

**Pre-flight (operator):**

```bash
docker exec revy-worker python -c "from app.core.config import settings; print('judge_llm_enabled:', settings.judge_llm_enabled())"
```

**Cross-cutting:** backend-only dogfood pushes (VAL8); per-group DB sign-off; staging memo rows; no product code in D1 beyond probe fixture.

---

## D1.0 — Staging memo + deploy boundary

**Goal:** Wave D section in dogfood staging validation with post–#71 `--since` ISO.

**Scope in:** Memo table (deploy ISO, push rows, placeholders).  
**Scope out:** Probe code.

**Deliverables:** `FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md` Wave D table; deploy ISO recorded.

**Depends on:** D0 droplet deploy complete.

---

## D1.1 — Introduce probe (push 1)

**Goal:** Review-visible defect on anchored lines; capture group + revision ids.

**Scope in:** `backend/app/services/fr_cs4_staging_probe.py`; `test_fr_cs4_probe.py`; chore PR push 1.  
**Scope out:** Program docs in push.

**Deliverables:** pytest green; staging push 1 memo row with `head_sha`, `group_id`, `last_seen_revision_id`, finding lines.

**Depends on:** D1.0 memo stub; branch `chore/fr-cs4-structural-fix-staging`.

---

## D1.2 — Structural fix (push 2)

**Goal:** Fix defect outside finding line region; wait for Revy publish.

**Scope in:** Probe fixture edit only (backend).  
**Scope out:** File deletion; line-region overlap fix.

**Deliverables:** Memo row; evidence that diff avoids anchored hunk; push-2 `gen=0` for probe fingerprint (no re-report).

**Depends on:** D1.1 PASS (≥1 active group on probe).

---

## D1.3 — Sign-off inspection

**Goal:** FR-CS4 → **closed PASS** or documented blocker.

**Scope in:** DB group fields; judge outcome row; optional metrics script; memo sign-off.  
**Scope out:** New code.

**Deliverables:** `state=resolved` + `resolution_method=verification_dismissed` + `github_finding_judge_outcomes` row (`judge_purpose=verification`); gap registry update deferred to **D3**.

**Depends on:** D1.2 publish complete.

**Human gate:** LOOP stops until memo signed PASS or blocker documented.

---

## Dependencies

```text
D0 deploy → D1.0 memo → D1.1 push 1 → D1.2 push 2 → D1.3 sign-off → D3 doc sync
```

---

## Remaining open item

**D0 deploy ISO** — operator must fill TBD row in memo before metrics queries.

**Next step:** `phase-execution` from [FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md](./waves/FINDING_RESOLUTION_POST_WAVE_C_D1_EXECUTION.md).
