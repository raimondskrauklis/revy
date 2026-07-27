# Review quality — dogfood PR #50 (Greptile + Revy)

**PR:** [#50](https://github.com/raimondskrauklis/revy/pull/50) · **branch:** `feat/review-quality` · **phase:** RQ0  
**Raw paste:** [actual_output_revy_greptile.txt](./actual_output_revy_greptile.txt) (GitHub copy, 2026-07-27)  
**Strategy:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](./REVIEW_QUALITY_REVIEW_CONTEXT.md) · **Lessons:** [CODE_REVIEW_LEARNINGS](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) · **Agents:** [agents/](../agents/README.md)

**Deploy context:** Revy autostart ran on **pre-RQ0 production/staging** — findings about `github_review.py` reflect **shipped** code, not this branch. **On GitHub for #50:** Greptile only (RC0 wiring). **Local:** Cursor Bugbot pre-push. No GitHub Bugbot on this repo.

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

**Not the product architecture.** On **PR #50** we actually run **Greptile (GitHub) + local Bugbot (Cursor) + Revy (deploy)** — compare outputs and distill into findings / RQ waves. **GitHub Bugbot is not on this repo**; operator experience on other GitHub PRs + [arch notes](../code-review-arch_perplexity_searcj_advice_only.md) inform what Revy should absorb (deeper agentic review, RQ4+). Goal: **Revy absorbs those patterns** — external tools are benchmarks, not layers customers need forever.

```text
  PR #50 (what we run)                         NORTH STAR
  ────────────────────                         ──────────
  Local Bugbot (Cursor, pre-push) ──┐          Revy pipeline:
  Greptile (GitHub, post-push) ─────┼── distill  • spec/rules (RC4)
  Revy (deploy, post-push) ─────────┘      →    • trace agents (RQ4+)
                                                • Greptile UX (RQ7)

  GitHub Bugbot — not on #50; industry reference for deeper review bar
  Local Bugbot likely stays — Cursor dev gate, not Revy SKU
```

| Reference | On #50? | What they do well | Revy absorbs via | #50 example |
|-----------|---------|-------------------|------------------|-------------|
| **Local Bugbot** | Yes (pre-push) | Fast diff hygiene; read/grep on harder hunks | Dev habit only | Clean on `index_mode` fix; missed AS1 before babysit |
| **Greptile** | Yes (GitHub) | RC0 execution-doc citations; schema/FK; P-badge inline | RQ7 + RC4 | P1 `index_mode`, O8 index, SET NULL FKs |
| **GitHub Bugbot** | **No** — other repos / operator knowledge | Deeper cross-file; often finds what local skips; multi-pass agent loop ([arch notes](../code-review-arch_perplexity_searcj_advice_only.md)) | RQ4 evidence + trace | — (not logged on #50) |
| **Revy** | Yes (deploy) | Intent vs **shipped** code | The product | `github_review.py` full-RAG vs diff-first |

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
| RQ1 | — | — | Diff-first deploy target |
