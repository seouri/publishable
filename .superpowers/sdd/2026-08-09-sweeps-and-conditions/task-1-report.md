# Task 1 report — `sweep.py`

## What was built

- `src/publishable/sweep.py`: `Condition` frozen dataclass (`index: int`,
  `label: str | None`, `values: dict[str, Any]`, `is_baseline: bool`) and
  `expand(config: dict) -> list[Condition]`, transcribed from the brief.
  `label_for` is the Task-1 placeholder (last dotted segment), signature
  unchanged for Task 2 to replace the body.
- `tests/test_sweep.py`: the 7 tests from the brief, transcribed verbatim.

Pure module: no imports of `config`, `artifacts`, `runner`, `cli`; no
filesystem access.

## Commands run

```
$ uv run pytest tests/test_sweep.py -v
ModuleNotFoundError: No module named 'publishable.sweep'   (expected failure, Step 2)

$ uv run pytest tests/test_sweep.py -v
7 passed in 0.01s

$ uv run pytest -v
341 passed in 13.69s   (334 pre-existing + 7 new)

$ uv run ruff check .
B905 `zip()` without an explicit `strict=` parameter   (sweep.py:48)
B017 Do not assert blind exception: `Exception`         (test_sweep.py:61)
Found 2 errors.

$ uv run mypy
Success: no issues found in 33 source files
```

## Deviations from the brief's literal code, and why

The brief's code blocks fail `ruff check` as pasted. Both are trivial,
non-semantic fixes, applied to satisfy the task's own verification gate
(`ruff check .` clean) without changing behavior:

1. **`sweep.py`** — `zip(axes, combo)` triggered `B905` (zip without
   `strict=`). Added `strict=True`: `axes` and `combo` are always the same
   length (`combo` comes from `itertools.product` over exactly `len(axes)`
   iterables), so `strict=True` is a no-op at runtime and only adds a
   defensive check.
2. **`tests/test_sweep.py`** — `pytest.raises(Exception)` triggered `B017`
   (blind exception assert) on the frozen-dataclass mutation test. Added
   `# noqa: B017 — frozen dataclass raises FrozenInstanceError`, matching
   the exact precedent already in the codebase at
   `tests/test_units.py:123` for the identical pattern.

No other changes. Both fixes were re-verified: `uv run pytest -v` (341
passed), `uv run ruff check .` (all checks passed), `uv run mypy` (success,
33 source files) — all clean after the fix.

## Semantics double-checked against the brief

- No `sweep` block → `[Condition(0, None, {}, False)]` — flat tree,
  confirmed by `test_no_sweep_block_is_one_unlabelled_condition`.
- A bare baseline (no grid) still gets a label and the tree level, even
  though it's the sole condition — "declared, not count."
- Grid axes use `itertools.product`, which varies the *last* argument
  fastest — matches declaration order without sorting or reordering, per
  `test_the_last_declared_axis_varies_fastest`.
- `expand({"sweep": {"grid": {"a.x": []}}})` returns `[]` — no raise added;
  pinned exactly as instructed, refusal deferred to a later `validate` task
  (`E-SWEEP-AXIS-EMPTY`).
- `Condition` is frozen; mutation raises (tested).
- `sweep.py` does not import `config`, `artifacts`, `runner`, or `cli`, and
  does no filesystem I/O.
- `Condition` and `expand`/`label_for` are not added to
  `src/publishable/__init__.py` — `Condition` stays internal, per the task
  instructions.

## Anything I'm unsure about

- None outstanding. `label_for`'s placeholder body (last dotted segment,
  joined with `__`) is deliberately temporary per the brief and is left
  as given for Task 2 to replace.

## Commit

```
919e128 Expand a declared sweep into ordered conditions
 2 files changed, 118 insertions(+)
 create mode 100644 src/publishable/sweep.py
 create mode 100644 tests/test_sweep.py
```

## Post-review addendum: `Condition.values` immutability

Coordinator review flagged that `Condition.values` was a plain mutable
`dict` inside an otherwise-frozen dataclass — `conds[0].values["x"] = 1`
succeeded silently, since `frozen=True` only stops field rebinding, not
mutation of a mutable field's contents. `Unit.attributes` in `units.py`
hit the identical issue and fixed it with `MappingProxyType(dict(...))` in
`__post_init__`; applied the same pattern here:

- `Condition.values` is now typed `Mapping[str, Any]` (was `dict[str, Any]`).
- `__post_init__` does `object.__setattr__(self, "values", MappingProxyType(dict(self.values)))`
  — copy first, then wrap, so a caller mutating the dict they passed into
  the constructor cannot reach the condition through the back door either.
- Added a module-docstring note: a `baseline` whose values coincide with a
  grid cell produces two conditions with identical `values` (`00_baseline`
  plus the matching grid row), and `expand` deliberately does not dedup —
  the baseline is declared, the grid is mechanical, reconciling them isn't
  `expand`'s job.

New tests in `tests/test_sweep.py`:
- `test_condition_values_are_immutable` — `conds[0].values["x"] = 1` raises
  `TypeError`; reading an existing key still works.
- `test_condition_values_are_copied_not_aliased` — mutating the source dict
  after `Condition` construction does not change the condition's `values`.
- Confirmed (not just assumed) that the existing equality test still
  passes: `expand({}) == [Condition(index=0, label=None, values={},
  is_baseline=False)]` — `MappingProxyType({})` compares equal to `{}`.

Also moved `import pytest` from a local import inside
`test_conditions_are_frozen` to a top-of-file import, now that two more
tests need it.

### Re-verification

```
$ uv run pytest -v
343 passed in 12.67s   (341 previous + 2 new)

$ uv run ruff check .
UP035 Import from `collections.abc` instead: `Mapping`   (sweep.py:17, from `typing`)
Found 1 error.
# fixed: moved `Mapping` import to `from collections.abc import Mapping`
$ uv run ruff check .
All checks passed!

$ uv run mypy
Success: no issues found in 33 source files
```

### Second commit

```
8548f03 Make Condition.values immutable, matching Unit.attributes
 2 files changed, 34 insertions(+), 2 deletions(-)
```
