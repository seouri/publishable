# Whole-branch Critical: a `sweep.baseline` fixing a `sweep.groups` level renders the arm twice

Status: **fixed**. `uv run pytest` 1502 passed / 2 xfailed, `ruff check` and `mypy` clean.

## The ruling as implemented

A `sweep.baseline` may never fix a level of a `sweep.groups` axis. `validate` refuses the
declaration outright, under **two mutually exclusive codes**.

## 1. Widen or mint — the choice, and why

**Minted a sibling, `E-SWEEP-BASELINE-GROUP`, guarded exclusively against the existing
`E-SWEEP-ABLATE-BASELINE-GROUP`.** The argument is stronger than "the name would be wrong":
the two shapes fail in *different ways*, and one message cannot state both truthfully.

`sweep.expand`'s `crossed` branch is the discriminator. Under `ablate` over group axes alone —
the one composition § Expansion modes permits — the bare product rows are **not emitted**, so
the fixed level is not duplicated; what goes wrong is that the baseline expands over nothing
and every *other* level executes nowhere. That is exactly what
`E-SWEEP-ABLATE-BASELINE-GROUP` already says. Without `ablate` the product rows *are* emitted
and the fixed level is rendered twice, which is the defect under review. A single widened code
would carry one of those two consequences and be false about the other — the
"comment claims a guarantee the branch does not provide" class this branch hit seven times.

So: one rule, two codes, exclusive guards (`if ablate and fixed_levels` / `elif fixed_levels`).
No config collects both, and each message names the consequence its own shape produces.

Two scoping corrections went in with it:

- The ablate message previously asserted "every other level would be executed by no condition
  at all" unconditionally. `crossed` requires *every* axis to be a group axis, so `ablate` +
  `groups` + `grid` takes the other branch of `expand` and duplicates the level after all. The
  message and its registry row now scope the claim to the permitted composition, and note that
  the parameter-axis cross is co-refused by `E-SWEEP-ABLATE-CROSSED`. The three-code finding
  set for that config is pinned in the test so the co-report is not something a reader has to
  re-derive.
- The new message's duplicate consequence is stated for the case that produces it — a value
  naming a level the axis declares. A baseline fixing a group path to something no level names
  is refused by the same rule, not by that consequence; the comment says so.
- The new message's remedy clause is scoped to "where the axis declares two or more levels".
  On the one-level config this Critical came from there is no second arm, so an unqualified
  "name it as a contrast instead" would point at a route that config cannot take.
- The co-report with `E-DATA-ALLOCATION-CONTRAST` is stated as a mechanism (the other levels'
  product rows cross the single baseline) rather than as an unconditional promise, in both the
  registry row and the code comment.

## 2. Documents

`reference.md` § Expansion modes (the `groups` and `baseline` blocks are what the brief calls
§ Group axes):

- Added the governing statement to the `groups` block: **the arms are peers, and
  `sweep.baseline` may not fix one of them**, with the mechanism (baseline row and product row
  are the same cell) and the route: a named comparison between two arms is a
  `statistics.contrasts` entry naming both labels. That route is stated with its build
  restriction attached — `E-DATA-ALLOCATION-CONTRAST` refuses that delta today, so until the
  unpaired estimators exist it is a `summary`-step `Estimate` or two runs joined in a `study`.
  Promising the contrast plainly would have been a guarantee this build does not provide.
- `baseline` mode: "It accepts group levels as well as parameter paths, so `{arm: control}`
  designates the control arm" → it fixes *parameter* paths and only those.
- Baseline-count table, first row: the example `{arm: control, analysis.method: pearson}` is
  now `{analysis.method: pearson, analysis.min_samples: 30}` over a grid sweeping both. A
  group axis is always on the unfixed side, so a design carrying one is always in the second
  row — stated in the rule paragraph beneath the table.
- The "expansion doesn't distinguish group axes from parameter axes" paragraph is now about
  the *unfixed* side; its "Fixing a randomized arm and leaving an observed `sex` axis free"
  example described a refused config and is gone.
- The `ablate × groups` paragraph and the earlier § Expansion modes sentence both said
  `validate` rejects the shape "while `ablate` is declared"; both now say it is rejected
  everywhere, and name which code reports where.
- Config schema block: `sweep.baseline`'s inline comment now says parameter paths only.

§ Validation and the error registry:

- New rows for the new code in both (§ Validation *Baseline isn't a group level*; registry row
  alphabetically between `E-SWEEP-AXIS-EMPTY` and `E-SWEEP-EXPANDS-EMPTY`). No row anywhere is
  located by position, and I checked the rows the two insertions move.
- *Allocation deltas aren't computed* and the `E-DATA-ALLOCATION-CONTRAST` registry row: both
  led with a generated `vs_baseline` example (`00_arm=control` vs `01_arm=treatment`), which
  requires a baseline fixing a group level. They now lead with the declared contrast and say
  the `vs_baseline` route is always co-reported with the new refusal.
- *Baseline leaves contrasts confounded*: "A baseline fixing a group axis too is outside this
  check" described a refused shape as merely unchecked; it now points at the refusal.

`experimental-designs.md`:

- § Between-subjects factorial told the reader to fix the randomized axis in `sweep.baseline`
  and leave the observed one free. Both axes there are `groups` axes, so **no** baseline can
  fix either; the passage now says so and routes the arm comparison to a declared contrast and
  a `summary` `Estimate`.
- § Factorial's "the baseline expands over whichever axes it doesn't fix" keeps its rule and
  gains the qualifier that only a parameter axis is ever on the fixed side. Its "one treatment
  across three assay lots" example, whose fixed side reads as a group axis, is now "one
  normalization setting".
- § Mistakes core prevents' *two identical measurements reported as two arms* said "a fourth
  closes the route…". Per the branch's own `e91cf0d` lesson, the counting phrase is gone: the
  codes are named instead, and the new one is named with them.

`README.md` and `design-principles.md` needed no change (no baseline/group-axis material).
The feasibility analysis's two baselines fix parameter paths (`transform.arm`,
`cohort.*`), not group levels.

## 3. Tests

- `test_the_one_level_control_arm_baseline_reports_where_it_once_validated_clean` — the defect
  config itself: `between` + `by_attribute` over 8 `control` units, one level, baseline fixing
  it. Before the fix it reported **literally nothing** (verified: `codes()` including warnings
  was empty); it now reports the exact set `{E-SWEEP-BASELINE-GROUP}`.
- `test_a_baseline_may_not_fix_a_group_level` (the rewritten
  `test_a_baseline_may_fix_a_group_level`) — exact finding sets at one level and at two, plus
  four controls that must each report something different: a parameter-path baseline beside a
  group axis stays legal; the same key with no axis declaring it stays
  `E-SWEEP-PATH-UNKNOWN`; a misspelled parameter path beside a real axis is still checked; and
  `ablate` takes the sibling code alone, or beside `E-SWEEP-ABLATE-CROSSED` when a parameter
  axis is crossed in.
- Updated exact sets and docstrings in `test_a_baseline_may_not_fix_a_group_level_while_ablate_is_declared`
  (its third control gains the new code) and the `E-SWEEP-LEVEL-DUPLICATE` and generated
  cross-arm tests, whose prose claimed the old reading.
- Docstrings in `test_sweep.py`, `test_runner.py`, `test_cli.py` and `cli._wide_swept_paths`
  that quoted "accepts group levels … designates the control arm" or asserted the shape's
  legality are rewritten. Those tests keep their now-refused `sweep` blocks on purpose —
  `expand` and `_wide_swept_paths` are deliberately permissive and total — and each says so.

**Mutation proof** (`__pycache__` cleared between every run):

| Mutation | Result |
|---|---|
| `elif fixed_levels:` → `elif False:` | both named tests FAIL; reverted, PASS |
| guard widened to every baseline path (drop `if path in group_axes`) | both FAIL — the legal parameter-path control is what catches it; reverted, PASS |

## 4. What the refusal makes unreachable

`E-DATA-ALLOCATION-CONTRAST` has two routes. The declared-`statistics.contrasts` route is
untouched and is now the only one reachable in an otherwise-valid config
(`test_a_declared_contrast_across_arms_is_refused` covers it). The generated `vs_baseline`
route required a baseline fixing a group level — every other baseline expands over the group
axis, so `contrasts.baseline_for` matches each condition to its own cell's reference and the
comparison never crosses an arm. That route is now always co-reported with the new refusal
(`validate` collects rather than stops, so it still fires and its per-comparison guard is still
exercised). No coverage is dead; three prose sites that cited the generated route as the code's
example were corrected rather than left claiming a reachable shape.

Also corrected in passing: `_check_sweep`'s docstring claimed *Ablation baseline isn't a group
level* was "the one § Validation row still open" — it has been implemented since; it now names
both codes.

## Concerns — configs that still produce two conditions with identical non-empty rosters

Verified empirically against `validate`; none is in scope for this fix, all are the
*parameter*-path twin of the defect just closed (the roster is the full roster on both sides,
so it is non-empty and identical):

1. **A baseline whose fixed value is also a swept value.**
   `baseline: {analysis.method: pearson}` beside `grid: {analysis.method: [pearson, spearman]}`
   reports **nothing at all** — no error, no warning. `00_baseline` and `01_method=pearson`
   resolve to the same parameters over the same units.
   `W-SWEEP-BASELINE-CONFOUNDED` does not reach it (its `crossed` list is empty at one axis).
2. **A baseline fixing a value equal to the config's default, beside any axis.** Same shape
   reached without a grid: the product row inherits the default, the baseline row states it.
3. **A `paired` axis repeating a row** — `paired: [{analysis.min_samples: 30},
   {analysis.min_samples: 30}]` reports nothing.
4. **A `grid` axis repeating a value crossed with a group axis** — the gap already recorded on
   `E-SWEEP-LEVEL-DUPLICATE`'s registry row: `00_arm=control__method=pearson` and
   `01_arm=control__method=pearson`, identical at every artifact, exit 0, and the duplicated
   label bodies carry the arm so they are selectors.

**(1) is recorded nowhere in any of the four documents** — no error, no warning, no registry
row, no prose — and it is the one a reader is most likely to write by accident: naming the
baseline's value among the swept values is a natural way to say "pearson is the reference". It
is the strongest candidate for a follow-up slice. (2) and (3) are likewise unrecorded; (4) is
recorded on `E-SWEEP-LEVEL-DUPLICATE`'s registry row as a known gap. All
four duplicate a *parameter* setting rather than a claim about which units, which is the line
`E-SWEEP-LEVEL-DUPLICATE` and this fix both draw — but (1) and (2) in particular are one
declaration away from what a reader will write, and produce two identical condition directories
on a green run.
