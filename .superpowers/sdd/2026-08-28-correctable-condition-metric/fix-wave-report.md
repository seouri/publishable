# Fix wave report — G2 whole-branch review, six findings

All six fixed on `main`. Four commands clean; the F5 mutation is proved in both arms below.

## Per finding

**F1 — `reference.md`, the `fdr_bh` contradiction.** Resolved as a **prior condition**, not a third
exception. `correction._level_for` returns `None` for `fdr_bh`, so *no* member of *any* kind carries
a corrected bound under BH; that is a property of the method, never of the constant form. Three
passages changed: § What a hypothesis is tested against now promises the bound under `holm` or
`bonferroni` and names BH separately ("not a third case, because it is not about this form at all");
§ Pre-registration's verdict paragraph gains the same clause; the "Which corrected interval a bound
test uses" paragraph states that BH is not among the two standing exceptions because it withholds an
interval from every member equally. § Statistical reporting's four-reason list was already true and
is untouched. Checked against `experimental-designs.md`, which says the same thing from the other end.

**F2 — Decision 1's row 4.** Conclusion right, stated cause false: a derived metric is resampled
whenever a `compute` callable and a seed exist, declared `statistics.resample` or not, so it has a
percentile interval and is row 3. What reaches the no-interval state is a resample that produced no
usable interval (all-degenerate draws, or a count below the floor). Corrected in the two live homes
the brief named (`spec-defects.md`, `hypotheses.py`) **and in a third it did not**: `cli.py`'s
condition-member loop comment, whose copy of the false premise wraps across two lines and so survives
a `grep -F`. The design spec and the plan are untouched; the correction is appended to `progress.md`
naming exactly what it replaces.

**F3 — feasibility finding #2.** Corrected to name the template's condition-scoped `auroc` (the one
`growth_label`'s `aggregate` derives) as the metric that could carry `compare: {to: constant}`, and
to state that `step03_compare.auroc_count_only` — which E2's `h1` names today, with no `compare`
block — *is* the `summary`-step `Estimate`. Now agrees with the dated § Executability entry, which
was left alone.

**F4 — `pools_by_key` deleted.** Declaration (with its comment) and the single write both removed;
`grep -rn pools_by_key src tests` is empty. The `report_by` pop's comment now reads "carried into a
per-(condition, step) cache nothing would ever read", naming the shape without naming a dead symbol.

**F5 — the `declaration_index` offset and the co-family case, pinned.** New test
`test_a_comparison_and_a_condition_metric_in_one_family_rank_by_declaration_order` in
`tests/test_cli.py`, on a new `_CO_FAMILY_STEP` fixture (baseline records `i`, the swept arm `2i`, so
the paired differences are bit-identical to the baseline's own column).

*Why the obvious test could not have worked.* `declaration_index` is the third element of
`rank_family`'s key, so it decides nothing unless the evidence ratios tie — and a tie alone is still
not enough, because `sorted` is stable and `hypotheses.evaluate` builds `family_members_` in the
hypotheses' **declaration order**. So the fixture forces an exact tie (same `delta`, same raw
interval, same floats) *and* declares the constant hypothesis first. Correct indices (comparison 0,
condition member 1) put the comparison at rank 1 (α/2, tighter interval); the collided pair (both 0)
falls back to list order and puts the condition member there. The arms swap which hypothesis reads
α/2 and which reads α, and both bounds are computed from `stats.t_over_units` rather than pinned.

**F6 — `spec-defects.md`'s stale "Why open".** Deleted rather than rewritten, per CLAUDE.md. Its one
surviving true half — the "no slice follows, so this is what the project ships with" formula the repo
requires of an *unassigned* entry — moved into the residual-case paragraph, scoped to the
weighted+clustered combination, with a one-line note saying the old paragraph was deleted and why.

## Verification

- `uv run pytest`: `3545 passed, 1 skipped, 2 xfailed in 543.19s (0:09:03)` — one above the 3544
  baseline, which is the F5 pin. `uv run ruff check .`: `All checks passed!`. `uv run ruff format
  --check .`: `101 files already formatted`. `uv run mypy`: `Success: no issues found in 56 source
  files`.
- F5 mutation, both arms, run through the real test:
  - `declaration_index=i` (mutated): `FAILED tests/test_cli.py::test_a_comparison_and_a_condition_metric_in_one_family_rank_by_declaration_order`
    / `1 failed in 1.26s`, on
    `Obtained 15.761212085024908 / Expected 15.190838094452271` for element 0 of
    `spearman_beats_baseline`'s `ci95_corrected` — the comparison member reading α instead of α/2,
    exactly the swap predicted.
  - restored from a pre-mutation `cp` backup and re-verified **by behaviour**: `1 passed in 1.06s`.
- Mechanical `*.md` pass over the four documents plus the two edited non-normative files: no new
  broken link, anchor, table row, trailing space, tab, en dash or invisible unicode introduced by
  this wave (checked against the diff, not only the tree).
- T1's bit-stability oracle golden literal untouched and green.
