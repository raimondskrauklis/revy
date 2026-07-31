---
name: create-general-plan
description: >-
  Turn a baseline-ready findings doc into a concise, phased GENERAL plan (not
  execution). Indicates phases, goals, deliverables, dependencies — per-phase
  execution files come later. Use when the user asks for a general plan or to
  plan full implementation from findings.
---

# Create General Plan

A general plan = **phases and their goals/deliverables**. **NOT execution** (no file lists, no steps — those live in per-phase execution files, see `create-execution-plan`).

## Process

1. Read `.cursorrules` and the findings doc. It must be baseline-ready (decisions locked, contradictions resolved).
2. **Phase 0 = foundations/prerequisites** — shared-infra repairs, enums, schema, anything every later phase depends on. Schedule first; never discover mid-build.
3. Order phases **on evidence**. If cost/feasibility is unknown, put an **experiment/spike phase early**. Many phases is fine; group into **waves** if needed — never a v1/v2 split.
4. Carry findings decisions as **locked**. The only open items are calibration (numbers from experiment). Don't re-open direction.

## File

`docs/<area>/<TOPIC>_GENERAL_PLAN.md`.

## Phase format (one tight block each)

- **Goal** — one line.
- **Scope** — in / out.
- **Deliverables** — the outcomes (not the steps).
- **Depends on** — prior phase(s).

## Cross-cutting (state once as first-class, woven through every phase)

**Lineage/explainability, coverage + exclusion surfacing, visualization, i18n (EN+LV), unit tests** are not a final phase — each phase ships them. Call this out explicitly; when findings require it, prioritize visualization + full lineage + user-facing explainability.

## Rules

- **Concise. Long plans are not followed by agents.** No micro-explaining, no estimates, no timelines, no scope tables.
- One paragraph per phase max. If a phase needs detail, that's the execution plan's job.
- **Sizing for `phase-execution`:** each general-plan phase should map to **one** execution file with **3–6 subphases** — if a phase would exceed that, split the general plan before writing execution docs (see `create-execution-plan`).
- End with: the single remaining open item (if any) and the next step (**`create-execution-plan`**).
