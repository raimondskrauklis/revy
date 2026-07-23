---
name: author-community-group-corpus
description: >-
  Author PG Louvain community group methodology in corpus/platform/en/.
  Wraps author-corpus with bundle overlay keys, L0/L1 layering, ownership
  matrix, and composer service paths. Use for co-bid-graph group reading and
  overlay pages — not for cpv-market screens, lot indicators, or graph-stack
  three-graph treatise.
---

# Author community group corpus

**Prerequisite:** Read and follow [`author-corpus`](../author-corpus/SKILL.md) (manifest, eval, ship checklist).

**Program:** `docs/corpus_implementation/communities/` — [`AGENT_BRIEF.md`](../../../docs/corpus_implementation/communities/AGENT_BRIEF.md), [`COMMUNITY_GROUP_CORPUS_FINDINGS.md`](../../../docs/corpus_implementation/communities/COMMUNITY_GROUP_CORPUS_FINDINGS.md) § Content ownership.

**Split rule (RAG):** Default **one bundle overlay family → one L1 file** owns formulas and `compute_status` gates. **L0 overview** = batch Louvain/scopes/UI. **L0 group-reading** = how to read one group (Wachs, members, panels) — **no overlay formulas**. **Conduct + corroboration** share one L1 file (paired top-level bundle keys). **Structural depth + lookalikes** share one L1 file. **Subclique + subperiod** share one L1 file. Never a nine-overlay megadoc.

**Terminology (locked):**

| Say | Not |
|:---|:---|
| **PG community group** / **Louvain group** | “market community” without grain |
| **co-bid graph** | Neo4j UUID graph or `IND-N06` market screen |
| **overlay** / **bundle key** | generic “panel” without key name |
| **advisory structure** | collusion verdict |

---

## Before you write — decision tree

```
Which page type?
├── Batch algorithm, scopes, browse tables → overview L0 — STOP (link only)
├── Three graphs PG vs market vs Neo4j → graph-stack MD — STOP (link only)
├── IND-N08 on CPV market → cpv-market-advisory-ind-n08 — STOP (link only)
├── C15 live JSON in bundle → DI handoff — STOP (methodology-only bridge page OK)
├── Read one group (Wachs, members, surfacing) → L0 group-reading — no overlay math
└── One overlay key family → proceed (L1 filename below)
```

**Source of truth for bundle keys:** `backend/app/services/genai/composer/community_group.py` (`CommunityGroupComposer`).

---

## Mandatory code reads (by overlay family)

Read the **service `get_*` method**, `compute_status` branches, and composer caps.

| Bundle key | Service | Engine / SQL | Also read |
|:---|:---|:---|:---|
| `conduct` | `CommunityConductService` | `conduct_service.py` | `graph_community.py` constants |
| `corroboration` | `CommunityPairOverlayService` | `pair_overlay_service.py` | pairs cap `_MAX_PAIRS` |
| `overlays.collaborator_topology` | `CollaboratorReadService` | `collaborator_read_service.py`, `collaborator_topology_sql.py` | `bridge_pairs`, C9/C10 |
| `overlays.partition_crosswalk` | `PartitionCrosswalkService` | `partition_crosswalk_service.py` | C12 |
| `overlays.structural_depth` | `StructuralDepthService` | `structural_depth_service.py` | C5/C6 |
| `overlays.lookalikes` | `LookalikeService` | `lookalike_service.py` | C4 |
| `overlays.buyer_carveout` | `BuyerCarveoutService` | `buyer_carveout_service.py` | C14 |
| `overlays.subclique_conduct` | `SubcliqueConductService` | `subclique_conduct_service.py` | ML-V2 P5 |
| `overlays.subperiod_overlay` | `CommunitySubperiodOverlayService` | `subperiod_overlay_service.py` | C17 batch window |

**Shared (every page):**

- `backend/app/constants/graph_community.py` — `CONDUCT_LAZY_MEMBER_THRESHOLD`, scope enums
- `backend/app/services/genai/composer/community_group.py` — `_MAX_MEMBERS`, `_MAX_PAIRS`
- Wachs metrics — `wachs_metrics.py` (group-reading L0 only)
- Product UX hints — `docs/graph_integration/community_discovery/GRAPH_COMMUNITIES_INVESTIGATOR_GUIDE.md` (**distill**, do not index)

**GenAI bundle (no chart twin):**

- `backend/app/services/genai/prompts/community_group_v1.py` — overlay vocabulary for narration
- `backend/tests/fixtures/genai/community_group_v1_sample.json` — fixture v2 shape

---

## Layering — do not duplicate

| Topic | Owner corpus file | Your L1 page |
|:---|:---|:---|
| Louvain batch, scopes, UI routes | `co-bid-graph-communities-louvain-wachs-scopes-and-ui` | link |
| Read one group (Wachs, members, panels) | `co-bid-graph-group-reading-…` | link from L1; L1 does not repeat Wachs table |
| PG ≠ market network ≠ Neo4j | `graph-stack-three-graph-views-…` | link + one sentence |
| IND-N08 advisory on CPV market | `cpv-market-advisory-ind-n08-…` | link when digest references N08 |
| Market N06/N37 screen math | `cpv-market-network-rotation-…` or L2 screen | link — trap stays on three-graph or market doc |
| **This overlay’s formula + gates** | **your L1 file** | own |
| **`compute_status` / defer_reason** | **your L1 file** | own |

Full matrix: `docs/corpus_implementation/communities/COMMUNITY_GROUP_CORPUS_FINDINGS.md` § Content ownership.

---

## Filename + doc_id

```text
co-bid-graph-overlay-{family-kebab}.md
co-bid-graph-group-reading-{topic}.md   # L0 reader only
```

**`doc_id` pattern (locked):** `platform:co_bid_graph_{suffix}:en`

| Page | File | doc_id |
|:---|:---|:---|
| Overview (L0 existing) | `co-bid-graph-communities-louvain-wachs-scopes-and-ui.md` | `platform:co_bid_graph_communities_overview:en` |
| Group reading (L0) | `co-bid-graph-group-reading-louvain-wachs-members-and-panels.md` | `platform:co_bid_graph_group_reading:en` |
| Conduct + corroboration | `co-bid-graph-overlay-conduct-corroboration.md` | `platform:co_bid_graph_overlay_conduct_corroboration:en` |
| Collaborator C9+C10 | `co-bid-graph-overlay-collaborator-topology.md` | `platform:co_bid_graph_overlay_collaborator_topology:en` |
| Partition crosswalk | `co-bid-graph-overlay-partition-crosswalk.md` | `platform:co_bid_graph_overlay_partition_crosswalk:en` |
| Structural + lookalikes | `co-bid-graph-overlay-structural-depth-lookalikes.md` | `platform:co_bid_graph_overlay_structural_depth_lookalikes:en` |
| Buyer carveout | `co-bid-graph-overlay-buyer-carveout.md` | `platform:co_bid_graph_overlay_buyer_carveout:en` |
| Subclique + subperiod | `co-bid-graph-overlay-subclique-subperiod.md` | `platform:co_bid_graph_overlay_subclique_subperiod:en` |
| DI bridge (methodology only) | `co-bid-graph-overlay-di-relationship-bridge.md` | `platform:co_bid_graph_overlay_di_relationship_bridge:en` |

❌ Do not use `platform:community_group_*` or rename shipped `doc_id`s.

---

## L1 section checklist (overlay family)

Copy depth from exemplar after G1 depth pass — structure per overlay:

1. **Bundle key + catalog panels** — which UI panels consume this payload
2. **Service identity** — module path, entry method
3. **Payload shape** — top-level JSON keys investigators see in bundle
4. **`compute_status` table** — `ready` / `deferred` / `insufficient_data` / `error` with exact triggers from code
5. **Thresholds and caps** — `CONDUCT_LAZY_MEMBER_THRESHOLD`, `_MAX_MEMBERS`, `_MAX_PAIRS`, scope rules
6. **`defer_reason` / `insufficient_reason`** — JSON keys when present
7. **Interpretation** — advisory screening tone; what not to infer
8. **Traps** — PG vs market graph, Louvain vs collaborator-only bridges, subperiod = batch window
9. **What not to claim** — overlay-specific mistakes
10. **See also** — concrete `doc_id` links (not wildcards)
11. **References (code)** — bullet paths

**Group-reading L0** uses Wachs/members/surfacing checklist in findings — no overlay formulas.

---

## Manifest

```yaml
metadata:
  domain_prefix: co-bid-graph
indicator_codes: []   # or IND-N08-CPV on overview only
```

---

## Eval pairs (required)

Add to `corpus/eval/en/methodology_qa.yaml`:

1. **Definition** — overlay purpose, key fields, service.
2. **Trap** — defer gate, three-graph, or surfacing — tag `community_trap` when appropriate.

`expected_doc_id` must match the **L1 owner** for overlay-specific questions (not overview when answer is overlay semantics).

Tags: `co_bid_graph`, overlay slug (`collaborator_topology`, etc.).

---

## Group-reading sync

In `co-bid-graph-group-reading-louvain-wachs-members-and-panels.md`, **See also** table lists each L1 `doc_id` by bundle key — no formula paste.

---

## Ship

Complete [`author-corpus`](../author-corpus/SKILL.md) ship checklist, then:

- [ ] Findings inventory row → L1 depth done
- [ ] Group-reading See also updated
- [ ] `rg 'CONDUCT_LAZY' corpus/platform/en/co-bid-graph-overlay` — threshold in overlay owner only
- [ ] Eval pair targets correct `doc_id` (**defer/trap retarget → G2.1**, not new overview rows during G1)
- [ ] `test_co_bid_graph_methodology_retrieval_recall_on_manifest_md` green (**G2 gate only**)
