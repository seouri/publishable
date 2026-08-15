# Task 11 report — verify the invariant decision 2 rests on

**Status:** COMPLETE.

**Commit:** `d5f6b6b` (initial), plus a review-response commit — see § Review response below.

**Test summary:** `uv run pytest` → 1765 passed, 2 xfailed (baseline 1752 + 2 xfailed + 13 new tests,
after the review response added 3 more to the initial 10). `uv run mypy` and `uv run ruff check .`
both clean.

## The verification

Read `percentile_over_units` (`src/publishable/stats.py`) and `usable_weight`
(`src/publishable/units.py`) directly rather than accepting the brief's argument on faith.

- **Unweighted branch:** `sum(pool[rng.randrange(n)] for _ in range(n)) / n`, gated by
  `if len(values) < 2: return None` above — so `n >= 2` always when this branch runs, no division
  by zero reachable.
- **Weighted branch:** `_weighted_mean` over a drawn subset, gated by `checked_weights`, which
  reads `units.usable_weight`. Confirmed the guard is `if not math.isfinite(number) or number <= 0:
  return None` (line 552) — a weight of `0`, negative, non-finite, or non-numeric (including `bool`,
  explicitly excluded by `is_measurement_numeric`) is refused with `E-DATA-WEIGHT-INVALID`
  **before any draw**. Σw over a non-empty drawn subset is therefore strictly positive.
- **Stratified branch:** draws `len(group)` rows from each `group` in `ordered`, and every group is
  non-empty by construction (it came from at least one `(value, weight)` pair). No degenerate draw
  reachable there either.

Wrote `tests/test_stats.py::test_a_column_resample_refuses_a_bad_weight_before_any_draw` (parametrized
over `0, 0.0, -1.0, nan, inf, "heavy", None, True`),
`test_a_column_resample_is_never_degenerate_across_adversarial_columns` (zero variance, near-zero
spread, extreme weight ratios, a one-unit stratum, combined strata+weights), and
`test_percentile_over_units_still_returns_a_bare_interval` (the negative pin: decision 2 is that the
return type does NOT become `(Interval, int)`). All ten pass immediately, which is the expected shape
for a verify-and-pin task — a pass on first run is the evidence the decision asked for, not a sign the
test is inert (see the mutation below).

**Mutation (Step 5):** changed `usable_weight`'s guard from `number <= 0` to `number < 0`, admitting a
weight of exactly zero. Re-ran `test_a_column_resample_refuses_a_bad_weight_before_any_draw` — the `0`
and `0.0` parameters FAILED with `ZeroDivisionError: float division by zero` at
`stats.py:167` (inside `_weighted_mean`), confirming the invariant rests on that specific guard and not
on incidental luck. Deleted `__pycache__`, edited the guard back to `number <= 0` in place (never
`git checkout`), re-ran: all 8 weight-refusal parameters pass again.

**Conclusion: no reachable degenerate column draw exists.** The decision holds under the conditions
stated — `values` has length ≥ 2, and any declared weight vector is validated by `checked_weights`
before a draw is taken. `percentile_over_units`'s return type is unchanged.

## Disagreement between brief and code (found, per the standing question for this slice)

The brief's Step 3 docstring text to append read, in present tense: "a column's `resample_draws` is
the requested `n` and is recorded as such by `summarize_step`." Checked against the code
(`c5de085`): `summarize_step`'s recorded-column branch (`out[column] = {...}`, distinct from the
derived-metric branch several lines below it) carries **no `resample_draws` key at all** today —
only `value`, `basis`, `n`, `ci95`, `method`, `correction`. Wiring `statistics.resample` into that
branch, and adding `resample_draws` there, is task 12/14's work; `E-STATS-RESAMPLE-UNSUPPORTED`
still refuses a declared `resample` end to end (confirmed via `grep` in `cli.py`).

Writing the brief's sentence verbatim into `stats.py`'s docstring would have been exactly the failure
mode CLAUDE.md names repeatedly ("a comment or docstring claiming a guarantee the code does not
provide") — a present-tense claim about what `summarize_step` does, when it does not yet do it. I
reworded the appended docstring text to state the invariant conditionally — safe for whenever a later
slice wires column resample into `summarize_step` — rather than asserting current behavior, and
recorded the same distinction in `docs/superpowers/spec-defects.md`'s new entry (its final paragraph)
so the gap between the brief's wording and the code's current state is on the durable record, not just
in this report.

The spec decision itself (record the requested `n`, don't change `percentile_over_units`'s return
type) is unaffected by this — it's a forward-looking ruling about how task 12/14 *should* wire things
when it lands, and that ruling is sound. Only the tense of one sentence needed correcting.

## Review response

The coordinator's review found the invariant as originally stated was **false**, which is exactly
what a verify-and-pin task is for. Findings addressed, in the order given:

**1 — Critical, non-finite inputs.** Confirmed by direct reproduction:
`percentile_over_units([1.0, 2.0, 3.0, float("nan")], seed=1, draws=100)` returns
`Interval(nan, nan)` today, and so does an individually-finite-and-positive weight vector whose
sum overflows (`weights=[1e308]*4`) — `checked_weights` gates each weight alone, not the sum.
Neither `values` nor a weight vector is checked for finiteness anywhere on this path. Per the
review's explicit instruction, **did not change the return type** — confirmed `(Interval, int)`
is not the remedy either, since nothing here treats a `nan`/`inf` draw statistic as a failed draw
to filter, so a survivor count would report `(Interval(nan, nan), n)`, the same false claim with
an extra field. Instead: (a) the `percentile_over_units` docstring now states the finiteness
condition explicitly rather than an unconditional "always defined," and says the gap is real,
reachable, and out of scope; (b) filed the gap as its own `spec-defects.md` entry ("A column
resample is only ever defined given finite inputs, and nothing checks that today"), separate from
the decision-2 entry, naming task 12/14 as the likely owner since that is when column resample
actually gets wired into a config-driven run; (c) added two tests that pin the *current, unfixed*
behavior as a known gap rather than as correct — `test_a_column_resample_over_non_finite_values_is_a_known_unfixed_gap`
and `test_a_column_resample_with_an_overflowing_weight_sum_is_a_known_unfixed_gap` — each says in
its own docstring that it is not asserting correctness. Verified the coupling is real: temporarily
added a finiteness check ahead of `min_honest_draws` inside `percentile_over_units`, reran, and
the `nan`-values gap test FAILED (`assert None is not None`) — proof that fixing the gap without
touching the test would be caught. Deleted `__pycache__`, reverted the check in place (never
`git checkout`), reran: all pass again, full suite still 1765 passed + 2 xfailed.

**2 — Important, the false citation.** The original entry claimed `reference.md` § Statistical
reporting already states the column/derived provenance split. Checked the actual text: it says
`resample_draws` is "recorded beside every derived metric" and never mentions columns. **Chose
the second option the review offered — stopped citing it as already true, and named the amendment
as owed** (to task 12/14, alongside the wiring itself, since the section can't honestly describe a
field no config path produces yet). Corrected in the `spec-defects.md` entry.

**3 — Important, the `None` coherence question.** Worked out and ruled on: `resample_draws` is
`null` whenever `ci95` is `null`, for any of `percentile_over_units`'s three refusal reasons (too
few values, too few draws, or the tasks-9/10 constant-pair refusal), and the requested `n`
otherwise. This repurposes the derived metric's "`null` = never attempted" bucket to also cover
"attempted, but structurally refused before any draw" — a fourth case in truth, collapsed onto
`null` because its observable effect (no interval, no evidence) is identical. Consequence named
explicitly: a column's field is genuinely **two-valued** (`null` or the full requested `n`), not
three-valued like the derived metric's, because nothing on this path can make one draw fail while
others succeed given finite inputs — the derived metric's `0` ("attempted, every draw
individually degenerate") bucket is structurally unreachable for a column. Recorded in
`spec-defects.md` as new content owed to `reference.md`, not forced into the existing three-way
prose.

**4 — Important, "digit for digit."** Reproduced the counterexample:
`percentile_over_units([5.0]*4, seed=1, draws=100)` gives `Interval(5.0, 5.0)` while the same
values with `strata=["a"]*4` give `None` — the docstring's general claim is false for the
constant-value case. Added the qualification "when neither path is itself refused" to the
docstring, named the exact divergence, and added
`test_a_column_resample_refuses_the_constant_one_stratum_case_the_unstratified_path_does_not` to
pin it. Mutated the refusal check (`if all(len(set(group)) <= 1 ...)` → `if False and ...`),
confirmed the new test FAILS (`assert Interval(...) is None` → actual `Interval(5.0, 5.0)`),
deleted `__pycache__`, reverted in place, confirmed PASS again.

**5 — Minor, internalised.** The original adversarial set varied column *shape* (variance, weight
ratios, stratum size) but never value *domain* (`nan`/`inf`). Renamed that test to
`..._of_finite_values` to say so explicitly, and added the two domain-varying tests from finding 1
beside it — CLAUDE.md's own named trap ("varying config shape when the property is about content")
reproduced in a different register, exactly as the review said. Also noted (not separately fixed)
that "today's build still refuses..." is a perishable present-tense claim in the docstring,
matching two existing sites in the same file rather than improving on them — left as is since
correcting the pattern repo-wide is out of this task's scope.

Full suite after all fixes: `uv run pytest` → 1765 passed, 2 xfailed; `uv run mypy` and
`uv run ruff check .` both clean.

## Concerns

The invariant now holds **only given finite inputs** — that condition is stated explicitly in the
docstring and is not, and cannot be, enforced by `percentile_over_units` itself without a scope
change task 11 was not asked to make. The non-finite gap is real, reachable today via direct calls
to `percentile_over_units`, and will become reachable through a full run once task 12/14 wires
`statistics.resample` for columns — unless that wiring adds the finiteness check the gap's
`spec-defects.md` entry proposes. This is the one thing a later task must not silently skip: task
12/14 should read that entry before wiring, not just this one.
