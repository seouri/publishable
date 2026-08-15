# Task 14 report — `allocation.json` records the draw; `E-DATA-ASSIGN-DRAWN` retires

**Status: COMPLETE.** Commits `d2799d5`, `c3e61cc`, `9579dba`. 1615 passed + 2 xfailed; `ruff check` and
`mypy` green. (`ruff format` deliberately not run.)

## Step 1 had no code change, and that needs an owner

`artifacts.build_allocation_document` **already** emitted per-axis `seed` and `strata`
(`{axis: plan.seed ... if plan.seed is not None}`), so nothing about the empties had to be
"replaced" — a `by_attribute`-only document still writes `{}` for both, correctly, and the two
pinned `allocation_hash` literals never moved. What changed there is the four-paragraph docstring
(which argued the keys were empty *in this build*) and the tests. A reviewer expecting a code diff
at Step 1 will not find one; the behaviour was built ahead of its record.

**The mixed case** is `tests/test_artifacts.py::test_a_drawn_axis_records_its_seed_and_strata_and_a_read_one_records_neither`
— one `by_attribute` axis and one `random` axis in one document, exact mappings
(`seed == {"arm": 11}`, `strata == {"arm": ["site"]}`) rather than membership. Because there was no
code change to give it teeth, it was mutation-tested in **both** directions (M1/M2 below): the
drawn axis's presence and the read axis's absence each fail their own mutation.

`tests/test_cli.py::test_a_drawn_axis_runs_end_to_end_and_records_its_seed` is the retirement end to
end: a `method: random` config now reaches a run directory at all (`command_run` validates first and
used to return), completes, and leaves a `seed` in `allocation.json` over a roster carrying no `arm`
column.

## The retirement

`DRAWN_ASSIGN_METHODS` and the `elif` **stay** — the brief's "remove the `elif` branch" predates
tasks 8–13, which filled that branch with the `ratio`/`block_size`/`stratify_by` rows. Only the
`c.error("E-DATA-ASSIGN-DRAWN", ...)` call is gone. The tuple's *reason* changed from "which values
this build refuses" to "which branch a block takes", and that is now what `units.py`'s and
`validate.py`'s comments say.

Twelve doc sites, all cleared: the ten that named the code (nine `reference.md` — plus two more the
`E-DATA-ASSIGN-BLOCK-SIZE`/`-BLOCKED-CLUSTER` rows added since task 1 measured it — and one
`experimental-designs.md`) and the two that described the refusal without naming it
(`reference.md` § Expansion modes, `experimental-designs.md` § Crossed group axes; both deleted
outright, since the sentence they carried was only the refusal). `git grep E-DATA-ASSIGN-DRAWN` over
the four documents now returns nothing; the control (`E-DATA-ASSIGN-LEVELS`, 5 hits) proves the sweep
can find something and `E-DATA-NOTHING` (0) that it can find nothing. Every sweep filtered the
**file list**; no sweep's output was filtered. `docs/superpowers/` is gitignored and was left as
found (task 1's ruling on point-in-time scoping records).

Source: the § Validation row *Assignment method isn't drawn* and the § Errors `validate` reports row
are deleted; § Allocation's refusal paragraph is replaced by "**All three methods execute**";
`units.py`, `cli.py`, `artifacts.py` and `validate.py` docstrings rewritten. Four past-tense
references survive **in code comments only** ("it carried `E-DATA-ASSIGN-DRAWN` until…"), because
they are what explain why `DRAWN_ASSIGN_METHODS` lives where it does.

**Allowlist re-checked empirically, not read**: over an 8-unit roster, `random`, `blocked` and
`by_attribute` each realize a plan, stratified and unstratified; `random` clustered realizes one;
`blocked` beside `clusters` is the **only** `NotImplementedError` left, and `validate` still refuses
that combination as `E-DATA-ASSIGN-BLOCKED-CLUSTER` (task 11 untouched).

## Both routed defects were CLOSED, not recorded

Neither needed a new code, so both are the existing rule reaching further.

**1. `ratio` that starves an arm** — § Validation's new row *Every arm draws units*,
`E-DATA-ASSIGN-LEVELS`. The drawn branch ends by calling `units.assignment_for` on a block every row
above accepted and turning its `ContractError` into a finding; the plan is **discarded**, and the
comment says why (a validate-time plan anyone reused would be the second membership producer,
inside the check written to close a gap).

**Gated to the unstratified, unclustered draw, and the residue is documented in the same row.**
`validate` has no design digest, so it may only draw where the sizes are seed-independent —
`_apportion` decides them from `(len(roster), ratio)` alone. `_assign_whole_clusters_by_ratio`
shuffles the cluster order before its stable size sort, so which arm is left empty there genuinely
varies by seed and a placeholder-digest draw could be wrong in *either* direction; a stratum naming
an earlier group axis needs a membership only the run's own ordered draw produces. Those two still
reach `E-DATA-ASSIGN-LEVELS` at the draw, which is now a row in § Errors core raises as well — that
table had no entry for it at all, and the closing phrase that located a row by position ("That last
row") is rewritten to name the row by its codes.

**2. Cluster straddle** — `E-DATA-ASSIGN-STRATIFY-VARIES`, same row, broadened. A `stratify_by`
naming an earlier axis is now read through the column that axis reads (`validate._read_axis_column`,
which resolves `from` the way `assignment_for` does rather than re-deriving it), so a `from` varying
within a cluster is refused before the cluster can be split. An earlier axis that **draws** is
exempt by construction — it allocated whole clusters. Zero draws are performed for this check.
Recorded in `reference.md` § Validation and § Errors `validate` reports; **not** in
`spec-defects.md`.

## Mutations (applied, run, FAIL confirmed, reverted, PASS confirmed; `__pycache__` deleted each way)

| # | Mutation | Result |
|---|---|---|
| 1 | `seed`/`strata` → `{}` in `build_allocation_document` | mixed-document test FAILS |
| 2 | drop the `plan.seed is not None` / `plan.strata` filters | mixed-document test FAILS (read axis appears) |
| 3 | *Every arm draws units* never runs | `..._ratio_that_starves_an_arm...` and the `blocked` sibling FAIL |
| 4 | drop the already-reported guard | `..._draw_check_is_skipped_for_a_block_already_reported` FAILS |
| 5 | drop the unstratified/unclustered gate | `..._does_not_reach_a_stratified_or_clustered_block` FAILS |
| 6 | `_read_axis_column` ignores the method (drawn axes read a column too) | **SURVIVED at first** — see below; FAILS after the fixture fix |
| 7 | axis-name strata never recorded | `..._axis_that_splits_a_cluster_is_refused` FAILS |
| 8 | `_read_axis_column` ignores a declared `from` | same test FAILS |
| 9 | reinstate the `E-DATA-ASSIGN-DRAWN` error | the end-to-end `run` test FAILS |
| 10 | `findings_before_block` → `0` (the skip read per config, not per block) | `..._skip_is_per_block_and_not_per_config` FAILS |

**The dimension my own tests could not see (mutation 6).** The control asserting "an earlier axis
that *draws* earns no finding" passed with the method guard deleted — because its `sex` block
declared no `from`, so the mutated helper defaulted to the axis name, found no such attribute, and
returned `None` anyway. The test was proving the *absence of a column*, not the *method*. Fixed by
declaring `from: patient_sex` on the drawn axis — a field `random` ignores — so the mutated helper
finds a real varying column and refuses a design core performs correctly. Commit `c3e61cc`.

## Two verifications the reviewer asked for

- **The out-of-enum arm of `_read_axis_column` is reachable and correct.** An earlier axis declaring
  `method: by_column` earns `E-DATA-ASSIGN-METHOD` and the loop continues, so the helper does run for
  it — and returns `None`, so no `-STRATIFY-VARIES` is derived from a fault already reported. Checked
  by running `_check_assign` on exactly that config: the finding set is `{E-DATA-ASSIGN-METHOD}`
  alone.
- **The already-reported skip is per *block*, not per config**, and is now pinned by
  `test_the_skip_is_per_block_and_not_per_config`: a config whose first axis has a malformed `ratio`
  and whose second is a clean drawn block over a starving roster reports both codes. Mutation 10
  below is the one that test exists for — without it, comparing against `0` instead of the branch's
  own entry count survives every single-axis test in the file.

## Test churn worth knowing about

Retiring the code made 34 tests fail. Most were `{DRAWN, X} → {X}`. Three classes needed more than
that:

- Tests whose whole subject was the refusal (`test_a_drawn_assignment_method_is_refused`) were
  **repurposed, not deleted into tautologies**: it now asserts a clean `validate` *and* the
  partition `assignment_for` realizes (every unit placed, once, both arms non-empty).
- Accept-path tests collapsed to `found == set()`. Each such assertion is paired with a realized
  outcome or with a sibling refusal test on the same fixture, per the "an empty set is
  indistinguishable from a deleted check" hazard.
- `write_config`'s roster is **one** unit, which is a broken roster for a two-arm draw: *Every arm
  draws units* correctly reports it everywhere. A `_wide_roster(tmp_path)` helper (8 units) is called
  by the tests whose subject is a block that should validate clean; its docstring says why.

## Concerns

1. **Open, by decision, and documented in the registry row: a clustered or axis-stratified draw that
   starves an arm still validates clean and raises at the draw.** This is the residue of defect 1's
   close. Closing it needs a real design digest at validate time (or a second emptiness rule, which
   the single-producer seam forbids). `tests/test_validate.py::test_the_draw_check_does_not_reach_a_stratified_or_clustered_block`
   pins the gate so widening it is a deliberate act.
2. **`resume` still does not exist, and the "read rather than re-drawn" rule now matters.** Recorded
   in `reference.md` § Resuming and in `build_allocation_document`'s docstring: under `by_attribute`
   a re-derivation re-read a column and agreed; under a draw a second draw is a second allocation,
   and `assign_seed_for` makes it *likely* to agree, which is the wrong property for the record of
   which patient was in which arm. Not built, per the brief.
3. **Task 13's concern 1 is untouched and still reachable**: an axis with absent/empty
   `groups[].levels` is admitted by `sweep.selector_paths` and skipped by `_resolved_group_axes`, so
   `validate` can approve an order the draw then raises on. Refusing it is a separate rule with no
   row; not this task's.
4. **The `NOT BUILT` register is unchanged, checked rather than assumed.** It marks four
   *declarations* (`data.units.holdout`, `{resolver:}`, `statistics.resample`,
   `statistics.null_test`); this was a *method value*. The spelled count ("Four"), the enumeration,
   and the inline markers were all read — and § The one config file's `# random | by_attribute |
   blocked` enum comment carries no marker to remove.
5. **Row-position sweep run in both directions.** No count phrase names the size of either error
   table or of § Validation. The one positional phrase near a table I touched — § Errors core raises'
   "That last row" — is rewritten because I inserted a row into that table; my insertion is
   mid-table, so the phrase was still *true*, and it was fixed anyway per the standing rule. Rows
   that cross-reference by name plus direction (`E-DATA-ASSIGN-NO-DRAW` "above") keep their
   direction: removal and insertion do not reorder the rows that remain.
6. **Worked example untouched**: no `cohort-pilot` number, interval, hash prefix, or step name is in
   any file this task edited.

---

## Review round — the residue is three classes, and a ninth surviving mutation

Commit `5c97686`. 1616 passed + 2 xfailed; `ruff check` and `mypy` green.

### Important 1: the enumeration was wrong by one class, and so was my justification

The reviewer is right, and I reproduced it before changing anything: `stratify_by: [site]` with
`ratio: {control: 1, treatment: 1000}` over 10 units raises `E-DATA-ASSIGN-LEVELS` at the draw **at
every one of 50 seeds** — two strata of five, `[0, 5]` in each. So the excluded set is *three*
draws, not two, and the reason I gave — that `validate` can only draw where the sizes are
seed-independent — is **false for that class**: an attribute-stratified draw is perfectly
seed-independent. Corrected at all five sites: § Validation's *Every arm draws units* row, § Errors
core raises' new row, the `E-DATA-ASSIGN-LEVELS` registry row's residue paragraph,
`_check_assign`'s comment, and the test's docstring.

**The real reason for that exclusion, now stated where the claim is made:** `units._stratum_groups`
raises `NotImplementedError` for a stratum naming an attribute `data.units.attributes` declares that
no resolved unit carries — a broken roster *Allocation strata exist* passes, because that row reads
the declaration. Verified directly: `stratify_by: ["ghost"]` over a roster carrying no `ghost` raises
out of `_stratum_groups`. `validate` is contracted to collect findings and never raise, so drawing
there would turn a broken roster into a traceback.

**I declined the optional widening** (admitting attribute strata and excluding only axis-name ones).
Doing it safely means either swallowing that `NotImplementedError` or repeating `_stratum_groups`'
own precedence rule inside `validate` — a second rule either way, and the second copy is the exact
shape of defect the single-producer seam exists to prevent. The gap is real, seed-independent, and
open; it is now described accurately rather than mis-justified.

`tests/test_validate.py::test_the_draw_check_does_not_reach_a_stratified_or_clustered_block` no
longer merely asserts silence: it now also asserts that the same declaration **does** raise
`E-DATA-ASSIGN-LEVELS` from `assignment_for` at five seeds, so the silence reads as "a check
declining to run" rather than "a config that is fine."

### Important 2: mutation 11, killed

`if drawn_levels is not None:` → `if True:` survived the whole suite. Pinned by
`test_a_drawn_block_whose_levels_do_not_resolve_draws_nothing`: `sweep.groups: [{by: arm, levels:
[]}]` with `method: random`, asserting the exact set `{"E-SWEEP-EXPANDS-EMPTY"}`. Mutated it crashes
`validate` with `TypeError: object of type 'NoneType' has no len()`; reverted it passes.

| # | Mutation | Result |
|---|---|---|
| 11 | `if drawn_levels is not None:` → `if True:` | `..._levels_do_not_resolve_draws_nothing` FAILS with a `TypeError` out of `validate` |
| 12 | the gate admits stratified blocks | `..._does_not_reach_a_stratified_or_clustered_block` FAILS |

### The `allocation_hash` literals

Confirmed as the coordinator says: no 64-hex literal exists in `tests/` or `docs/`, both tests
recompute the hash, and I did not go looking for them. The invariant that mattered — a
`by_attribute`-only document is unmoved — holds and is pinned by
`test_build_allocation_document_maps_axis_to_level_to_unit_keys_in_roster_order`.
