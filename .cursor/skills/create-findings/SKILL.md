---
name: create-findings
description: >-
  Investigate a feature/problem against the real codebase, DB, and docs, then
  write a concise findings doc that becomes the baseline for a general plan. Use
  when the user asks to research a topic, make findings, or scope new work
  before planning.
---

# Create Findings

A findings doc is the **baseline for the plan — no implementation, no execution steps**.

Findings are not limited to a single screen or greenfield feature. They may cover **any platform slice** — domain logic, shared infra, data pipelines, APIs, UI, ops, compliance, eval/QA, third-party integrations — or a **cross-cutting** topic that touches many areas.

When the user needs more than a gap inventory, the same doc may also carry **advice** (recommended direction, phased options, trade-offs) and **external research** (industry patterns, literature, vendor docs) — still **no execution steps**. Match depth to scope: a narrow bug may need one section; a platform program may need tracks, phases, and a subfolder index.

## Process

1. Read `.cursorrules`.
2. Investigate: **codebase + DB (`docs/DATABASE_CONNECTION_GUIDE.md`) + relevant docs**. Newer docs win, but **always verify against code** — docs go stale. Cite `file.py:line`, migrations, MV names.
3. **Discuss decisions one at a time in chat. Push back; don't agree by default.** Don't poll uselessly.
4. **Ground every claim.** Mark **verified** (with path) vs **assumption**. Never assert a "current behavior" you haven't read.
5. Bake in **build principles**: real data only / **no fallbacks/imputation**; **never mislead** (precise or N/A); full **lineage/transparency** where the product needs it; **no corner-cutting** (fix shared infra so all consumers benefit); reuse math, don't fork.
6. Keep it living — update as decisions resolve. Record every **exclusion + coverage**.

## File

`docs/<area>/<TOPIC>_FINDINGS.md`.

Use `docs/<area>/<topic>/` + `README.md` when the topic is large, multi-phase, or will spawn several related docs — not only for one product vertical.

## Structure (drop sections that don't apply)

- **Build principles** — the non-negotiables for this work.
- **Terminology** — new terms, enum values, code namespaces.
- **What exists vs genuinely new** — inventory with **reuse caveats / traps** (stale filters, wrong grain, scope coupling).
- **Catalog** — capabilities, screens, jobs, or workstreams; each with rationale (domain or literature basis) and exact method. For large programs, split into **phases or tracks** with verification gates — labels should match the topic, not a fixed template.
- **Advice / options** *(optional)* — recommended path, alternatives, defer/reject — when the ask is directional, not only descriptive.
- **External research / patterns** *(optional)* — outside methods or prior art; explicit **adopt / defer / reject** for this project.
- **Data scope & exclusions** — universes, what's excluded (compute-time vs filter-late), why.
- **Edge cases** — the hard things, named, not swallowed.
- **Decisions registry** — table: `Q# | question | status | resolution`. One source of truth.
- **Parking lot** — open items + **Phase-0 prerequisites** (foundation/shared-infra repairs).
- **Devil's advocate** — what would undermine this.
- **Experiment / verification** — pass/fail outputs to measure, not just wall-clock.
- **References** — code paths, docs, literature.

## Rules

- Concise. A finding the agent won't read is worthless.
- Reconcile contradictions before declaring baseline-ready; run a peer-review pass (`architecture-peer-review`).
- Verify, don't trust. The biggest risk is a confident stale claim.
- Do not force every section or a subfolder — use what fits the topic's size and shape.
