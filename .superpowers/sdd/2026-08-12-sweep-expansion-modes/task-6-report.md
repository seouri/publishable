# Task 6 report: the baseline expands over unfixed axes

Commit: `0857a37` — *feat: a baseline expands over the axes it does not fix*.
Suite: **1061 passed, 0 failed, 0 xfailed** (1055 before + 6 new tests in
`tests/test_sweep.py`). `uv run ruff check .` clean, `uv run mypy` clean.
`ruff format` was not run.

## What changed

`src/publishable/sweep.py` only:

- **`_baseline_cells(axes, baseline)`** (new, module-private). One `{path: value}`
  cell per combination of the axes the baseline does not fix, in axis order.
  `itertools.product()` over no unfixed axes yields exactly one empty tuple, so
  the table's **first** row (a baseline fixing every axis → one row, empty cell)
  falls out of the same expression as the second rather than needing a branch
  that could disagree with it.
- **`expand`**: `_axes` is now computed before the baseline rows (it was after);
  the single unconditional baseline row becomes one row per cell, each carrying
  `dict(cell)` overlaid with the fixed values, and each `is_baseline=True`. The
  row's *label* source is the cell alone.
- **`label_for`**: the `is_baseline` early return is gone. The body is rendered
  the same way for every row; a baseline then appends `AXIS_SEPARATOR + "baseline"`
  when the body is non-empty, and returns the bare `"baseline"` when it is empty.

`condition_dir_name` is **untouched**, as are `validate.py`, `contrasts.py`,
`cli.py`, `runner.py`, `artifacts.py`. `E-SWEEP-BASELINE-PARTIAL` is untouched
(task 7). `vs_baseline` targeting and the comparison count are untouched (task 8).

## Operation-by-operation enumeration, and the guard for each

Every operation the new code performs, with the input class that makes it raise
and where that class is stopped. (Guarding the class, not imagined inputs.)

| Operation | New code | Input class that breaks it | Guard |
|---|---|---|---|
| `dict(baseline)` | `expand` | `baseline` not a mapping/pair-sequence → `ValueError`/`TypeError` | Pre-existing behaviour, deliberately kept and moved *before* any read of `baseline`: `path in baseline` would silently answer for a string. `validate._check_shape` refuses the shape fatally (`E-CONFIG-SHAPE`); verified `{"baseline": "pearson"}` still raises `ValueError`, as at `HEAD~1` |
| iterate `axes`, then each axis's cells | `_baseline_cells` | none — `_axes` is the sole producer and builds `list[list[dict]]`; a malformed `paired`/`sample` raises inside `_axes` before this code is reached (`dict(entry)`, `sample_fault`/`E-SWEEP-SAMPLE-INVALID`) | `_axes`, unchanged |
| `path in baseline` for each cell key | `_baseline_cells` | an unhashable path → `TypeError`. Unreachable: `path` came from a dict key, so it is already hashable | structural |
| `itertools.product(*unfixed)` | `_baseline_cells` | a non-list axis → `TypeError`. Unreachable: `_axes` appends only lists. Size is bounded by the product `expand` already takes | structural |
| `cell.update(part)` / `row_values.update(fixed)` | both | non-mapping `part`/`fixed` → `TypeError`. `part` is an `_axes` cell; `fixed` is the already-constructed `dict` | above |
| `body` join in `label_for` | `label_for` | a non-`str` path reaching `path.rsplit` → `AttributeError` | pre-existing and unchanged: `_keys_for` already does `path.split(".")` on the same paths, so a non-string `grid` key raises there first, exactly as before this task |
| `f"{body}__baseline"` | `label_for` | none — `body` is a `str` by construction | — |

Two things the enumeration turned up that are *not* obvious from reading:

1. **Fixedness is read off the cells' paths, not off the mode's declaration.**
   An axis with **no cells** (`grid: {a.x: []}`) therefore carries no paths, so
   no baseline can fix it, so it is unfixed and the product over it is empty.
   Consequence: `expand({"sweep": {"baseline": {"a.x": 1}, "grid": {"a.x": []}}})`
   now returns `[]`, where at `HEAD~1` it returned one lone baseline condition.
   **Chosen deliberately, not inherited**: it is the same answer `expand` already
   gave for the no-baseline case (`test_an_empty_grid_axis_still_expands_to_nothing_here`),
   and a lone baseline row standing in for a design with no cells is a design
   nobody declared. `E-SWEEP-AXIS-EMPTY` is the refusal that reports it. Pinned
   by `test_an_empty_axis_leaves_no_conditions_even_under_a_baseline`, both
   directions (baseline fixes the empty axis's path; baseline fixes an unrelated
   path). No pre-existing test pinned the old answer.
2. **An axis counts as fixed when the baseline names *any* path it varies.** A
   `paired`/`sample` cell sets several paths at once; expanding an axis the
   baseline half-fixes would have to discard either the baseline's declared value
   or the cell's. The declaration wins, the axis contributes no cells. Pinned by
   `test_a_baseline_naming_one_path_of_a_paired_entry_fixes_that_whole_axis`.

## The label scheme for per-cell baselines

`<cell rendered exactly as a non-baseline row>` + `__` + `baseline`; a baseline
with an empty cell stays the bare `baseline`. The cell is rendered by the same
`_keys_for`-shortened `key=value` join every other condition uses, over the same
`swept` path set (axis paths ∪ ablated paths), so a per-cell baseline
disambiguates against shared leaves exactly as its cell-mates do. The fixed
values never enter the label — restating them would name the condition by what
every row in the run holds constant.

Worked examples (all executed, not predicted):

| Declaration | Labels |
|---|---|
| `baseline: {analysis.method: pearson}`, `grid: {analysis.method: [pearson, spearman], data.sex: [f, m]}` | `00_sex=f__baseline`, `01_sex=m__baseline`, `02_method=pearson__sex=f`, `03_method=pearson__sex=m`, `04_method=spearman__sex=f`, `05_method=spearman__sex=m` |
| `baseline: {analysis.method: pearson}` + `paired: [{min_samples: 30, confidence: 0.95}, {…: 50, …: 0.99}]` | `min_samples=30__confidence=0.95__baseline`, `min_samples=50__confidence=0.99__baseline` (one cell, not a product of its keys) |
| `baseline: {analysis.method: pearson, data.sex: f}` fixing both axes | `00_baseline` only — first row of the table, unchanged |
| no cell, no axes (`baseline` alone) | `baseline` |

The literal `baseline` is the one `=`-less segment in a label body. That is not
new — the bare `baseline` label has always been one — and nothing in `src/`
parses a label body: `grep -rn 'split("__")\|split(AXIS_SEPARATOR)\|split("=")'`
over `src/` returns nothing outside `sweep.py`, and `sweep.py` itself never
splits a label. `condition_dir_name` is unchanged, so `runner.step_dir_for` and
`artifacts.StepIO.read_condition` nest through the same single source of truth.

**Ordering: baseline rows come first as a block, not interleaved into their cells.**
The product's numbering is declared-order nested loops with the last axis varying
fastest (`test_the_last_declared_axis_varies_fastest`); making each cell's rows
contiguous would reorder the product and renumber every condition in every
existing design. § Expansion modes' one *interleaved* example
(`00_cohort=derivation__baseline`, `01_…__labs=false`, `03_cohort=validation__baseline`)
is the `ablate × groups` design, which **no config can reach in this build**:
`ablate` composes with no axis (`E-SWEEP-ABLATE-CROSSED`) and `groups` expands to
nothing, so an `ablate` sweep has no axes and therefore exactly one baseline. The
latent item for the `groups` slice is recorded under *Questionable* below.

## Existing tests left failing because `E-SWEEP-BASELINE-PARTIAL` still refuses this

**None.** The brief expected some; the suite is fully green (1061 passed). The
reason is structural rather than lucky: `validate._check_unimplemented` computes
`unfixed` from `_swept_paths(sweep)` and the `baseline` mapping **directly**, never
from `expand`, so the refusal fires on exactly the configs it fired on before and
`tests/test_validate.py:2345`, `:2369`, `:4457` still pass unchanged. The
sites that *could* have moved were checked explicitly:

- `validate._condition_labels` (validate.py:1943) returns `baselines` as a **set**
  of labels; it is now potentially multi-element, and every consumer treats it as
  a set already. No test moved.
- `W-SWEEP-BASELINE-CONFOUNDED` (validate.py:1578) gates on
  `all(axis in baseline_fixed …)` — the table's first row only — so per-cell
  expansion cannot reach it. Untouched, `tests/test_validate.py:4225` unchanged.
- `contrasts.py:48` takes `next(c for c in conditions if c.is_baseline)`, i.e. the
  first baseline, and would compare the *other* baselines against it. That is
  precisely task 8's "each `vs_baseline` targets its own cell's baseline" and
  "six conditions under two per-arm baselines are four comparisons, not five".
  It is unreachable today because `E-SWEEP-BASELINE-PARTIAL` refuses the config
  before `run`, which is why the refusal was left standing rather than deleted:
  removing it now would ship per-cell expansion with single-baseline contrast
  targeting, i.e. a wrong correction family, in the window between task 6 and
  task 8.

## Worked-example re-verification

```
expand({'sweep': {'baseline': {'analysis.method': 'pearson'},
                  'grid': {'analysis.method': ['spearman', 'kendall']}}})
→ 3 conditions
→ ['00_baseline', '01_method=spearman', '02_method=kendall']   (condition_dir_name)
→ is_baseline: [True, False, False]
```

`cohort-pilot`'s baseline fixes `analysis.method`, the only axis it sweeps, so
`unfixed` is empty, it stays in the table's first row, and its labels and count
are byte-identical to before. `git diff HEAD~1 -- tests/test_artifacts.py
tests/test_runner.py src/publishable/validate.py` is empty; both files pass
untouched.

## Mutation table (all run against the committed tree, `tests/test_sweep.py`)

| # | Mutation | Result |
|---|---|---|
| 1 | Expand over the axes the baseline **does** fix (drop the `not` in `_baseline_cells`) | **7 failed**, incl. `…_expands_over_the_rest`, `…_fixing_every_axis_is_still_one_condition_labelled_baseline`, `…_naming_one_path_of_a_paired_entry_fixes_that_whole_axis`, `test_baseline_plus_grid_prepends_the_baseline` |
| 2 | Never expand (`itertools.product()` over nothing — always one empty cell) | **3 failed**: `…_expands_over_the_rest`, `…_per_cell_baseline_label_carries_its_cell`, `…_unfixed_paired_axis_as_one_cell` |
| 3 | A per-cell baseline's label omits its cell (`return "baseline"` unconditionally) | **2 failed**: `…_per_cell_baseline_label_carries_its_cell`, `…_unfixed_paired_axis_as_one_cell` |
| 4 | `is_baseline` true only at index 0 (`is_baseline and i == 0`) | **2 failed**: `…_expands_over_the_rest`, `…_unfixed_paired_axis_as_one_cell` |

Each mutation was reverted with `git checkout --` and the tree confirmed clean
before the next.

## Docstrings corrected rather than left to rot

Two existing claims became half-false and were reworded (the task-5 lesson, in
mirror image — a claimed invariant must be the provided one):

- `check_swept_value`: the baseline exemption's *reason* said `label_for`
  "renders a baseline condition as the literal `baseline` and never joins its
  fixed values into a label". The exemption still holds — only unfixed axes'
  values enter a per-cell label, and those are axis values already checked as the
  axis's own — but the reason now rests on "never joins its **fixed** values".
- The module docstring's non-dedup paragraph: with per-cell expansion, a baseline
  cell coinciding with a product row is the ordinary case (it happens once per
  cell whenever the fixed value is also a level on a fixed axis, as in the
  brief's own test). Phrasing updated; the policy — no dedup — is unchanged.

## Questionable / for later tasks

1. **Ordering: this is a divergence from a normative rule, and it is now recorded
   in `docs/superpowers/spec-defects.md`, not only here.** The rule is
   `reference.md` § How artifacts are organized, label-grammar table, **Index**
   row — which I originally cited only through its § Expansion modes
   illustration:

   > Assigned over the expansion in order, each cell's baseline first *within its
   > cell*. … With one baseline it is condition `00`; with one per cell they land
   > at the head of each cell, which is why `ablate × groups` numbers
   > `00_cohort=derivation__baseline` and `03_cohort=validation__baseline` rather
   > than putting both baselines first.

   That is a general rule ("which is why"), and this build emits baselines as a
   leading block instead. Unreachable today — `E-SWEEP-BASELINE-PARTIAL` gates
   every multi-baseline config — but it is the numbering task 8 builds on. The
   entry carries the argument that the interleaved rule is **ill-defined** rather
   than merely unimplemented (with the free axis not outermost, a cell's rows are
   not contiguous and "head of each cell" has no referent), which is why the
   document is the thing that should change and why no code change was taken here.
2. **A half-fixed `paired`/`sample` axis** is treated as fixed. Today
   `E-SWEEP-BASELINE-PARTIAL` refuses it (the refusal is path-granular). When
   task 7 retires that refusal, the config becomes *accepted* and silently takes
   this reading — task 7 should decide whether it deserves its own refusal
   (a baseline naming half a coupled cell arguably never means anything).
3. **A `sample` axis the baseline does not fix yields `n` baseline conditions** —
   `n: 50` becomes 50 baselines plus 50 draws, doubling the metered work of a
   sweep whose declaration says 50. That is what the rule states ("group axes and
   parameter axes alike"), and `dry-run`/`limits.max_executions` report the real
   number, but it is worth a sentence in the docs or a warning; noted for task 7/8
   rather than invented here.
4. **`contrasts.py` now has a reachable-in-principle wrong answer** (first
   baseline wins, and other baselines are themselves compared), gated shut only
   by `E-SWEEP-BASELINE-PARTIAL`. Task 7 must not retire the refusal before task
   8 lands, or must land them together.

## Addendum after review (2026-08-12)

No code changed. `uv run pytest` → **1061 passed**, `uv run ruff check .` clean,
`uv run mypy` clean; `ruff format` not run.

**One entry appended to `docs/superpowers/spec-defects.md`**: *"Per-cell baseline
numbering: `expand` emits baselines as a leading block, and the § How artifacts
are organized Index row says it must not"*. A task-report bullet is not that
file — this slice has already had to move a finding out of a disappearing report
— so the divergence now lives where it survives the slice. The entry carries four
parts and an owner each:

| Part | Owner |
|---|---|
| The divergence itself, plus the argument that the interleaved rule is **ill-defined** (a cell's rows are not contiguous when the free axis is not outermost, so "head of each cell" has no referent; satisfying it would either contradict the same row's declaration-order nesting or need "cell" redefined — both design decisions) | **The `groups` slice**, which makes multi-baseline configs reachable. Its deliverable is a document decision on the Index row, not a code change taken in passing. Recorded there: **task 8 must resolve a condition's baseline by matching unfixed-axis values, not by position**, which is invariant under either numbering |
| § Expansion modes row 2's example is **circular** — it says `arm` and `sex` are free while naming `sex=f__arm=control` as the target, but a free `arm` means the baseline expands over it too, so `sex=f__arm=control__baseline` is what exists and the named target is a product row. The rule text is unambiguous and this build follows it; the example is the defective half | **Task 8**, which owns targeting |
| A baseline fixing **no** swept path duplicates the whole run (`{z.unknown: 9}` over a four-cell grid → eight conditions, and the correction family doubles) — the same shape as the `sample` n-doubling my Questionable #3 named | **Task 7**, which retires `E-SWEEP-BASELINE-PARTIAL` and must route both |
| The label body now mixes `key=value` with a bare `baseline`. Not a defect: nothing in `src/` parses a label body (checked recursively, `templates/` and `generators/` included). The residual is that a future parser must handle `baseline` as a **trailing component of a mixed body**, not only as a whole-label special case — which my `check_swept_value` docstring rewrite did not say | No owner today; recorded for the first label-body parser |

Corrections to this report's own premises, from the review:

- **Questionable #1 rewritten** to quote the Index row rather than the
  § Expansion modes example, and to point at the `spec-defects.md` entry.
- The "cell-ordering divergence" between the two doc passages that the brief
  asked me to defend was the brief's misreading, confirmed by the reviewer: a
  baseline row and a product row render in the same `axes` order, the baseline
  merely omitting the fixed axes — one order over two subsets, not two orders.
  The real divergence is the **Index** row, above, which is about numbering.
- My reasoning that `validate` is computed independently of `expand` — hence no
  existing test moved and `contrasts.py`'s single-baseline `next(...)` is
  unreachable — was verified by probe rather than assumed: `validate` is
  uniformly *stricter*, and the gate holds across `grid × grid`, `grid × paired`,
  a half-fixed `paired`, a baseline fixing nothing swept, and both `sample` cases.
