# Task 2 report: the label grammar

## What was done

Replaced the placeholder `label_for` in `src/publishable/sweep.py` with the real
grammar, exactly per the brief:

- Added `SWEPT_VALUE_PATTERN = r"^[A-Za-z0-9._+-]+$"`.
- Added `render_value(value)`: `true`/`false` for `bool`, `repr()` for `float`
  (shortest round-trip), `str()` otherwise.
- Added `_keys_for(paths)`: for each dotted path, walks suffix depth 1..N and
  picks the shortest suffix that is not equal to, or a dotted-boundary suffix
  of, any *other* swept path — falling back to the full path if no depth
  disambiguates.
- Rewrote `label_for` to look up each value's path in `_keys_for(list(grid))`,
  falling back to the last segment for any path not in `grid` (defensive; not
  exercised since `values` keys are always a subset of `grid`'s keys or the
  baseline dict).

Added the six tests from the brief verbatim to `tests/test_sweep.py`.

## Verification

- `uv run pytest tests/test_sweep.py -v`: 15 passed (9 pre-existing + 6 new).
- `uv run pytest -v`: **349 passed** (343 pre-existing + 6 new), no regressions.
- `uv run ruff check .`: All checks passed.
- `uv run mypy`: Success, no issues found in 33 source files.

## Concern to flag rather than work around

`SWEPT_VALUE_PATTERN` (`^[A-Za-z0-9._+-]+$`) permits `_` (single underscore),
and therefore permits the two-character sequence `__` inside a rendered
value — e.g. a swept string value `"a__b"` renders to `a__b` and matches the
pattern cleanly. But `__` is also the axis separator the grammar splits
labels on. A label like `key=a__b__other=x` is ambiguous to parse back: is
the first axis's value `a` or `a__b`? The brief's own round-trip test
(`test_every_generated_label_body_matches_the_selector_pattern`) only checks
that each value substring matches `SWEPT_VALUE_PATTERN` after splitting on
`__` — it doesn't (and can't) catch this, because the ambiguity is in the
split itself, not in any individual part.

This didn't come up in the required tests (all swept values there are
method names, booleans, or floats — none containing `__`), so I left
`SWEPT_VALUE_PATTERN` and the separator exactly as specified rather than
narrowing the pattern or changing the separator on my own judgment. Flagging
per instructions: a swept value containing a double underscore is a real
selector-ambiguity case, and whether to exclude `_` from
`SWEPT_VALUE_PATTERN`, forbid `__` specifically, or accept the ambiguity (on
the theory that no real config sweeps such values) is a decision for you,
not for `sweep.py` as currently scoped — especially since Task 4 (`validate`)
is where value-shape enforcement is said to live, per the brief's own
comment on `test_an_empty_grid_axis_still_expands_to_nothing_here`.

## Commit

Committed as `src/publishable/sweep.py` + `tests/test_sweep.py`,
message: "Label a condition so a reader can type its name".

## Follow-up: the coordinator ruled on the concern above

The coordinator confirmed the `__`-in-value concern is a genuine specification
contradiction (`SWEPT_VALUE_PATTERN` admits `_`; the label separator is `__`)
and ruled to refuse it: a value may use `_`, but not the two-character
separator sequence.

Added `AXIS_SEPARATOR = "__"` and `check_swept_value(value) -> str | None` to
`src/publishable/sweep.py`. It runs the existing pattern check first, then
separately refuses any rendered value containing `AXIS_SEPARATOR`, with a
message naming the value and explaining that `__` is the axis separator and
that a label is a selector. `label_for` now references `AXIS_SEPARATOR`
instead of the `"__"` literal so the join and the refusal cannot drift apart.

`check_swept_value` is **not yet wired into `validate`** — Task 4's
`_check_sweep` doesn't exist in the tree yet (no `sweep`-shape check exists
in `validate.py` beyond the unimplemented-axis warning at line ~397). The
predicate is added to `sweep.py` now, written for Task 4's `_check_sweep` to
call once it exists, so that implementer inherits the check rather than
duplicating it.

Added three tests to `tests/test_sweep.py`:
`test_a_value_rendering_the_axis_separator_is_refused`,
`test_a_single_underscore_is_still_accepted` (confirms `a_b` alone is not
over-corrected away), and
`test_values_already_refused_by_the_pattern_are_still_refused` (confirms the
new check is additive, not a replacement).

Recorded the conflict, both candidate resolutions, and which one this build
implements in `docs/superpowers/spec-defects.md` under "The swept-value
pattern and the label separator contradict each other on `_`".

Re-verified: `uv run pytest -v` → 352 passed (349 + 3 new); `uv run ruff
check .` → All checks passed; `uv run mypy` → Success, no issues found in 33
source files. Committed as `src/publishable/sweep.py` + `tests/test_sweep.py`
+ `docs/superpowers/spec-defects.md`.
