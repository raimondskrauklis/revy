# Post review-quality — general plan

**Baseline:** [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) — platform research locked (2026-07-27, revised).

**Thesis:** Close the **GitHub review surface** gap (L1–L3). Greptile on this repo is the **visual bar** on every real PR. Engine (L4) is shipped; **review intelligence** (recall, graph, prompts) is **track B** — after GitHub looks and behaves right.

**Prerequisite:** RQ0–RQ9 on `main` (incl. PR #51). Validation on **PR branch pushes** (pre-merge autostart) — same as Greptile. Worker image updates on `main` deploy only.

**Ship model:** Per-phase execution files in this folder (`GITHUB_SURFACE_P*_EXECUTION.md`) — index [GITHUB_SURFACE_EXECUTION.md](./GITHUB_SURFACE_EXECUTION.md).

---

## Sequencing (locked)

```text
  Track A (this program)          Track B (later)
  ─────────────────────          ─────────────────
  L2 triage comment              STRUCT / cross-file context
  L1 presence (G10)              Prompt / lens tuning for recall
  L3 inline breadth              RC4 workspace rules
         │                                │
         └─ credible GitHub UX ──────────┘
            before chasing Greptile depth
```

---

## Cross-cutting (every phase)

- **Dogfood:** Greptile vs Revy row per **PR push** → [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md) (pre-merge).
- **Tenancy:** workspace scope on all publish paths.
- **Trace:** pipeline artifacts when publish logic changes.
- **Tests:** unit tests for formatter / inline / G10 changes (`backend/tests/unit/`).
- **i18n:** EN+LV for new **app** strings and optional webhook ack — GitHub markdown stays English v1.
- **Migrations:** hand-written only if schema required (expect none).
- **Docs:** sync [PRODUCT_PATTERNS](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) when L1–L3 rows validated.

**Layers:** L1 presence · L2 triage · L3 inline · L4 memory (**closed** — do not re-open).

---

## Dogfood rubric (pass / fail per real PR)

Use on the **first post-deploy PR** and whenever something looks wrong.

| Layer | Pass (Greptile-comparable) | Fail → phase |
|-------|----------------------------|--------------|
| **L2** | Issue comment: confidence, files list, findings table, G9 prose when applicable; markdown not JSON | P1 — wiring or formatter |
| **L1** | Check shows `in_progress` early; completes with sensible conclusion; draft-after-index → neutral (RQ9) | P2 |
| **L3** | Error/critical findings with line → inline thread; suggestion when line-accurate | P3 if missing for severities we already publish |
| **H3 (recall)** | L2/L3 presentation OK but Revy **empty** vs Greptile on **code** hunks | **Investigate** track B (index/DB/prompts) — not L2 markdown work |

**L2 v1 bar:** `build_pr_review_comment_fallback` is sufficient to pass. Moonshot narrative (H2) is optional enhancement.

---

## P0 — Worker current + live validation

**Goal:** Staging **workers** run post-merge image; first PR branch push answers PQ-2.

**Scope — in:**

- Ops once: `main` deploy, `0026`, app enabled, autostart on.
- Open PR, push branch → autostart on `synchronize` (same as Greptile timing).
- Record row in [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md).

**Scope — out:**

- Feature code unless push shows broken publisher (JSON comment, formatter not wired).
- Artificial smoke-only PRs (PQ-6).

**Deliverables:** Ops checklist ticked; at least one dogfood row; scope for P1–P3 (or H3 investigate note).

**Depends on:** `main` includes RQ0–RQ9.

---

## P1 — Triage surface (L2)

**Goal:** Top-level issue comment matches Greptile **triage** class — confidence, files needing attention, G9, table; check stays compact (G3).

**Scope — in:**

- Confirm `github_publish_formatter` on deploy; fix gaps dogfood proves (sections missing, wrong body on comment vs check, JSON leak).
- Harden deterministic fallback if Moonshot unavailable (H2).
- Golden-style unit test on fallback markdown shape (regression guard).

**Scope — out:** mermaid, merge-verdict automation, new LLM vendor, recall tuning.

**Deliverables:** L2 rubric pass on a real PR; check body compact per G3.

**Depends on:** P0 first row (H1 or H2). If H3 (empty vs Greptile on code) — finish L2/L3 visual work first, then investigate separately.

---

## P2 — Presence (L1)

**Goal:** PR feels “under review” before publish completes.

**Scope — in:**

- G10 `in_progress` → `completed` on real PRs (pipeline check linked to publish).
- RQ9 neutral finalize when PR draft/closed after index.
- Optional ack on `@revy review` / webhook (Greptile 👀 class).

**Scope — out:** draft autostart (skipped by design); orphan-check hardening (defer log only).

**Deliverables:** L1 rubric pass; ack shipped or explicitly deferred in dogfood.

**Depends on:** P0. Can overlap P1 once L2 is readable.

---

## P3 — Inline action (L3)

**Goal:** Act from the diff — not only error/critical **inline** (table already shows all severities).

**Scope — in:**

- Extend `inline_publish_findings_statement` to warnings (and info if line-accurate).
- Thread body: title + message; R6 `suggestion` when `is_publishable_suggestion`.
- Findings need `file_path` + `start_line` for inline — check DB if table has rows but no threads.

**Scope — out:** P-badge markup parity; Greptile thread volume on docs-only PRs.

**Deliverables:** L3 rubric pass on a PR with warning+ line findings; table remains overflow fallback.

**Depends on:** P1 (triage credible). Visual polish before chasing track B depth.

---

## P4 — Doc sync (optional tags)

**Goal:** Docs match what GitHub actually shows.

**Scope — in:**

- PRODUCT_PATTERNS consistency sweep (L1–L3 rows); DOGFOOD gap table updated.
- post-review-quality README; Greptile benchmark log template.
- Git tag **only if** you want a deploy bookmark (first demo / prod) — see findings §11.

**Scope — out:** STRUCT / RC execution plans; tag ceremony as a gate.

**Deliverables:** Doc consistency. Tags optional.

**Depends on:** P1–P3 or waived with explicit dogfood rationale.

**Note:** First surgical PRODUCT_PATTERNS touch can happen after P0/P1 dogfood — do not wait for P4.

---

## Locked (do not re-open)

| Topic | Resolution |
|-------|------------|
| Greptile in Revy repo | Benchmark + distill (PQ-4) |
| Graph / deep recall now | No — STRUCT track B (PQ-5) |
| Visual before intelligence | Yes (PQ-7) |
| Dogfood method | Real pushes, not smoke PRs (PQ-6) |
| G3 split bodies | Check compact; full narrative on issue comment |
| GitHub-first | `/reviewer` secondary |
| Confidence 0–5 | Comment/check prose — not check `conclusion` (G2) |
| L2 minimum | Deterministic fallback — Moonshot optional |

---

## Open items

| ID | Question | Resolved by |
|----|----------|-------------|
| **PQ-1** | Surface vs recall? | Dogfood rows; H3 on code PR → track B |
| **PQ-2** | Formatter sufficient? | First post-deploy real PR |

---

## Next step

**`phase-execution`** → [GITHUB_SURFACE_EXECUTION.md](./GITHUB_SURFACE_EXECUTION.md) — LOOP P0 → P4.
