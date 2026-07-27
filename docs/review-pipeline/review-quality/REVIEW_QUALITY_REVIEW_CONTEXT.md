# Review quality — PR review context (strategy)

**Purpose:** Capture how Revy wires **planning docs and locked decisions** into **Greptile** and **Bugbot** during dogfood — and the product path to workspace-scoped review policy. Complements [structural context](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) (code graph) with **engineering context** (what the PR is supposed to implement).

**Status:** strategy locked (2026-07-27). **v0 ships in RQ0**; improvements are **post-`review-quality-v1`**.

**Related:** [REVIEW_QUALITY_EXECUTION.md](../waves/REVIEW_QUALITY_EXECUTION.md) § PR review context · [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) · [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) · `phase-execution` / `create-execution-plan` skills.

---

## Short answer

| Decision | Verdict |
|----------|---------|
| **Wire Greptile + Bugbot to execution + findings in v1** | **Yes** — `.greptile/files.json` + `.cursor/BUGBOT.md` in **RQ0** (first commit) |
| **Treat changed `.md` in PR diff as authoritative spec** | **No** — bots need explicit wiring; diff alone is insufficient |
| **Productize as workspace policy in v1** | **No** — dogfood repo config first; `.revy/rules` → post-G (DB) |
| **Improve iteratively after dogfood** | **Yes** — **RQ-RC-1** track after `review-quality-v1` tag |

**Why it matters:** Large program PRs (RQ0–RQ8) ship code + docs together. Without wired context, Greptile/Bugbot review **implementation** against **intent** — route mismatches, missing migration columns, wrong API paths — are missed or rediscovered late.

---

## Platform view — two context layers

| Layer | What it answers | v1 (`review-quality`) | Post-v1 |
|-------|-----------------|----------------------|---------|
| **Engineering context** (this doc) | What should this PR implement? Locked Q#? Phase contract? | Greptile `files.json` + Bugbot `BUGBOT.md` → execution + findings | Scoped rules, auto slice selection, workspace policy |
| **Structural context** ([SC doc](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md)) | Who calls X? Impact beyond diff? | Manifest instrumentation (SC3); RQ-STRUCT-1 v1.1 | Graph + agent (SC8) |

Both feed the **north star** ([SC8](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md#north-star--combine-both-not-a-xor-b)): agents and reviewers need **intent** (RC) and **structure** (SC).

```text
  Planning docs (execution, findings, authority)
           │
           ▼
  ┌────────────────────┐     ┌─────────────────────┐
  │ Greptile files.json │     │ Bugbot BUGBOT.md    │
  │ scope: backend/**   │     │ links to same docs  │
  └─────────┬──────────┘     └──────────┬──────────┘
            │                            │
            └────────────┬───────────────┘
                         ▼
              PR review (dogfood on feat/review-quality)
                         │
                         ▼
              Code matches locked execution contract?
```

---

## v0 — dogfood wiring (`review-quality-v1`)

Shipped in **RQ0** (same commit as migration `0026`):

| File | Role |
|------|------|
| `.greptile/files.json` | `path` entries for execution + findings; `scope: ["backend/**"]` |
| `.cursor/BUGBOT.md` | Markdown links to same docs (paths relative to `.cursor/`) |

**Per-phase commit pattern** (LOOP): phase code + **minimal** doc touch (README status / execution table row). Do **not** re-edit full findings + peer-review corpus every push — context budget.

**Skills:** `phase-execution` and `create-execution-plan` require this wiring on first LOOP iteration for code+docs programs.

---

## Improvement ladder (post-v1)

Evaluate during **`feat/review-quality` PR** dogfood; ship improvements in **RQ-RC-1** (separate PR after tag).

| Rung | ID | What | Trigger |
|------|-----|------|---------|
| **v0** | RC0 | Static `files.json` + `BUGBOT.md` | RQ0 — **shipped** (`64f661c`) |
| **v1** | **G10** | **`revy/review` check `in_progress` → `completed`** (Greptile/Bugbot parity) | **RQ3** start + **RQ7** finalize — [dogfood log](#dogfood-log-pr-50) |
| **v1.1** | RC1 | **Path-scoped** doc sets — e.g. `backend/**` → execution RQn section + findings D/O locks only | Greptile noise from irrelevant Q# |
| **v1.1** | RC2 | **Active slice pointer** — README or `BUGBOT.md` names current RQ phase; update each LOOP commit | Bugbot cites wrong subphase |
| **v1.2** | RC3 | **Greptile cascading rules** — `.greptile/rules` per directory (mirror vendor pattern) for monorepo areas | Frontend-heavy phases |
| **v2** | RC4 | **`.revy/rules` in DB** — workspace `review_policy` EN+LV; publish + reviewer prompts | Post-G product row |
| **v2** | RC5 | **Auto-wiring from pipeline** — on review run, inject locked Q# from workspace findings registry | Customer repos, not just Revy dogfood |
| **v3** | RC6 | **Reviewer agent tool** — `read_planning_doc(path)` in Track A investigator | SC8 agent runtime |

**RQ-RC-1 scope (draft):** RC1 + RC2 from dogfood metrics; RC3 only if frontend phases need it. RC4+ stays product program.

---

## Q-registry (RC)

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| **RC0** | Wire Greptile + Bugbot in v1 dogfood PR? | **locked** | **Yes** — RQ0; see [execution](../waves/REVIEW_QUALITY_EXECUTION.md) |
| **RC1** | Path-scoped doc subsets in `files.json`? | **open** | **RQ-RC-1** if dogfood shows context noise |
| **RC2** | Active RQ phase pointer in `BUGBOT.md`? | **open** | **RQ-RC-1** — manual update each phase until automated |
| **RC3** | Per-directory `.greptile/rules` in this repo? | **open** | **RQ-RC-1** if backend-only scope too narrow |
| **RC4** | `.revy/rules` workspace policy (product)? | **open** | Post-G — was parking lot; see [findings](./REVIEW_QUALITY_FINDINGS.md) |
| **RC5** | Pipeline injects locked decisions into review prompt? | **open** | Track A + workspace policy |
| **RC6** | `read_planning_doc` agent tool? | **open** | Track A — pairs with SC8 investigator |
| **G10** | `revy/review` check shows in-progress on PR? | **locked** | **Yes** — RQ3 create `in_progress`; RQ7 `update_check_run` → `completed` |

---

## Dogfood log (PR #50)

**PR:** [#50](https://github.com/raimondskrauklis/revy/pull/50) · **branch:** `feat/review-quality` · **RQ0:** `64f661c` · **deploy:** pre-RQ0 prod/staging (findings reflect **current** pipeline, not this branch).

| ID | Date | Signal | Result | Action |
|----|------|--------|--------|--------|
| **RC-D1** | 2026-07-27 | GitHub Checks UX — Greptile shows spinner; Revy does not | **Gap** — `create_check_run` posts `status: completed` only at publish end | **G10** locked → RQ3/RQ7 |
| **RC-D2** | 2026-07-27 | Revy autostart on planning PR (old deploy) | **Useful** — flagged full-RAG vs diff-first (`github_review.py`) | Validates RQ1 scope; not a false positive |
| **RC-D3** | 2026-07-27 | Greptile wired context (RC0) | **Pass** — 37 files, 6 comments | Triage threads; note schema/route hits vs noise |
| **RC-D4** | 2026-07-27 | CI on RQ0 migration | **Pass** | — |
| **RC-D5** | 2026-07-27 | Local Bugbot pre-push | **No findings** | — |

**G10 target behavior (parity with Greptile/Bugbot):**

```text
Pipeline enqueue / first worker
        │
        ▼
  create_check_run(status=in_progress)   ← visible on PR immediately
        │
        ▼
  index → review → reconcile → judge → publish
        │
        ▼
  update_check_run(status=completed, conclusion=…)   ← RQ7 publish path
```

On failure: `update_check_run` with `failure` or `neutral` — never leave orphan `in_progress`.

---

## Dogfood success metrics

After each RQ phase merge on the PR, note:

| Signal | Good | Bad → action |
|--------|------|----------------|
| Greptile cites execution route / schema | Matches locked contract | **RC1** — tighten scope or add authority link |
| Bugbot flags plan/code drift | Catches peer-review locks | Missing → expand `BUGBOT.md` links |
| False positives from stale Q# | Low | **RC1** — slice findings by track (D/O/G…) |
| Review latency / token blow-up | Stable | Trim per-phase doc commits; avoid full corpus edits |
| **`revy/review` in-progress on PR** | Spinner like Greptile/Bugbot | **G10** — RQ3/RQ7 |

Log anecdotes in [CODE_REVIEW_LEARNINGS](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) § PR review context and [dogfood log](#dogfood-log-pr-50) above.

---

## Honest positioning

| Claim | v0 (RQ0) | After RQ-RC-1 | Product (RC4+) |
|-------|----------|---------------|----------------|
| Bots see **execution contract** | Wired manually | Scoped + active slice | Workspace DB policy |
| Bots see **locked findings** | Full baseline doc | Track-filtered subsets | Per-repo registry |
| **Revy customer** gets same | No — Revy repo only | No | Yes — `.revy/rules` |

**Distinction:** [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) says Greptile **vendor config in customer repos** is product-owned via DB — **except** this Revy repo uses `.greptile/` for **dogfood**, same as we use `.cursor/BUGBOT.md` for Cursor.

---

## References

| Source | Path / URL |
|--------|------------|
| Execution wiring | [REVIEW_QUALITY_EXECUTION.md](../waves/REVIEW_QUALITY_EXECUTION.md) |
| Greptile files config | https://www.greptile.com/docs/code-review/greptile-config |
| Bugbot docs | https://cursor.com/docs/bugbot |
| phase-execution skill | `.cursor/skills/phase-execution/SKILL.md` |
| Structural north star | [REVIEW_QUALITY_STRUCTURAL_CONTEXT.md](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md) |

---

## Next

1. **RQ0** — ship RC0 wiring with migration `0026` — **done** (`64f661c`).
2. **During RQ1–RQ8** — minimal README status updates; extend [dogfood log](#dogfood-log-pr-50).
3. **After `review-quality-v1` tag** — if metrics warrant, draft `REVIEW_QUALITY_RQ_RC_1_GENERAL_PLAN.md` + execution file under `waves/`.
4. **Product** — keep RC4–RC6 aligned with workspace policy row in [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md).
