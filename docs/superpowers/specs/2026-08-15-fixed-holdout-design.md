# H3d — a fixed holdout split — design

**Goal:** `data.units.holdout` partitions the roster once, a step sees the test units as
`io.units` and the train units as `io.units.train`, and every denominator that should
narrow does. This retires `E-DATA-HOLDOUT-UNSUPPORTED`.

**What it delivers, stated honestly.** **One refusal retired that 6 of 9 feasibility configs
hit, one live defect closed, and zero experiments newly executing.** All nine still earn
`E-DATA-RESOLVER-UNSUPPORTED`, which is H7b's. Under a table-roster substitution *the analysis
does not itself make*, the generous count is **three** (E1, E2, E5) — **not six**: E3, E4 and E6
validate clean and still cannot run, because they read a frozen program through `io.reuse_from`,
which no build provides. The charter's "unblocks 6 of 9" drifts from the feasibility document's
own words, which say *validate clean*.

**What it is not.** Not folds inside cells, and not a holdout inside cells — H3c-3 owns
retrofitting both. Not `io.reuse_from`. Not the resolver.

---

## The measurement this rests on

`docs/superpowers/H3d-SCOPING-2.md`, taken 2026-08-15 against `main` at `78bb794`. It
re-measures `H3d-SCOPING.md`, pinned to `cb96c7d` — **four slices back** (H3c-1, H3c-2, H7a,
H4a). The charter's 16 becomes **19**, and three of its conclusions do not survive.

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Ship as one slice or two? | **One slice, ordered exactly as the scoping's seam prescribes** — refusals and declarations first, the wholesale refusal alive until task 17, honouring last | The seam's argument is an **ordering** argument, and its own cited precedent — `resample` closed one level in before its refusal retired — happened **within H4a**, as its tasks 3 and 12. H4a ran 19 tasks in one slice on exactly this shape. Splitting doubles the spec, plan, whole-branch review and merge for a benefit ordering already delivers. **The seam at 8/9 is recorded as the cut line if the slice runs long** |
| 2 | `groups`/`allocation: between` beside a `holdout` or a `fold` | **Refuse, both, at one check site under one code family** | The two faults are one fault — *a roster-wide evaluation split beside a cell structure* — and both are knowable from declarations alone. Disclosure fails H4a's test: `allocation.json` would record the imbalance truthfully and **no reader would cross the two lists by hand**. This is H3c-3's 3-task refusal and H3d's own, merged into one |
| 3 | Whether the cells refusal waits for H3c-3 | **No — it ships here, with H3c-3 named as the owner of its retirement** | The defect is **live today**: probed at 15 units split 12/3 by arm, `fold_basis` reports 15 so `k=5` is permitted and arm `b` gets **two empty folds**; a roster-wide `frac: 0.2` holdout gives arm `b` **zero test units**. `groups` + `between` + `fold k=5` validates clean right now. No other scheduled slice closes it sooner |
| 4 | The payoff figure | **"One refusal retired that 6 of 9 hit, zero newly executing"** — and where the table-roster substitution is discussed, **three**, not six | H4a's lesson. A refusal-count read as an executable-count a month later is what `CLAUDE.md`'s feasibility procedure step 10 exists to prevent, and the charter's six is wrong even under the substitution |
| 5 | Held-out units and the inference base | **Settled in task 1, before any code** — `CLAUDE.md`'s invariant is that units are the inference base and `n` counts units, so what a holdout does to `n`, the per-unit table and the correction family constrains every later task | H4a's largest disruption was a cross-cutting question surfacing at task 14 and forcing a plan amendment at 15. This one is knowable now |
| 6 | Where the split is recorded | **`allocation.json` gains a fourth key**, and `allocation_hash` needs no change | A holdout is a seeded partition of the same kind H3c-2 already records. `allocation_hash` canonicalizes whatever document it is handed, and its docstring already rules out a `holdout_hash`. Without this a reader cannot tell which units were held out |

---

## What the scoping overturned

**The retirement makes 13 comments in `src/` false, not 4.** The old scoping counted three
prose blocks plus `envelope.py`'s. The real owned set spans `validate.py` ×4, `cli.py` ×3,
`envelope.py` ×2, `units.py` ×2, `artifacts.py` and `materialize.py`, against 8 forward
references that are fine as written. **Three sweeps in H4a stopped one file short**; this one
is swept by claim, not by file.

**`holdout.from` is not reachable through `CONSTANT_COLUMN_RULES`** — asserted in the present
tense at two sites in `units.py`, and **absent from the old decomposition entirely**.

**The draw is two constructions, not one.** `_assign_whole_clusters_by_ratio` takes a
non-optional `Mapping` and indexes it, so the unclustered path is `_apportion` + shuffle.
H3c-2's own experience is that a fixture cannot tell the two apart unless it is built to.

---

## The traps

| Trap | The rule |
|---|---|
| The denominators are the item most likely to ship wrong | `_cond_roster`/`attrition` must receive the **test-narrowed** roster; `max_failed_fraction` and `_units_failed_anywhere` likewise; `provenance.units.n`/`units_hash` **stay whole-roster**, with a comment saying why 240-here and 48-there is not a bug. `runner._counts` computes Kish and cluster counts over *completed* units, so those are holdout-safe by construction — only `resolved`/`failed` need narrowing |
| `W-STATS-RESAMPLE-CLUSTERS` reads the wrong roster | It reads `fold_basis` over the **whole** roster while the draw runs over the test partition — **under-warning by ~1/frac, in the direction of not firing**. H4a shipped it; only a task scoped past `holdout` alone would notice |
| `stratum_varies_within_cluster`'s docstring is stale | It has **three** callers today and claims two rows. H3d is the fourth |
| A fixture that cannot tell the two constructions apart | The clustered and unclustered draws must be pinned against each other, with the bit-stability relation **stated**, or a fixture will pass under either |
| A test pinning the wholesale refusal | Every Part A check is exercised against configs that *also* earn `E-DATA-HOLDOUT-UNSUPPORTED`, and task 17 retires it. **Each such test asserts its new finding appears *alongside* the refusal, never instead of it** — an assertion that survives retirement as a one-line deletion rather than a rewrite |
| A second false present-tense cell claim | `experimental-designs.md` and § A fixed holdout split both carry cell-interaction prose. Task 7 marks them honestly rather than adding a third |

---

## Task decomposition — 19

From the scoping's § 8, in its order. **Tasks 1–8 refuse and declare, with
`E-DATA-HOLDOUT-UNSUPPORTED` alive throughout; 9–16 draw, narrow and record; 17 retires it;
18–19 sweep and pin.**

1. Documents first — the three under-specifications, every new `E-DATA-HOLDOUT-*`, two new
   § Validation rows, the `resample` × `holdout` sentence, **and decision 5's inference-base
   ruling**. Both consistency passes.
2. Envelope closure one level in; rewrite `envelope.py`'s two holdout-stays-whole comments.
3. `design_digest` excludes `holdout.seed`; close the open half of its `spec-defects.md` entry.
4. `_check_holdout`, declaration half A — `method` enum, `frac` in (0, 1), `from` required under
   `by_attribute`, fields meaning nothing under the other method, the seed pin.
5. `_check_holdout`, declaration half B — `stratify_by` existence; the `holdout` × `fold`
   mutual exclusion.
6. `_check_holdout`, roster half — the `by_attribute` two-literal rule, *Holdout strata survive
   clustering* through the **fourth** `stratum_varies_within_cluster` call site (**and that
   docstring corrected**), the zero-size test partition.
7. **The shared cells refusal** — decision 2, with H3c-3 named as owner of its retirement.
8. `holdout.from`'s constant-column accessor and its severity ordering.
9. `units.holdout_for`, construction 1 — unclustered.
10. Construction 2 — clustered, plus `stratify_by`; the bit-stability relation **pinned**.
11. The holdout seed derivation, its own digest suffix with the reason stated.
12. Realize once in `cli.command_run`.
13. Runner narrowing — `io.units` = test, `io.units.train` = train, at every scope.
14. **The denominators.**
15. `W-STATS-RESAMPLE-CLUSTERS` against the test partition.
16. `allocation.json` gains its fourth key.
17. **Retire `E-DATA-HOLDOUT-UNSUPPORTED`** — the loop's last entry, so the loop goes.
18. The owned prose sweep — **13 sites, by claim not by file** — plus the `NOT BUILT` marker and
    its count phrases.
19. Regression and the reader-facing half — a no-holdout run byte-identical to today, and the
    honest count written into the dated executability section.

**Sequencing.** 1 before everything. The refusal stays alive to 17. 14 is the task most likely
to ship wrong and gets the sharpest fixture.

---

## Corrections from planning — appended 2026-08-15, replacing nothing above but qualifying it

The plan author found six disagreements with this spec or the scoping. Two are verified here and
change what gets built; all six are carried in the plan.

1. **The scoping is wrong that passing `"holdout"` to `_stratum_groups` is harmless.** Its § 1
   says the `axis` parameter "is a label used only in messages, so a holdout caller passes
   `"holdout"` and is otherwise unaffected." It *is* used only in messages — but the message is a
   **fixed template** that hardcodes `assign`: verified at `units.py:1235`, a holdout caller would
   print `` `data.units.assign.holdout.stratify_by` ``, **a path no config can hold.** The
   parameter becomes a full dotted path, with its three existing call sites updated.
2. **A thirteenth code is needed and the scoping does not name it.** Its § 4 prescribes a
   `CONSTANT_COLUMN_RULES` entry keyed `holdout`, but that registry's values are `(code, message)`
   pairs and **`E-DATA-HOLDOUT-VARIES` does not exist** — verified, zero hits in `src/` and
   `reference.md`. Minted in the documents task, emitted where the accessor lands.
3. **The draw is three things, not two.** The seed derivation cannot live inside `holdout_for`
   given the task order, so `seed` is a **required keyword argument** that `holdout_for` never
   derives — the same separation `_assign_whole_clusters_by_ratio` already makes by taking an
   `rng` — with `cli.command_run` composing them. Otherwise a task carries a forward reference.
4. **Tasks 13–17 are untestable end to end, and no cell said so.** No config validates while the
   wholesale refusal stands, so those tasks test their seams by direct call and **the retirement
   task carries five enumerated end-to-end pins**, one per wiring task.
5. **Trap 1's four sites are six.** `command_run` passes the roster at six places that decide a
   denominator, including both `_compute_*(roster=)` calls reaching `units_matching`. Three others
   are deliberately **not** narrowed — `weights`, `unit_attributes`, `resample_strata` — being
   key-indexed, so surplus keys are inert.
6. **One unbudgeted gap, filed not fixed.** `technical_n` is a whole-roster `{min, max, median}`
   that would sit beside a test-partition `n` — exactly what `_cond_beside_n` already withholds
   under an arm. It needs `measurements` *and* `holdout` together, which no feasibility config
   declares. Filed with an owner; the denominators task may not be "completed" by absorbing it.

**Task count is 20, not 19** — the regression pin moved to first (see the plan's header), which
splits the old final task in two.

---

## Out of scope, with the route

Folds and holdouts **inside cells** — H3c-3, named in task 7's filing. `io.reuse_from` — unbuilt,
and the reason E3/E4/E6 cannot run whatever H3d does. The resolver — H7b. `allocation_hash`
changes — none needed.
