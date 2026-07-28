# Local Bugbot — judge evidence `+`/`−` CLOSE (PR #56)

**Date:** 2026-07-28 · **Branch:** `feat/judge-input-quality` · **Commit:** `fe703cb`  
**Raw thinking exports:** [cursor_bugbot_1.txt](./cursor_bugbot_1.txt) · [cursor_bugbot_from_ui8.txt](./cursor_bugbot_from_ui8.txt)

**Context:** CLOSE pass after `extract_evidence_from_patch` hardening (`pending_minus` + old-line tracking). Master asked whether Bugbot cut corners; this distill captures what the traces show.

---

## RC-D23 — Two Bugbot runtimes (do not conflate)

| Runtime | When | Config | Output |
|---------|------|--------|--------|
| **Hosted GitHub Bugbot** | After push on PR | `.cursor/BUGBOT.md` on **`main`** (appended to Cursor default — [does not replace](https://forum.cursor.com/t/does-bugbot-md-override-cursor-s-default-base-prompt/150078)) | Product XML / PR comments; team dashboard rules can override repo |
| **Local Task subagent** | Pre-push gate (`Task` `subagent_type=bugbot`) | `VERB` + failure path; accept XML / any shape |

**Tuning limits (hosted):** `BUGBOT.md` is plaintext append; no auto-read of `.cursor/rules`; scoped globs via dashboard; `@cursor remember` on PR for learned rules. **Cannot** override core detection/format entirely — steer with contract links and “what to ignore.”

**Internal reviewer:** Local Task subagent **is** our Bugbot job today. Alternative: `generalPurpose` agent with [ROLES.md](../prompts/ROLES.md) brief (no platform XML cage) — tradeoff: less “Bugbot-trained” bias, more format compliance.

---

## What `cursor_bugbot_1.txt` did well (~140 lines)

- Traced every `+`/`−` path: spacer in window, `+` outside new window, hunk reset, tail flush, duplicate flush
- **CLOSED** prior finding (“out-of-window `+` drops in-window removals”) with mechanism proof
- Explicitly noticed **XML vs OUTPUT_FORMAT** conflict (lines 59–67, 105–111)
- Rejected net-new hypotheses after concrete traces (two-change hunk, strict zip safety)

---

## Where output looked thin (not a format bug)

| Observation | Response |
|-------------|----------|
| Empty `<answer>` / “no bugs” | **Expected** for local subagent — read thinking export ([bugbot_1](./cursor_bugbot_1.txt)) |
| No Deferred table in XML | Master writes Deferred for human from thinking — not subagent job |
| ui8 scoped to four threads | Brief issue — net-new paths need explicit “file any bugs found while tracing” |

**Locked rule (RC-D23):** Do not fight platform XML. Custom Instructions = **VERB + path + scope**; master owns synthesis.

**Master gate:** Read thinking → fix real bugs → re-CLOSE until reasoning is clean (pytest/ruff still required).

---

## revybot thread triage (same session — master VALIDATE)

| Thread | Verdict |
|--------|---------|
| `edited` title not persisted | **REJECTED** — `existing.title = fields["title"]` in `_upsert_pull_request` |
| PR body not truncated | **REJECTED** — `_truncate_utf8` in `_build_review_prompt` |
| Dedup drops duplicate `-` | **Mostly REJECTED** on current code — both lines kept when in old-line window |
| `end_line` string parsing | **CONFIRMED** (info) — fixed via `normalize_finding_end_line` in `fe703cb` |

---

## Bugs found in Bugbot thinking — fixed in this pass

| Issue | Fix |
|-------|-----|
| Context between **separate** `-` groups paired unrelated removal with later `+` | New `-` after `space`/`plus` clears pending (does not flush to collected) |
| Hunk boundary dropped orphan `-` in previous hunk | Flush pending via old-line window on `@@` header |
| Empty lines in hunk caused line drift | Skip blank lines without advancing counters |
| `+` outside window dropped in-window removals | Flush old-line window before clear (prior commit) |
| Unrelated minus in same hunk as target change | Clear pending between change groups |

## Deferred (documented — not bugs for v1)

| Topic | Why |
|-------|-----|
| old_line vs new_line numeric window | `start_line` is new-file; Moonshot prompt now states this; removal-only uses old-line final flush |
| Hosted vs local Bugbot output shape | RC-D23 — context over format |

---

## Links

- [OUTPUT_FORMAT.md](../prompts/OUTPUT_FORMAT.md)
- [ROLES.md — VERB table](../prompts/ROLES.md)
- [CODE_REVIEW_LEARNINGS.md § RC-D23](../../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md)
