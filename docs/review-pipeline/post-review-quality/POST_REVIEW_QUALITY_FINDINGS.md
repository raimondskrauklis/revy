# Post review-quality — platform findings

**Purpose:** Baseline for the **next program** after review-quality (RQ0–RQ9). Platform research — not an execution plan.

**Date:** 2026-07-27 (revised after PR #52 ship)  
**Code:** RQ0–RQ9 on `main`; **GitHub surface P0–P4** on [PR #52](https://github.com/raimondskrauklis/revy/pull/52) (ready to merge). Staging worker deploy after merge validates L1–L3 on next PRs.

**Evidence:** PR [#50](https://github.com/raimondskrauklis/revy/pull/50), PR [#51](https://github.com/raimondskrauklis/revy/pull/51), PR [#52](https://github.com/raimondskrauklis/revy/pull/52) (surface dogfood), staging [#44](../REVIEW_PIPELINE_STAGING_SMOKE_VALIDATION.md) (infra only — pre-RQ), [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md), Greptile on every Revy repo PR.

---

## 1. The platform question

Revy is a **workspace-scoped GitHub review product**: install app → PR events → index → LLM review → reconcile → publish on GitHub + detail in Revy app.

Greptile on the Revy repo is **not the product**. It is a **parallel benchmark** — same PRs, same pushes, category reference, distill source. Greptile works well here; Revy should **keep up on GitHub first** (look and feel), then close the intelligence gap in later programs.

After review-quality, the honest question is not “do we need more pipeline?” It is:

> **When a developer opens a PR on GitHub, does Revy feel like a serious review agent — or like infrastructure with a table and a link?**

PR #51 ran on a **staging worker still on pre-formatter image** (JSON comment) — it reviewed the PR branch correctly; the **publisher code** was old. Not a verdict on `github_publish_formatter` on `main`. Next evidence: PR branch push after staging workers run current image.

---

## 2. Two tracks — visual first, intelligence later

| Track | When | Question | Programs |
|-------|------|----------|----------|
| **A — GitHub surface** | **Now** | Does Revy *look and behave* like Greptile on the PR? (check, comment, inline) | This program (P0–P4) |
| **B — Review intelligence** | **After A is credible** | Does Revy *find the right things* on hard PRs? | STRUCT, prompts, RC4 — not mixed into surface polish |

**Locked sequencing:** Do not open STRUCT to “fix” a broken formatter or missing G10. Do not polish UI to hide zero findings on a code PR where Greptile found real issues — that is track B.

Greptile’s graph and swarm are track B north stars. Copy from Greptile in track A only: summary shape, confidence, files list, inline threads, early presence.

---

## 3. Two products, two jobs

| | **Revy (ship)** | **Greptile (benchmark)** |
|--|-----------------|---------------------------|
| **Business** | B2B SaaS — workspace, billing, audit, `/reviewer` | Category leader — graph index + agent swarm |
| **Moat (target)** | Stable findings, explainable pipeline, tenant policy, cost-aware diff index | Full-repo graph, cross-file impact, learning from team comments |
| **Primary surface** | GitHub check + comment + selective inline; app for workflow | GitHub summary + inline + suggestions + check |
| **In this repo** | Dogfood our own pipeline on real PRs | Install alongside; archive output for comparison |

---

## 4. Category model — L1–L4

Users evaluate four layers. Revy after review-quality on `main` (**code**; deploy unverified):

| Layer | What the user perceives | Category bar (Greptile class) | Revy today (`main` code) |
|-------|-------------------------|-------------------------------|---------------------------|
| **L1 — Presence** | Something is reviewing my PR now | Check `in_progress`; bot visible early | **Shipped** (#52): G10 + **Revy Review** check; advisory `neutral`/`success` |
| **L2 — Triage** | One comment tells me what matters | Summary, confidence, files list, narrative | **Shipped** (#52): formatter + JSON unwrap; **one issue comment per PR** |
| **L3 — Action** | I can fix from the PR | Inline threads, suggestions on lines | **Shipped** (#52): inline all severities with line; GraphQL thread resolve; map in `summary_json` |
| **L4 — Memory** | Same nit doesn’t respam every push | Dedupe, “fixed since last review” | **Strong**: D10 fingerprint, `resolution_status` (RQ6), judge dismiss |

**Insight:** Review-quality invested in **L4** and pipeline internals. **L2 exists in code**; PRODUCT_PATTERNS still marks G10 / confidence as “defer” / “in flight” — doc drift. This program owns **L1–L3 on GitHub**; L4 stays closed.

**L2 v1 bar:** Treat `build_pr_review_comment_fallback` as the product minimum (confidence, G9 prose, files needing attention, findings table, metadata). Moonshot narrative is a plus, not required to match Greptile visually.

---

## 5. What review-quality bought

| Capability | User-visible? | Notes |
|------------|---------------|-------|
| Diff-scoped index (D13) | No (latency/cost) | Default index mode on new jobs; staging #44 was full-repo (different profile) |
| Pipeline trace (O) | No on GitHub | API + artifacts; `/reviewer` tab deferred |
| Greptile-shaped formatter (G) | **Yes** — when publish runs | `build_pr_review_comment`; G3 compact check + full issue comment |
| G10 lifecycle | **Yes** | `in_progress` at pipeline start → `completed` at publish; RQ9 neutral on draft-after-index |
| Resolution prose (G9) | **Yes** — in issue comment | Feeds formatter |
| Confidence 0–5 (G2) | **Yes** — in comment/check | `compute_confidence` — PRODUCT_PATTERNS stale |
| Evidence + judge (E) | No on GitHub | Quality filter — track B tuning, not this program |
| Agent doc wiring (RC0) | No on Revy output | Dogfood only; Greptile used RC0 on #51 |

---

## 6. What PR #51 measured (facts only)

| Surface | Result | Usable for L2 verdict? |
|---------|--------|-------------------------|
| **Greptile** | 4/5 confidence; understood RQ9; 2× P2 inline — valid | Benchmark reference |
| **Revy** | Check ~6m neutral; issue comment **JSON** (pre-formatter deploy) | **No** — wrong deploy |
| **CI** | Green; deploy skipped on PR (main push only) | Expected |

---

## 7. How we validate — dogfood on real pushes (pre-merge)

No dedicated smoke PRs. **Revy and Greptile both review each PR push before merge** — same webhook timing ([R8 autostart](../GITHUB_WEBHOOK_DEV.md#automation-r8): `pull_request` `opened` / `synchronize` → index `head_sha` → review → publish on the PR).

```text
Branch PR (docs + code):
  1. Push to PR branch → GitHub webhooks → Revy autostart (and Greptile in parallel)
  2. On the open PR: compare Revy check + issue comment + inline vs Greptile
  3. One row in [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md)
  4. Merge when ready — main push deploys new worker image for the next PRs
```

**What “stale” means (and does not):**

| Means | Does **not** mean |
|-------|-------------------|
| Staging **worker/API image** still on old code after `main` merge (#51 JSON) | Reviewing `main` instead of PR branch |
| Fix: deploy `main` once so workers run current publisher | Branch code is wrong |

**Prefer code hunks** when later investigating empty findings vs Greptile. Docs-only PRs are fine for L1/L2 visual checks.

**Ops checklist** (once after `main` catches up, then forget until next migration):

| Step | Done when |
|------|-----------|
| `main` deploy completed (worker + beat image) | Publisher code matches repo |
| Staging `alembic upgrade head` through `0026` | Migrations applied |
| Revy GitHub App **re-enabled** | Webhooks deliver |
| Workspace `review_autostart_enabled=true` | Autostart on `opened` / `synchronize` |

---

## 8. Gap hypotheses (update per dogfood row)

| ID | Hypothesis | If true on a real PR | Action |
|----|------------|----------------------|--------|
| **H1** | Formatter works; #51 was stale deploy | Greptile-shaped markdown comment on first post-deploy PR | Small polish only (P3 inline, P2 ack) |
| **H2** | Fallback is the real L2 path; Moonshot rarely adds value | Fallback looks good; Moonshot fails or adds little | Lock fallback as v1; optional LLM polish |
| **H3** | L2/L3 look fine but Revy **empty** while Greptile has substance on **code** hunks | Presentation OK; recall/index/generation gap | **Investigate** (DB, index jobs, prompts) — track B tuning, not markdown polish |
| **H4** | Users read comment, ignore check | Comment strong; check ignored | Keep G3 — invest issue comment first |

**PQ-1** (surface vs recall): answered incrementally from dogfood rows, not one gate PR.

---

## 9. Recommended program (one bet)

**Name:** GitHub review surface  
**Thesis:** Make L1–L3 on GitHub match the Greptile **experience** using code on `main`, fixing only what real pushes prove broken. Intelligence parity is explicitly **later**.

**In scope (priority order):**

1. **Deploy + first dogfood row** — ops checklist above; first real PR after deploy.
2. **L2 triage comment** — formatter visible on GitHub; fix wiring/sections if broken.
3. **L1 presence** — G10 lifecycle + neutral paths on real PRs.
4. **L3 inline breadth** — warnings where line-accurate; readable threads.
5. **L1 ack snack** (optional) — Greptile 👀 class on webhook / `@revy review`.

**Out of scope (this program):**

- Repo graph / LSP (STRUCT) — **track B**
- Finding quality / recall tuning beyond publish presentation
- Workspace `.revy/rules` (RC4)
- `/reviewer` pipeline tab
- Human dismiss (R7.6)
- Greptile config parity in customer repos

**Deferred hardening (log, don’t block v1):** orphan G10 check if pipeline link fails; `SKIP_CI_TESTS=false` in Actions.

---

## 10. Greptile as benchmark

On each dogfood PR archive:

- Greptile summary + inline → what did category do?
- Revy check + comment + inline → what did we ship?
- One row: L1 / L2 / L3 gap Y/N vs Greptile **presentation** (not graph depth).

Copy: summary structure, confidence framing, files needing attention, inline explanation, early presence.  
Do not copy: mermaid, agent swarm, vendor MCP loop.

---

## 11. Milestones — optional (not progress bars)

Scaffold programs used git tags (`saas-base-v1`, `review-r*-v*`) as **deploy anchors** for multi-wave work. Revy is **one product** now — dogfood rows on real PRs are the real progress signal, not tag ceremony.

| If you tag at all | Purpose | Optional when |
|-------------------|---------|---------------|
| `review-quality-v1` | Ops bookmark: engine + `0026` + AS2 on staging | You need to bisect “when did pipeline last work?” |
| `review-github-v1` | Ops bookmark: L1–L3 acceptable on GitHub | First PR you’d show a design partner |

**Advice:** Skip tags until you care (e.g. first external demo or prod cut). No agent or phase should block on tagging. PROGRAM folders can stay for history; product truth = **GitHub on the next merge**.

---

## 12. Stale doc debt + PRODUCT_PATTERNS

| Doc | Drift | When to fix |
|-----|-------|-------------|
| PRODUCT_PATTERNS | G10, confidence 0–5 still “in flight” / “defer” | **First dogfood row** that confirms L2 on deploy — surgical row updates only (§ advice below) |
| DOGFOOD #50 | “Gap → wave map (not landed yet)”; Revy suspended | As dogfood rows land |
| P4 full pass | Remaining rows, benchmark template | End of this program |

**PRODUCT_PATTERNS sync advice:** Touch **only rows this wave owns** (L1–L3 / G2, G3, G10, inline, idempotent publish). Flip status `shipped` when GitHub proves it — not when code merges. Do **not** rewrite the catalog or defer track-B rows. One 5-minute edit beats waiting for P4; P4 is consistency sweep, not first sync.

---

## 13. Q-registry

| Q# | Question | Status |
|----|----------|--------|
| **PQ-1** | Surface or recall bottleneck? | **partial** — #52 L2/L3 presentation OK; recall (H3) still track B |
| **PQ-2** | Is formatter on `main` enough for L2? | **yes** on #52 dogfood (after JSON unwrap + comment reuse fixes) |
| **PQ-4** | Greptile role in Revy repo? | **locked** | Benchmark + distill only |
| **PQ-5** | Build graph to match Greptile? | **locked** | **No** now — STRUCT later (track B) |
| **PQ-6** | Dedicated smoke PRs? | **locked** | **No** — dogfood on real pushes |
| **PQ-7** | Visual before intelligence? | **locked** | **Yes** — this program = L1–L3; STRUCT after |

---

## 14. Next doc step

1. Merge [PR #52](https://github.com/raimondskrauklis/revy/pull/52) → deploy staging workers.
2. Append [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md) on next real PR after deploy.
3. **`create-findings`** → general plan from [POST_REVIEW_QUALITY_FOLLOWUPS.md](./POST_REVIEW_QUALITY_FOLLOWUPS.md) (P5+: auto-resolve threads, GraphQL hardening, deploy gate).
