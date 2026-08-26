## Task 21

> **AMENDED 2026-08-25 by the controller, from batch C's sweep.** **`E-REPL-FOLD-CELLS` survives at SIX
> sites, not four**: `reference.md` 4 **and `CLAUDE.md` 2**, measured newline-insensitively with a can-fail
> control. **M15's count phrase says "reference.md-only", so a task checking itself against M15 alone reads
> 4 and stops** — which is how a documented refusal outlives the code that raised it. **The `CLAUDE.md`
> pair is the controller's to edit; report them rather than taking them**, and treat M15's number as the
> claim it is rather than the count it looks like.

**Corrections that bind this task: C2, C18.**

**The document sites, none of them locatable by position.** Name what a sibling row *does*; when you
insert or remove a row, check every row it **moved** and every count phrase near it.

| Site | What happens |
|---|---|
| `reference.md` § Validation, *One split, not one cell each* | **Removed** — the refusal it describes is gone |
| `reference.md` § Validation, *Folds fit inside the cells* | **Rewritten BACK, not deleted.** It currently reads *"Superseded by One split, not one cell each"* — deleting the pointed-at row and leaving the pointer is how a table acquires a dangling reference. Restore its pre-H3d meaning: `k` bounded by the smallest cell's unit count, or its cluster count under `cluster_by` |
| `reference.md` § Errors `validate` reports | The `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS` rows **removed from the registry** |
| `reference.md` § A fixed holdout split | The *"A roster-wide split beside a cell structure is refused, not drawn"* bullet **replaced** by what is now true: the split happens within each cell, and `frac` is bounded by the smallest cell |
| `reference.md` § Clustered units | The *"Under `allocation: between`, a roster-wide fold is refused rather than drawn within each cell"* paragraph **rewritten to the present tense**, keeping *"Partitions are computed once per run, not once per condition"* and the paragraph that reconciles the two — **which survives cells and needs no change** |
| `experimental-designs.md` § Between-subjects factorial | *"A fold or a holdout drawn within each cell is not built"* → what is built |

**C2: none of these is repairing a present-tense falsehood** — all three "not built" sentences are
honestly marked today. They are repairing a **build state that moved**.

**Run both consistency passes.** Mechanical: every relative link and `#anchor` resolves, no duplicate
anchors, table rows match header column counts, no trailing whitespace or tabs, `×` not `x`, hyphens
in anchors — skipping fenced blocks throughout. Cross-document: the shared worked example (untouched
here, and confirm it), config completeness, enum comments, schema fields in prose, declared vs.
derived, prevented mistakes. **After removing `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS`, grep
the four documents, `CLAUDE.md` and the feasibility analysis for what should no longer exist** —
and **filter the file list, never the output of the sweep.**

**Run every sweep NEWLINE-INSENSITIVELY.** These files are hard-wrapped and a phrase can straddle a
break; a line-based `grep -n` undercounts in the direction that makes a table look complete. The
design's § 0 M15 records the pre-edit counts to check yours against: `within each cell` → **2**, both
inside § Clustered units' one paragraph; `is not built` → 3 in `reference.md` and 1 in
`experimental-designs.md`; `E-DATA-HOLDOUT-CELLS` → 3 and `E-REPL-FOLD-CELLS` → 4, both
`reference.md`-only; *Cells are populated* → 2 and *Allocation is coherent* → 2; *One split, not one
cell each* → 2. **Prove each sweep can fail** by running it against a string known to be present.

**Must not touch:** `docs/superpowers/**` except as tasks 20 and 23 direct; the development record is
exempt from both passes and retro-editing it destroys the evidence it holds.

