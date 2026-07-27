# Review quality — dogfood PR #50 (Greptile + Revy)

**PR:** [#50](https://github.com/raimondskrauklis/revy/pull/50) · **branch:** `feat/review-quality` · **phase:** RQ0  
**Raw paste:** [actual_output_revy_greptile.txt](./actual_output_revy_greptile.txt) (GitHub copy, 2026-07-27)  
**Strategy:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) · **Lessons:** [CODE_REVIEW_LEARNINGS](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) · **Agents:** [agents/](../agents/README.md)

**Deploy context:** Revy autostart ran on **pre-RQ0 production/staging** — findings about `github_review.py` reflect **shipped** code, not this branch. **On GitHub for #50:** Greptile only (RC0 wiring). **Local:** Cursor Bugbot pre-push. No GitHub Bugbot on this repo.

**2026-07-27:** Revy GitHub App **suspended** on GitHub for this dogfood window — saves tokens; current Revy behavior on old deploy is already captured (RC-D2). **No new Revy check/comments** on pushes until app is re-enabled. Focus: **Greptile** monitoring + local Bugbot + distill. Re-enable Revy when branch is deployed (RQ1+ smoke) or RQ8 human gate.

---

## Visual & context UX — Greptile / Bugbot vs Revy (target bar)

**What we are building toward:** Greptile-shaped **GitHub triage** (RQ7 **G** track) + Bugbot-class **inline threads** — not copying vendor config, matching the **surface** humans use on PR #50.

### At a glance (PR #50 screenshots)

| Surface | Greptile / Bugbot | Revy today (`build_summary_markdown`) | Target (locked) |
|---------|-------------------|--------------------------------------|-----------------|
| **Check status** | `in_progress` spinner while reviewing | Check appears **only when done** | **G10** — RQ3 start / RQ7 finalize |
| **Top-level triage** | Long **summary comment**: narrative, confidence 0–5, “files needing attention”, merge verdict | **Check body only**: `## Revy review summary` + 4-col table + `Open in Revy` | **RQ7** — `github_publish_formatter` issue comment (G3: full narrative on comment, compact on check) |
| **Inline on code** | **P1/P2 badge** on exact lines; diff hunk visible; “Resolve conversation” | Inline only **error/critical** with line; title+message in thread — **no P-badge**, no `suggestion` block for warnings | **RQ7** — extend inline threshold; map severity → P0–P2 badge; R6 suggestion blocks |
| **Context depth** | Cites **AS1**, execution contract, behavioral regression (“RQ0→RQ1 window”) | Table row: title + file — **message lives in Revy UI** | **G5** narrative + execution-aware prompts when wired |
| **Actionability** | `suggestion` fenced blocks on some threads | Table is read-only; action in app | Inline `suggestion` + check footer `@revy review` |
| **Planning docs** | Low noise on `.md` when scoped to `backend/**` | Flags doc inconsistencies in table | RC1 slice scoping if needed |

### What Greptile does well (copy the pattern, not the vendor)

```text
  [Check: Greptile Review — in_progress … completed]
           │
           ├── Top comment: narrative + confidence + files list
           │
           └── Inline threads (per file/line)
                 P1 badge + title
                 Explanation (why + locked spec reference)
                 Optional ```suggestion``` block
                 Resolve conversation
```

**PR #50 example (inline):** P1 on `github_index_job.py` `index_mode` default — explains that **AS1** requires manual admin index → `full`, warns of regression before RQ1 wires job-create paths. That is **engineering-context review** (RC0 wiring working).

### What Revy does today

```text
  [Check: revy/review — appears only at end, often failure on old deploy]
           │
           └── output.summary (same body as issue comment today)
                 ## Revy review summary
                 [Open in Revy](app link)     ← detail behind click
                 | Severity | Category | Title | File |
                 (no confidence, no narrative, no per-line explanation in check)
```

Inline comments **exist** (`inline_publish_findings_statement` — error/critical only) but PR #50 findings on **docs** and **architectural** gaps show up in the **table only**, not as anchored threads — feels thinner than Greptile/Bugbot even when the underlying finding is valid.

### Bugbot (local)

Same **class** as Greptile for UX: severity table, file:line, explanation in review output — not on GitHub Checks unless Cursor posts to PR. Use as **pre-push** gate; Greptile as **post-push** gate; Revy must match **both** on GitHub after RQ7.

### Gap → wave map (not landed yet)

| UX gap | ID | Ships in | Notes |
|--------|-----|----------|-------|
| In-progress check on PR | **G10** | RQ3 + RQ7 | `create_check_run(in_progress)` → `update_check_run(completed)` |
| Narrative + confidence 0–5 | **G2**, **G5** | RQ7 | Formatter LLM; deterministic score prose |
| Split check vs issue comment | **G3** | RQ7 | Check = compact; comment = Greptile-shaped sections |
| P1/P2 inline badges + explanation | **G6/G7** | RQ7 (+ R6 suggestion) | Warnings in table today → should be inline optional |
| “Fixed since last review” | **G9** | RQ6 + RQ7 | Reads `resolution_status` |
| Execution-doc-aware findings | **RC0** | Done | Greptile; Revy prompts not wired to planning docs |
| Pipeline trace in GitHub | **O9 GET** | RQ3 | Until then: paste / Revy UI only |

**North star:** GitHub = **triage + inline action** (Greptile bar); Revy app = **workflow + trace + dismiss** — but GitHub must not be a bare table with a link.

---

## What we can fetch automatically

| Source | `gh` / API | Full detail | Gap |
|--------|------------|-------------|-----|
| **Greptile** threads | GraphQL `reviewThreads` + REST `pulls/comments` | P1/P2 body, path, line, suggestions | Need filter `greptile-apps` login |
| **Greptile** summary | Check run `output.summary` | Confidence, files needing attention | In check run API |
| **Revy** check | `gh pr checks` / check-runs API | Compact table + link to Revy UI | No pipeline trace until RQ3 ships |
| **Revy** reviewer UI | — | Full messages, judge, dismiss | Needs app login — not in `gh` |
| **Bugbot** | Local subagent only | Pre-push diff review | Not on GitHub Checks unless Cursor PR integration |

**Babysit workflow:** GraphQL gives all Greptile inline threads; no extra GitHub permissions needed beyond repo read. Revy internal run detail requires Revy API or UI — document paste (like `actual_output_revy_greptile.txt`) until pipeline GET ships (RQ3).

---

## Side-by-side (RQ0 commit)

| Dimension | Greptile | Revy (old deploy) |
|-----------|----------|-------------------|
| **Checks UX** | `in_progress` spinner ~5m | Appears only at end — **G10** |
| **Wired to execution doc** | Yes (RC0 `files.json`) | No — reviews code behavior only |
| **Confidence / narrative** | 3/5 + summary prose | Table only |
| **Schema review** | Strong — FK semantics, O8 index | N/A |
| **Intent vs code** | Migration + ORM vs execution | Flags RQ1 gap (full RAG) |
| **Planning doc findings** | Low | Yes — README, findings, execution |

---

## Greptile — triage (babysit)

| Sev | Location | Finding | Action |
|-----|----------|---------|--------|
| P1 | `0026_review_quality.py` | Nullable pipeline FKs need `ON DELETE SET NULL` | **Fixed** |
| P1 | `github_pipeline.py` | ORM FK `ondelete` match | **Fixed** |
| P1 | `0026_review_quality.py` | `ix_github_pipeline_runs_created_at` for O8 purge | **Fixed** |
| P2 | `0026_review_quality.py` | Historical `index_mode` backfill → `full` | **Fixed** |
| P2 | `0026_review_quality.py` | `revision_id` → `ON DELETE CASCADE` | **Fixed** |
| P2 | `0026_review_quality.py` | Artifact `CHECK` content present | **Fixed** |
| P1 | `github_index_job.py` | ORM `index_mode` default `diff` breaks AS1 manual → `full` | **Fixed** (`87c50d2`) — `full` default + explicit at job create (manual=`full`, pipeline=`diff`) |

**Greptile verdict:** RC0 wiring worked — cited O8, execution contract, AS1 on inline thread. Visual UX is the bar for RQ7.

**Babysit pass 2 (`87c50d2`):** Local Bugbot clean on same fix; Greptile had caught AS1 earlier — see [distillation §](#reference-reviewers--distill-for-revy-pr-50).

---

## Reference reviewers — distill for Revy (PR #50)

**Not the product architecture.** On **PR #50** we run **Greptile (GitHub) + local Bugbot (Cursor)** and distill into findings / RQ waves. **Revy GitHub App suspended** (2026-07-27) — prior deploy findings captured; no new runs until re-enabled. **GitHub Bugbot is not on this repo**; operator experience on other GitHub PRs + [arch notes](../code-review-arch_perplexity_searcj_advice_only.md) inform what Revy should absorb (deeper agentic review, RQ4+). Goal: **Revy absorbs those patterns** — external tools are benchmarks, not layers customers need forever.

```text
  PR #50 (what we run)                         NORTH STAR
  ────────────────────                         ──────────
  Local Bugbot (Cursor, pre-push) ──┐          Revy pipeline:
  Greptile (GitHub, post-push) ─────┼── distill  • spec/rules (RC4)
  Revy — suspended (prior findings) ─┘      →    • trace agents (RQ4+)
                                                • Greptile UX (RQ7)

  GitHub Bugbot — not on #50; industry reference for deeper review bar
  Local Bugbot likely stays — Cursor dev gate, not Revy SKU
```

| Reference | On #50? | What they do well | Revy absorbs via | #50 example |
|-----------|---------|-------------------|------------------|-------------|
| **Local Bugbot** | Yes (pre-push) | Fast diff hygiene; read/grep on harder hunks | Dev habit only | Clean on `index_mode` fix; missed AS1 before babysit |
| **Greptile** | Yes (GitHub) | RC0 execution-doc citations; schema/FK; P-badge inline | RQ7 + RC4 | P1 `index_mode`, O8 index, SET NULL FKs |
| **GitHub Bugbot** | **No** — other repos / operator knowledge | Deeper cross-file; often finds what local skips; multi-pass agent loop ([arch notes](../code-review-arch_perplexity_searcj_advice_only.md)) | RQ4 evidence + trace | — (not logged on #50) |
| **Revy** | **Suspended** (was deploy) | Intent vs shipped code — captured RC-D2 | The product | `github_review.py` full-RAG (historical) |

### Under the hood (working hypothesis)

Greptile (and **GitHub Bugbot where available**) are probably **agent-shaped** for harder findings — not one static prompt. Local Bugbot is the same **class** (subagent + read/grep), lighter and single-pass. Distillation job: note **which behaviors** to copy (contract wiring, inline severity, trace-before-claim), not which vendor to stack.

| Signal | Local Bugbot | Greptile (#50) | GitHub Bugbot (reference) |
|--------|--------------|----------------|---------------------------|
| On our PR #50 | Yes | Yes | No |
| Input | `.cursor/BUGBOT.md` + diff | `.greptile/files.json` + diff | PR + repo index (other repos) |
| Mechanism | Cursor `bugbot` subagent | Opaque; RC0 suggests doc-aware agent | Documented agentic loop + multi-pass |
| Distill into Revy | — (dev only) | Rules + narrative + inline UX | Trace agents + judge (RQ4+) |

**`index_mode` lesson:** Greptile caught **contract** regression (AS1); local Bugbot validated the **fix** diff. Both observations go into findings — neither replaces shipping Revy.

---

## Iterative agent review — RQ1 local Bugbot

**Context:** Revy is built **in complement** with Cursor (Composer) + local Bugbot during dogfood (RC-D7). End users run **Revy on the repo**; we use Cursor today to explore agent patterns we must ship.

### Mechanism (observed on RQ1 subagent transcripts)

```text
  INPUT: git diff + .cursor/BUGBOT.md (active RQ phase)
           │
           ▼
  SEED: changed files in diff
           │
           ├── Read (callers, workers, tests)
           ├── Grep (index_mode, get_latest_*, create_index_job, …)
           ├── Read (REVIEW_QUALITY_EXECUTION.md when steered)
           └── (optional) prior run notes / chain-of-thought saves
           │
           ▼
  OUTPUT: 0–N findings table (severity, file:line)
```

Not embedding / RAG — **plaintext repo + agentic trace**. Same class as Cursor Bugbot blog and target RQ4+ Revy trace.

### Explicitly iterative (RQ1 pre-push passes)

After each fix, re-run Bugbot on the **same feature slice**. New passes found **different** bugs — expected (RC-D8):

| Pass theme | Example finding | Fixed in RQ1 |
|------------|-----------------|--------------|
| Lifecycle / DB | Chunk `DELETE` before embed succeeds → data loss on failed job | Yes |
| Diff edge | Empty `raw_chunks` left stale chunks for changed paths | Yes |
| Job selection | `get_latest_index_job` vs `get_latest_completed` vs `index_in_progress` | Yes |
| Wiring | Missing `index_job_in_progress` import | Yes |
| API limits | GitHub compare 300-file cap → fallback | Yes |
| Tenancy | p50 duration query not workspace-scoped | Yes |

**Workflow:** fix blockers → Bugbot again → push. Do not treat first “no bugs” as ship-ready when the change is large.

### Parent agent discipline

| Do | Why |
|----|-----|
| **Skim subagent transcript** after each Bugbot spin | Findings table hides the grep/read path; transcript shows what Revy must replicate |
| Save gate exports when useful | `agents/chain_of_thoughts/` — committed evidence archive; add selectively, not every run |
| Narrow `BUGBOT.md` to active RQ | Steers without overwhelming; subagent still explores |
| Expect Greptile **post-push** on different axis | Contract/spec (AS1) vs implementation lifecycle |

**Economics (operator note):** local Bugbot subagent runs are bundled with Composer usage and can issue many tool calls per run — cheap R&D. Customer Revy = **intelligence + passes** as the SKU; no Cursor subsidy.

### RQ1 gate outcome (validated on code push)

```text
  ~6× iterative local Bugbot on RQ1 code  →  fix  →  re-gate  →  clean
           │
           ▼
  push bd4d084 (RQ1 code)
           │
           ▼
  Greptile on that CODE push  →  no new findings
```

**Theory confirmed (RC-D10):** iterative pre-push Bugbot found **implementation** bugs (lifecycle, cross-file, API limits) that **Greptile did not** on the same RQ1 code slice — not a claim of completeness. Greptile’s earlier wins on this PR remain **contract/spec** (AS1, schema — RQ0 babysit). After Bugbot-hardened code landed, Greptile’s pass on `bd4d084` added nothing new.

**Separate:** `854a8e1` (docs + `chain_of_thoughts`) — Greptile run in progress; not part of RC-D10.

---

## RQ2 Bugbot — focus vs bias

**Yes — this is review-quality dogfood.** Local Bugbot on RQ2 (`ed0ef7a`) is high-signal product research, not a side note.

### Focus vs bias (both, different layers)

| Layer | What | RQ2 example |
|-------|------|-------------|
| **Focus** | Narrow *where* the model looks | Diff-first prompt: metadata → changed files → **unified diff** → bounded supplemental. Review worker scopes RAG to changed paths (D7). |
| **Bias** | Steer *what kinds* of issues to prefer | Search lenses (`security`, `logic bugs`, …); system prompt “prioritize diff hunks”. Mild category bias **inside** a focused scope. |
| **Contract focus** | Steer the **review agent** (Bugbot), not just the review LLM | `.BUGBOT.md` + EXECUTION § RQ2 + FINDINGS D13-F — subagent reasons against locked Q#, not generic advice. |

**We want focus + contract focus for v1.** Category bias stays light (generators exploratory; judge/publish filter downstream). **Not** whole-repo haystack “focus” that is actually no focus.

**Revy product:** customer review LLM gets diff-first pack (RQ2); future **trace agents** (RQ4) get rules + tools — same split as Cursor Bugbot today.

### RQ2 iterative Bugbot (2 passes)

```text
  Pass 1 — read EXECUTION/FINDINGS + diff
           → D13-F: index fallback_reason missing from manifest
           → compare failure left supplemental empty in diff mode
           → fix both

  Pass 2 — re-gate on same slice
           → explicitly verifies prior findings addressed
           → clean
```

**Why valuable:** catches **cross-worker consistency** (index job vs review worker) that pytest slices often miss. Pass 2 **closure** (“prior findings addressed”) is the behavior we want Revy resolution + re-review to automate (RQ5/RQ6).

### Greptile hypothesis (unverified on #50)

Greptile likely combines **PR diff** + **codebase graph** (signup index) for cross-file recall — marketing aside, the bug class is real ([STRUCTURAL_CONTEXT](./REVIEW_QUALITY_STRUCTURAL_CONTEXT.md)). Our v1 path: diff-first (RQ2) → manifest instrumentation (SC3) → grep/graph bridge (RQ-STRUCT-1) → focused agents (RQ4+). Parallel research tracks, same north star.

---

## LOOP discipline failure — RQ3/RQ4 (RC-D13)

**What went wrong (operator + agent):** RQ3 and RQ4 were **pushed without completing the mandatory local Bugbot loop** from [phase-execution](../../../.cursor/skills/phase-execution/SKILL.md) § Local Bugbot:

| Phase | Expected | What happened |
|-------|----------|---------------|
| **RQ3** | Pass 1 → fix → **pass 2 clean** → commit/push | Pass 1 ran; fixes landed; **no pass 2** before push (`c03a8ba`) |
| **RQ4** | Full loop before first push | **No Bugbot** before push (`6abe242`) |

**Why it matters:** pytest + ruff are necessary but not sufficient. RQ4 retroactive pass 1 (on `c03a8ba..6abe242`) found **3 bugs** pytest missed:

| Sev | Finding | Fix (pass 2) |
|-----|---------|--------------|
| high | Copy-forward skipped when `paths_to_index` empty (deletion-only sync) | Gate on `use_diff and paths_to_index is not None`, not truthy `changed_paths` |
| medium | Incremental retry duplicated chunks (no revision wipe before copy-forward) | Delete all revision chunks before incremental rebuild when parent exists |
| medium | G10 check marked **failure** when review skipped for benign reasons (draft, pending review) | Remove `finalize_pipeline_github_check_failure` on benign `prepare_review_after_index` `None` |

**Pass 2 outcome:** clean — fixes committed after re-gate (not amend of `6abe242`; follow-up commit on same branch).

**Hard rule (repeat):** `implement → pytest → ruff → Bugbot pass N → fix → Bugbot pass N+1 until clean → commit → push → Greptile`. **Never** treat pass 1 fixes as ship-ready. **Never** skip Bugbot because “tests are green.”

**RQ3:** already on remote — **no retroactive re-gate** unless a targeted bug is found; pass 1 findings were fixed pre-push but pass 2 was not recorded.

---

## RQ4 Bugbot pass 2 — closure vs thinking trace (RC-D14)

**Source:** [local_bugbot_from_ui_1.txt](../agents/chain_of_thoughts/local_bugbot_from_ui_1.txt) (full UI thinking export, ~200 lines).

### What pass 2 was asked to do

```text
verify pass 1 findings closed → report NEW bugs only
```

Pass 1 had **3 real bugs** (copy-forward gate, false G10 failure, retry duplicates). Pass 2 correctly verified all three fixed in `ec85d7e` and returned **“no bugs.”** That answer was **correct for closure scope** — not “found 3, reported 0.”

### Why it felt wrong

The thinking trace explores **many** hypotheses (deletion-only sync, `paths_to_index is None`, embed-after-copy-forward commit, orphan `in_progress` checks, duplicate chunks, …) and self-dismisses most. Final output is only the last line — **no “considered but deferred” section**. Operator sees 199 lines of worry → 1 line “clean.”

### Pass 2 rule addition (dogfood)

| Pass | Report |
|------|--------|
| **Pass 1** | All actionable bugs in diff |
| **Pass 2+** | New bugs **or** explicit table: pass 1 items closed + **deferred** pre-existing / out-of-scope items with severity |

### Deferred items from pass 2 thinking (fixed before RQ5)

| Sev | Issue | Thinking lines | Fix |
|-----|-------|----------------|-----|
| medium | Embed fails after copy-forward → partial chunks **committed** (`get_db_context` commits on normal return) | 179–183 | `_fail_index_job_after_chunk_work` → `session.rollback()` then mark job failed |
| medium | Index succeeds, `ServiceUnavailableError` on `create_review_run` → G10 check stuck `in_progress` | 133–135 | `ReviewAfterIndexOutcome.fail_pipeline_check`; `index_tasks` finalizes failure for transient enqueue errors only (draft/closed/pending review stay benign) |

**Still open (parking):** draft/closed PR leaves check `in_progress` after index — needs G10 `neutral` finalize (RQ7/G10 polish), not failure.

**Archive:** commit `local_bugbot_from_ui_1.txt` under `agents/chain_of_thoughts/` when useful; thin exports (`cursor_bugbot_rq4_pass_6.md`) are not sufficient for dogfood.

---

## Prompt handling — RC-D15

**Insight:** Composer (implement) and Bugbot (review) share the same model class but **different tasks**. Smart agents need **contract context + thin routers**, not long prompts. Long thinking traces that “talk themselves out” of hypotheses are **valuable** — the bug is collapsing that to one line.

**Shipped:** [agents/prompts/](../agents/prompts/)

| File | Role |
|------|------|
| [TWO_AGENTS.md](../agents/prompts/TWO_AGENTS.md) | Implementer blind spots vs reviewer adversarial trace |
| [OUTPUT_FORMAT.md](../agents/prompts/OUTPUT_FORMAT.md) | Pass 1 FIND; Pass 2+ CLOSED + **Deferred** (required) |
| [PHASES.md](../agents/prompts/PHASES.md) | One distilled Custom Instructions block per RQn |
| [README.md](../agents/prompts/README.md) | Stack diagram + gate sequence |

**RQ5+:** update `PHASES.md § RQ5` when implementing; append OUTPUT_FORMAT tail unchanged.

---

## Revy — triage (old deploy)

| Sev | Location | Finding | Action |
|-----|----------|---------|--------|
| error | `github_review.py` | Full-revision RAG not diff-first | **RQ1** — expected; not a babysit fix |
| warning | `README.md` | Inconsistent dependency baseline | **Doc** — align prerequisite line (RQ8) |
| warning | `FINDINGS.md` | Raw LLM storage / encryption | **Parking** — O4/O6; ops note for v1 |
| warning | `EXECUTION.md` | Duplicate index job on deep/critical | **Verify AS1** in RQ1 — execution already locks behavior |

**Revy verdict:** Useful product dogfood — caught the main RQ1 gap without reading Greptile. Check `failure` is expected until RQ1 lands on deploy.

---

## What is good (keep)

| # | Observation |
|---|-------------|
| G1 | Greptile + RC0 reads execution/findings — schema defects caught pre-staging |
| G2 | Revy autostart on planning PR — validates intent drift even on doc-heavy diffs |
| G3 | Greptile AS1 on `index_mode` — **distill** contract-aware review into Revy (RC4/RQ7); local Bugbot stays dev-only |
| G4 | CI green on migration + models |
| G5 | Greptile confidence + “files needing attention” — good triage surface |
| G6 | Greptile inline cites locked spec (AS1) on exact line — **target UX for Revy RQ7** |

---

## What needs updates (parallel waves)

| ID | Wave | Item |
|----|------|------|
| **G-UX** | RQ7 | Greptile-shaped **issue comment** + P-badge inline + G3 split bodies — see [visual UX §](./REVIEW_QUALITY_DOGFOOD_PR50.md#visual--context-ux--greptile--bugbot-vs-revy-target-bar) |
| **RQ1** | RQ1 | Diff-first retrieval — fixes Revy error on deploy |
| **RQ3** | RQ3 | Pipeline GET — agents can read trace without UI paste |
| **RC1** | RQ-RC-1 | Scope Greptile files to active RQ slice if noise grows |
| **RC-API** | Post-RQ3 | Expose check-run / run metadata via API for babysit automation |
| **O-sec** | Parking | Document retention + secret redaction in pipeline artifacts (Revy warning) |

---

## Permissions / tooling notes

- **`gh api graphql`** — sufficient for Greptile babysit on private repo (repo scope).
- **Revy run detail** — `gh` only sees GitHub check output; link `Open in Revy` needs human or future Revy API token for agents.
- **Paste file** — keep `actual_output_revy_greptile.txt` or per-PR snapshots when API gap matters.

---

## Next entries (per RQ phase)

After each LOOP commit on #50, add a row:

| Phase | Greptile | Revy | Notes |
|-------|----------|------|-------|
| RQ0 | 6 threads, FK fixes; pass 2 `index_mode` | 4 findings, 1 error (RQ1) | Distillation notes; babysit `87c50d2` |
| RQ1 code | **No new findings** on `bd4d084` after ~6× iterative local Bugbot | suspended | RC-D10 — Bugbot caught impl bugs Greptile missed; [§](#iterative-agent-review--rq1-local-bugbot); [chain_of_thoughts](../agents/chain_of_thoughts/) |
| RQ2 | pending | suspended | Bugbot 2-pass: D13-F + compare supplemental; pass 2 closure — [§](#rq2-bugbot--focus-vs-bias) RC-D12 |
| RQ4 | pending | suspended | RC-D13 — initial push skipped Bugbot; retro pass 1 → 3 bugs; pass 2 clean — [§](#loop-discipline-failure--rq3rq4-rc-d13) |
| RQ4 pass 2 | — | — | RC-D14 closure trace + 2 deferred fixes before RQ5 — [§](#rq4-bugbot-pass-2--closure-vs-thinking-trace-rc-d14) |
| prompts | — | — | RC-D15 — `agents/prompts/` distill directory — [§](#prompt-handling--rc-d15) |
