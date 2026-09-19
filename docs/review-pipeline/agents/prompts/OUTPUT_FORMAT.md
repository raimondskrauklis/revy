# Bugbot output — context over format

**Index:** [prompts/README.md](./README.md)

**Principle (RC-D23):** We want **reasoning and trace quality**, not a specific handoff shape. Local `Task(subagent_type=bugbot)` often returns platform XML (`<answer>`, `<bug>`) or a one-line “no bugs” — **accept that**. Do not fight OUTPUT_FORMAT in Custom Instructions.

| Who | Owns what |
|-----|-----------|
| **Reviewer subagent** | Trace code; challenge mechanism; any output format the platform allows |
| **Master** | Read **thinking export** when answer is thin; synthesize gate decision for human; optional tables below are **master templates**, not subagent requirements |

Smart reviewer + good context needs **depth**, not markdown tables. Archive thinking when useful — [chain_of_thoughts/](../chain_of_thoughts/).

**Two runtimes:** Hosted GitHub Bugbot (`BUGBOT.md` on `main`, append-only) vs local Task subagent — [distill § RC-D23](../chain_of_thoughts/cursor_bugbot_judge_p56_evidence_close.md).

---

## Custom Instructions (paste to subagent)

**Keep brief:** `VERB` + `SCOPE` + failure path + contract §. **Do not** demand table shape — platform XML wins.

### FIND (phase gate)

```text
PASS: 1 (find)
Report actionable bugs introduced by the diff.
Trace code; cite file:line and mechanism.
Cite locked FINDINGS/EXECUTION IDs when applicable.
Out of scope: pre-existing issues unless this diff worsens them.
Any output format is fine — XML, bullets, prose.
```

### VALIDATE (babysit pass 1)

```text
PASS: 1 (validate)
VALIDATE: <fn → failure path>
Prove or break the claim — trace the path; do not rubber-stamp.
Greptile/revybot thread: <verbatim or summary>
Any output format is fine.
```

### CLOSE (pass 2+)

```text
PASS: 2 (closure)
Prior findings: <list from master handoff>
Mark each CLOSED or STILL OPEN with evidence in your reasoning.
New actionable bugs only.
Any output format is fine.
```

Append from [PHASES.md](./PHASES.md) § RQn for FIND only.

---

## Master synthesis (after subagent returns)

Use these sections when briefing the **human** — write them yourself from subagent answer **+ thinking export**:

| Section | Purpose |
|---------|---------|
| **Findings / closure** | What to fix or CLOSED items |
| **Deferred** | Hypotheses traced but not filed (RC-D16) — often only visible in thinking |
| **Scope note** | § RQn or Greptile thread + path traced |

If subagent says “no bugs” but thinking explored edge cases → master records Deferred rows; gate stays green only when reasoning supports it.

**When to export thinking:** Non-trivial gate, empty XML answer, or distill candidate → `chain_of_thoughts/` · [judge P56 example](../chain_of_thoughts/cursor_bugbot_judge_p56_evidence_close.md).

---

## PR body (scope for humans + Revy)

A short PR body helps humans and Revy; it is not a substitute for `.revy/review-context.json` + `BUGBOT.md`.

```markdown
## Scope
<phase> — <one line>

## Mechanism
<failure path or locked decision>

## Contract
<execution file>

## Test plan
- [ ] …

## Out of scope
…
```

Do not log or babysit Greptile comments.

---

## Example master Deferred rows (templates)

### RQ4 pass 2 (closure)

| Sev | Topic | Why deferred |
|-----|-------|----------------|
| low | Draft PR leaves G10 check `in_progress` | Pre-existing; needs `neutral` finalize (RQ7/G10 parking) |
| — | — | Fixed in follow-up commit: embed fail partial commit; review enqueue G10 |

### Greptile babysit (RC-D16)

Source: [local_bugbot_from_ui_2](../chain_of_thoughts/local_bugbot_from_ui_2) · commit `71e4911`.

| Sev | Topic | Why deferred |
|-----|-------|----------------|
| low | Worker dies after TX1, before TX2 | Celery redelivery; not introduced by split |
| medium | Migration supersede → publish before reconcile → green check | One-shot deploy; D10-M accepted |
| low | Duplicate Celery → second GitHub check | Pre-existing race |

### Judge P56 evidence CLOSE (RC-D23)

Source: [cursor_bugbot_1.txt](../chain_of_thoughts/cursor_bugbot_1.txt) · [ui8](../chain_of_thoughts/cursor_bugbot_from_ui8.txt).

| Sev | Topic | Why deferred |
|-----|-------|----------------|
| low | old_line vs new_line window | Design tension in `extract_evidence_from_patch`; document or dual anchor later |
| — | **Gate read** | ~140 lines thinking CLOSED prior finding; XML answer empty — **master used thinking**, not XML |

---

## Subagent shell (parent copies from PROMPTS.md)

```text
Full Repository Path: /Users/…/revy
Diff: uncommitted changes | branch changes
Custom Instructions:
  VERB: FIND | VALIDATE | CLOSE
  SCOPE: <files>
  VALIDATE: <fn → path>   # VALIDATE only
  OUT OF SCOPE: <one line>
  <PHASES § RQn — FIND only>
  <Greptile verbatim — VALIDATE only>
  <OUTPUT_FORMAT pass block — no table requirements>
```

**Legacy note (RC-D19):** Earlier gates asked subagents for Findings + Deferred tables; platform XML overrode that. **Do not re-litigate** — master reads thinking instead.
