# Task 6 report: the `assign.seed` derivation

## What was built

`assign_seed_for(block: Mapping[str, Any], axis: str, digest: str, roster: UnitList) -> int`
in `src/publishable/units.py`, placed beside `units_hash` and
`partition_units` (just above `units_hash`'s definition).

- A pinned integer `block["seed"]` is returned literally. The digest is not
  touched at all on that path — `block.get("seed", "auto")` is read first,
  and if it is an `int` (excluding `bool`), the function returns before the
  digest, axis, or roster are used for anything. This mirrors
  `sweep.sample_seed_for`'s own documented property, and is the reason
  `hashes.design_digest` can safely strip `assign.<axis>.seed` per axis: a
  pinned seed does not move a digest it is never mixed with.
- Otherwise: `hashlib.sha256(f"{digest}|assign|{axis}|{units_hash(roster)}")`,
  truncated to 4 bytes big-endian — same construction as `_seed_from` and
  `_sample_seed`, with `|assign|` as the disambiguating tag so an assign
  seed, a fold seed, and a sample seed derived from the same digest never
  collide.

## Where it belongs, and why

Put it in `units.py`, not a new module and not `hashes.py`.

- The repo's settled precedent (per the brief) is "hashes what its own
  module built." `units.py` already builds `units_hash` and already hosts
  `partition_units`/`_seed_from`, which is the same shape of function:
  mix a digest with something the module owns, produce a seed for a
  roster-splitting operation. `assign_seed_for` is one more instance of
  that pattern, not a new category.
- `hashes.py` builds `design_digest`, which this function *consumes* but
  does not build — putting the derivation there would make `hashes.py`
  reach into `units.py`'s `units_hash` instead of the other way around,
  inverting the direction every other module in this repo uses.
- A new module isn't warranted yet: there is no `assign.py` today, and this
  task's job is narrowly the seed, not the draw itself (tasks 8/10/12
  build the arm allocation that consumes this). If a later task
  introduces an `assign` module for the draw logic, `assign_seed_for`
  could move there with it — but speculatively creating that module now,
  for a single small function, would split roster-seed derivations across
  two homes for no present reason. `sweep.py` is the closest counter-example
  (`sample_seed_for` lives with `sweep`'s own concerns, not in `hashes.py`),
  but `sweep.py` already existed as the home of the thing it seeds
  (`sweep.sample`). No analogous home exists yet for `assign`.

## Tests

Four tests added to `tests/test_units.py`, each with the control named in
the brief:

- `test_a_pinned_assign_seed_is_returned_literally` — pins `seed: 42`,
  asserts `== 42` under two different rosters (control: roster changes,
  answer does not).
- `test_the_derived_seed_moves_with_the_roster` — asserts the seed changes
  both when a unit is added **and** when the same 10 units are reversed in
  order (the control named in the brief, exercising `units_hash`'s
  order-sensitivity, which that function's own test already establishes
  independently).
- `test_the_derived_seed_moves_with_the_axis_name` — same roster, same
  digest, two axis names (`arm`, `sex`) draw different seeds.
- `test_the_derived_seed_moves_with_the_digest` — same block, same roster,
  two digests draw different seeds.

## Verification

- `uv run pytest -k "assign_seed or derived_seed"` — 4 passed (0 before
  implementation: import error, confirmed as the "failing" step).
- `uv run pytest` — 1523 passed, 2 xfailed (full suite, unrelated xfails
  pre-existing).
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — no issues found in 40 source files.

### Mutation testing (drop each of the three inputs, in turn)

For each mutation: applied the edit, cleared `__pycache__`, ran the exact
four-test selection (`-k "assign_seed or derived_seed"`), confirmed FAIL for
exactly the named test and PASS for the other three, reverted the edit,
cleared `__pycache__` again, and confirmed all four PASS by re-running (never
by `git status`).

| Dropped input | Payload mutated to | Failing test | Others |
|---|---|---|---|
| digest | `f"|assign|{axis}|{units_hash(roster)}"` | `test_the_derived_seed_moves_with_the_digest` (1065675093 == 1065675093) | 3 passed |
| axis | `f"{digest}|assign|{units_hash(roster)}"` | `test_the_derived_seed_moves_with_the_axis_name` (579532145 == 579532145) | 3 passed |
| roster | `f"{digest}|assign|{axis}"` | `test_the_derived_seed_moves_with_the_roster` (2450620141 == 2450620141) | 3 passed |

Each of the three inputs is load-bearing and each mutation is caught by
exactly the test named for it — no cross-firing, no silent survivor.

## Concerns

None. The brief's requirements were all satisfiable as stated; no
document/code conflict was found. The one judgment call — module
placement — is argued above; `units.py` is the least speculative choice
given no `assign` module exists yet.
