# Task 5 report — `sweep.groups` expands

**Status:** complete.

**Commits:** `2535200` — *feat(sweep): a group axis is a product axis, so expand it — cells,
labels, and the ablation that crosses it*; and `379cc18` — *feat(validate): a baseline fixing
a group level under `ablate` executes no other level, so refuse it*.

**Tests:** full suite `1407 passed, 2 xfailed` (was `1396 passed, 2 xfailed` at `493eb8d`);
`ruff check` and `mypy` clean. `ruff format` not run. Ten new tests — six in `tests/test_sweep.py`
(`test_a_group_axis_gives_one_condition_per_level`,
`test_a_group_axis_crosses_a_parameter_axis_with_the_group_axis_outermost`,
`test_two_group_axes_cross_each_other`,
`test_a_baseline_expands_over_a_free_group_axis_and_is_fixed_by_one_it_names`,
`test_a_group_key_is_disambiguated_against_a_parameter_path_ending_in_it`,
`test_ablate_crosses_a_group_axis_into_one_baseline_and_n_ablations_per_level`,
plus `test_a_group_axis_is_total_over_a_malformed_groups_block`) and three in
`tests/test_validate.py` (`test_a_baseline_may_fix_a_group_level`,
`test_a_group_axis_may_not_name_a_path_a_parameter_axis_writes`,
`test_a_group_level_must_render_into_a_condition_label`,
`test_a_baseline_may_not_fix_a_group_level_while_ablate_is_declared`).

## What landed in `expand`

- `_axes` builds a group axis's cells from `{by, levels}` and **heads the list with them**.
  That is the ordering decision task 3 left open, and it is read rather than chosen:
  § How artifacts are organized fixes the axis order as "`groups` axes in declaration order,
  then parameter axes in declaration order", a row's label renders from its `values` in
  insertion order, and heading the list also makes the last *parameter* axis the one that
  varies fastest — the same Index row's other rule. Both directions pinned by exact labels
  (`arm=control__method=pearson`, `sex=f__arm=control`).
- Group paths are **unioned into `swept`, ahead of the parameter paths**, so `_keys_for`
  disambiguates them: a group axis `arm` beside a grid axis `data.arm` renders `arm=` and
  `data.arm=` rather than two identical keys. `_keys_for` only ever lengthens a key when
  shown another path, and no config without `groups` gains one, so nothing existing moved.
- The malformed-shape reading is `selector_paths`' — total, on `validate`'s
  expand-inside-a-`try` premise. A non-list `levels` contributes **no cells** rather than
  being iterated: a bare string is iterable, and expanding one character by character is the
  trap `_check_shape`'s per-axis `list` guard closes for `grid`. `levels: []` is an axis with
  no cells, so the product is empty and `E-SWEEP-EXPANDS-EMPTY` refuses it — deliberately the
  backstop rather than a `groups`-specific `E-SWEEP-AXIS-EMPTY`, which is the same answer an
  empty `grid` axis's *product* gets.

## The regression this task would otherwise have shipped: `ablate × groups`

**Not in the brief, and it is the finding.** The moment a group axis enters `_axes`, the
composition § Expansion modes *permits* starts expanding wrong. With the document's own
example (2 cohorts, baseline fixing two features, 2 removals) the pre-existing two-phase
`expand` produced 2 baseline rows + **2 bare product rows** (a cell carrying the base config's
parameters — neither that arm's baseline nor an ablation of it) + **2 ablate rows carrying no
cell at all** (both arms running one ablation). Six conditions, the right count by
coincidence, the wrong set — and no later task could fix it: task 19 is test-only and its
step 1 asserts exactly this shape.

So `expand` now crosses it: each ablation is repeated over each baseline cell, and the bare
product rows are suppressed — "(1 + n) conditions per level", the count § Expansion modes
states. Cells outer, changes inner, so a cell's ablations are contiguous; an ablate row's
values are cell → baseline → change, and its label is cell → change
(`cohort=derivation__labs=false`, the label the document shows).

**The crossing is gated on every axis being a group axis**, not on `ablate` being declared.
`ablate` beside a parameter axis is refused (`E-SWEEP-ABLATE-CROSSED`) and the document gives
that shape no reading at all, so it expands exactly as it did before — inventing one would be
a design decision taken where the specification declines to make one, and
`tests/test_contrasts.py::test_a_condition_whose_cell_has_no_baseline_gets_no_comparison`
builds a real `baseline_for` behaviour out of precisely that illegal shape. An unconditional
crossing broke it; that failure is what found the gate. (It is also the one existing test
outside `tests/test_sweep.py` that calls `expand` with `ablate` *and* an axis — worth knowing
for whoever revisits this.)

## The numbering is a leading block, and § How artifacts are organized still says otherwise

`expand` emits `00_cohort=derivation__baseline`, `01_cohort=validation__baseline`, then the
four ablations. The Index row shows `00`/`03` — baselines at the head of each cell.
**Not changed here, deliberately.** `docs/superpowers/spec-defects.md` § *Per-cell baseline
numbering* already owns this, its stated deliverable is "a document decision on the Index
row … not a code change taken on the way past", and its argument stands: "the head of each
cell" is undefined once a second axis makes a cell's rows non-contiguous, so satisfying it
would either contradict the declaration-order nesting of the same row or renumber every
existing design.

What changed is its **status**: that entry was written about a divergence reachable only
through `grid`, and this slice makes the row's own `ablate × groups` illustration reachable —
the example in the document now names indices `expand` does not produce. `spec-defects.md` is
gitignored and will not survive the merge, so this paragraph is the durable record.
**Recommendation, for task 18 or 20:** narrow the Index row to the single-axis case it
actually describes and bless the leading block. `expand`'s docstring now carries the
divergence and the pointer, and the ablate test pins it as behaviour.

## The two gaps task 4 routed here — both fixed, both `validate`'s

1. **A baseline may fix a group level.** `_check_sweep`'s baseline loop now `continue`s on a
   path in `selector_paths(sweep)` **before** `_path_resolves`, not after: `_value_checks`
   indexes `spec[path]` unguarded, so suppressing only the error would move the `KeyError`
   one line down inside a function contracted never to raise. The gate is the *declared axis
   names*, never the presence of a `groups` block — which also closes **task 3's open
   concern**: a baseline fixing a group path no axis declares is an unknown parameter path
   and stays `E-SWEEP-PATH-UNKNOWN`. Both controls are in the test and both must report.
2. **`groups: [{by: arm}]` beside `grid: {arm: [...]}` earns a refusal** — `E-SWEEP-PATH-DUPLICATE`,
   reused rather than a new code minted (same choke point; a new code drags in the registry
   and task 20's integrity check). It earns one because the harm is *worse* than the
   overwrite that code already names: `expand` marks the path a selector on every row, so
   `resolve_condition_cfg` plants nothing and `_wide_swept_paths` subtracts it — the grid
   axis claims to sweep `parameters.arm` while every condition runs the base value at every
   scope, which is § Mistakes core prevents' "a typo'd parameter silently using a default"
   by a route nothing else covers. `reference.md`'s row 480 was rewritten to state that harm
   rather than merely widening its mode list. The check reads `selector_paths`, the same
   function `expand` marks with, so it cannot disagree with the marking it is about.

   **Overlap with task 19 step 2, resolved:** step 2 ("a `groups` axis whose name collides
   with a parameter path — decide and pin") becomes *pin the refusal*, which a test-only task
   can do. **One adjacent case I did not fold in and am routing there rather than deciding
   silently:** a `by` naming a *declared parameter* that no axis sweeps. There is no
   overwrite and nothing is unplantable — the parameter simply keeps its base value, which is
   honest — so the only harm is a shared name, and inventing a refusal for it is the
   direction `CLAUDE.md` forbids. Task 19 owns it.

## A fourth gap, and it is the one that made a declared level vanish

The document says twice that `validate` rejects a baseline fixing a group level while
`ablate` is declared (§ Expansion modes, at the `ablate × groups` example and again at the
baseline table). **It was never implemented**, and this task made the consequence severe.
Traced through the code as shipped, with `baseline: {cohort: derivation, features.labs: true}`
beside that axis and one `remove`: the baseline fixes the group axis, so `_baseline_cells`
counts it fixed and `cells == [{}]`; the crossed ablation repeats over that one empty cell;
the product rows are suppressed. `expand` returns exactly `00_baseline` and `01_labs=false`,
both on `derivation` — **`validation` is executed by no condition at all** while the run
reports success. Verified by running it.

Worse, my gap-1 fix removed the accidental signal: before it, `baseline: {cohort: derivation}`
reported `E-SWEEP-PATH-UNKNOWN` because `cohort` is no parameter. Correct to remove — but it
was the only noise covering this shape.

So it is refused: **`E-SWEEP-ABLATE-BASELINE-GROUP`**, a new identifier with a new row in
§ Errors validate reports, beside the two ablate refusals it belongs with. This is not an
invented rule — the document states it twice and I quoted it in both the message and the row;
what the row adds is *why it is an error rather than a numbering nit*, which is the vanishing
level. The gate is `ablate` truthy and any `baseline` key in `selector_paths(sweep)`. Both
controls report: an ablation whose baseline fixes a *parameter* beside the same group axis is
the legal composition (`test_ablate_composes_with_a_group_axis`, untouched and still exactly
`{"E-SWEEP-GROUPS-UNSUPPORTED"}`), and the same baseline *without* `ablate` is the ordinary
per-cell design. Mutation: gate neutralized → its own test fails alone (`1 failed, 437 passed`).

## A third gap neither the brief nor task 4 named: group levels were unchecked

`check_swept_value` runs over `grid`, `paired` and `ablate.override` values; a baseline's
values are exempt *because `label_for` never renders them*, and its docstring justified the
exemption with "the only axes a baseline can leave free are `grid` and `paired`". **Expanding
`groups` makes that false** — a group cell renders into a label, so `levels: [a__b]` passes
`SWEPT_VALUE_PATTERN`, destroys the axis separator, and yields a label that cannot be parsed
back into axes; `a/b` yields one that resolves outside the condition directory. New exposure
created by this change, so it is closed here rather than reported: every level goes through
`check_swept_value` and reports `E-SWEEP-VALUE-UNNAMEABLE`. Not through `_value_checks` — a
level names a set of units, so there is no `Param` and `spec[path]` would raise.
`reference.md`'s row 484 and the docstring both say so now.

## How the end-to-end cases were reached without retiring `E-SWEEP-GROUPS-UNSUPPORTED`

`validate` **collects rather than stops**, so every one of the three `validate` tests asserts
the *exact error set* — `E-SWEEP-GROUPS-UNSUPPORTED` present **and** the code under test
present or absent as the claim requires. No refusal was retired, and
`test_ablate_composes_with_a_group_axis`'s `found == {"E-SWEEP-GROUPS-UNSUPPORTED"}` still
holds. The `expand` behaviour is tested directly, as the brief required.

One user-facing message did have to move: `E-SWEEP-GROUPS-UNSUPPORTED` said "this build
expands `baseline`, `grid`, `paired`, `sample` and `ablate` only", which this task makes
false. It now says `expand` crosses a group axis into the product but nothing yet resolves a
level into the units it names — which is the real reason the block is still refused, and the
thing task 17 will delete.

## Two existing tests moved, and neither is "every other mode"

The whole H2 sweep suite ran untouched and green. Two tests that pinned *`groups` not
expanding* as an explicit task-5 boundary had to change, both written by earlier tasks of
this slice: `test_the_mode_vocabulary_is_partitioned_and_parameter_axes_are_a_subset`
(task 2's `assert expand({"sweep": {"groups": …}}) == []`, now the two labels it produces) and
`test_a_group_path_is_marked_a_selector_and_a_parameter_path_is_not` / task 4's
`test_a_group_cell_adds_no_parameter` (both pinned the 4-row expansion of
`groups + grid + baseline{arm: control}`, now 6 rows — 2 baseline + the 2 × 2 product). Their
probes and controls are unchanged; task 4's gained the assertion § Expansion modes actually
makes, which was previously unreachable: the two *arms* at one method resolve to the same
`parameters_hash`.

## Mutations: seven, each killing its own named test

`__pycache__` deleted between every mutation and revert; every revert verified by the suite
passing, never by `git status`.

| Mutation | Result |
|---|---|
| `groups` out of the product (`_axes` reads no entries) | **10 failed** — every count and label assertion, in `test_sweep.py` and `test_runner.py` |
| Axis order rotated (`axes[1:] + axes[:1]`) | **14 failed.** Honest label: a global rotation, so it also moves parameter-only designs — `test_a_per_cell_baseline_label_carries_its_cell` declares no `groups` and died too. It does not isolate "group axes last"; the ordering decision is separately pinned by the exact-label assertions in the two crossing tests |
| Ablate rows not crossed with the cells (`for cell in [{}]`) | **1 failed**, the named ablate test alone |
| Group paths out of the labelling set (`swept = []`) | **1 failed**, the disambiguation test alone |
| Baseline selector skip neutralized | **1 failed**, `test_a_baseline_may_fix_a_group_level` alone |
| Collision check neutralized | **1 failed**, its own test alone |
| Level nameability check neutralized | **1 failed**, its own test alone |
| `E-SWEEP-ABLATE-BASELINE-GROUP`'s gate neutralized | **1 failed**, its own test alone |

Every probe carries a control that must report: the empty sweep (one unlabelled condition),
the grid-only sweep at every group assertion, the one-axis expansion against the crossed one,
a plain ablation against the crossed one, `data.arm` shortening to `arm=` with no group axis
competing, a baseline path named `arm` with **no** `groups` declared still reported unknown,
and a misspelled parameter path beside a real group axis still reported.

## Concerns

- **The Index row above is the one document decision this slice still owes**, and it is now a
  reachable divergence rather than a theoretical one.
- **`groups` has no shape guard in `_check_shape`.** `grid` and `paired` each got one; a
  non-list `groups`, a non-mapping entry, a non-string `by` and a non-list `levels` are all
  merely *tolerated* by `_axes` and `selector_paths` (contributing no axis), so a typo'd
  block silently expands to the parameter product instead of being refused. Whoever retires
  `E-SWEEP-GROUPS-UNSUPPORTED` (task 17) inherits this: today the mode is refused wholesale,
  so a malformed one is refused too, and the day that stops being true a malformed `groups`
  validates clean. Not taken here — it is a `_check_shape` question, and its sibling rows
  were each written with the crash they close named.
- **The correction family and the budget both change size**, which is task 6's ("*Grid size
  sane* … the row was already implemented and this slice makes it wrong"). Confirmed live:
  `len(expand(doc))` now multiplies by the group levels, and under `ablate × groups` it is
  levels × (1 + n) rather than 1 + n.
- The worked example is untouched: `cohort-pilot` declares no `groups`, so `_axes` gains no
  axis, `swept` gains no path, and `crossed` is false for every config in the four documents.
  The only `reference.md` edits are three rows of § Errors validate reports — two rewritten,
  one added (mechanical pass run over all three: links resolve, two columns each, no trailing
  whitespace, tabs or invisible unicode). None is a cross-document class — no shared-example
  value, config field, enum comment, version or declared/derived claim moved.
- **`E-SWEEP-ABLATE-BASELINE-GROUP` is a new identifier**, so task 20's registry-integrity
  pass has one more row to reconcile, and task 17's retirement list is unaffected by it.
