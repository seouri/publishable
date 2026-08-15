# Task 8 report — the comparison count under multiple baselines

**Commit:** `632018b` — *feat: each vs_baseline targets its own cell's baseline*
(the report itself, and the `docs/superpowers/spec-defects.md` edits described below, are in
gitignored paths and so are not in that commit's diff).

**Suite:** `1069 passed, 0 xfailed` (was 1062 passed + 2 xfailed). `uv run ruff check .` clean,
`uv run mypy` clean, `ruff format` not run.

## How a condition resolves to its cell's baseline, and why it is index-independent

Two new functions in `src/publishable/contrasts.py`:

- `_free_axis_paths(baselines)` — the paths the **baseline rows disagree on**. `expand` lays the
  same fixed mapping over every baseline cell, fixed values last, so a path the baseline *fixes*
  holds one value across every baseline row and can never appear in that set; a multi-path axis the
  baseline half-fixes counts as fixed in `_baseline_cells` and contributes no cell path at all.
  What is left is exactly the unfixed axes, minus any whose single level makes it constant — and
  matching on a constant path distinguishes nothing, so that omission changes no answer.
- `baseline_for(condition, baselines, free)` — the baseline agreeing with the condition on every
  free path. `None` when no cell matches.

**Nothing reads a condition index.** That is the constraint the numbering entry in
`spec-defects.md` imposes: § How artifacts are organized's Index row says per-cell baselines land
"at the head of each cell" while `expand` emits them as a leading block, and that divergence is an
open document question routed to the `groups` slice — so targeting built on numbering would be
built on numbering that may change. Matching values is invariant under either answer.

**Why not `fixed = set(sweep["baseline"])`, as the brief sketched it.** Both tracked xfails call
`resolve_contrasts({}, conditions)` — there is no `sweep` block in the config they hand it, so
`fixed` would be empty, every path would count as free, and every non-baseline condition would
match no baseline at all (the `spearman` rows hold no baseline's `values`). Verified rather than
reasoned: that reading yields 2 comparisons, not 4. Deriving the free axes from the conditions
gives the same path set from the data `resolve_contrasts` is actually handed. `data.sex` for the
document's design, confirmed by running it.

Three more decisions, each measured:

| Decision | Why |
|---|---|
| A baseline is skipped as an `of` in the **generated loop only**, never by filtering the returned list | A declared `statistics.contrasts` entry may legitimately name a baseline as either side (`Comparison.declared`'s own docstring). A post-filter passes both tracked xfails and silently drops it — pinned by `test_a_declared_contrast_naming_a_baseline_as_its_subject_survives` |
| No match → **no comparison**, not a fallback to the first baseline | A fallback is the cross-cell contrast per-cell baselines exist to remove. Not claimed unreachable: `expand` builds an `ablate` row beside a grid (the composition `E-SWEEP-ABLATE-CROSSED` refuses, so `run` never sees it) and that row holds no value for the free axis, so it belongs to no cell — pinned by `test_a_condition_whose_cell_has_no_baseline_gets_no_comparison` |
| Free paths compared pairwise with `!=`, not collected into a set | A condition's value is arbitrary YAML; a list level (refused by `E-SWEEP-VALUE-UNNAMEABLE` at `validate`, not by `expand`) is unhashable, and `{...}` over it would raise `TypeError` from a function whose answer needs no hashing |

With one baseline the free set is empty, every condition matches `baselines[0]`, and the answer is
the single-baseline behaviour this replaced — which is why the worked example needed no carve-out
(below).

## The arithmetic, before and after

§ Expansion modes: *"Baseline conditions are references rather than comparisons, so they never
count as one: six conditions under two per-arm baselines are **four** comparisons in the correction
family, not five."*

`baseline: {analysis.method: pearson}` over `grid: {analysis.method: [pearson, spearman],
data.sex: [f, m]}` — 6 conditions, 2 baselines:

| | Before | After |
|---|---|---|
| Comparisons | 5 | **4** |
| `(of, against)` | (1,0) (2,0) (3,0) (4,0) (5,0) | (2,0) (3,1) (4,0) (5,1) |
| A baseline as a subject | `sex=m__baseline` of=1 against=0 | none |
| `_differing_axes` per comparison | `['data.sex']`, `[]`, `['analysis.method']`, `['analysis.method']`, `['analysis.method','data.sex']` | `[]`, `[]`, `['analysis.method']`, `['analysis.method']` |

The two `[]` entries are the baseline coinciding with a grid cell — `pearson` is both the fixed
value and a grid level — which `sweep.py`'s module docstring calls the ordinary case under per-cell
expansion and deliberately does not dedup. The count the document states is 4 either way.

## What happened to `family_size`, and which `ci95_corrected` moved

Measured end to end on the same shape with a real run (40 units, 5 seed repeats, one recorded
column), `baseline: {analysis.method: pearson}` over `grid: {analysis.method: [pearson, spearman],
analysis.min_samples: [10, 20]}` — `analysis.min_samples` free:

| Condition | Before: level / `ci95_corrected` | After |
|---|---|---|
| `1 min_samples=20__baseline` | α/5 = 0.01, `[0.0, 0.0]` — **a comparison of one reference against another** | no `vs_baseline` at all |
| `2 method=pearson__min_samples=10` | 0.0125, `[0.0, 0.0]` | 0.0125, `[0.0, 0.0]` |
| `3 method=pearson__min_samples=20` | 0.01667, `[0.0, 0.0]` | 0.01667, `[0.0, 0.0]` |
| `4 method=spearman__min_samples=10` | 0.025, `[0.81335, 1.18665]` | unchanged |
| `5 method=spearman__min_samples=20` | 0.05, `[0.83806, 1.16194]`, **`confounded: true`, `differs_on: [analysis.method, analysis.min_samples]`** | 0.05, same interval, **no `confounded`, no `differs_on`** |
| `family` on every entry | `{comparisons: 5, metrics: 1}`, `family_size: 5` | `{comparisons: 4, metrics: 1}`, `family_size: 4` |

So three things moved: `family_size` 5 → 4 on **every** entry in the run, the phantom
baseline-against-baseline entry disappeared, and condition 5 lost a `confounded` mark it only
carried because it was being taken against the wrong cell's reference. All three are measured on
**this** design; the phantom member's *rank* within the family is a property of the data (here a
zero-width interval at delta 0, which ranks first), not of the defect, which is why the bounds
below do not move here and would in a design where it ranked lower.

**No corrected bound moved in this particular design, and that is worth stating precisely rather
than overclaiming.** Holm's level is α/(m − i + 1) for rank i of m, so removing the member that
ranked *first* leaves every other member's level identical (each drops one rank and m drops by
one). The phantom member here was a zero-width interval at delta 0, which ranks first. Remove a
member ranked below a real comparison instead and every stronger comparison's α *rises* — its
`ci95_corrected` narrows — so the general harm the brief describes is real; this design is the case
where the visible damage is the recorded `family_size` and the phantom entry rather than the bounds
beside them.

## The circular example — fixed in the document

§ Expansion modes row 2 read `{analysis.method: pearson}` "with `arm` and `sex` left free" while
naming `sex=f__arm=control` as the target — but a free `arm` means the baseline expands over `arm`
too, so that target is a *product* row and no such baseline exists. **The example changed; the rule
text did not.** Row 2 now reads `{analysis.method: pearson}` over a grid sweeping `analysis.method`
and `data.sex`, names the baselines it produces (`sex=f__baseline`, `sex=m__baseline`) and states
the target as `method=spearman__sex=f` against `sex=f__baseline` — strings pasted from `expand`'s
own output, and the exact shape the tests run. Two further arguments for replacing rather than
repairing: `arm` is a group level, so that design is not executable at all while
`E-SWEEP-GROUPS-UNSUPPORTED` stands; and the new example is the one the targeting code is tested
against.

`experimental-designs.md` § Crossed group axes carried the same circular claim
(`sex=f__arm=treatment` compares against `sex=f__arm=control`) — found by grepping `arm=control`
across tracked `*.md` — and is corrected the same way, to `sex=f__baseline`, "that stratum's own
reference, holding `arm: control`". The rule text ("group axes and parameter axes alike") is
untouched in both files, as is the `ablate × groups` paragraph below the table, which leans on the
row rather than on its example.

## The warning's remedy — added

`W-SWEEP-BASELINE-CONFOUNDED` now ends: *"fix the axis you are measuring and leave the ones you are
stratifying over free, and each cell gets its own baseline"*. Its guard is "the baseline fixes every
swept axis", so it fires only on a single-baseline design, and per-cell targeting is what makes the
advice true — freeing the stratifying axis now removes it from `differs_on` entirely, which is
exactly the outcome task 7 could not promise and therefore correctly withheld. No build-state hedge
is needed, so none is written. The emit-site comment is rewritten at the point of the decision, and
the two sentences that existed only because this window did — the `contrasts.resolve_contrasts`
paragraph there, and the "not settled" paragraph in `_check_unimplemented`'s docstring — are gone.

**§ Warnings core reports' row is left as it is, and the checklist's suggested softening is
declined, on evidence.** The row says silence on a free-axis baseline "is not a verdict that such a
design confounds nothing", and that is still literally true: a baseline fixing *two* of three swept
axes leaves the third free, so the guard is `False` and nothing is reported, while every cell that
moves both fixed axes differs from **its own cell's** baseline on both and is marked `confounded` at
run time. Measured on `baseline: {analysis.method: pearson, analysis.min_samples: 10}` over a
`method × min_samples × confidence` grid: no `W-SWEEP-BASELINE-CONFOUNDED`, `analysis.confidence`
absent from every `differs_on`, and exactly two comparisons carrying
`['analysis.method', 'analysis.min_samples']`. Pinned by
`test_a_partly_fixed_baseline_is_silent_while_its_run_marks_confounded`.

## The xfail markers, and evidence they flipped for the right reason

Both markers removed. Neither test asserts only what it did before:

- `test_two_per_cell_baselines_are_four_comparisons_not_five` now asserts the **pairs**
  `[(2,0), (3,1), (4,0), (5,1)]` and the two baseline labels, not just `== 4`. Four comparisons all
  aimed at baseline `0` satisfy `== 4` — that is the confound the previous window nearly flipped
  green on, and mutation M1 below shows this assertion catches it.
- `test_no_comparison_has_a_baseline_condition_as_its_subject` is unchanged in substance; its
  docstring now says why a *declared* entry may still name one.

Three tests added beside them (`test_each_per_cell_comparison_differs_on_at_most_the_swept_axis`,
`test_a_condition_whose_cell_has_no_baseline_gets_no_comparison`,
`test_a_declared_contrast_naming_a_baseline_as_its_subject_survives`), one in `tests/test_cli.py`
(`test_per_cell_baselines_correct_against_four_comparisons_not_five`, which observes `family`,
`family_size` and the Holm levels α/4 … α end to end — the two xfails stop at
`resolve_contrasts`, so `family_size` would otherwise be an inference), and one in
`tests/test_validate.py` (the silence-while-confounded case above).

## Mutations

Run against the committed tree, `__pycache__` cleared before each (see § Anything questionable).

| # | Mutation | Result |
|---|---|---|
| M1 | `against = baselines[0]` — first-baseline targeting, the defect | **5 failed**: both per-cell contrast tests, the no-match test, the cli `family_size` test, and the validate silence test. The count test fails on the *pairs*, which is the point |
| M2 | Drop `c.is_baseline` from the subject skip — baselines admitted as subjects | **9 failed**, including `test_no_comparison_has_a_baseline_condition_as_its_subject`, the declared-entry test, the cli `family_size` test, and three pre-existing single-baseline tests |
| M3 | Match on the **fixed** axes instead of the free ones (`any(... != ...)` → `all(... == ...)`) | **6 failed**. The count does not coincidentally hold: matching on `analysis.method` gives `[(2,0), (3,0)]` — 2 comparisons, since the `spearman` rows then match no baseline |

## Anything questionable

- **One mutation revert did not take effect where I read it as having taken effect, and I cannot
  name the mechanism.** Mid-session, after M3 (whose edits are byte-length-preserving: `any(`→`all(`,
  `!=`→`==`) and a `git checkout` that reported "Updated 1 path", several runs behaved exactly like
  the M3 mutant — 2 comparisons, `family: {comparisons: 2}` — while `git status --short` printed
  nothing. I diagnosed it as stale bytecode; that explanation does not survive scrutiny, since
  `git checkout` refreshes mtime and CPython invalidates on mtime or size. Whatever it was, it is
  not reproducible now. What I can support: the current tree has `git status --porcelain` empty, no
  stash, `git diff HEAD` empty over `src/`, `_free_axis_paths` reading `any(... != ...)`, and no
  tracing leftovers in `contrasts.py`/`cli.py`; and **every number in this report — the full suite,
  the three mutations, and both before/after tables — was re-produced from that verified-clean tree
  with `__pycache__` removed first.** Flagged rather than smoothed over: the next window that
  mutation-tests this repo should verify the revert by *behaviour*, not by `git status`.
- `family_size`'s reach is asserted on one design. `correction.family_shape` counts
  `len({m.where for m in members})`, so nothing about the count is per-design, but the end-to-end
  observation covers a two-baseline `grid × grid` only.
- The no-match branch is reachable only through a config `validate` refuses
  (`E-SWEEP-ABLATE-CROSSED`), so it is tested at `expand`'s level rather than through `run`. If a
  later slice makes a legal design reach it, a dropped comparison changes `family_size` with no
  diagnostic — the class of fault this task closed. Worth a `W-` at that point, not before: today
  there is no config that reaches it.
- `E-SWEEP-GROUPS-UNSUPPORTED` still fires (2 tests, verified by name), and the worked example is
  unchanged: `baseline` + `grid: [spearman, kendall]` still gives 3 conditions and comparisons
  `[(1,0), (2,0)]`, with the existing `family_size == 2` assertions passing.
- `docs/superpowers/spec-defects.md` is gitignored, so its two closures (the circular example, and
  the `resolve_contrasts` window) plus the three rulings — the message remedy, the declined
  softening, and no new `W-SWEEP-BASELINE-` identifier for a baseline fixing no swept path (a costed
  design: `dry-run`'s condition count, `validate`'s execution-count warning and `family`'s own
  `comparisons` breakout are the disclosure; the degenerate equal-`parameters_hash` sub-case is a
  duplicate-condition question, not a declaration one) — live only in the working tree.
