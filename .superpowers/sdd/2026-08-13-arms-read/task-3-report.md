# Task 3 report — a group cell is a selector, not a parameter

**Status:** complete.

**Commits:** `b8499e9` — *feat: a group cell selects units, so mark it as one on the condition*.

**Tests:** full suite `1393 passed, 2 xfailed`; `ruff check` and `mypy` clean. Two new
tests in `tests/test_sweep.py`:
`test_a_group_path_is_marked_a_selector_and_a_parameter_path_is_not` and
`test_selector_paths_is_total_over_a_malformed_groups_block`.

## What landed

- `Condition.selectors: frozenset[str]`, after `is_baseline` so no positional
  construction moves. Coerced in `__post_init__` via `object.__setattr__`, the same
  treatment `values` gets and for the same reason — a caller's plain `set` would stay a
  live handle.
- `SELECTOR_MODES`, derived as `PRODUCT_MODES` minus `PARAMETER_AXIS_MODES` rather than
  written as `("groups",)`, so a product mode forgotten in the parameter-axis predicate
  becomes a selector automatically (the safe direction). The residual is pinned as a
  literal in the test.
- `selector_paths(sweep)`, the counterpart to `_swept_paths`, reading `groups`' own
  `{by, levels}` shape. Total over malformed input on `validate`'s expand-inside-a-`try`
  premise.
- `expand` marks per row, not per sweep: a group path is marked only when that row's
  baseline or cell actually fixed it.

## The brief was wrong about the `groups` shape

The brief's test config is `{"groups": {"arm": ["control", "treatment"]}}`. That mapping
form is one `reference.md` § Expansion modes explicitly refuses: "`groups` is a **list**,
always — one axis is a list of one. Two spellings for one concept is the drift this
project exists to prevent, so there is no mapping shorthand." The real shape is
`[{by: arm, levels: [control, treatment]}]`, which `tests/test_sweep.py` already used at
the `PRODUCT_MODES` residual assertion. I used the list form, and `selector_paths` returns
no paths for the mapping form rather than crashing — that being the shape a user most
plausibly writes.

## It is tested end to end through `expand`, not pinned at the unit level

`groups` still expands to no cells, but a **baseline** can fix a group level today —
§ Expansion modes: a baseline "accepts group levels as well as parameter paths, so
`{arm: control}` designates the control arm". So
`groups + grid: {analysis.method: [...]} + baseline: {arm: control}` expands to two
baseline rows carrying `arm` and two product rows carrying only `analysis.method`: probe
and control in one `expand` call, through real code. Exact lists are asserted, not shapes.
A second control — a grid-only sweep whose axis is *named* `arm` — marks nothing.

**Mutation, both directions.** Marking nothing → the named test fails at index 0.
Marking every path in `values` → it fails at index 0, and the grid-only control was
separately confirmed to report `{arm}` under that mutation, so the control is not a check
that can only pass. `__pycache__` deleted between each; the revert was verified by the
full suite passing, never by `git status`.

## Deliberate boundaries, and the gap they leave

- Group paths are **not** unioned into `swept`. `_keys_for` shortening one more path would
  move existing label assertions, and § How artifacts are organized orders group axes
  before parameter ones — that is task 5's.
- `selectors` is **not** written to `sweep.yaml` (`sweep_document`), nor to `cli.py`'s
  condition metadata or `run_record`. That payload "matches § `sweep.yaml` — the resolved
  plan exactly", so adding a key needs a document change outside this task's scope. Known
  gap; whether the marking should be recorded belongs with task 4/5.
- No reader was changed, per the brief. Until task 4, the field is a marking with no
  consequence, and the field's own docstring says so.

## Concerns

- Only `groups` has a selector shape today, so `selector_paths` iterates a one-element
  tuple and then reads that mode's shape by hand. That is `_swept_paths`' idiom, and the
  docstring says a second selector mode must be read there explicitly — membership in
  `SELECTOR_MODES` alone will not find its paths.
- Nothing yet refuses a `baseline` fixing a group path when no `groups` axis declares it;
  such a path stays unmarked and will reach `resolve_condition_cfg` as a parameter. That is
  a `validate` question (§ Validation already has "Every assignment names an axis"), not
  `expand`'s, and no code in this build reaches it.
