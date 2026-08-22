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

---

## Fix round 1

Both verdicts were PASS with one Major and three Minors; all four are closed below. Full unfiltered
suite re-run after the fixes, and again after each of the three prescribed mutations and their
reverts: **2855 passed, 1 skipped, 2 xfailed** (2854 prior + 1 new arm for Minor 1). All four gates
clean (`ruff check .`, `ruff format --check .`, `mypy` — 52 files, `pytest`).

### Major 1 — the resolver retirement claim was false; corrected to name three real retirements and leave the resolver surface to its own payload

Verified the reviewer's measurement independently before touching anything: `grep -rn
'coerce_scalars' src/units.py` returns nothing, `_from_resolver` (`units.py:438`) projects
`attributes={a: unit.attributes[a] …}` with no coercion, and
`_decode_parquet(_encode_parquet([{"unit": "u1", "site": np.str_("north"), "v": 1.0}]))` returns
`[{'unit': 'u1', 'site': 'north', 'v': 1.0}]` — a resolver-yielded `np.str_` attribute writes
cleanly today and wrote cleanly before this task. It was never refused, so "used to be refused" is
false under any reading; it does not now coerce either, since nothing calls `coerce_scalars` on a
roster attribute value until a later task's coercion lands.

**Deleted the false clause rather than rewording it** (`docs/reference.md` § Steps and artifacts,
the paragraph naming the mechanism and its exceptions). The sentence now names exactly three
retirements — `io.record`/a step's return/`aggregate`/a derived metric all moving from
`E-STEP-RETURN-TYPE` to a coerced value (verified by mutation (i) below, which fails the arms
covering all four call sites), the apparatus fact retirement, and the `Estimate.n` retirement
(Minor 1) — and closes with an explicit sentence that a resolver-yielded attribute value retires
nothing: nothing coerces it today, it already wrote cleanly uncoerced before and after this
commit, and coercing it belongs to whichever later task builds that call site. No task or plan
task number is cited inside `reference.md` itself, consistent with this repo's citation-by-section
convention — the carry-forward is named in this report instead, below.

### Minor 1 — `Estimate.n` stated as a third retirement, and pinned by a new arm

`_coerce_estimate` calls `_coerce_one` on `n`, and `n` is held to no numeric rule
(`_is_number` is never applied to it) — so a `str`-subclass `n` does not move to a narrower code
the way `value`/`ci95` do; it simply stops being refused. Verified by running against the
pre-task code (mutation (i) applied): `Estimate(value=0.5, n=np.str_("612 pairs"))` raised
`E-STEP-RETURN-TYPE`; unmutated it returns the string `'612 pairs'`.

Added `test_an_estimates_n_retires_the_refusal_a_str_subclass_used_to_draw` in
`tests/test_coercion.py`, asserting `type(got.n) is str` and `got.n == "612 pairs"`. Named as the
third retirement in the corrected `reference.md` sentence (Major 1's fix).

### Minor 2 — the module docstring's paraphrase updated to match the edited `reference.md` paragraph

`src/publishable/coercion.py`'s module docstring said "which is why `__len__` is the refusal
test" as an unqualified general statement — now false, since `np.str_` has `__len__` and is
coerced rather than refused. Rewrote the sentence to say the guard is the refusal test "for
everything with a length" and added one sentence naming `np.str_` as the one carve-out from that
guard rather than a counterexample to it, pointing to `_coerce_one`'s own comments for which
ground each of `np.str_`/`np.bytes_` rests on. Verified by reading the result against
`reference.md:1238`'s corrected paragraph — the two now agree, where before this fix only the
document had been updated in-commit and the paraphrase had not (the exact drift shape `CLAUDE.md`
§ Habits warns about: a comment/docstring left behind when its source moves).

### Minor 3 — the ordering constraint's enforcement scope stated where a reader meets it, and the remaining hole named for task 6

Added a comment directly after the `str`-by-inheritance branch in `_coerce_one`, stating plainly
that the branch's placement here is what closes the window correction 6 named for the *shared
function*, and that the mutation pin (i)/(ii) proves only that — it proves nothing about
`units.py`, which does not call this function yet. Named the remaining gap as the coercion call
site's own job "once one exists," rather than claiming it closed. This is prose stating scope, not
a new guard — no additional pin was invented for a surface that does not exist yet, per this
task's own file list.

### Carry-forwards named explicitly, as requested

- **To task 6** (roster attribute coercion, Decision 6): the ordering constraint from plan
  correction 6 is enforced today only at the shared `coerce_scalars`/`_coerce_one` function
  (mutations (i)/(ii), 6 tests each after this fix round). Nothing pins the resolver surface
  itself — `grep -rn 'np.str_' tests/` still returns hits only in `tests/test_coercion.py` and
  `tests/test_apparatus.py`. Task 6's own Fixture R is what must close that hole, and
  `reference.md`'s corrected sentence (Major 1) now makes it load-bearing rather than
  informational, since the document asserts the "no retirement here" property and Fixture R is
  what the property depends on holding.
- **To task 12** (filings): the reviewer found that `Estimate.method` is exempt from the shared
  scalar rule — `_coerce_estimate` returns `method=value.method` uncoerced, guarded only by a
  truthiness check — and that `docs/superpowers/spec-defects.md:1914`'s RESOLVED note ("the
  exemption also had to coerce the `Estimate`'s own fields") is therefore a **stale closed
  claim**: true of `value`, `ci95`, and `n`, and false of `method`. Verified independently by
  reading `_coerce_estimate`'s return statement and running
  `coerce_scalars({"d": Estimate(value=0.5, ci95=[0.1, 0.9], method=np.str_("bootstrap"))}, "s",
  scope="summary")["d"].method` — still `np.str_`, and `yaml.safe_dump` on it raises
  `RepresenterError`. This is pre-existing, not created or widened by task 10, and is out of this
  task's file list (`coercion.py`'s `_coerce_estimate` fields beyond `value`/`ci95`/`n` were never
  task 10's surface). Not fixed here; routed to task 12 by name, which owns "file what H5a leaves
  open," alongside the already-noted half-stale `np.str_`/`np.bytes_` OPEN row at
  `spec-defects.md:1923`.

### Mutations re-run after the fix round, against the full unfiltered suite, reverted by editing back and diffed byte-identical against a saved pre-mutation copy

**(i) Remove the branch.** FAIL — **6** of 9+1 new tests failed (2849 passed / 6 failed / 2855
total): the same 5 as fix round 0 (3 direct coercion tests, 2 `_coerce_estimate` value/ci95 tests,
1 apparatus test) **plus** the new `Estimate.n` test — the failure text for the new arm is
`ContractError: step04_agreement gave 'd.n' a str_; values must be a scalar …`, i.e. the guard
this branch exists to bypass. Property-preserving arms (`np.bytes_`, plain `bytes`, both array
controls) are unaffected, as before.

**(ii) Move the branch after the `__len__` guard.** FAIL — the identical 6 tests fail, with the
identical failure text, confirming placement (not presence) is still the whole of the fix after
this round's edits.

**(iii) Replace `str.__str__(value)` with `str(value)`.** FAIL — exactly **1** test fails (the
enum arm, `'Color.RED' != 'red'`); the new `Estimate.n` arm and the `np.str_` arm both still pass,
because `str()` and `str.__str__()` agree on `np.str_` and on a plain, non-overriding `str` value
— only a `str` subclass whose own `__str__` disagrees (the enum) discriminates the two
constructors.

All three reverted by copying the saved pre-mutation file back; `diff` against the same saved copy
confirmed byte-identical after each revert; full suite re-run green (2855/1/2) after the final
revert.

**No count of zero disagreements is reported here** — two concerns were raised in the original
report and both checked out (attack 8a/8b in the review); this fix round names four findings, all
closed or explicitly routed, and no fifth was found beyond what the review already named.
