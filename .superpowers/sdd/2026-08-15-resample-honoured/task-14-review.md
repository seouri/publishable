## Task 14 review — a recorded column takes a percentile interval under a declared resample

Reviewed `ce2f2db..556d13d` on `h4a-resample-honoured`.

**Spec compliance: ✅** — the behaviour matches `reference.md` § Statistical reporting and the
slice design: `declared` (not `n`) is the gate in code, the value is unchanged in every branch,
`n.effective`/`n.clusters` survive, `resample_draws` is absent-undeclared / `null`-when-`ci95`-is /
otherwise the requested `n`, and the retry call is correctly left alone.

**Task quality: findings** — 4 Important, 4 Minor. No Critical.

---

### Verified good (by mutation, `__pycache__` cleared each run, reverted in place)

- **Task 1's pin bites and still reaches the changed code.** Emitting `resample_draws`
  unconditionally fails `test_the_undeclared_resample_shape_is_pinned_absent_key`,
  `…_explicit_null`, `test_an_undeclared_resample_leaves_a_column_untouched_end_to_end`, and
  `test_a_recorded_column_takes_a_percentile_interval_under_resample` — four tests, two of them the
  task-1 acceptance pins.
- **The null-under-refused-interval guard is pinned.** `draws if interval else None` → `draws`
  fails `test_a_column_below_two_units_reports_a_null_draw_count_under_resample`.
- **The weighted unclustered draw is pinned properly.** Dropping `weights=column_weights` fails on
  the exact `ci95` match against a direct `percentile_over_units(values, seed=5, draws=2000,
  weights=column_weights)` call. The implementer replaced the brief's bracketing assertion with
  that exact match and was right to: the brief's assertions (weighted value, Kish `n`, "differs
  from unweighted") do not discriminate a dropped weight *in the draw*. Credit.
- **The brief/ruling contradiction was real and correctly resolved.** `spec-defects.md:5058` rules
  verbatim: "`resample_draws` is `null` whenever `ci95` is `null`, for any of the three reasons."
  The brief's Step 1 fourth test asserted `== 2000` for a one-unit column. Implemented per the
  ruling, test rewritten and renamed, defect filed. Correct.
- **The `summary`-step `Estimate` risk is not live.** `summary_values(r.returned)` feeds
  `evaluate_hypotheses(summary=…)` at `cli.py:2231`; it never touches `summarize_step`'s
  `collapsed`. The two paths are disjoint, so deferring the assertion to task 18 is fine.
- **The warning loop is safe.** `used == 0` cannot match `None`; `elif used is not None and used <
  derived_metric_draws` guards the null column. The primary call passes `draws=derived_metric_draws`
  — the same variable the loop compares against — so the comment's "`used == derived_metric_draws`,
  so the `elif` can't fire" is exact, not an overclaim.
- **`report_by` untouched** (call at `:2089` gets no `resample_columns`; task 15 owns it). Level
  blocks' positive presence is pinned in several existing tests (`step_block["by"]["cohort"][…]`),
  and `test_strata_do_not_join_the_correction_family` is a with/without comparison rather than a
  pure absence, so the family-membership leaf is adequately guarded.
- **`paired` and `cohens_d` appear nowhere** in the `src/` or `tests/` diff.
- Tree at `556d13d`: **1776 passed + 2 xfailed**, `ruff check .` clean, `mypy` clean (42 files).

---

### Important

**I1. The `declared` gate is correct in code and undiscriminated by any test.**
Mutating `cli.py:1756` to `resample_columns=(resample_spec["n"] != 2000)` leaves the **full suite
green — 1776 passed, 2 xfailed**. No test in the repo declares `statistics.resample` with exactly
`n: 2000`, which is the only config that separates `declared` from `n != 2000`: task 1's pins run
undeclared (resolves to 2000, mutant False, passes), and every declared test uses `n: 500`. This is
the exact seam `_resolved_resample`'s own docstring says "would silently make that sentence false",
and it is the standing *check that could not fail* shape.

The report's claim that "Task 1's acceptance pin caught the gate mutation directly" is true only of
the presence/`True` mutation, not this one. Verified the fix is one test: with a config declaring
`{"method": "bootstrap", "n": 2000}` on clean code the column reads `percentile_over_units` /
`resample_draws: 2000`; under the mutant the same test fails with `t_over_units`.

**I2. The fourth combination (clustered + weighted) ships unpinned.**
Changing `weights=column_weights` → `weights=None` in the `percentile_over_units_clustered` call
leaves the **full suite green**. Three of the brief's four combinations are pinned
(unclustered/unweighted, clustered/unweighted, unclustered/weighted); the brief required all four
"land together". One test — clusters *and* weights, exact `ci95` against a direct
`percentile_over_units_clustered` call, same standard as I1's sibling.

**I3. `reference.md` now asserts a guarantee the code does not provide.**
The new paragraph says the column's sample is "non-empty … **finite throughout**, so it is always
defined once an interval exists at all", with no hedge. The ruling it derives from
(`spec-defects.md:5043`) says the opposite in its own heading — "**conditional on finite inputs**"
— and adds "**The finiteness condition does not hold unconditionally** — see the separate entry
below." The hedge was lost in transcription into normative text.

Verified live on this build:

```
summarize_step(<40 units, one `pred: nan`>, …, resample_columns=True)["pred"]
  → {'value': nan, 'ci95': [nan, nan], 'method': 'percentile_over_units', 'resample_draws': 2000}
```

Two consequences. (a) That is the precise false claim the earlier entry warned about
("publishing `nan` under a false `resample_draws: n`"), and **task 14 is what makes it reachable
from a real run** — before this commit it was reachable only by calling `percentile_over_units`
directly. (b) That entry's stated resolution assigns the finiteness check to "whichever slice wires
column resample into `summarize_step` (task 12/14)". Task 14 is that slice; it neither did it nor
recorded that it was declining. At minimum the `reference.md` sentence must carry the ruling's own
conditional, and the deferral must be stated where the assignment was made.

**I4. `stratify_by`: the judgment call is right, the option set is not exhausted, and the gap gets
worse with this commit.**
Agreed on the substance — wiring the column path alone would put a stratified
`percentile_over_units` beside an unstratified `percentile_of_derived` in one `aggregated` block
with `method` identical either way, and the record could not tell them apart. Not wiring is the
better of those two.

But the spec-defects entry frames the alternatives as *column-only wiring* vs. *retroactive
validate-time refusal*, and rejects the second because § Weighted samples documents `stratify_by`
with a worked YAML. The option not named is a **run-time warning** — "declared, not honoured on
this build" — which is neither a divergent construction nor a document change.

The sharper point: **task 14 is what makes this half-honoured.** Before it, a declared `resample`
moved nothing on the column path, so `stratify_by` was inert alongside everything else. After it
the declaration visibly moves the interval `t_over_units → percentile_over_units` while the
stratification silently does not. Six of seven non-null `resample` declarations in
`feasibility-llm-growth-studies.md` carry a `stratify_by`. Confirmed by reading the record: nothing
in `run.yaml` implies stratification took effect, and nothing tells the user it didn't. "Nothing
implies it and nothing tells them" does not meet this project's standard.

Not a blocker on task 14 — the gap is filed, cited from two code sites, and argued honestly. But
**H4a should not merge without a user-visible route**, and this should not be read as permission to
carry it silently to task 19.

---

### Minor

**M1. The retry-call comment states a consequence the code does not have.**
`cli.py:1775–1785` says passing `resample_columns=resample_spec["declared"]` at the retry "would
flip a column's interval to a percentile one on the containment path only". Verified false: the
retry call passes no `seed`, and the gate is `resample_columns and seed is not None`, so adding it
changes nothing — the **full suite stays green** under exactly that mutation. The decision is
right; the operative reason is the missing `seed`, not the one written down. This is the
"comment claiming a guarantee the code does not provide" class, inverted.

**M2. Positional locators in normative and defect text.** The new `reference.md` paragraph locates
siblings three times ("the paragraph above contrasts it with", "the `0` bucket above", "the
derived metric's three-valued scheme above"); the spec-defects entries add "the ruling two entries
above" and "the entry above". CLAUDE.md names this class (seven instances, wrong twice). Two of the
five quote their content, which mitigates; "the paragraph above" and "two entries above" do not.

**M3. The `stats.py` docstring contradicts itself in one sentence** — "a mean (or weighted mean)
over a non-empty, **finite** sample, which is always defined" followed by "see spec-defects.md for
the non-finite-input gap this leaves open … **not this docstring's claim**". It is either
conditional on finiteness or it isn't. Same fix as I3.

**M4. Two of seam 2's three `null` paths are unexercised for a column.** Structurally they are all
covered by the single `draws if interval else None` expression, so this is completeness rather than
risk: the honest-draw floor is unreachable end-to-end (`E-STATS-RESAMPLE-N` refuses `n < 80` at
validate) and untested at unit level, and the constant-pair refusal is unreachable at all while
`strata` is unwired (I4). Worth a one-line note in the report rather than a test.

---

### Method

Mutations run where the behaviour lives, `__pycache__` cleared between runs, every revert done by
editing in place (never `git checkout`) and confirmed by behaviour. Mutations run: `n != 2000` gate;
unconditional `resample_draws`; `draws` in place of `draws if interval else None`; dropped
`weights=` in the unclustered percentile call; dropped `weights=` in the clustered one;
`resample_columns` added to the retry call. Final tree at `556d13d` re-verified green
(1776 + 2 xfailed), `ruff check` and `mypy` clean; only `progress.md` is modified, which is the
dispatcher's. `ruff format --check` drift is pre-existing and out of scope.
