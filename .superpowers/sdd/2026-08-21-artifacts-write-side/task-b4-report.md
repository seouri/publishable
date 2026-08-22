# H5a task 10 — report

Commit: (recorded below after commit).

Test summary: full suite green at **2854 passed, 1 skipped, 2 xfailed** — the stated baseline of
**2845 passed, 1 skipped, 2 xfailed** plus 9 new tests (8 in `tests/test_coercion.py`, 1 in
`tests/test_apparatus.py`), all passing. All four gates clean: `ruff check .`, `ruff format
--check .`, `mypy` (52 source files), `pytest`.

## What changed

**`src/publishable/coercion.py` — one branch in `_coerce_one`**, placed after the exact-type test
(`type(value) in _SCALARS`) and before the `__len__` guard:

```python
if isinstance(value, str):
    return str.__str__(value)
```

**`docs/reference.md` § Steps and artifacts** — the mechanism paragraph ("A value that is a scalar
in every sense but its type is coerced, and only that") gains a sentence for the new clause,
naming both retirements and the `_SCALARS` ground for each half. No other section touched — task 9
owns "One rule, all three surfaces."

## Why `np.str_` coerces and `np.bytes_` does not, in terms of `_SCALARS`

`str` **is** one of the four types `_SCALARS = (bool, int, float, str)` closes over; `bytes` is
**not**. `np.str_` is a genuine `str` subclass — `isinstance(np.str_("a"), str)` is `True` and
`type(np.str_("a"))` is not — so before this task the only thing wrong with it was its type not
being exactly `str`, the identical situation `np.float64` is in (handled by the `item()` unwrap a
few lines down). Both `np.str_` and `np.bytes_` have `__len__`, so both used to reach the
structural guard and be refused as if they were arrays. The new branch runs before that guard and
catches only `isinstance(value, str)`; `np.bytes_` still falls through to the `__len__` guard and
is refused there, on the same ground plain `bytes` is refused — `bytes` was never in `_SCALARS`,
so admitting `np.bytes_` by its NumPy spelling while refusing plain `bytes` would be exactly the
divergence this module's one rule exists to prevent. The `__len__` guard is no longer part of the
answer for `np.str_`, but it is still the *whole* answer for `np.bytes_`.

`str` only, not "any `_SCALARS` type by inheritance": measured (Fixture C, and confirmed by
reading `_coerce_one`) — `np.int64` is not an `int` subclass and `np.bool_` is not a `bool`
subclass, and neither has `__len__`, so neither would ever reach a branch keyed off `__len__`-first
placement; both are already handled by the `item()` unwrap. A branch admitting all four types by
inheritance would be three parts unreachable — `str` is the only one of the four for which
"subclass with `__len__`" is a real, reachable case.

## `str.__str__`, confirmed, and what `str()` would have corrupted

Confirmed in the code (`return str.__str__(value)`) and pinned by mutation (iii) below. `str()` on
a `str` subclass calls that subclass's own `__str__` override when one exists. For
`class Color(str, Enum): RED = "red"`, `str(Color.RED)` is `'Color.RED'` under Python 3.11+ (Enum's
`__str__` formats as `ClassName.MEMBER`), which would silently replace the value `'red'` the enum
actually declares with a different string. `str.__str__(value)` calls the base `str` type's own
`__str__` directly, bypassing any subclass override, and returns the underlying character data —
`'red'` for `Color.RED`, and `'a'` for `np.str_('a')` (where the two constructors happen to agree,
which is why the `np.str_` arm cannot discriminate between them and the enum arm is what does).

## The two retirements, stated

1. **`apparatus.check_facts`** (`src/publishable/apparatus.py:193`, which catches
   `coerce_scalars`'s `ContractError` and re-codes it to `E-APPARATUS-FACT-TYPE`): an `np.str_`
   apparatus fact value used to be refused there and now resolves and is recorded. Pinned by
   `test_an_np_str_fact_value_resolves_instead_of_being_refused` in `tests/test_apparatus.py`,
   asserting the fact resolves to exactly `str`. `E-APPARATUS-FACT-TYPE`'s § Errors row in
   `docs/reference.md` reads "a fact value outside the closed scalar set `coercion` already
   enforces" — it derives its scope from `coercion.py` rather than enumerating types, so it needs
   no edit; confirmed by reading the row, not assumed.
2. **`_coerce_estimate`** (`src/publishable/coercion.py`, the `Estimate.value` and each `ci95`
   bound): a `str`-subclass value used to raise `E-STEP-RETURN-TYPE` directly from `_coerce_one`
   (reached the `__len__` guard before this task, since a `str` subclass has `__len__`); it now
   coerces to plain `str` and then fails `_is_number`, raising the more precise
   `E-STEP-ESTIMATE-VALUE` (for `value`) or `E-STEP-ESTIMATE-CI95` (for a `ci95` bound) instead —
   refused both before and after, only the code moves. Pinned by
   `test_an_estimate_value_that_is_a_str_subclass_now_raises_the_more_precise_code` and
   `test_an_estimate_ci95_bound_that_is_a_str_subclass_now_raises_the_more_precise_code`. Both
   codes' § Errors rows already read "whose `ci95` is not two numbers … or whose `value` is not a
   number" — derived scope, no edit needed; confirmed by reading, not assumed.

## Every `coerce_scalars` caller, and what changes for each

Enumerated by reading `src/`, confirmed with `grep -rn 'coerce_scalars' src/` (7 call sites across
5 modules — matches the brief's list with no extra site found):

- **`runner.py:785`** (a step's `run` return) — an `np.str_` value, or any `str`-subclass value
  (e.g. a `str`-Enum), now coerces instead of raising `E-STEP-RETURN-TYPE`. This is the point of
  the widening.
- **`apparatus.py:193`** (`check_facts`) — the first retirement, above.
- **`cli.py:812, 2922, 2974`** (a template's `aggregate` return, a derived metric, a null-test
  draw) — same widening as `runner.py`: an `np.str_`/`str`-subclass value coerces rather than
  refuses.
- **`artifacts.py:668, 691`** (`io.record`, both the `measurement=` branch and the plain branch)
  — same widening.
- **`coercion.py`'s own `_coerce_estimate`** (called from `coerce_scalars` for an `Estimate`'s
  `value` and each `ci95` bound, reachable from `runner.py` and `io.record` at `summary` scope) —
  the second retirement, above: code moves from `E-STEP-RETURN-TYPE` to
  `E-STEP-ESTIMATE-VALUE`/`E-STEP-ESTIMATE-CI95`, the shape unchanged.

No caller needed its own code change; the widening is entirely in the one shared function, which
is the point of `coercion.py` existing as "the one scalar rule, shared by every surface."

## Mutations run, against the full unfiltered suite each time

Reverted by editing the file back after each; verified by re-running (never by `git status`).
Byte-identical revert confirmed with `diff` against a saved copy before the first mutation.

**(i) Remove the branch entirely.**
Result: **FAIL** — exactly 5 of the 9 new tests failed (the 3 direct `np.str_`/enum-coercion tests
in `test_coercion.py`, the 2 `_coerce_estimate` retirement tests, and the 1 apparatus retirement
test in `test_apparatus.py`); the other 4 new tests (both `np.bytes_`/`bytes` refusal tests and the
two array positive controls) still passed, since they exercise the unchanged `__len__` guard.
Full suite: 2849 passed, 5 failed (2854 total, matching baseline + 9). Failure text:
`AssertionError: assert 'E-STEP-RETURN-TYPE' == 'E-STEP-ESTIMATE-VALUE'` (and the `np.str_`/enum
arms raised `ContractError` where they were expected to return a value) — the assertion that
failed is exactly the one asserting the new behaviour; nothing else moved.
**A property-preserving arm**: any test not exercising a `str`-by-inheritance value (e.g.
`test_a_numpy_bytes_is_still_refused`, `test_a_numpy_array_of_floats_still_raises`) is unaffected
by this mutation, because it never reaches the removed branch.

**(ii) Move the branch after the `__len__` guard.**
Result: **FAIL** — the identical 5 tests failed, with the identical failure text (`np.str_` has
`__len__`, so it now hits the guard and raises before ever reaching the moved branch). This
confirms placement, not presence, is the whole of the fix — a mutation one line off from removal
tests the same property removal does, because `np.str_` and the enum both have `__len__` and are
caught by the guard before reaching the branch either way.
**A property-preserving arm**: none of the 4 non-`str`-by-inheritance tests move, for the same
reason as (i).

**(iii) Replace `str.__str__(value)` with `str(value)`.**
Result: **FAIL** — exactly 1 test failed:
`test_a_str_enum_member_coerces_to_its_declared_value_not_its_repr`, with
`AssertionError: assert 'Color.RED' == 'red'`. `test_a_numpy_str_coerces_to_exactly_str` (the
`np.str_` arm) still **passed**, because `str(np.str_("a"))` and `str.__str__(np.str_("a"))` agree
— `np.str_` does not override `__str__` to do anything but return its own characters, so this
mutation and the fix agree on that arm and disagree only on the enum arm, which is why the enum
arm exists in Fixture C at all (design Decision 7's own point).
**A property-preserving arm**: `test_a_numpy_str_coerces_to_exactly_str`, `test_a_numpy_bytes_is_
still_refused`, `test_plain_bytes_is_refused_with_the_same_code`, and both array controls — none
touches a `str` subclass whose own `__str__` disagrees with `str.__str__`.

All three mutations reverted by editing the file back (verified byte-identical against the saved
pre-mutation copy with `diff`); full suite re-run green at 2854/1/2 after each revert, and once
more after the final `noqa` fix below.

## Fixture C — every literal, computed

- `np.str_('a')` coerces to exactly `str` with value `'a'`: asserted `type(...) is str` (not
  `isinstance`, since `np.str_` passes `isinstance(..., str)` regardless of the fix) and
  `== 'a'`. Computed by running `coerce_scalars`, not hand-copied.
- `np.bytes_(b'a')` and plain `b'a'` both raise `E-STEP-RETURN-TYPE`: measured — both are
  `hasattr(..., '__len__')`, `bytes` is not in `_SCALARS`, so both reach `_refuse` unchanged by
  this task's branch.
- A `str`-Enum member (`class Color(str, Enum): RED = "red"`) coerces to `'red'`, not
  `'Color.RED'`: measured directly (`str(Color.RED)` prints `'Color.RED'` under this repo's
  Python; `str.__str__(Color.RED)` prints `'red'`) — this is why the fix calls `str.__str__`.
- `np.array([1.0, 2.0])` still raises `E-STEP-RETURN-TYPE` — the sized-array positive control,
  unchanged behaviour.
- `np.array(1.0)` still raises `E-STEP-RETURN-TYPE` — measured that `hasattr(np.array(1.0),
  '__len__')` is `True` even though `len(np.array(1.0))` itself raises `TypeError`, because
  `ndarray` always carries the `__len__` method regardless of shape; this 0-d array reaches the
  `__len__` guard the same as a sized one and never reaches the `item()` unwrap a true scalar
  would. Without this arm, the sized-array control alone would not rule out "0-d arrays are
  special-cased," which they are not.

## Other

`ruff check .` initially flagged `UP042` (three `class Color(str, Enum)` definitions — "inherit
from `enum.StrEnum` instead"). Not applied: `StrEnum.__str__` returns the value directly rather
than the mixin's `ClassName.MEMBER` formatting, which would silence exactly the corruption Fixture
C exists to demonstrate. Suppressed with `# noqa: UP042` and a one-line reason at each of the three
sites, following this repo's existing `noqa`-with-reason convention (`test_apparatus.py`,
`test_units.py`, `test_sweep.py`'s `# noqa: B017` comments).

I did not touch `docs/superpowers/spec-defects.md`. Its `np.str_`/`np.bytes_` OPEN row (owner "H5
Artifacts") is now half-stale — the `np.str_` half of its claim no longer holds — but striking or
splitting it is task 12's named job in the plan's task decomposition, not this task's file list.
Noting it here so task 12's author does not have to re-discover it.

## Concerns

None found that block this task. The one thing worth a reviewer's attention: this task's branch
widens what every one of the 7 `coerce_scalars` call sites accepts, and I verified all 7 by
reading `src/` first and confirming with grep second, per the enumeration above — no eighth site
was found.
