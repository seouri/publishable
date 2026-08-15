# Task 8 report: the weighted interval

**Status:** complete, through fix round 1. `uv run pytest` 1203 passed, 2 xfailed;
`uv run ruff check .` and `uv run mypy` clean. `ruff format .` was not run.

**Commits:**

- `35d1ef8` — *feat: a weighted interval takes its df from Kish's effective size*. The predicate
  promotion and the `_t_critical` extraction ride along, because each changes two call sites and
  neither is a coherent tree on its own.
- `0278926` — *fix: Kish's effective size gates its own weights instead of answering nan*
  (fix round 1).

`uv run pytest` 1203 passed, 2 xfailed after round 1.

## Four brief defects, all found before writing

The brief's Step 3 code is wrong in a way that breaks the brief's own Step 1 tests. Three of the
four were confirmed numerically before any code was written.

**1. The variance denominator narrows the interval, and fails the brief's own boundary test.**
The brief divides the weighted sum of squares by `Σw`. That is the population form. `t_over_units`
divides by `n − 1`, so at equal weights the two constructions do not agree and
`test_equal_weights_reproduce_the_unweighted_interval` — prescribed verbatim by the brief — fails
against the brief's own implementation. Measured: `[1..5]` with unit weights gives
`(1.244, 4.756)` weighted against `(1.037, 4.963)` plain.

The fix is `Σw − Σw²/Σw`, and it is determined rather than chosen. It reduces to `n − 1` at equal
weights, so the boundary holds digit for digit; it is invariant under rescaling every weight, which
matters because survey weights routinely sum to a population size rather than to the row count; and
it errs wide, which is the direction § Weighted samples explicitly argues for. The brief's form errs
narrow — "narrower than the sample supports" is the exact failure the section names.

**2. The headline test's weights make the function return `None`.** `[1.0]*7 + [20.0]` has a Kish
size of 1.791, below the brief's own `effective < 2` guard, so `weighted.high` is an attribute
error on `None`. Changed to `[1.0]*7 + [8.0]` (Kish 3.169). The `20.0` case was not discarded — it
is now `test_an_effective_size_below_two_has_no_interval`, which pins the guard the brief wrote and
never exercised.

**3. The headline test does not kill the brief's own mutation #1.** The widening assertion survives
taking df from `len(values) − 1`: the weighted variance inflates enough on its own that the
weighted interval is still wider than the unweighted one — measured at the values now in the test,
the mutated width is 7.766 against the plain 4.096. It survives replacing
`effective` in *both* the sem and the df, too. So Step 5's first mutation had no test that could
fail. The headline test still earns its keep — it kills the nominal bug, an unweighted interval
wearing a weighted label — but a second test had to carry the df.

That test is `test_the_weighted_interval_is_the_t_interval_at_kishs_effective_size`, and it is
non-circular: the weights are chosen so Kish's size is an exact integer, which lets the expectation
be built from the already-trusted `t_over_units` rather than from a second copy of the formula
under test. `values = [1, 2, 3, 6]`, `weights = [1, 1, 1, 3]`: `Σw = 6`, `Σw² = 12`, so the
effective size is exactly 3; the weighted mean is 4.0 and the weighted variance is
`26 / (6 − 12/6) = 6.5`, so the interval must equal `t_over_units([4 − √6.5, 4, 4 + √6.5])`.

**Why those values discriminate** (the Task 5 symmetry trap): dropping the weights from the
variance gives 6.0 or 4.5, never 6.5; taking df from the row count gives t(3), not t(2); dividing
the sem by √4 rather than √3 moves it again. No two of the three coincide, and one unit carrying
half the weight is genuinely uneven.

**4. The Files list omits `units.py` and `validate.py`**, which the brief's own § First mandates
changing.

## What was built

- **`units.usable_weight`**, promoted from `validate._usable_weight` verbatim, sitting beside
  `is_measurement_numeric` with a docstring naming both readers. `validate` imports it; its two
  call sites and the now-unused `import math` were updated in the same commit.
- **`stats._t_critical(df, confidence)`** — I took the extraction route, not the duplication route,
  and changed both call sites in the one commit. `df` is typed `float`: Kish's size is fractional
  and is passed unrounded.
- **`kish_effective_n`** as the brief specifies, including the `Σw² == 0` → `0.0` guard.
- **`weighted_t_over_units`**, with the corrected denominator and the `effective < 2` guard placed
  *before* the variance, which is also what keeps the denominator away from zero — it vanishes
  exactly when the effective size is 1.

**Two deliberate departures from the brief's signature**, both consequences of `usable_weight`
being the gate:

- `weights` is annotated `Sequence[Any]`, not `Sequence[float]`. A weight is a unit attribute and
  `_from_table` builds those from `csv.DictReader`, so every real weight arrives as `str`. A
  `float` annotation would let the production call site pass the real thing only by lying to mypy —
  trap #1 returning in a form the type checker blesses.
- An unusable weight raises `ContractError` with `E-DATA-WEIGHT-INVALID` rather than returning
  `None` or dropping the unit. `coerce_for_rule` is the precedent and it is exact: gate with the
  shared predicate, then raise under the same identifier `validate` reports. Dropping a unit would
  change `n` silently; `None` would discard the diagnostic.

## Mutation results

Every mutation ran a three-point control — baseline passes, mutant fails, revert passes — with
`__pycache__` deleted between mutate and revert, and every revert verified by re-running the tests
rather than by `git status`.

| Mutation | Result |
|---|---|
| df from `len(values) − 1` instead of Kish's size | `..._at_kishs_effective_size` FAILED. The headline widening test **passed** — brief defect 3 |
| Weights out of the variance, kept in the mean | `..._at_kishs_effective_size` and `..._in_the_variance_and_not_only_in_the_mean` FAILED. The equal-weights test **passed**, which is why the dedicated test exists |
| The brief's `/ Σw` denominator | `..._at_kishs_effective_size` and `test_equal_weights_reproduce_the_unweighted_interval` FAILED |
| `usable_weight` gated on `isinstance` instead of `is_measurement_numeric` | FAILED in **both** files: `test_stats.py` (`..._table_sourced_weight...`, `..._validate_would_refuse...[True]`) and `test_validate.py` (`..._weight_looking_column_warns...`, both parametrisations). The single-authority claim is provided, not stated |

Two controls fired and were worth having. The first mutation run reported "no tests ran" for both
the control and the mutant — two node IDs in one shell variable — and would have read as a clean
result had the baseline not been required to report a pass; re-run under `-k`. The 2b revert's
`assert count == 1` refused to fire because the pattern also matched the weighted-mean line, and
the behaviour check caught the failed revert on the same breath.

## Concerns

1. **`E-DATA-WEIGHT-INVALID` has no run-time registry row.** `reference.md` § Validation carries
   it; § Errors core raises at run time does not, unlike `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`, which
   carries both for exactly this arrangement. Nothing diverges yet — no wiring reaches
   `weighted_t_over_units`, so the raise is unreachable outside its tests — but it starts diverging
   the moment task 9 or task 11 wires the weighted path. Recorded in
   `docs/superpowers/spec-defects.md` — and, because that path is gitignored, as a comment at the
   raise site in `stats.py`, so the owed row is tracked where task 11 will be reading. The row
   belongs with task 11's retirement of `E-DATA-WEIGHT-UNSUPPORTED`, which is the same table.
   **This is the one thing a later task must not drop.**
2. ~~`kish_effective_n` is the CSV trap one layer up~~ — **fixed in round 1, see below.**
3. **The brief's purity claim is no longer literally true.** `stats.py` now imports
   `publishable.units`, not only `errors` and `replication`. The brief asked for purity and for the
   shared predicate, and those pull against each other; the predicate won, on the argument the
   brief itself makes. It is still acyclic — `units` imports only `publishable.errors` — and still
   pure in the sense the module docstring means: no filesystem, no config parsing, no git.
4. **Nothing was wired.** `effective` does not reach `n`, no caller computes a weighted interval,
   and `E-DATA-WEIGHT-UNSUPPORTED` is untouched. Task 6's `counts: dict[str, int]` was not widened
   and nothing here makes widening harder — `kish_effective_n` returns a bare `float` with no
   opinion about which channel carries it.
5. **The `effective < 2` → `None` branch is now pinned but not specified.** § Weighted samples says
   nothing about what a weighting that concentrates a roster onto fewer than two effective units
   should report. The brief chose `None` and I kept it, on the argument that it is the same refusal
   `t_over_units` makes at one row. Whoever wires this should confirm a `None` interval beside a
   real point estimate reports sensibly rather than looking like a bug.


## Fix round 1

Spec ✅. Three items, all closed in `0278926`, one commit.

### `kish_effective_n` now gates its own weights

The coordinator was right that this was worse than I disclosed. I had reported the `TypeError` and
missed that the other four cases answer *silently*. Reproduced, with a control:

| Input | Ungated | Now |
|---|---|---|
| `[1, 1, 1, 1]` (control) | `4.0` | `4.0` |
| `[-1, 1]` | `0.0` | `ContractError` |
| `[nan, 1]` | `nan` | `ContractError` |
| `[inf, 1]` | `nan` | `ContractError` |
| `[0, 0]` | `0.0` | `ContractError` |
| `["1", "3"]` | `TypeError`, no `.code` | `3.0` for `["1","1","1","3"]` |

A plausible-looking number with no error is strictly worse than the traceback, because nothing
downstream can tell it from a real answer, and this value lands in `run.yaml` as `n.effective`.

The gate is **inside** the function, per the ruling: it is public, the guarantee belongs to it, and
a caller that has to remember to pre-validate eventually forgets. It went into a new
`checked_weights`, which `weighted_t_over_units` now shares, so there is one gate rather than two
and no fourth notion of a usable weight can appear — `units.usable_weight` remains the single
authority and `E-DATA-WEIGHT-INVALID` the single identifier.

The `Σw² == 0` guard is kept. It is unreachable through the gate, since no usable weight is zero,
but it is what answers the empty sequence, which is a real call rather than an error — the
docstring now says so.

`test_kish_effective_n_reads_a_table_sourced_column` covers the `str` case specifically, since that
is the one task 9 will actually hit.

### Two Minors

- `test_the_weighted_interval_honours_its_confidence` — the weighted path's `confidence` had no
  test; the existing one only exercises `t_over_units`. Asserts the widening and pins both bounds.
- `inf` added to the bad-weight parametrization, which now matches what the code refuses.

### Round-1 mutations

Each with a three-point control, `__pycache__` cleared between mutate and revert, every revert
verified by re-running the tests.

| Mutation | Result |
|---|---|
| Gate removed from `kish_effective_n` (`checked_weights` → `list`) | 7 FAILED — the `str` test and all six refusal parametrisations. The equal-weights and empty-sequence tests passed, correctly: neither can see the gate |
| `confidence` hardcoded to 0.95 on the weighted path | `..._honours_its_confidence` FAILED; `test_confidence_widens_the_interval` **passed**, which is the gap it was written for |
| `usable_weight` gated on `isinstance` (re-run after the refactor moved the gate) | Still FAILS in **both** files — 4 in `test_stats.py`, 3 in `test_validate.py`. The single-authority claim survives the round-1 refactor |

### Also fixed

The owed-registry-row note had been written as `#`-prefixed lines inside a docstring, where they
read as commented-out code. Rewritten as prose.
