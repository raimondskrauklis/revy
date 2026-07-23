---
name: author-scope-screen-corpus
description: >-
  Author Deep Investigation scope screen (IND-*-SCOPE) methodology in
  corpus/platform/en/. Wraps author-corpus; prefix scope-screen. Not lot
  indicators; not -CPV market screens.
---

# Author scope screen corpus

**Prerequisite:** [`author-corpus`](../author-corpus/SKILL.md), [`TERMINOLOGY.md`](../../../docs/corpus_implementation/TERMINOLOGY.md).

**Split rule:** One active `-SCOPE` code → one L2 file. L1 catalog lists six codes — no formulas. L3 provenance doc is cross-cutting (market adapter).

**Say:** scope **screen** (product: investigator **scope** lot set). **Not:** scope indicator in investigator prose. **Not:** signal (signals = triggered lot indicators or entity findings in DI).

**Code unchanged:** `IND-M01-SCOPE`, `analysis_level = historical`.

**Prefix:** `scope-screen` · **`doc_id`:** `platform:scope_screen_ind_{code_base}:en` (e.g. `platform:scope_screen_ind_m01_scope:en`).

**Code reads:** `calculators/scope/*.py`, `scope_indicator_orchestrator.py`, `di_market_l3_source.py` for L3/provenance links.

**Layering:** Link `platform-grain`, lot L2 twins (`indicator-lot-ind-*`), CPV twins (`cpv-market-screen-*`). Own formula + L1/L2/L3 behaviour in scope L2 only.

**Ship:** manifest + README + eval pair + L1 catalog **See also**; complete `author-corpus` checklist.
