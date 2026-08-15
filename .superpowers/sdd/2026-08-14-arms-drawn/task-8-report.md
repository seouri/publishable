# Task 8 report: `random` honouring `ratio`, unclustered

## What was built

`units.assignment_for` now has a third branch, `method == "random"` (still gated to `clusters is None` — a `clusters` mapping passed alongside `random` raises `NotImplementedError` naming task 9 rather than silently falling back to an unclustered draw).

The draw:

1. `weights = [ratio[level] for level in levels]` when `assign.<axis>.ratio` is a non-empty dict, else `[1] * len(levels)` — `{}` is equal allocation.
2. `sizes = _apportion(len(roster), weights)` — a new helper, largest-remainder (Hamilton) apportionment: floor each level's exact share, then hand the roster-size-minus-sum-of-floors remainder to the largest fractional parts, ties broken by declared order.
3. `seed = assign_seed_for(block, axis, digest, roster)` (task 6, unchanged) and the whole roster's keys are shuffled once with `random.Random(seed)`.
4. The shuffled list is cut into consecutive slices sized by `sizes`, in `levels`' declared order, and returned as `ArmPlan(levels=..., members=..., seed=seed, strata=())`.

`strata` is always `()` on this path — no balancing is implemented (see gap #1 below).

## Tests written (`tests/test_units.py`)

- `test_a_random_draw_honours_an_unequal_ratio` — 12 units, `ratio: {control: 1, treatment: 2}`, pinned `seed: 7` → sizes 4/8 and exact membership tuples asserted literally.
- `test_a_random_draw_is_a_partition` — same fixture: every declared level's tuple is truthy, the two tuples concatenated have no duplicates, and their union is exactly the roster's key set.
- `test_the_same_seed_draws_the_same_arms` — two calls with `seed: 1` give identical `.members`; the control, `seed: 2`, gives different `.members` (equal ratio, 12 units, so no ratio interaction).
- `test_a_ratio_that_does_not_divide_the_roster_is_reported_not_rounded_away` — 13 units, `ratio: {a: 1, b: 2}` (sum 3 does not divide 13) → sizes 4 and 9 asserted exactly, docstring names which level absorbed the remainder and why (larger fractional part, 0.667 vs 0.333).

Two pre-existing tests had a false premise once `random` stopped raising and were updated rather than left to rot:
- `test_assignment_for_refuses_a_drawn_method_rather_than_reading_a_column` (`tests/test_units.py`) — was parametrized directly over `DRAWN_ASSIGN_METHODS`, which still contains `"random"`. Now parametrized over `[m for m in DRAWN_ASSIGN_METHODS if m != "random"]`, i.e. just `"blocked"`, with the docstring saying why.
- `test_resolved_group_axes_raises_rather_than_reading_a_column_under_a_drawn_method` (`tests/test_cli.py`) — used `method: random` as its "still a hole" example; switched to `method: blocked`, docstring updated.

## Mutation testing (each applied, run, confirmed FAIL, reverted, confirmed PASS; `__pycache__` cleared between apply/revert)

1. **Ignore the ratio** (`weights = [1] * len(levels)` unconditionally): kills `test_a_random_draw_honours_an_unequal_ratio` (4/8 → wrong sizes) and `test_a_ratio_that_does_not_divide_the_roster_is_reported_not_rounded_away` (4/9 → wrong sizes). No other test affected (132 passed, 2 failed).
2. **Ignore the seed** (shuffle with `random.Random(0)` while still recording the real `assign_seed_for(...)` value in `.seed`): kills `test_the_same_seed_draws_the_same_arms` (seed 1 and seed 2 now shuffle identically) **and** `test_a_random_draw_honours_an_unequal_ratio` (its exact-membership assertion was itself pinned to the seed-7 shuffle, so a seed-ignoring bug is a real, correct hit on that test too — not overlap from a weak test). 132 passed, 2 failed; no test outside this pair failed.
3. **Drop the remainder unit** (`_apportion` returns `list(floors)` with no remainder distribution): kills exactly `test_a_ratio_that_does_not_divide_the_roster_is_reported_not_rounded_away` (`b` comes out 8 instead of 9). 133 passed, 1 failed — no other test touched.

Every mutation was killed by at least the test the brief names for it; mutation 2's second kill is a legitimate second sensor (test 1 asserts exact seeded membership per the brief's own instruction), not a fault in test isolation.

## The task-7 review item — every declared level non-empty

Decided: **no floor-of-one guarantee, no new `E-` code.** `_apportion`'s docstring says so explicitly and ties it to the existing, already-recorded gap (`reference.md` § Allocation, `limits.min_units_per_cell`: "declared, typed, and read by nothing in this build") rather than inventing a new promise.

What *is* guaranteed unconditionally: the `zip(levels, sizes, strict=True)` loop that builds `members` walks `levels` itself, so `set(members) == set(levels)` always — every declared level is a key, even when its apportioned size is 0 (an empty tuple, not a missing key). That closes the specific concern task 7's review raised (`build_allocation_document` iterates `plan.members`, not `plan.levels`): coverage of every declared level is guaranteed for a draw the same way `arms_of` guarantees it for `by_attribute`, just not that function's *non-emptiness* half. I did not re-check `artifacts.build_allocation_document` for whether it tolerates an empty tuple for a level (no division, no indexing a first element) — flagging that as a follow-up check for whoever wires the drawn path into artifact writing, since it's outside this task's file list.

`test_a_random_draw_is_a_partition`'s non-empty assertions cannot fail under the fixture used (12 units, ratio 1:2 can't floor either level to 0) — they document the property rather than sense it. The coverage/no-duplicate assertions in the same test are the real sensor for a slicing bug.

## Concerns / gaps for the record (not fixed here)

1. **`stratify_by` is silently ignored under `random`.** `strata=()` regardless of a declared `assign.<axis>.stratify_by`, and no balancing is performed — the draw is a plain shuffle. This is unreachable today only because `validate` still refuses `method: random` outright as `E-DATA-ASSIGN-DRAWN`. Whoever lifts that refusal (task 14, per `DRAWN_ASSIGN_METHODS`'s docstring) must either implement stratified balancing for `random` or make `validate` refuse a non-empty `stratify_by` under `random` explicitly — otherwise lifting the refusal ships a silently-unbalanced draw despite a declared balance requirement. This is the highest-value item in this report.
2. **A zero-sum `ratio` divides by zero.** `validate`'s only check on `ratio` is `set(ratio) == set(levels)` (`E-DATA-ASSIGN-RATIO`); nothing checks the values are positive. `ratio: {a: 0, b: 0}` reaches `_apportion`'s `total = sum(weights)` as `0` and raises `ZeroDivisionError`, not a `ContractError`. Not fixed here — it needs a `validate`-side check and, per this task's instructions, I'm not minting a new `E-` code unasked. Recording it rather than guessing at the right code/message.
3. Did not touch `docs/reference.md` — § Allocation's "`random` and `blocked` are refused in this build" is still literally true at the `validate` layer (this task only changed `units.assignment_for`, which `validate` doesn't yet let `run` reach for `random`), so no doc drift was introduced.

## Files touched

- `src/publishable/units.py` — `_apportion` (new), `assignment_for`'s `random` branch, docstring updates to `assignment_for`, `DRAWN_ASSIGN_METHODS`, and `ArmPlan.strata` to stop claiming `random` still raises / stop implying `strata` gets filled by any draw.
- `tests/test_units.py` — four new tests, one retargeted parametrize.
- `tests/test_cli.py` — one test's fixture method switched from `random` to `blocked` to keep its "a drawn method still raises" premise true.

---

# Task 8, second pass (commit `1a951d9`)

Written by the implementer who took the task over. Everything above stands as
the record of what `067d046` built; this section says what changed and, where
it reverses a decision above, says so.

## The task-7 review item, **reversed**

§ "The task-7 review item" above records "**Decided:** no floor-of-one
guarantee, no new `E-` code." The first half of that is now wrong and is
overturned: **a drawn arm the apportionment leaves empty raises
`E-DATA-ASSIGN-LEVELS`.** The second half survives — no code was minted.

The reasoning that replaces it: `units.arms_of` refuses exactly this for a
*read* assignment, with the reason attached ("or that arm's condition resolves
zero of them"), and `reference.md` § Allocation's sentence is method-agnostic —
"**An arm no unit resolves to is already refused, as `E-DATA-ASSIGN-LEVELS`**"
— sitting in the sentence whose job is to *contrast* that already-refused case
with the thin-but-nonzero cell `limits.min_units_per_cell` does not yet warn
about. The previous pass cited that gap as cover for the empty arm; it is the
opposite, the gap the refusal is contrasted against. Same fault, same words, so
the same code — and reuse leaves both documents true with **zero doc edits**,
where minting would have needed a registry row, a § Validation row, and an
audit of every row an insertion moved.

Where it lives: `assignment_for`, right after `sizes = _apportion(...)`, not
inside `_apportion` — only the caller holds the axis name, the declared ratio,
and the roster size the message names. All empty levels are collected and
joined, `arms_of`'s own shape.

Not added: a `validate`-side check. The fault is roster-dependent, and `units`
raising is the surface for that.

## `stratify_by` under `random` now refuses

Gap #1 above ("the highest-value item in this report") is closed rather than
deferred to whoever lifts the `validate` refusal. `assignment_for` raises
`NotImplementedError` naming task 12 for a **non-empty** `stratify_by`, from the
`clusters` raise's own argument in the same function: do not silently ignore a
declared field. Presence is read structurally (`if block_map.get("stratify_by")`),
`validate`'s convention for this field, so a bare `stratify_by: site` refuses as
well as a list, and the `stratify_by: []` `init` writes still draws.
`ArmPlan.strata` is therefore `()` on every plan **truthfully**: the only
declaration that reaches a plan is one describing no strata.

## The `ratio` value family (`228e2d6`) is tested, and its predicate fixed

The committed implementation was right in shape and short by one case. Extracted
to `validate._usable_ratio_share` with a docstring, and `math.isfinite` added.

- Why not `units.usable_weight`, the house predicate for the neighbouring
  question: it reads through `is_measurement_numeric`, which accepts a numeric
  *string* — it must, because a weight arrives from `csv.DictReader`. A `ratio`
  never comes from a table and `_apportion` **sums** its values, so accepting
  `"1"` would validate clean and raise a bare `TypeError` on `sum`. Said in the
  docstring.
- `.nan` was already caught, but by polarity rather than by design: the old
  check tested `value <= 0` (nan slips through), the new one tests `value > 0`
  (nan does not). Pinned by a test so the polarity cannot flip back.
- `.inf` was **not** caught and is the case finiteness earns: `inf > 0` is
  `True`, and `10 * inf / inf` is `nan`, so an infinite share reaches `int(nan)`
  inside the draw. Found by mutation — deleting `math.isfinite` initially
  survived the suite, which is what added the case.

`reference.md`'s `E-DATA-ASSIGN-RATIO` row and `_check_assign`'s docstring both
now say "not a finite positive number" with `.nan` beside `-1`.

## Minor items

- `test_a_ratio_that_does_not_divide_the_roster...` asserts exact membership
  now, not sizes alone — it is the one roster here whose remainder is
  *distributed*, so it is where a right-sizes-wrong-offsets slicing bug shows.
- `test_a_random_draw_is_a_partition`'s two vacuous non-emptiness assertions are
  gone, with the docstring saying which test owns that half instead.
- The redundant `method == "random" and isinstance(block, Mapping)` guard and
  the two other `isinstance(block, Mapping)` repeats are replaced by one
  `block_map: Mapping[str, Any] = block if isinstance(block, Mapping) else {}`
  bound at the top — mypy keeps its narrowing and no branch re-tests the block.

## Mutation testing (apply → run → confirm FAIL → revert → confirm PASS, `__pycache__` cleared between)

| Mutation | Test | Mutated | Reverted |
|---|---|---|---|
| `_apportion` remainder in reverse order (`key=lambda i: -i`) | `-k apportion` | 1 failed | 3 passed |
| Empty-arm raise removed | `-k apportions_no_unit` | 2 failed | 2 passed |
| `stratify_by` raise removed | `-k stratify` | 2 failed | 3 passed |
| `clusters` raise removed | `-k cluster_by` | 1 failed | 1 passed |
| `math.isfinite` dropped from `_usable_ratio_share` | `-k usable_shares` | 1 failed | 5 passed |
| `_usable_ratio_share` returns `True` always | `-k usable_shares` | 3 failed | 4 passed |
| `isinstance(value, (int, float))` dropped | `-k usable_shares` | 1 failed | 4 passed |
| `ratio` gate back to `isinstance(ratio, dict) and ratio` | `-k not_a_mapping` | 1 failed | 5 passed |

The reverse-order mutation — which previously left all 1534 tests green — is
killed by `test_apportion_hands_the_remainder_to_the_largest_fraction`.
`(10, [1,2,4])` is deliberately **not** a case in it: it coincides with that
mutant, which is the same accident that let the mutant live.

Reverts verified by behaviour (the test re-passing), never by `git status`.

## Verification

`uv run pytest` 1549 passed, 2 xfailed · `uv run ruff check .` clean ·
`uv run mypy` clean. `ruff format` not run.

## Still open

- `blocked`, and `random` beside a declared `cluster_by`, still raise
  `NotImplementedError` (tasks 10 and 9). `validate` still refuses `random`
  outright as `E-DATA-ASSIGN-DRAWN`, so none of the raises above is reachable
  from a `run` yet — they are reachable from `units.assignment_for` directly,
  which is where their tests call them.
- `units.arms_of`'s run-time raise of `E-DATA-ASSIGN-LEVELS` is absent from
  `reference.md` § Errors core raises, and the draw's raise inherits that
  absence. Pre-existing, not introduced here; left alone because inserting a
  row moves every row after it and § Errors core raises' closing paragraph
  locates one by position ("**That last row**").
- `artifacts.build_allocation_document` against a drawn plan is still unchecked
  by anyone (flagged in the first pass and unchanged) — though the empty-arm
  refusal removes the empty-tuple case that flag was mostly about.
- **Task 14 inherits a validate-clean-then-disagree gap.**
  `test_a_well_formed_ratio_reports_nothing_of_its_own` pins that
  `{control: 1, treatment: 2}` reports only `E-DATA-ASSIGN-DRAWN`. Once task 14
  retires that code, `ratio: {a: 1, b: 1000}` over a 10-unit roster validates
  **completely clean** and then raises `E-DATA-ASSIGN-LEVELS` at the draw. The
  check that would close it is roster-dependent — it needs the resolved roster's
  size, not just the declaration — so it belongs beside `E-DATA-ASSIGN-LEVELS`'s
  own roster-resolved check, not in the `ratio` value family, which is
  declaration-only by construction. Out of scope here; named so it is not
  discovered by a user.
- The `assign_seed_for(block, ...)` → `assign_seed_for(block_map, ...)` swap
  does not move any seed: on the `random` path the two are the same object. The
  evidence, not just the argument, is that the seed-pinned membership tuples
  (`u07, u11, u03, u10`; the 13-unit pair) still pass after the swap — they
  would have moved if the hashed input had.
