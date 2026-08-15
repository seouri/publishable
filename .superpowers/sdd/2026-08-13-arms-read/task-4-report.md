# Task 4 report — the readers learn the distinction

**Status:** complete.

**Commits:** `493eb8d` — *feat: a group cell selects units, so no reader may plant it as
a parameter*.

**Tests:** full suite `1396 passed, 2 xfailed` (was 1393); `ruff check` and `mypy` clean.
Three new tests: `tests/test_runner.py::test_a_group_cell_adds_no_parameter`,
`::test_an_existing_condition_resolves_byte_identically`, and
`tests/test_cli.py::test_a_group_path_gets_no_swept_away_marker`.

## The seven, one at a time

| Site | Verdict |
|---|---|
| `runner.resolve_condition_cfg` | **Changed.** Skips a path in `condition.selectors` |
| `cli` run.yaml conditions block | **Correct as-is.** The document prescribes verbatim |
| `sweep.sweep_document` | **Correct as-is.** Same, and its payload matches the document exactly |
| `sweep.label_for` | **Correct as-is.** A group cell must render — `arm=control` |
| `contrasts` free-axis matching | **Correct as-is.** A group axis *is* an axis for baseline matching |
| `validate` swept-value checks | **Correct as-is.** Reads `sweep.sample.ranges`, which no group path enters |
| `validate` confounded check | **Correct as-is.** `swept_axes = list(grid)` — task 1's finding |

Each "correct as-is" is a reading of what the site consumes, not an assumption:

- **The two records.** § Expansion modes says outright: "The design cell is recorded in
  `results.conditions[i].values` (`{arm: treatment}`) and the realized membership in
  `allocation.json`." Recording it verbatim is what the document asks for.
- **`label_for`.** § How artifacts are organized shows `arm=control` in a condition
  directory name, so the cell must reach the label. Verified by running it:
  `label_for({arm: control, analysis.method: pearson}, …)` → `arm=control__method=pearson`.
  Ordering of group axes against parameter axes is task 5's, per task 3's boundary.
- **`contrasts`.** Verified by running `_free_axis_paths` + `baseline_for` over
  `groups + grid + baseline: {arm: control}`: free axes are `[analysis.method]`, and each
  product row matches the baseline row of its own method. A group path *should* participate
  — that is how each arm gets its own baseline once `groups` expands.
- **`validate`'s swept-value check** (`_check_sampled_values`) iterates `sample["ranges"]`
  and only asks `condition.values` about those paths. A group path is not a sample range.
- **`validate`'s confounded check** reads `swept_axes = list(grid)` — grid's axes alone.
  Task 1 already found this and rewrote the row's `arm: control` example for exactly this
  reason ("the row's example described a warning that never fires").

## An eighth site the brief's seven do not list, and it is the same leak

`cli`'s wide config: `resolve_wide_cfg(doc, swept_paths)` where `swept_paths` unions
`_swept_paths | ablated_paths | set(sweep.baseline)`. A `baseline` may fix a group level,
so `arm` arrives through the third term and would be planted as a `SweptAway` marker at
`parameters.arm` — a `run`- or `summary`-scoped step reading `cfg.parameters.arm` would get
`E-STEP-SWEPT-PARAM` ("this is varied by `sweep`") for a parameter that exists in no scope,
instead of the honest `E-STEP-PARAM-UNKNOWN`. Fixing only the condition side would have left
it. The inline union is now `cli._wide_swept_paths`, a named function carrying the union's
existing reasoning plus the subtraction, extracted because it is otherwise untestable:
`validate` refuses `groups` outright in this build (`E-SWEEP-GROUPS-UNSUPPORTED`), so no
`run` reaches the line with a group axis declared.

`cli._differing_axes` is a ninth reader (union of both sides' keys, sentinel comparison).
Correct as-is and unchanged, on `contrasts`' rule: a condition and a baseline in different
arms genuinely differ on that axis, and `confounded` should say so.

## The brief's `parameters_hash` premise is false, and the constraint as written is unsatisfiable

`parameters_hash` covers the whole config except `metadata` and the two host paths, so
`sweep.groups` is *inside* it — adding a group axis necessarily changes it, and "unchanged
by adding a group axis" cannot be asserted at the config level. And `cli` computes
`ph = parameters_hash(doc)` over the **base** config: the `cfgs` from
`resolve_condition_cfg` are never hashed, so the phantom parameter never reached
`parameters_hash` at all. The stated harm is wrong; the real harm is that a `condition`- or
`repeat`-scoped step reads `cfg.parameters.arm`, a name no `parameter_spec` declares, and
that two arms of one design resolve to configs that are *not* the same parameters.

The headline test asserts the satisfiable form, directly rather than by inspection: hash the
**resolved condition configs**, and require the arm-fixing row and the arm-free row at the
same method to agree (`parameters_hash(resolved[0].raw) == parameters_hash(resolved[2].raw)`),
which is § Expansion modes' "two conditions on a group axis can share a `parameters_hash`".
Its non-vacuity control is in the same test: the two *methods* must still differ, and a grid
axis literally named `arm` must still be planted.

`test_an_existing_condition_resolves_byte_identically` pins the no-`groups` case as a
literal document, not against a second call.

## Signature: the `Condition`, not a `selectors` argument

`resolve_condition_cfg(base, condition)` rather than `(base, values, selectors=…)`. A
defaulted `selectors` leaks silently for any future caller who forgets it; the whole
condition cannot be mismatched or forgotten, and it is the invariant the controller pinned
before task 3 — the answer lives on the condition rather than being re-derived or re-passed
per reader. `runner` already imported from `publishable.sweep`, so no new cycle. Four test
call sites moved to a `_condition(...)` helper.

## The decision the brief left open: the record does not need a new key

**No document change, and none was made.** Split by file, because the two arguments differ:

- **`run.yaml`** — a reader *can* tell an arm from a parameter. It embeds "the config
  embedded verbatim" (§ The two files), so `config.sweep.groups[].by` names every group
  axis, and `results.conditions[i].values` carrying `{arm: treatment}` is what § Expansion
  modes literally prescribes. The distinction is recoverable one level up; a `selectors`
  key would be a second spelling of it, which is the drift this project exists to prevent.
- **`sweep.yaml`** — it embeds no config and does not self-describe, so the distinction is
  genuinely not recoverable from that file alone. It is still left unchanged, on task 3's
  reason rather than a recoverability one: its payload "matches § `sweep.yaml` — the
  resolved plan exactly", `sweep.yaml` is not the reporting artifact (`run.yaml` is), and
  adding a key needs the document to move first. If task 5 or a later slice decides
  `sweep.yaml` must stand alone, that is a document change and belongs there.

**The check that could have invalidated this, and its answer.** § "`sweep.yaml` — the
resolved plan" says "`resume` reads it back rather than re-deriving it" — so if `resume`
rebuilt `Condition`s from `conditions[].values`, it would rebuild them with
`selectors=frozenset()` and re-plant `parameters.arm` on the resumed leg of the very run
that refused it on the first. **`resume` is not built** (no `resume` command in `cli.py`),
and `Condition(...)` is constructed in exactly two places, both inside `sweep.expand`. So
the decision stands — and the constraint whoever builds `resume` inherits is: re-derive the
marking with `selector_paths(config["sweep"])` from the config `run.yaml` embeds, rather
than reading it back from `sweep.yaml`. Only if a resumed run has no config in hand does
`sweep.yaml` need the key, and then the document moves first.

## Mutations: two sites changed, two mutations, two named tests

**Six mutations was the brief presuming six sites change.** Only two did, so two mutations —
inventing four against unchanged code would be the could-not-fail check task 2 refused.

1. Delete the `if path in condition.selectors: continue` from `resolve_condition_cfg` →
   `test_a_group_cell_adds_no_parameter` **failed**, alone (`1 failed, 204 passed`).
2. Neutralize the subtraction in `_wide_swept_paths` (`- selectors` → `| (selectors -
   selectors)`, so the name stays used and `ruff` is not what reports it) →
   `test_a_group_path_gets_no_swept_away_marker` **failed**, alone (`1 failed, 130 passed`).

The **opposite** direction of mutation 1 — skip *every* path, not just the selectors — is
covered without a mutation of its own: `test_an_existing_condition_resolves_byte_identically`
pins a no-`groups` condition's resolved document as a literal, so a `resolve_condition_cfg`
that planted nothing fails it. The single mutated direction is therefore sufficient rather
than half of task 3's both-directions discipline.

`__pycache__` deleted between every mutation and revert; both reverts verified by the suite
passing, never by `git status`. Every probe carries a control that must report: the
grid-only `arm` axis in test 1, the baseline-only `analysis.min_samples` in test 2 (same
term of the union the group path arrives by, so a subtraction taking the whole `baseline`
fails there).

## Concerns

- **A latent `validate` defect task 5 will hit immediately, and it is an eighth reader of
  the distinction — of `sweep`, not of `values`.** `_check_sweep`'s `_path_resolves` scans
  `sweep.baseline` keys against `template.parameter_spec` and reports
  `E-SWEEP-PATH-UNKNOWN`. `baseline: {arm: control}` is exactly such a key, and `arm` is in
  no `parameter_spec` — yet § Expansion modes says a baseline "accepts group levels as well
  as parameter paths". So the config every test in this slice is built from is one
  `validate` would refuse, masked today only because `E-SWEEP-GROUPS-UNSUPPORTED` fires
  first. `selector_paths(sweep)` must be subtracted there when `groups` becomes supported;
  this is the same shape as task 3's unresolved concern (nothing refuses a baseline fixing a
  group path that no `groups` axis declares) approached from the other side.
- **A collision nothing refuses, reachable once `groups` is supported: `groups: [{by: arm}]`
  *and* `grid: {arm: [...]}` at once.** `expand` marks per row by path, so the grid row's
  `arm` is marked a selector; `resolve_condition_cfg` then skips planting it and
  `_wide_swept_paths` subtracts it, so the grid claims to sweep `parameters.arm` while every
  condition silently runs the base value at every scope — `experimental-designs.md`
  § Mistakes core prevents' "a typo'd parameter silently using a default", reached by a route
  no check covers: `E-SWEEP-PATH-DUPLICATE` reads only grid/paired/sample, and nothing checks
  a `groups.by` name against `parameter_spec` or against the axis-shaped modes' paths.
  Unreachable today (`E-SWEEP-GROUPS-UNSUPPORTED`), so reported rather than fixed — it is the
  same missing question as the concern above ("is this name a parameter or an axis?") asked
  from the other side, and both are `validate`'s.
- The worked example is untouched: it declares no `groups`, every condition it produces has
  empty `selectors`, and `test_an_existing_condition_resolves_byte_identically` pins the
  resolved document as a literal.
- No document changed, so no cross-document pass was owed.
