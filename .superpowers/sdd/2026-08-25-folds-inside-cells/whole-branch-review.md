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

## Check 7 — § Errors / § Warnings: one row per code, covering every emit site

**Row-count delta, derived mechanically** (last-cell code extraction over every
table row of `main:docs/reference.md` and `HEAD:docs/reference.md`):

```
E-DATA-HOLDOUT-CELLS:  1 → 0      E-REPL-FOLD-CELLS:  2 → 0
W-DATA-CELL-THIN:      0 → 3      E-DATA-ASSIGN-LEVELS: 2 → 3
```

Nothing else moved. `W-DATA-CELL-THIN`'s three are **one** registry row in
§ Warnings core reports (counted directly: `rows in Warnings core reports: 1`)
plus the two § Validation rows *Cells are populated* and *Allocation is
coherent* that name it; `E-DATA-ASSIGN-LEVELS`' third is the cross-reference
inside *Cells are populated* (*"an arm no unit resolves to is refused as
`E-DATA-ASSIGN-LEVELS` rather than reported as a thin cell"*), not a second
registry row.

**Emit sites enumerated by grepping the quoted code string in `src/`, then
checked against each row's own claim:**

| Code | Sites | Row's claim | Verdict |
|---|---|---|---|
| `W-DATA-CELL-THIN` | 1 (`validate.py:6105`) | thinnest **populated** cell; gated on a cell structure resolving; silent when the draw faults; reported once | Each clause verified in `_check_cell_size` (`if roster is None or cells is None: return`, `min(populated, key=len)`, single `c.warn`) and in `_resolved_cells` (every fault → `None`) |
| `E-DATA-HOLDOUT-EMPTY` | 2 (`validate.py:3560`, `units.py:1821`) | validate row: denominator is the thinnest populated cell **when the cells resolve**, test side only; core-raises row: the re-raise names the cell | `_check_holdout` computes `bound_n` from `populated_cells(cells or {})` and falls back to `len(roster)`; `holdout_within_cells` re-raises under the same code with `cell_label`. Both rows are in the right table for their site |
| `E-REPL-FOLD-K-TOO-LARGE` | 3 (`replication.py:172`, `:178`, reported at `validate.py`'s `resolve_repeats` `except`) | *"One row, three emit sites … `validate` reports it as a finding, and `replication._fold_k` raises it twice — once counting units and once counting clusters"* | Exactly right, and **both** raises carry the `in_cell` / `because` clauses, so the widening reaches all three rather than the one a message is asserted at |
| `E-RUN-FOLD-UNRESOLVED` | 5 (was 3; `units.py:3215` and `:3225` are new) | the § Errors core raises row gained *"a cell decomposition that does not partition the roster the folds are drawn inside"* | One clause covers both new raises (a unit in two cells, a unit in none) — which is the *one row per code* rule, not an undercount |

`validate.py:3713` is a **membership set** (`REPL_DECLARATION_CODES`), not an
emit site, and is excluded from the count above — which is what makes the row's
"three" right rather than four.

I also swept all 293 `E-`/`W-` literals in `src/` against the tables. The six
with no last-cell row (`E-IO-FAILED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`,
`E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`, `E-INPUT-CHANGED`) are **identical on
`main`** — pre-existing, and outside this slice.

**No finding.**

## Check 8 — the filings

### The struck entry really is closed by code

*"an evaluation split cannot be drawn within a cell"* turned on the sentence
**"No build draws one."** `units.partition_within_cells` and
`units.holdout_within_cells` exist, are the single producers `validate` and
`run` both call, and Check 5 above shows a real run drawing four units per arm
per fold end to end. Both registry rows are gone (Check 3, Check 7). Closed.

### The `RE-OWNED 2026-08-25` entry's own counts, re-derived by me

Sections split on `^## `, each body whitespace-collapsed before matching (the
file is hard-wrapped and `H3c-3's remaining 14` wraps mid-phrase):

```
## OPEN headings: 59      naming H3c-3: 37
naming "whichever slice": 10      union: 41
control: "Owner:" -> 58 sections, "H99z-4" -> 0
```

The entry predicts in writing *"re-running this sweep at this commit returns
**59 and 41**, not 56 and 38"*. **Both figures reproduce exactly.** The sweep
was proved able to fail by the entry's own control and by mine.

### The three new filings, each reproduced

- **A cluster may span two cells.** Reproduced by building C1's own measured
  roster (15 units, `S1`×7 / `S2`×3 / `S3`×3 / `S4` / `S5`, `control` = 0–7),
  drawing the axis through the real `assignment_for(method: by_attribute)` and
  intersecting through `cells_of`: cluster **`S2` lands in both**
  `(('arm','control'),)` and `(('arm','treatment'),)`. And
  `stratum_varies_within_cluster(roster, "cl", "arm")` returns
  `('S2', ['control', 'treatment'])` — so the helper the filing names as *the
  check that would close it* really does report the pair today. Filing accurate.
- **The per-stratum fold bound.** Reproduced exactly as filed:
  `partition_units(6 units, k=6, strata=3+3)` returns
  `[['v1','v3'], ['v0','v5'], ['v2','v4'], [], [], []]` — **three empty
  folds**, nothing refused. Filing accurate.
- **`limits.min_clusters` under cells.** The call really is unchanged:
  `groups = fold_basis(holdout_test if holdout_test is not None else roster, cluster_by)`
  is byte-identical at `main:6149` and `HEAD:6399`, and `_check_resample(doc,
  roster, c, holdout_test=holdout_test)` is byte-identical too. **But see the
  finding below** — one clause of this filing is false.

### Finding — MAJOR: the `min_clusters` filing's *"and into nothing else"* is false, and its *"did not move it"* is false with it

The filing says:

> **H3c-3 did not move it and did not make it worse** … the slice threads
> `cells` into `_check_holdout` and into the fold basis and **into nothing
> else**, and `_check_resample`'s call is unchanged, still
> `fold_basis(roster, cluster_by)` over the roster or over the holdout's
> realized test side.

The AST signature diff (Check 2) shows `cells` was threaded into **four**
functions, not two: `_check_holdout`, the fold basis (`thinnest_cell` at
`:718`), `cli._resolved_holdout` — and **`validate._holdout_test_roster`**,
whose return value *is* `_check_resample`'s `holdout_test`. So `cells` reaches
that denominator by one hop, and *"the holdout's realized test side"* is a
**different set of units** after this slice than before it.

And the denominator genuinely moves. Searching over rosters drawn through the
real `assignment_for(by_attribute)` and `cells_of`: 24 units, two arms of 12,
6 clusters nested inside the arms, `frac: 0.25`, holdout seed `67096` (a legal
pinned `data.units.holdout.seed`) — the **per-cell** test side spans **4**
clusters, the flat one spans **3**. At `limits.min_clusters: 4` that is one
`W-STATS-RESAMPLE-CLUSTERS` present before this slice and absent after it, on
an unchanged config.

The filing's *substance* survives — the warning is still roster-wide rather
than per-arm, still wrong in the not-firing direction, and Ruling LL still
stands. What is false is the two sentences saying this slice touched nothing
here, and they are exactly the sentences the entry says exist *"so that is on
the record rather than inferred from silence."*

**Route: no slice follows. Correct it in this slice's fix round** by appending
to that entry (never by rewriting the body): `cells` reaches the denominator
through `_holdout_test_roster`, the test side is now a per-cell draw, and the
figure can move in either direction. It is the same site as the Check 2 Major,
so one fix round can close both.

### Finding — MINOR: 14 OPEN entries are outside the governing entry's stated scope and say only `Owner: unassigned`

The `RE-OWNED 2026-08-25` entry scopes itself explicitly — *"the union, which
is what this entry governs: **38**"* and *"Read every one of those
thirty-eight reasons this way"*. Of the 59 OPEN entries, **18 name neither
`H3c-3` nor *whichever slice***, and of those **14 never say that no slice
follows** anywhere in their bodies: `required_env`'s two unbuilt readers,
`BaseTemplate.field_convention`, `main`'s un-redacted last-resort handler, the
unloaded installed template class, the plugin-side collision, the escaping
`glob`, the derived-metric clustered null, the contrast-side `null_draws`, the
two `check_facts` credential entries, the four fact-contract refusals,
`resolves_inside_repo`, `nondeterministic`, and the `basis: "repeats"` entry.
Each says `Owner: unassigned` (one says `Owner: none; accepted`) and stops
there.

`unassigned` and *no slice follows* are different claims: the first reads as
*awaiting an owner*, which is what this file's own `RE-OWNED 2026-08-19` entry
rejects. Four of the 18 already carry *"no remaining slice owns X"*, which is
the shape the other 14 lack.

**Route: no slice follows.** Cheapest correct fix, one sentence in the fix
round: widen the governing entry's scope sentence from *the 38* to *every
unclosed entry in this file*, adding the count of the ones it newly covers.
No body is edited, so nothing is retro-edited.

## Check 9 — § Executability, both consistency passes, and the development record

### § Executability, re-derived by me

**The four-row table is byte-identical.** A programmatic walk finds **13**
`| Figure | Count | Visible to` headers in the analysis; blocks 1 through 12
are **equal to the last, line for line**, six lines each, by both the
walk-forward method and a fixed six-line slice. Only block **0** differs, and
it is the pre-H8a table in an older dated entry — correct, since H8a is the
entry that changed it. **Four rows, no fifth number**, and the new entry quotes
no single figure for executability.

**The pinned commit is still accurate.** The entry says *"Measured on
2026-08-25 against commit `7ef6846`"*; `git diff --stat 7ef6846..HEAD -- src/`
is **empty**, so no code moved under the claim after it was measured.

**The row-1 greps, re-run by me:** `groups:` → two config hits, both
`groups: []`; `allocation:` → two config hits, both `within`; `holdout:` → one
real block plus one `null`, beside that same `within`/`[]`;
`min_units_per_cell: 20` at lines 216, 339, 629 — **three config blocks**, as
claimed; `cluster_by:` → two hits, both `null`. So no config here resolves a
cell structure, both retirements are unreachable, and `W-DATA-CELL-THIN`'s gate
excludes all of them. Row 1 stands.

#### Finding — MINOR: one grep in § Executability is falsified by its own sentence

The entry writes *"`grep -n "kind: fold"` returns **nothing** — no config here
declares a `fold` level at all."* Run today it returns **one** line: line 2343,
the sentence itself. The substance is right — no config block declares a fold —
but the claim as written is a build claim a reader cannot reproduce, and it is
the self-matching-sweep shape `CLAUDE.md` § Mechanical traps names.

**Route: no slice follows.** One-word fix in this slice's fix round: say the
grep returns one hit and that it is this sentence, or scope the grep to the
config blocks.

### Mechanical pass — clean

Over `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md` (and, separately, the feasibility analysis and `CLAUDE.md`
for the whitespace half):

- every relative link and `#anchor` resolves — **0 broken**, fenced blocks
  skipped, GitHub's slugger reproduced (punctuation stripped, each space → one
  hyphen, so `Secrets & credentials` → `secrets--credentials`);
- **no duplicate heading anchors** in any of the four;
- every table's rows match its header's column count, pipes inside inline code
  and escaped pipes discounted — **0 mismatches, 0 empty rows**;
- **no trailing whitespace, no tab, no invisible unicode** (the class was
  corrected mid-check and then controlled: it rejects U+0020 and accepts
  U+00A0);
- no ASCII `x` used for multiplication.

### Cross-document pass — the worked example did not move

Every `cohort-pilot` figure was counted across the four documents at `main` and
at `HEAD` and compared: `0.581 / 0.488 / 0.661`, `0.607 / 0.517 / 0.683`,
`0.412 / 0.347 / 0.477`, `0.026 / −0.007 / 0.059`, `−0.169 / −0.213 / −0.125`,
`0.014`, `240`, `228`, and the hash prefixes `8e21 / 1a2b / 3d8a / 6b1f /
2f5c8d0`. **Not one count changed.** The scan was proved able to fail:
`E-REPL-FOLD-CELLS` reads `main=4 head=0` through the identical loop. **The
intervals are not narrowed back.**

The two document edits are both behaviour-tracking, not example-touching:
`experimental-designs.md` loses one false sentence (*"a fold or a holdout drawn
within each cell is not built"*), and `reference.md`'s § A fixed holdout split,
§ Clustered units, § Validation, § Errors, § Warnings and `sweep.yaml` sections
follow the code.

### The development record was not retro-edited

`git diff --numstat` over `docs/superpowers/` and `.superpowers/`: the plan
(+43/−0), the design (+56/−0) and all five batch reports (+0 deletions) are
**append-only**. The only file with deletions is `docs/superpowers/spec-defects.md`
— **3 lines**, the sole permitted exception — and all three are the strike
(`## OPEN — an evaluation split…` → the struck heading) plus one
`prints` → `printed` tense change that preserves the original 195 and appends
the re-measurement beside it.

`.superpowers/sdd/.gitignore` is intact (not clobbered to a bare `*`).

#### Finding — MINOR: this slice has no `progress.md`, alone among 33

Every other slice directory under `.superpowers/sdd/` carries a `progress.md`;
`2026-08-25-folds-inside-cells` does not, and none was ever committed
(`git log --all -- …/progress.md` is empty; the path is not gitignored).
`CLAUDE.md` § The development record names that file as *"The ledger: every
ruling, its reason, and what it costs if wrong"* and tells a reader to read it
before re-deriving anything.

**Mitigated but not closed:** Rulings HH, II, JJ, KK and LL are each defined in
the tracked design (numbered Decisions 2, 5, …) and the tracked plan, and no
report on this branch claims a ledger entry that does not exist — so no
*content* is lost, and the pointer in `CLAUDE.md` still resolves to something.
What is lost is the one place the table promises it.

**Route: no slice follows.** Either write the ledger from the design's
decisions and the five batch reports in this slice's fix round, or record in
this review that the last slice deliberately kept its rulings in the design
instead — the second costs one sentence and is honest.

## Final state — all mutations reverted, everything re-run

Every mutation in this review was reverted **by editing back** (never
`git checkout --`), each revert confirmed by `git diff --quiet`, and the tree
was then re-verified end to end on the clean branch:

```
$ git status --short                     (empty)
$ uv run pytest -q                       3416 passed, 1 skipped, 2 xfailed in 382.08s
$ uv run ruff check .                    All checks passed!
$ uv run ruff format --check .           101 files already formatted
$ uv run mypy                            Success: no issues found in 56 source files
$ <the 336-case oracle, re-run>          ORACLE STILL BIT-IDENTICAL
```

## Checks I did not reach

- **Row 1 of § Executability re-run through `validate`.** I verified the greps
  the entry derives it from and that neither retirement is reachable, but I did
  not transplant all eight configs and run `validate_config` on them. The entry
  claims that row *unchanged* rather than newly derived, and nothing this slice
  built can reach a config with no group axis — so the risk is low, but the
  number is the entry's, not mine.
- **The five batch reports' own claims, item by item.** I checked the claims
  the priority list routed me to (Rulings II, JJ, KK, LL; guard-pin arm
  authorizations; the retirements; the filings) and the three report claims
  `3e69757` says it corrected, but I did not audit every assertion in
  `task-b1`–`task-b5` against the code.
- **The `statistics` interaction surface** enumerated at the end of `task-b4`
  (`runner._units_failed_anywhere`, `runner.attrition`, `cli._cond_roster` and
  its four downstream readers) — the newly reachable
  `holdout × arm_members` pairs. The report calls them *believed correct,
  untested for this pair*, and I did not build fixtures for them. **No slice
  follows, so anything wrong there ships.**
- **`E-DATA-HOLDOUT-STRATIFY-UNKNOWN`'s reworded message** and the other
  docstring/message rewrites in `units.py` — read, not mutation-tested.

## VERDICT: **HOLD** — for a fix round, not for a redesign

The slice is sound where it matters most: **the bit-stability oracle holds by
my own measurement across 336 cases against a real `main` worktree**, the
retirements leave no live claim anywhere, the guard pin is intact and every arm
can fail, Ruling KK's replacement is derived and survives a real
crash-and-resume with a group axis, `W-DATA-CELL-THIN` does not fire on a
generated project, § Errors carries one row per code covering every emit site,
the worked example did not move, and the development record is append-only.

Four findings, none of which requires a design change:

| # | Sev | Finding |
|---|---|---|
| 1 | **Major** | `validate._holdout_test_roster`'s `cells` argument is pinned by nothing — the whole suite is green with it wired to `None`, while a real config discriminates (4 clusters vs 3 in the holdout test side) |
| 2 | **Major** | The `min_clusters` filing's *"threads `cells` … into nothing else"* and *"did not move it"* are false: `cells` reaches that denominator through `_holdout_test_roster` |
| 3 | **Minor** | 14 OPEN `spec-defects.md` entries sit outside the `RE-OWNED 2026-08-25` entry's own stated scope and say only `Owner: unassigned` |
| 4 | **Minor** | § Executability's *"`grep -n "kind: fold"` returns **nothing**"* is falsified by its own sentence |
| 5 | **Minor** | This slice has no `progress.md`, alone among 33 slice directories |

Findings 1 and 2 are **one site** and close together: one test pinning the
`cells` forward at `_holdout_test_roster`, and one appended paragraph on the
filing. Findings 3, 4 and 5 are one sentence each. **No later slice exists to
route any of them to** — H3c-3 is the last slice in the project, so what is not
closed in this slice's fix round ships as it stands.

