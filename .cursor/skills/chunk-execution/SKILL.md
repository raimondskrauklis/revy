---
name: chunk-execution
description: >-
  Execute one plan subphase at a time (P0.1, P0.2, …) with Cursor TODOs, then
  stop. Use only when the user explicitly invokes chunk-execution or asks for a
  single subphase — not for full plan LOOP.
---

# Chunk execution (one subphase)

**When:** user explicitly asks for **one** subphase / chunk (e.g. “do P0.1 only”, `@chunk-execution`).

**Not:** full plan delivery — use **`phase-execution`** for that (no stops between subphases).

---

## Steps

1. Read `.cursorrules` §2 if migrations; §5 anti-patterns.
2. Open execution file; identify **single** subphase (e.g. P0.1).
3. Create **2–5** TODOs for that subphase only — target files, deliverable, verify command.
4. Implement → run deliverable tests → mark TODOs done.
5. If subphase is **P0.0 / PR review context**: SSOT + agent mirror + `BUGBOT.md` + `test_engineering_context_manifest.py` — see `phase-execution` skill (never skip). Do not babysit Greptile.
6. **Stop.** Report what shipped and what subphase is next. **`ship-changes`** if user wants commit/PR.

Do **not** pre-create TODOs for later subphases. Do **not** continue to P0.2 unless user asks in a **new** message.

---

## Backend

From **`backend/`**: `pipenv run …`. Migrations: handwritten only — no `--autogenerate`.
