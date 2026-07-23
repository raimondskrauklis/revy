---
name: architecture-peer-review
description: >-
  After an architecture or implementation plan is drafted, perform a careful
  peer review against the real codebase. Use when cross-checking a single
  findings, general, or design doc. For per-phase execution file sets, use
  execution-peer-review instead.
---

# Architecture peer review

**Not for execution file sets** — use **`execution-peer-review`** (reviews P0…Pn **one file at a time** with per-file gap tables).

1. Read the user’s plan/spec (and any linked paths they mention).
2. Verify claims **in the repo**—models, migrations, services, APIs, workers, frontend if relevant. Prefer evidence over assumptions.
3. Report: **gaps, inconsistencies, shortcuts, and improvements** (prioritize what would cause wrong behavior or rework).
4. **Questions:** only those needed to resolve ambiguity or product scope; avoid generic brainstorming.
5. Stay proportional: short plans → shorter answers; large plans → structured sections or a checklist.

**Default user request (invoke with):**  
“Read this plan, cross-check with the codebase. Look for gaps, inconsistencies, corners cut, and things to improve. Ask any questions you have.”