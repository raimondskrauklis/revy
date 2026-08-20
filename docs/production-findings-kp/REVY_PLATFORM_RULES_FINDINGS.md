# docs/agents/findings/REVY_PLATFORM_RULES_FINDINGS.md

# Revy platform rule packs — findings

**Status:** Baseline for what Revy checks besides the program contract  
**Date:** 2026-08-14  
**Scope:** House rules on **files the diff touches** (whole file, not hunk-only). Not Bugbot. Not dumping `.cursorrules`.

**Verified against:** `.cursorrules` §2–5 (coding) vs §0/§6 (agent chat + LOOP); `.revy/review-context.json` `paths[]` + `scope` as today’s include mechanism; Greptile-style explicit `rules.md` + glob-scoped file pointers (not CodeRabbit auto-ingest of `.cursorrules` / `AGENTS.md`).

---

## Build principles

- The coding agent implements the phase. It does **not** re-audit the rest of a touched file for platform drift. Revy does — that is the split.
- Revy is a reviewer (comments / check). Pack markdown must not say “do not rewrite the PR” — that is already the product.
- Packs are short. Reviewer and coding agents are capable; a checklist of every token name is noise.
- Do not paste `.cursorrules` into Revy. Section 0 (chat, “no docs”) and section 6 (LOOP) are not review criteria and cause false positives on existing files.

---

## Why whole-file + short packs

Revy’s review unit is **files in the diff**, not the hunk. A one-function change can still leave `HTTPException`, a PascalCase enum, or `bg-blue-500` on an unchanged line in the same file. That is the gap the coding agent will not close on its own.

Greptile-class reviewers load explicit rule packs and optional file pointers **scoped to paths**. CodeRabbit auto-slurps `.cursorrules`; that fights this repo (mixed agent process + coding standards). Adopt the Greptile shape.

---

## Three options (compared)

| # | What | Verdict |
|:---|:---|:---|
| **1** | Dump `.cursorrules` / `AGENTS.md` into every review | **Reject.** LOOP, “no md”, file-header-on-generate become nags on legacy lines. |
| **2** | Chat: “include frontend packs?” per program | **Reject.** Same failure mode as “Continue?”. Forgotten, inconsistent. |
| **3** | Predefine packs. P0.0 sets `rule_packs` from `scope` (same moment as today’s review-context). Docs-only → `[]`. | **Adopt.** |

Override lives in the **execution file** JSON, once. Not in chat.

---

## Packs (predefined)

| Id | File | Derive from `programs[].scope` |
|:---|:---|:---|
| `platform` | `.revy/rules/platform.md` | `backend/**` **or** `frontend/**` |
| `backend` | `.revy/rules/backend.md` | `backend/**` |
| `frontend` | `.revy/rules/frontend.md` | `frontend/**` |

Catalog SSOT: `.revy/review-context.json` → `rule_packs_catalog` (present even when idle).

Program entry:

```json
"scope": ["backend/**"],
"rule_packs": ["platform", "backend"]
```

Also list those markdown files on `programs[].paths` with `description: "rules"` so today’s path-based ingest still loads them. Keep `.cursor/BUGBOT.md` on the **three program docs only** — Bugbot does not need the packs.

**Ad-hoc ship** (`active_program` null): do not wire a fake program. Product should load catalog packs whose tree matches files in the review set (`backend/**` → platform+backend, and so on). Until that exists, a one-off PR can set `rule_packs` on a transient program entry — still no chat prompt.

**Corpus / docs-only** scope (`corpus/**`, `docs/…`): `rule_packs: []`. QuietChip rules on a markdown PR are noise.

---

## Agent vs Revy (token split)

| Who | Does | Does not |
|:---|:---|:---|
| Coding agent | Phase work, patterns in **new** code | Re-scan the whole existing file for house style |
| Revy | Whole touched file vs packs; **findings** | (N/A — reviewer, not an implementer) |
| LOOP (batch / WHILE) | Fetch comments; fix what still applies | File-wide restyle because a 400-line file exists |

Triage (smart, not a matrix):

- Real anti-pattern in a touched file (bare `HTTPException`, unsafe JSONB expand, native `<select>`, hardcoded chroma) → fix even if the line was not in the hunk. That is the point.
- Taste / ~150-line soft limit / “this file is old” → skip with a one-line note. Do not expand the phase into a rewrite.

---

## What stays out of packs

- LOOP cadence, Bugbot shells, “do not write md unless asked”
- `PLATFORM_CONTEXT.md` and the full color-token guide (unscoped, every review)
- File-header-on-generate (false positive on every legacy file)

If `.cursorrules` §2–5 gains a new **checkable** anti-pattern, add one line to the matching pack. Do not sync prose both ways.

---

## Decisions registry

| Q | Question | Status | Resolution |
|:---|:---|:---|:---|
| Q1 | Feed Revy `.cursorrules`? | **locked** | No. Short packs. |
| Q2 | Agent asks include frontend/backend in chat? | **locked** | No. Derive from `scope` at P0.0. |
| Q3 | Always both packs? | **locked** | No. Scope-derived. Corpus → none. |
| Q4 | Put “do not rewrite” in pack files? | **locked** | No. Revy already returns findings. |
| Q5 | Must-fix every pre-existing nit in a touched file? | **locked** | LOOP: anti-patterns yes, file-wide restyle no. Not a Revy prompt. |
| Q6 | Scoped extra docs (color guide, decimal JSON)? | **open** | Add later via catalog pointers if packs prove too thin. |

---

## Devil's advocate

- Short packs miss edge cases. That is acceptable; Revy already catches many without a novel. Grow a line when a real PR shows a hole.
- Hygiene on unchanged lines can inflate a line-count extract. Triage (Q5) is the valve — do not turn packs off to avoid it.
- Dual SSOT (`.cursorrules` vs packs) will drift. Packs stay tiny so drift is obvious.

---

## Experiment / verification (next PR with packs on)

- Backend-only program: Revy comments cite backend/platform rules; no QuietChip / `--tp-*` comments. **Pass** if frontend pack is absent from that review.
- A hunk-local change in a file that still has a pack violation on another line: Revy comments on that line. **Pass** if the coding agent had not touched it.
- Docs-only corpus PR: `rule_packs: []`. **Fail** if Revy nags SQLAlchemy style on markdown.

---

## References

- Packs: `.revy/rules/`
- Wiring: `.revy/review-context.json` `rule_packs_catalog` + `programs[].rule_packs`
- Agent coding rules (not for Revy ingest): `.cursorrules`
- Greptile: explicit `rules.md` + scoped `files.json`; no `.cursorrules` auto-ingest
- CodeRabbit: auto-detects `.cursorrules` / `AGENTS.md` — **reject** for this repo
- Sibling: [REVY_PUSH_CADENCE_FINDINGS.md](./REVY_PUSH_CADENCE_FINDINGS.md)
- Product handoff: [REVY_PRODUCT_RULE_PACKS_HANDOFF.md](./REVY_PRODUCT_RULE_PACKS_HANDOFF.md)
