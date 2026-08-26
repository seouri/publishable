# H3c-3 — whole-branch review

Branch `h3c3-folds-inside-cells` at `ff53cf4`, against `main` at `dfc6b7d`.
Written incrementally; each section is appended as its check completes.

**VERDICT: IN PROGRESS** (see the end of this file for the final line).

---

## Check 1 — the bit-stability oracle: **HOLDS**

Measured, not read. A `main` worktree was created at
`…/scratchpad/wbr_h3c3/main` (commit `dfc6b7d`) and one probe script
(`…/scratchpad/wbr_h3c3/oracle.py`) was run under **both** trees' own
`uv run python`, writing a sorted JSON of every case.

**336 cases**, covering every no-cell input the two producers take:

- fold: rosters of 7 / 12 / 40 / 240 units × digests `3d8a1f`, `deadbeefcafe`,
  `0` × `k` ∈ {2,3,5} × `clusters` present/absent × `strata` present/absent.
  HEAD calls `partition_within_cells(roster, k, digest, {}, …)` **and**
  `partition_within_cells(…, None or {}, …)` and asserts the two agree; `main`
  calls `partition_units(roster, k, digest, …)`.
- holdout: the same rosters × `frac` ∈ {0.1,0.2,0.25,0.5} × `method` ∈
  {`random`, `by_attribute`, `stratified`} × two seeds × clusters
  present/absent. HEAD calls `holdout_within_cells(…, cells=None, …)` **and**
  `cells={}` and asserts the two agree; `main` calls `holdout_for`.
  Both sides record `train`, `test`, `seed` and `strata`, and a raise is
  recorded as its `type: message` so a refusal that moved would show as a
  difference too.

Result: `diff head.json mainout.json` → **byte-identical**, both for the
partitions' key lists in order and for the holdout plans' four fields.

**The oracle was proven able to fail.** With `partition_within_cells`'
reduction mutated to `digest + "x"` and `holdout_within_cells`' reduction to
`seed + 1` — the two lines the reduction rests on — the same comparison
produced **13021 differing lines**. Both mutations were reverted by editing
back and the comparison re-run: byte-identical again.

## Check 10 — gates

| Gate | Result |
|---|---|
| `uv run pytest` | **3416 passed, 1 skipped, 2 xfailed** in 383s |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 101 files already formatted |
| `uv run mypy` | Success: no issues found in 56 source files |

Run in the foreground, whole suite, after clearing `pytest-of-joon` and every
`__pycache__`. `main`'s 3338 → **+78** collected-and-passing, 1 skipped and
2 xfailed unchanged. Delta accounted for below (Check 10a).

### Check 10a — the delta against `main`'s 3338, accounted for

`pytest --collect-only` under both trees, ids sorted and `comm`-ed:
`main` collects **3341**, HEAD collects **3419** (= 3416 passed + 1 skipped +
2 xfailed, so nothing is silently deselected).

**9 ids removed, 87 added**, 3341 − 9 + 87 = 3419.

The 9 removals are each accounted for and none is a lost guarantee:

- 8 are the refusal tests of the two codes this slice retires —
  `test_a_fold_beside_a_cell_structure_is_refused`,
  `test_a_holdout_beside_a_cell_structure_is_refused`,
  `test_both_split_kinds_beside_a_cell_structure_report_both_codes`,
  `test_a_group_axis_alone_triggers_the_refusal_without_between`,
  `test_allocation_between_alone_triggers_the_refusal_without_a_group_axis`,
  `test_an_empty_group_axis_alone_does_not_trigger_the_refusal`,
  `test_an_evaluation_split_without_a_cell_structure_is_not_refused`
  (all `test_validate.py`) and
  `test_a_holdout_beside_a_cell_structure_is_core_defect_not_a_silent_choice`
  (`test_runner.py`). A retired refusal's tests going with it is the point.
- 1 is the `docs/experimental-designs.md` parameter of H9d guard-pin arm C,
  retired by the controller ruling in `ff53cf4`.

The 87 additions land in 8 files; no test file lost a test other than the 9.

## Check 3 — the two retired codes: **no live claim survives**

A newline-insensitive sweep over **every tracked file** (`git ls-files`),
matching each code against the file's text with all whitespace, backticks and
asterisks stripped, so a code broken across a line or wrapped in emphasis
still matches. Proven able to fail two ways: `E-REPL-FOLD-K-TOO-LARGE` and
`E-DATA-HOLDOUT-EMPTY` hit 29 and 28 files, and the collapsed matcher finds
`E-REPL-\nFOLD-CELLS` in a synthetic string.

**Neither code appears anywhere in the four documents** — `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md` are all absent from the hit list, so § Errors carries no
row for either.

Survivors outside the development record, each read in place:

| File | Verdict |
|---|---|
| `src/publishable/units.py` (1×) | Historical: *"That combination was refused outright (`E-DATA-HOLDOUT-CELLS`, retired by H3c-3 task 16) until this function existed"* |
| `src/publishable/runner.py` (2×) | Historical: *"WAS refused"*, *"the leak … stood in for until this commit"* |
| `src/publishable/artifacts.py` (1×) | Historical: *"the imbalance `E-DATA-HOLDOUT-CELLS` was minted against does not exist"* |
| `tests/test_validate.py` (5+2) | Two are `assert "E-…-CELLS" not in found` — the retirement's own pins; the rest are past tense |
| `tests/test_cli.py`, `tests/test_runner.py` | Past tense, each dating the retirement to its task |
| `CLAUDE.md` (2+2) | Both sites amended in place with **"both retired by H3c-3 on 2026-08-25"** / **"Discharged: H3c-3 merged…"** — the pre-existing sentences are left standing and corrected beside, which is this repo's own correction convention |
| `docs/feasibility-llm-growth-studies.md` (2+2) | In the dated § Executability entry, describing the retirement |
| `docs/superpowers/spec-defects.md` (2+2) | Inside the **STRUCK 2026-08-25** entry |

The remaining ~50 hits are all in the development record (`docs/superpowers/`
specs, plans, scopings, `.superpowers/sdd/`), which is not to be retro-edited.

**No finding.**

## Check 2 — the accepted-and-never-forwarded class, swept

The sweep is mechanical rather than by eye. `ast.parse` over both `main:` and
`HEAD:` blobs of the seven changed modules, comparing each function's
`posonlyargs + args + kwonlyargs`. **Seven existing functions gained a
parameter; nine functions are new.** The gainers, exhaustively:

| Function | Gained | Forwarded from | Constant? |
|---|---|---|---|
| `cli._resolved_holdout` | `cells` | `cli.py:2982`, the `cells` local of `cli.py:2844` (`cells_of(group_axes) if group_axes else None`) | no |
| `validate._check_holdout` | `cells` | `validate.py:757`, the `cells` local of `:691` | no |
| `validate._check_replication` | `fold_cell` | `validate.py:763` as `fold_cell=basis_cell`, from `thinnest_cell` at `:718` | no |
| `validate._holdout_test_roster` | `cells` | `validate.py:748`, same local | no |
| `replication._fold_k` | `cell` | `replication.py:284`, `resolve_repeats`' own `fold_cell` | no |
| `replication.resolve_repeats` | `fold_cell` | `validate.py:3869` and `cli.py:2877`, both computed | no |
| `sweep.sweep_document` | `partitions_within` | `cli.py:3345`, from `populated_cells(cells or {})` at `:3334` | no |

A second AST pass confirms each new parameter is **read in the body**
(docstring excluded): 1, 1, 1, 1, 3, 1 and 2 `Name` loads respectively. So
task 13's exact shape — added, documented, wired to a constant — **does not
recur on this branch.**

The two remaining constant-looking arguments are conditionals, not constants:
`partition_within_cells(…, cells_of(axes) if axes else {}, …)` at `cli.py:2561`
and `partition_within_cells(…, cells or {}, …)` at `cli.py:2967`.

### Finding — MAJOR: `_holdout_test_roster`'s `cells` is forwarded and pinned by nothing

Mutating the forward at `validate.py:748` to the constant `None` —

```
_holdout_test_roster(doc, units_decl, roster, usable_cluster, cells)
  → _holdout_test_roster(doc, units_decl, roster, usable_cluster, None)
```

— leaves the **whole suite green**: `3416 passed, 1 skipped, 2 xfailed`,
identical to the unmutated run. (The same mutation applied to the *other* two
forwards on the same three lines is caught: `_check_holdout`'s constant fails
`test_the_empty_test_partition_is_bounded_by_the_thinnest_cell_not_the_roster`
and `test_an_empty_cell_beside_a_holdout_is_bounded_by_the_populated_cells`;
`fold_cell=None` fails three tests including
`test_a_k_past_the_thinnest_POPULATED_cell_is_refused_naming_that_cell`. So the
mutation apparatus is not the thing that is blind.)

**And the seam is real, not vacuous.** `holdout_test` reaches
`_check_resample`, where `groups = fold_basis(holdout_test …, cluster_by)`
decides `W-STATS-RESAMPLE-CLUSTERS`. A search over random rosters (clusters
nested inside arms, the legal shape) finds discriminating inputs immediately:
12 units, two arms, 4 clusters, `frac: 0.4`, holdout seed 6851 — the per-cell
draw's test side spans **4** clusters and the flat draw's spans **3**. With
`limits.min_clusters: 4` that is one warning present under the shipped code and
absent under the mutant. This is exactly the "seam named in the brief and
instantiated by no fixture" shape `CLAUDE.md` records, in the one place where
the docstring's own argument — *"a call that passed the decomposition here and
not there … would bound `limits.min_clusters` against a test partition no run
produces"* — is the claim going untested.

**Route: there is no later slice. H3c-3 is the last slice in the project, so
this ships unpinned unless it is closed in this slice's fix round.** The fix is
one test: the config above (or any `groups × holdout × cluster_by` config with
`limits.min_clusters` set at the discriminating value) asserting
`W-STATS-RESAMPLE-CLUSTERS`'s presence/absence and its cluster count.

## Check 4 — `W-DATA-CELL-THIN` on a generated project: **does not fire**

Run **outside the repo**, at
`…/scratchpad/wbr_h3c3/proj/cell-probe`, through the real console script
(`uv run --project /Users/joon/src/tries/publishable publishable …`):

1. `publishable new cell-probe`
2. `publishable generate experiment pilot --template generic --input-dir …/in --output-dir …/out`
3. the only edits are the three a scaffold demands anyway —
   `metadata.description`, `metadata.authors`, and `data.units.key` to match
   the 12-row `index.csv`.

The generated `configs/pilot/config.yaml` carries **`min_units_per_cell: 20`**
(grepped) over a **12-unit** roster — the exact under-floor shape an ungated
check would fire on.

```
$ publishable validate configs/pilot/config.yaml
  ✓ config valid · configs/pilot/config.yaml
```

Zero warnings. The gate holds: `sweep: {}` and `allocation: within` resolve no
cell structure, `_resolved_cells` returns `None`, and `_check_cell_size`
returns before the floor is read.

**Positive control, so this is not a silent check.** Editing the same config to
`attributes: [arm]`, `allocation: between`, `sweep: {groups: [{by: arm, levels: [a, b]}]}`
— arms of 9 and 3 — produces:

```
warning W-DATA-CELL-THIN     limits.min_units_per_cell
        is 20, and the design's thinnest cell (`arm=b`) holds 3 of 12 resolved units. …
```

**No finding.**

## Check 5 — Ruling KK: derived, not patched, and a real crash-and-resume

**The replacement is derived.** `_resumed_allocation` does not compute fold
membership itself; it calls **`units.partition_within_cells`** — the same
single producer `_prepare_run` calls — on the **overridden** axes
(`cells_of(axes)` built from the recorded plans), and `fold_members` follows
through `replication.fold_members_for`, exactly as in `_prepare_run`. The gate
is `prepared.partitions is not None` (*a fold level exists*), not *an axis
exists*, so the no-axis arm takes the producer's own byte-identical reduction
rather than a branch. `partition_units` is not called from that function.

**A real crash-and-resume with a group axis, run outside the repo through the
real console script.** `…/scratchpad/wbr_h3c3/proj2/resume-probe`: 24 units,
`allocation: between`, `sweep.groups: [{by: arm, levels: [a, b]}]`,
`assign.arm: {method: by_attribute, from: arm}`, `replication.repeats:
[{kind: fold, k: 3}]`. The step `os._exit(9)`s from its third execution
onward, keyed off a sentinel file **outside** `input_dir` and outside `src/`
so neither `input_manifest_hash` nor `code_hash` moves between the two
commands.

1. `publishable run configs/pilot/config.yaml` → process dies, run directory
   left with `allocation.json`, `sweep.yaml`, `identity.json` and **no
   `run.yaml`**.
2. sentinel removed; `publishable resume <run_dir>` → **exit 0**, `run.yaml`
   written.

Per-fold membership, read out of the `units.parquet` artifacts:

```
00_arm=a fold01 ['u04','u05','u06','u10']   01_arm=b fold01 ['u16','u17','u18','u22']
00_arm=a fold02 ['u02','u03','u08','u11']   01_arm=b fold02 ['u14','u15','u20','u23']
00_arm=a fold03 ['u00','u01','u07','u09']   01_arm=b fold03 ['u12','u13','u19','u21']
```

**Every arm holds four units in every fold** — the property the whole slice
exists for, observed end to end on a resumed run rather than by direct call.

**The lever, run for real.** Repeating the crash and then editing the recorded
`allocation.json` to swap `u11` (arm `a`) and `u12` (arm `b`) — the record
being what `_resumed_allocation` overrides with — the resumed arm-`b` fold03
comes out `['u11','u13','u19','u21']`. `u11` for `u12`, and nothing else
moved. The folds follow the **recorded** decomposition, not the tree's fresh
one: the exact claim Ruling KK's replacement makes, and the exact claim the
retired *"pure function of the roster and the design digest"* argument would
have got wrong.

**Observation, not a finding.** In that second run the pre-crash arm-`a`
artifacts still show `u11`, so across the crash boundary one unit appears in
two arms. That is the consequence of hand-editing `allocation.json`, which
`resume` treats as authoritative and which no hash on the resume path covers —
a property of H9's `resume`, recorded in this slice's own task-23 report, not
something H3c-3 introduces.

**No finding.**

## Check 6 — the guard-pin arms: green, able to fail, moved only where authorized

**Moved only where authorized.** The five arm bodies were extracted from
`bf68454` (task 1) and from `HEAD` by AST-free slicing and compared: arms
**A, B, C, D and E are all byte-identical**. (The two apparent diffs — a
trailing comment banner after arm A and the `_H3C3_ARM_ROSTER` literal after
arm E — are sibling content appended *after* the function, not edits inside
it.) Arm C, the only arm with an authorized editor (task 17), was **not**
edited, which is the post-edit state task 1 specified in advance.

**Able to fail — a mutation per arm, each reverted by editing back and
re-verified:**

| Arm | Mutation | Result |
|---|---|---|
| A | `units._seed_from`: `\|folds` → `\|foldz` | `test_h3c3_pin_arm_a_…` **FAILED** (1 failed, 271 deselected) |
| B | `sweep.sweep_document`: `if partitions_within:` → unconditional write | `test_h3c3_pin_arm_b_…` **FAILED** |
| C | `cli._resumed_allocation`: `tuple(keys)` → `tuple(sorted(keys, reverse=True))` | `test_h3c3_pin_arm_c_…` **FAILED** |
| D | `units.partition_within_cells` reduction: bare `digest` → `digest + "\|cell"` | **FAILED**; and a second, calling the producer twice, **FAILED** too |
| E | `validate._check_cell_size`: cell-structure gate removed, `cells=None` → one cell over the roster (MU-11) | `test_h3c3_pin_arm_e_…` **FAILED** |

One mutation was **not** discriminating and is recorded because it is the
"mutation whose two branches cannot differ" shape: setting `partitions_within`
to `[]` instead of `None` at `cli.py:3346` left arm B green, because
`sweep_document`'s `if partitions_within:` is falsy for both. The real MU-14
has to be applied in `sweep.py`, where the key is written.

**H9d guard-pin arm C, the half the controller kept.** Appending one newline to
`docs/design-principles.md` fails
`test_h9d_arm_c_…[docs/design-principles.md]`; reverting by editing back and
re-running passes. So the surviving parametrization is a live pin, not a
retired one, and the `docs/experimental-designs.md` parametrization is gone
from the collected set (Check 10a).

**No finding.**

