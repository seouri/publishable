# Batch C tail — tasks 11 and 12, and what tasks 8, 9 and 10 shipped

**Status: both complete, gates clean.** Written 2026-08-25.

| Task | Commit | What landed |
|---|---|---|
| 11 | `138434a` | `sweep.yaml`'s `partitions_within`, plus both orphaned obligations |
| 12 | `a86bc87` | Seven readers verified against a per-cell `fold_members`; **no code change** |

Branch base for this batch: task 10 at `25037ec`. Baseline measured here, full unfiltered suite:
**3384 passed, 1 skipped, 2 xfailed** — the figure the dispatch gave, confirmed rather than carried.
Final: **3395 passed, 1 skipped, 2 xfailed** (3 tests from task 11, 8 from task 12).
`ruff check`, `ruff format --check` and `mypy` clean at each commit.

---

## 1. Task 11 — the disclosure key

`sweep_document` gains `partitions_within: list[str] | None`, written **inside** the
`if partitions is not None:` branch and only when the list is non-empty. Placement rather than a
comment: no document can carry a key describing partitions it does not record, and that property is
structural rather than argued.

**C8, in the docstring rather than in the plan alone.** Composing `train` within the cell is
arithmetically the same set — cells partition the roster, the merge is index-wise, so
*"every other partition concatenated"* is `roster \ partition_i` either way. The key discloses the
thing that is *not* the same: under cells the flat `train` names a side no execution ever sees,
because every condition is arm-narrowed first, so a repeat-scope step in a cell is handed
`cell ∩ (roster \ partition_i)`. The fixture pins that as a number: `train` is 8 units, the side the
cell's execution sees is 2.

**One derivation, not two.** The predicate "were these drawn within cells?" now lives once, as
`units.populated_cells(cells)` — the list `partition_within_cells` loops over and reduces on, and
the list `cli` tests before writing the key. A second spelling at the `cli` site is a record claiming
a draw that did not happen; that is why the helper was extracted rather than the expression repeated.
The **axis names** come from a populated cell's own key (the object handed to the draw), not from
`group_axes` (the input it was built from).

`reference.md` § The other files a run writes gains the one sentence that is the record's own
description, naming the key and what a reader crosses (`allocation.json`'s arms) to recover a step's
real train side. Task 21 owns every other document site; this sentence's links (`#expansion-modes`,
`#allocationjson--who-went-where`) were checked to resolve, and the line carries no tab and no
trailing whitespace.

### C13 — the third emit site, re-read

`sweep.sweep_document`'s *"partitions were drawn but no `fold` level is declared"* guard is unchanged
and still correct, and **two** claims in that block needed re-confirming under the merge, not one:

- `zip(fold.members, partitions, strict=True)` still pairs. `partition_within_cells` returns
  `merged`, built as `[[] for _ in range(k)]`, so the list is `k` long by construction for the loop
  path, and `partition_units`' own `k` for the reduction path.
- **`train`'s composition by object identity (`other is not part`) still holds** — the half that
  would have broken silently. Its stated ground was *"`partition_units` builds a fresh list per
  fold"*, which is no longer the producer; the merged lists are freshly built here instead, so the
  property survives for a **new** reason. Both are asserted as behaviour in
  `tests/test_sweep.py::test_h3c3_merged_partitions_pair_with_the_fold_members_and_compose_train`,
  with the `strict=True` raise as the can-fail half.

**Naming disagreement:** the plan and the design call this function `build_sweep_document`; the code
has `sweep_document`, and has had since it was written. Nothing was renamed.

## 2. Task 11's two orphaned obligations — both were unclaimed, both taken here

### (a) `Prepared.cells` gains its unpack line

Measured before claiming it: `_execute_prepared`'s unpack block has no `cells` line and no local by
that name anywhere in phases 6-10 (`awk` over the function body, zero hits), so nothing earlier in
the slice had taken it. The line is added, and its first reader is the `partitions_within`
derivation.

The two docstring paragraphs asserting the field has no unpack line — *"`cells` is the second field
it does not unpack"* and *"It is a field with **no unpack line yet** … an unread one is an `F841`"* —
are **deleted, not rewritten**. Thirty-SEVEN is untouched (the field count does not move) and the `c`
sentence keeps its own claim.

**A disagreement with the amendment, measured:** *"measured, `ruff` reports one `F841`"* is false at
`25037ec` — `uv run ruff check .` there reports **All checks passed**. There was no unpack line, so
there was nothing unread to report; the `F841` is what would have appeared had the line landed
without a reader. C20's *"`_execute_prepared` unpacks them one per line"* was the accurate statement
of the intent, and it is now true of `cells` as well.

### (b) `units.cell_fold_basis` — **deleted**, not called

No production caller existed, and none was going to. Its own docstring's grounds for keeping it are
false against the plan it cites:

- *"H3c-3's own remaining tasks bound `E-DATA-HOLDOUT-EMPTY` and `W-DATA-CELL-THIN` over the thinnest
  cell, and **neither names it**"* — task 14's F7 says *"`E-DATA-HOLDOUT-EMPTY` at `validate`, naming
  the 2-unit cell"* and task 18's F3 says *"exactly one warning naming the smaller cell"*. **Both name
  it**, so both need `thinnest_cell`'s pair, not this function's scalar.
- Both bound over a cell's **unit count**; `cell_fold_basis` returns a **fold basis**, which is the
  cluster count under a declared `cluster_by`. Wrong shape as well as wrong signature.

That leaves no caller wanting the number without the label, so the function goes. Task 3's tests keep
**every literal** and are re-pointed to `thinnest_cell(...)[0]`; one test is renamed
(`test_the_cell_wise_fold_basis_…`) so no test name greps for a deleted function, and the one comment
asserting the two functions cannot drift is deleted with the delegation it described. The docstring
material that was only in `cell_fold_basis` — the one-number rule, the empty-cell rule, the
reduction, C4's *`fold_basis` does not gain a `cells` argument* — is now in `thinnest_cell`, which is
where the walk is.

Two prose references re-pointed rather than deleted, because each carries a live rule:
`validate._resolved_cells`' digest paragraph, and
`tests/test_validate.py::test_the_min_clusters_denominator_is_roster_wide_not_the_thinnest_cell`,
whose docstring states Ruling LL **and** names the mutation it exists to catch — that mutation is now
spelled `thinnest_cell(roster, cluster_by, cells)[0]`.

**Grepped, with every hit attributed** (`grep -rn cell_fold_basis` over `src/`, `tests/`, `docs/`,
`.superpowers/`, before and after): 14 hits in `tests/test_units.py` (import, section header, test
name, six call sites, three docstrings, one comment), 1 in `src/publishable/validate.py` (prose),
2 in `tests/test_validate.py` (docstring), 4 in `src/publishable/units.py` (the definition plus
`thinnest_cell`'s and `partition_within_cells`' prose). **Zero** in `src/publishable/__init__.py` and
**zero** in the four documents — this is an internal deletion with no document consequence. Every
remaining hit is in the **development record** (the plan, the design, the task briefs, batch reports
b1/b2), which is exempt from retro-editing and is left as written.

**Guard-pin arm A.** Batch B's mechanical proof — *"`git diff … tests/test_units.py` has no deleted
lines at all"* — no longer applies, because task 11 deletes lines in that file. Replacement, and it
is a stronger form: the arm's 55-line body extracted from `864f702` and from this tree diffs
**byte-identical** (sha1 `598497011eea9f1539846a38d402206e427e3b49` on both).

## 3. Task 11's mutations

All against the **full unfiltered** suite, counts read from that run's own summary line.

| Mutation | Result | Reads |
|---|---|---|
| **MU-14** (prescribed): write `partitions_within` unconditionally | **1 failed / 3386 passed** | guard-pin **arm B**, and it writes a key (`[]`) rather than crashing, so the arm fails for its own reason |
| **MU-A**: project the cell key's **levels** instead of its axes | **1 failed / 3386 passed** | `test_h3c3_partitions_within_names_the_axes_the_folds_were_drawn_inside`, alone |
| **MU-B**: `merged = [[]] * k` — one shared list for every fold | **7 failed / 3380 passed** | includes the new C13 test, whose `train` composes to nothing under it |
| **MU-3** (batch A's, re-run): `max` for `min` in `thinnest_cell` | **13 failed / 3374 passed** | includes the **re-pointed** task 3 assertions — the mutation that fails the moved assertions themselves |

Every revert was made by editing back, `__pycache__` cleared, and verified by **re-running**: the
tree after MU-A's revert diffs byte-identical against the pre-mutation copy, and the final suite is
green at 3387 (task 11) and 3395 (task 12).

**Two axes on purpose.** The fixture is `arm` × `site` over 12 units, four cells of three, because
one axis cannot distinguish the axis names from the levels, from a truncation to the first axis, or
from a reversal — its name is the whole list, the first element, and its own reverse.

## 4. Task 12 — seven readers, no code change

The expected outcome held: **no reader needed arm narrowing it does not have**, and nothing in `src/`
changed. Each unit is in exactly one cell and in exactly one partition, so `fold_members` stays the
flat `label -> frozenset(keys)` partitioning the roster that `fold_members_for` produced before.

Eight tests: one at the source (the mapping is a partition, in `test_units.py`), and one per reader —
`stats.handed_to`, `stats._gather_repeats`, `stats.collapse_repeats`, `stats.repeats_disagreeing`
(the last two H5b's split), `runner.attrition`, `runner._handed_keys`,
`runner._units_failed_anywhere`.

**Every test carries its own discriminator**, because the flat shape alone passes under the draw this
slice replaced — a test of nothing. The fixture (`h3c3_per_cell_fixture`, in `test_units.py`, imported
by the other two files) returns **two** mappings from one declaration: the per-cell draw and the
whole-roster draw, both at digest `"d"` over 9 `control` and 3 `treatment` at `k: 3`. The whole-roster
one is genuinely degenerate at that digest — treatment counts `[0, 1, 2]`, so `fold01` holds no
`treatment` unit — and each reader's answer is computed under **both** and pinned unequal:

| Reader | Per-cell | Whole-roster |
|---|---|---|
| `handed_to` | the three units cover all three folds | they cover `fold02`, `fold03` |
| `_gather_repeats` | 3 units admitted | 1 |
| `collapse_repeats` | 3 rows | 1 |
| `repeats_disagreeing` | `{"tag": 2}` | `{}` |
| `_handed_keys` | `[1, 1, 1]` per fold | `[0, 1, 2]` |
| `attrition` | resolved 3, completed 3, failed 0 | resolved 3, completed 1, failed 2 |
| `_units_failed_anywhere` | `set()` | `{"t0", "t1"}` |

Neither mapping is hand-written: both come from `partition_within_cells`/`partition_units` through
`fold_members_for`. Task 10's property (a non-empty `(arm, fold)` denominator, pinned by mutation
end-to-end) is **not** re-pinned here; these are direct-call reader tests with the stale mapping as
their control.

### Task 12's mutations

| Mutation | Result | Reads |
|---|---|---|
| **MU-C**: `handed_to` returns every label under a non-`None` mapping | **15 failed / 3380 passed** | readers 1-4 and `attrition` (reader 6), plus 6 pre-existing fold tests |
| **MU-D**: `_handed_keys` returns `keys` rather than the fold's | **14 failed / 3381 passed** | readers 5 and 7, plus 12 pre-existing |
| **MU-E**: `partition_within_cells` ignores its cells and draws whole-roster | **12 failed / 3383 passed** | **all eight tests added by this task** — the mutation that fails the discriminators as such |

Reverted by editing back and re-run green (3395).

## 5. `reference.md`'s four `E-REPL-FOLD-CELLS` sites — routed, and NOT folded in here

`E-REPL-FOLD-CELLS` is retired in the code (task 10) and `reference.md` still describes the refusal as
live at four sites. **Task 21 owns all four by name**, in its own table, so they are left alone:

| Site | Task 21's row |
|---|---|
| § Validation, *Folds fit inside the cells* | "Rewritten BACK, not deleted" — restore its pre-H3d meaning |
| § Errors `validate` reports, the `E-REPL-FOLD-CELLS` row | "removed from the registry" |
| § A fixed holdout split, the *"roster-wide split beside a cell structure is refused"* bullet | "replaced by what is now true" |
| § Clustered units, the *"a roster-wide fold is refused rather than drawn within each cell"* paragraph | "rewritten to the present tense" |

**Swept newline-insensitively** (each file read with newlines collapsed, then `re.findall`), with a
can-fail control: `E-REPL-FOLD-CELLS` → `README.md` 0, `design-principles.md` 0,
`experimental-designs.md` 0, **`reference.md` 4**, `feasibility-llm-growth-studies.md` 0,
**`CLAUDE.md` 2**. Control on a token known present: `E-DATA-HOLDOUT-CELLS` in `reference.md` → 3,
which is the design's own M15 figure, so the sweep can find what is there.

**One thing for the controller.** M15 records *"`E-DATA-HOLDOUT-CELLS` → 3 and `E-REPL-FOLD-CELLS` →
4, both `reference.md`-only"*. That is true of the four documents; **`CLAUDE.md` carries two more** —
in the H3d entry (*"both that and a holdout beside the same structure are now a named refusal"*) and
in the H3c-3 ownership sentence (*"retiring `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS`"*). Task
21's instruction names `CLAUDE.md` in its sweep, so they are routed; its **count phrase** does not
include them, and a task 21 that checks its sweep against M15 alone will read 4 and stop.

## 6. Tasks 8, 9 and 10 — read from their diffs, there being no report

**Task 8 (`49ff46e`)** — `units.partition_within_cells(roster, k, digest, cells, clusters=, strata=)`:
loops `partition_units` per **non-empty** cell in key order, each sub-roster rebuilt in **roster
order** and each `clusters`/`strata` map restricted and kept **total** over it (C26's contract
preserved), merging **index-wise**. The **bare** digest goes to every call. No populated cell reduces
to the single whole-roster call, which is the path guard-pin arm D counts. Beyond the brief, and
worth carrying: the function **checks that the cells partition the roster** rather than assuming it —
an overlapping cell and an uncovered unit each raise `ContractError` `E-RUN-FOLD-UNRESOLVED`, and
`reference.md`'s § Errors row for that code gained a clause naming this third shape. `cli`'s import
list keeps `partition_units` behind a `# noqa: F401`; that binding is **not** dead — guard-pin arm D
reads and patches `cli_mod.partition_units`, so the import cannot be removed while that arm stands.
Its commit message's *"the same rule `cell_fold_basis` states"* is now stale by the deletion above;
the rule is `thinnest_cell`'s.

**Task 9 (`e6802d1`)** — tests only, `tests/test_units.py`: `_f1`/`_f1_cells`/`_sizes` and two tests.
The empty-fold table with **C1's mapping stated in the docstring** (`S2` spans the arm boundary, which
is what makes the cluster counts 2 and 4), the whole-roster row `[7, 3, 3, 1, 1]` as the **can-fail
control**, and `[7, 1, 0, 0, 0]` / `[3, 2, 1, 1, 0]` per arm. Both directions of the bound: `k: 5`
refused with the cell named, `k: 2` honoured and no empty fold in either arm.

**Task 10 (`25037ec`)** — `validate._check_evaluation_split_cells` loses its `fold` arm and every
paragraph justifying it; the docstring now says what remains and that the function and its call site
go when the holdout is drawn per cell (task 16). `tests/test_validate.py`:
`test_a_fold_beside_a_cell_structure_is_refused` became
`…_is_drawn_per_cell_and_bounded_by_it`, and `test_both_split_kinds_beside_a_cell_structure_report_both_codes`
is **gone** (one code, one site). **C18's test survives, correctly** —
`test_a_group_axis_alone_triggers_the_refusal_without_between` is still present and still passing,
because the function keeps its `holdout` arm; **task 16 is the task that must delete it**, and C18
says delete, not adapt. `tests/test_cli.py` gained the property the refusal stood in for, pinned
end-to-end through `_handed_keys` and `run.yaml`'s per-fold denominators, with the `k: 5` refusal as
its second half. What is **not** visible in the diffs: any mutation counts. The commit message gives
gate figures (3384) and no mutation, so whether task 10's own prescribed mutation (remove the cell
clause from the bound, watch a zero denominator) was run is unrecorded — the test's docstring
describes it as the thing a mutation would fail, which is a claim about a mutation rather than a
measurement of one.

## 7. Concerns

1. **The `cell_fold_basis` deletion is a judgement call made under the amendment's "either call it or
   delete it".** Nothing in tasks 13-20 loses a helper it was promised: tasks 14 and 18 want
   `thinnest_cell`'s pair, which is untouched and now carries the full docstring. If a reviewer
   prefers the other branch, restoring the wrapper is a five-line revert of one hunk.
2. **`CLAUDE.md`'s two `E-REPL-FOLD-CELLS` mentions are outside M15's count** (§ 5 above). Whoever
   dispatches task 21 should carry that, since M15 is what that task checks itself against.
3. **Task 10's mutation is unrecorded** (§ 6). If the batch gate wants it, it is one edit —
   remove the cell clause from `_fold_k`'s bound — and the test that must fail is named in the
   docstring.
4. **`partitions_within` is written by `run` only**, never by `resume` (the whole `sweep.yaml` write
   sits under `if resumed is None:`), which is correct and worth stating: a resumed run reads the
   first attempt's document rather than re-deriving the key.
