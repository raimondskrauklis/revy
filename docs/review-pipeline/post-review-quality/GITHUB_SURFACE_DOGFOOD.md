# GitHub surface — dogfood log

**Purpose:** One row per real PR — Revy vs Greptile on **presentation** (L1–L3). Append as pushes land; do not split across DOGFOOD #50.

**When:** Every open PR push where autostart or `@revy review` runs (pre-merge). Same timing as Greptile.

---

## Row template

| PR | Push / SHA | L1 presence | L2 triage comment | L3 inline | Greptile delta | Notes |
|----|------------|-------------|-------------------|-----------|----------------|-------|
| #… | `abc1234` | Y/N | Y/N | Y/N | … | H1–H4 if applicable |

**L2 pass:** markdown issue comment — confidence, files, table, G9 when relevant; not JSON.  
**L3 pass:** error/critical/warning/info with line → inline when publishable; table for all severities.  
**Recall (later):** if L2/L3 look fine but Revy empty while Greptile has substance on **code** hunks → investigate (index/DB/prompts) — not a reason to polish markdown.

---

## Rows

| PR | Push / SHA | L1 | L2 | L3 | Greptile delta | Notes |
|----|------------|----|----|-----|----------------|-------|
| — | — | — | — | — | — | *First row after worker deploy + PR push* |
