# Tasks 13–15 report

**Status:** All three tasks complete and committed.

**Commits:**
- Task 13 — `61d3e35` — `validate: retire E-DATA-WEIGHT-CONTRAST — a weighted contrast is computed`
- Task 14 — `0f15c3f` — `docs: no claim left saying a contrast is unweighted, and every H4b filing re-ownered`
- Task 15 — `8ec3e2f` — `docs: H4b-1's dated count — three to six with no core-side blocker, three executable`

**Test summary:** `uv run pytest` → **2159 passed, 1 skipped, 2 xfailed** after task 13 (net −1 from
the pre-task baseline of 2160: two old tests replaced 1:1 by two new `validate` tests, two old tests
deleted outright, one new end-to-end test added — 2160 − 2 + 1 = 2159). Unchanged after tasks 14 and
15 (neither adds a test). `ruff check`, `ruff format --check` (80 files), and `mypy` (45 files) all
clean after every task.

**Measured executability figures:** measured 2026-08-17 against commit
`0f15c3f904e8ddc34d5533158e3f7478f28af977` (HEAD at the start of task 15, before its own commit), by
running each of the nine configs' `data`/`statistics` blocks through `validate_config` in a throwaway
probe (scaffolded project + a real installed resolver-plugin distribution registering
`patient_trajectory` against a 60-unit synthetic roster; deleted after the measurement, nothing
tracked). Result: all nine validate with **zero errors** (each also reports the pre-existing synthetic-
roster artifact `W-DATA-CLUSTER-UNDECLARED`). The no-remaining-core-side-blocker count goes **three →
six**: E1, E2, E5 unchanged; C1, C2, C3 newly, since `E-DATA-WEIGHT-CONTRAST` — the last core-side
refusal they carried — is retired. **The executable count stays at three**: E3, E4, E6 and now also C1,
C2, C3 all still depend on `io.reuse_from`, unbuilt and unowned, invisible to `validate` because it's a
step-level call. Can-fail control proven both ways: setting `data.units.holdout.frac` to `0` on an
otherwise-clean block produces `E-DATA-HOLDOUT-FRAC`, and reverting it restores the zero-error result.
Recorded as its own dated subsection in `docs/feasibility-llm-growth-studies.md` § Executability on
this build, appended after the H7b Part B entry — no earlier dated subsection retro-edited.

## Mutations, exact text and outcome

**Task 13, mutation 1** — `src/publishable/cli.py`, `command_run`'s two `weights=weights,` →
`weights=None,` (the `_compute_vs_baseline`/`_compute_declared_contrasts` call sites). Ran
`test_a_weighted_run_publishes_a_weighted_delta_end_to_end` → **FAIL**, on `entry["method"] ==
"weighted_paired_percentile_over_units"` (actual: `paired_percentile_over_units`) — `weighted_by` and
`n_paired_effective` assertions never even reached. Reverted by editing back; re-ran → PASS.

**Task 13, mutation 2** — same two call sites, `strata=resample_strata,` → `strata=None,`. Ran the same
test → **PASS** (does not discriminate) — confirmed by reading the test body first: it asserts no
forced bound, only the record shape. Per the brief's own permission, left as a stated blind spot rather
than forcing a fixture: building a discriminating end-to-end fixture would require `_METHOD_VARYING_STEP`'s
per-unit differences to fall into two point masses aligned with the stratify-by attribute, which its
existing per-unit formula (`i + shift + extra`) does not produce for the `band` attribute in the
roster shape `run_a_project` supports. `test_a_contrasts_column_draw_honours_resample_stratify_by`
(direct call) already pins the honouring itself; what stays unpinned is only `command_run`'s threading
of `strata` specifically into a *weighted* contrast (its threading into an *unweighted* one is already
pinned by `test_a_declared_stratify_by_reaches_a_contrasts_interval_through_run`). Reverted; re-ran →
still PASS (as expected, since nothing was mutated at that point).

**Task 13, mutation 3** — `src/publishable/validate.py`, restored the deleted `E-DATA-WEIGHT-CONTRAST`
guard verbatim (comment-stripped) right after `units_here = _units_declaration(...)`. Ran
`test_a_weighted_generated_comparison_validates_clean` and
`test_a_weighted_declared_contrast_validates_clean` → both **FAIL** on `codes(path) == set()` (actual:
`{"E-DATA-WEIGHT-CONTRAST"}`). Reverted by editing back; re-ran → both PASS.

**Task 14, mutation** — reinserted the deleted § Validation row *Weighted deltas aren't computed*
verbatim into `docs/reference.md`. Swept for it with sweep 1 (`no contrast construction\|contrast
construction in this build`) → **matched**, confirming the sweep can fail. Reverted; re-swept → no
match.

**Task 15, mutation** — changed the new table's C1 row from `*(none)*`/**Yes** to
`` `E-DATA-WEIGHT-CONTRAST` ``/No. Re-ran the probe for C1 alone → real result `errors: []`,
contradicting the mutated table entry. Reverted; diffed clean against the pre-mutation file.

All four reverts were done by editing the file back (never `git checkout --`) and verified by
re-running the relevant test/sweep/probe, never by `git status` alone.

## Disagreements between the brief/spec and the code

1. **Task 13's own prescribed test edit for
   `test_a_weighted_baseline_that_generates_no_comparison_stays_legal`** said to delete the "crossed"
   control and check whether the remaining assertion still says something — it does (a bare-baseline
   weighted config validating clean is a distinct shape from the already-covered "no sweep at all"
   case), so the test survives, matching the brief's own conditional expectation.
2. **`test_an_unweighted_comparison_is_untouched`'s prescribed strengthening to `codes(path) ==
   set()` is wrong as written.** Its fixture (`sampling_weight` at values 2.0/3.0 over 2 units, no
   `weight_by` declared) trips `W-DATA-WEIGHT-UNDECLARED` regardless of this slice — a real,
   pre-existing warning unrelated to the retirement. Fixed to `codes(path) == {"W-DATA-WEIGHT-UNDECLARED"}`,
   which is the accurate stronger claim the brief was reaching for.
3. **Several docstrings/comments beyond the five-tests-plus-two-comment-blocks the brief enumerated
   still cited `E-DATA-WEIGHT-CONTRAST` after task 13's own code changes**, which the brief's own
   verification grep (must be empty across `src/ docs/reference.md tests/`) would have caught had it
   been run to completion: `tests/test_cli.py`'s `_weighted_contrast_block` docstring,
   `test_the_three_comparison_functions_accept_weights_and_strata`'s docstring (which also asserted a
   now-false claim — that the `resample_columns=False` branch's interval stays unweighted even under a
   passed `weights`, when task 9/10 already wired `weighted_paired_t_over_units` into exactly that
   branch), `test_the_sibling_refusal_rows_state_their_own_reading` (whose own assertions referenced the
   retired code literally), and a stale docstring in `tests/test_validate.py`'s section-header comment.
   All fixed inline as part of task 13 to satisfy its own stated exit grep, since leaving them would
   have shipped exactly the "misreading a temporary refusal as permanent" trap `CLAUDE.md` names.
4. **Task 15's brief didn't specify a probe methodology**, only "the same way the 2026-08-17 entry
   did." Reconstructing it required building a throwaway resolver plugin (real installed
   `.dist-info`/`entry_points.txt`, not an in-process `@register_resolver` call, which `E-RESOLVER-UNKNOWN`
   proved insufficient) and a substituted `sweep`/`contrasts` stand-in for E2, C1, C2, C3 exactly mirroring
   the Part B entry's own described substitution — not otherwise written down anywhere reusable.
5. **`docs/superpowers/spec-defects.md`'s "column resample only defined given finite inputs" entry**
   was owned to bare "H4b" before this pass; re-owned to **H4b-2** with a note that the weighted paired
   constructions this slice built (`weighted_paired_t_over_units`, the weighted closure in
   `paired_percentile_of_derived`) already gate through `checked_weights`/`usable_weight`, so the
   unchecked-finiteness gap does not reach them — confirmed by reading `stats.py`, not assumed.

## Files touched

- `src/publishable/validate.py` — the retirement (task 13)
- `src/publishable/cli.py` — mutated and reverted only (task 13 mutations), no net change
- `docs/reference.md` — § Errors row and § Validation row deleted (task 13)
- `tests/test_validate.py`, `tests/test_cli.py` — five-plus test edits, new end-to-end test, stale
  docstring sweep (tasks 13–14)
- `docs/superpowers/spec-defects.md` — re-ownering (task 14)
- `docs/feasibility-llm-growth-studies.md` — three prose citations updated, one new dated subsection
  (task 15)
