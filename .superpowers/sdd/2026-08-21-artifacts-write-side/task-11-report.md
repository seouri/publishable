# Task 11 report — Fixture W, Fixture E, Fixture B's cross-spelling arm, and the whole-branch mutation re-run

## Status

Done. `tests/test_artifacts.py` gained 7 tests (Fixture W: 3, Fixture B cross-spelling: 1, Fixture E: 3).
Baseline before this task: **2884 passed, 1 skipped, 2 xfailed.** After: **2891 passed, 1 skipped, 2
xfailed** — delta **+7**, matching the new tests exactly (no test was edited in place, so the delta is
the full count of additions).

## Fixture W's round trip, measured per format before writing any assertion

**`.parquet`**: decodes to the input rows *as coerced* (`coerce_scalars`) — a NumPy scalar unwrapped to
its Python counterpart, everything else unchanged — **except** the `int`-beside-`float` arm, which
`_check_column_types` + pyarrow's own table construction promote to `float` for every value in the
column. Measured directly (`_decode_parquet(_encode_parquet(...))`) before writing the fixture:
`np.float64(1.5)` beside `2.5` → `[{'v': 1.5}, {'v': 2.5}]` both `float`; `np.str_('a')` beside `'b'` →
both `str`; `np.bool_(True)` beside `False` → both `bool`; `1` beside `2.5` → `[1.0, 2.5]` both `float`
(the promotion).

**`.csv`**: every cell decodes to `str(coerced_value)`, with **no promotion at all** — `_encode_csv`
never calls `_check_column_types`. Measured: `1` beside `2.5` → `['1', '2.5']` (not `['1.0', '2.5']`),
confirming correction 8 independently of correction 2 — the `.csv`/`.parquet` disagreement on this arm
has two separate causes (the `str()` rule, and the absence of cross-row unification), not one.

Fixture W is built as two tests (`.parquet`: one for the four non-promoting arms plus one for the
promoting fifth arm, so the promotion assertion — `isinstance` over decoded rows, per the brief — has
its own test; `.csv`: one test covering all five arms under the single `str(coerced)` rule).

## Fixture E, and a finding beyond the brief's own wording

Empty row list: writes an empty table, raises nothing, both formats — confirmed.

All-`None` column: **`.parquet` round-trips as `None`** (confirmed) but **`.csv` round-trips as an
empty string `''`, never `None` and never `str(None) == 'None'`.** This is `csv.DictWriter`'s own
special-casing of `None` (writes `''`), which is a *third* distinct `.csv` behaviour beyond correction
2's `str()` rule and correction 8's "no cross-row unification" — found by measuring rather than by
trusting the design's own Fixture E wording (*"round-trips as `None` in every row. Both formats"*),
which is false of `.csv`. Asserted on the measured behaviour (`{"v": ""}`), with the discrepancy stated
in the test's docstring and left for task 12 to correct in the design/plan text — not edited here, since
retro-editing the development record is not this task's job (`CLAUDE.md` § Checking consistency).

## Fixture B's cross-spelling arm

Built and measured byte-identical for both formats, with a docstring stating plainly that this is true
by construction after coercion and pins nothing controller requirement 2 needs — that pin is task 13's
arms A/B1/B2, cited by name.

## The whole-branch mutation re-run

Every mutation below was applied to a real copy of the file (never a proxy/helper body), run against
the **full, unfiltered `uv run pytest`**, read, and reverted by restoring the saved original and
`diff`-confirming byte-identity — never `git checkout --`. All 24 plan-listed mutations plus the design's
"emptying `_check_column_types`' body" (named blind, distinct from task 9 mutation (iii), and not run by
any single task) were re-run.

| # | Task.mut | Mutation | Result | Failures (read, not estimated) |
|---|---|---|---|---|
| 1 | 2 | `measurements.parquet` write merges roster attributes like `units.parquet` does | FAIL | 1: `test_h5a_task2_measurements_parquet_carries_no_declared_attribute` |
| 2 | 5(i)-unit | Drop `"unit"` from `RESERVED_COLUMNS` | FAIL | 3: the `[unit]` arms of `test_a_reserved_column_name_is_refused_with_a_decoy_on_each_side`, `test_a_resolver_yielding_a_reserved_column_attribute_is_refused`, `test_a_reserved_column_name_is_reported_at_validate_with_decoys_on_each_side` |
| 3 | 5(i)-measurement | Drop `"measurement"` | FAIL | 3: the identical three tests' `[measurement]` arms |
| 4 | 5(i)-by | Drop `"by"` | FAIL | 5: the three `[by]` arms **plus** `test_a_glob_source_reports_a_reserved_column_name` and `test_a_reserved_column_name_meets_the_same_refusal_at_run` — `by` alone reaches two more arms than `unit`/`measurement` do |
| 5 | 5(ii) | Point the attribute check at `UNIT_FIELDS` alone (all 3 call sites) | FAIL | 11: every `RESERVED_COLUMNS`-based arm across the three tests × three names, plus the glob and run-parity tests; the `paths`/`UNIT_FIELDS` arm stays green in all eleven, confirmed by its absence from the failure list |
| 6 | 5(iii) | Merge codes: `E-UNITS-ATTR-RESERVED` for a reserved column too | FAIL | 11: identical list to #5, now failing on the **code** assertion rather than on "validates clean" |
| 7 | 5(iv) | Point `finalize`'s `key != "unit"` at `RESERVED_COLUMNS` | FAIL | 2: `test_a_plain_recorded_by_column_survives_into_units_parquet`, `test_a_measured_by_column_survives_the_collapse_into_units_parquet` — both on the column's absence from the file |
| 8 | 6(i) | Remove the coercion from `resolve_units` | FAIL | 3: `test_arm_o1_a_structural_resolved_attribute_pays_for_nothing_before_it_refuses`, `test_a_resolver_yielding_a_structural_attribute_value_is_refused`, `test_a_resolver_yielding_a_numpy_scalar_attribute_coerces_to_exact_python_float` — see "Task 6 mutation (i), in its full shape" below; this is **not** the shape the brief's own sentence describes |
| 9 | 6(ii) | Coercion refuses `np.float64` instead of coercing it | FAIL | 2: `test_arm_o2_the_positive_control_for_the_ordering_pin_completes_and_coerces`, `test_a_resolver_yielding_a_numpy_scalar_attribute_coerces_to_exact_python_float` |
| 10 | 6(iii) | Move the coercion above the uniqueness loop | FAIL | 1: `test_the_coercion_runs_after_the_uniqueness_check` (reports `E-RESOLVER-YIELD` where `E-UNITS-KEY-DUPLICATE` was expected) |
| 11 | 7 | Plain branch's `measurement` guard → substring/prefix test | FAIL | 1: `test_fixture_m_a_plural_measurements_column_still_writes` (the plural `measurements` column now refuses) |
| 12 | 8 | Delete `_finalize_columns`' dedupe (**named blind** in the design) | FAIL | 1: `test_fixture_d_finalize_columns_is_deduped_by_name` — **not actually blind**: the list assertion catches it, confirming the design's own claim that a file-bytes assertion could not |
| 13 | 9(i) | Delete the coercion call from `_encode_parquet` | FAIL | 3: `test_h5a_fixture_w_parquet_round_trip_per_arm` (this task's own Fixture W), `test_h5a_step7_local_pin_parquet_coerces_numpy_float64_beside_float` (task 9's own local pin), `test_h5a_fixture_n_a_non_mapping_row_refuses_with_the_documented_code` (collateral — the non-mapping guard is fused into the same helper) |
| 14 | 9(ii) | Delete the coercion call from `_encode_csv` only | FAIL | 3: `test_h5a_arm_e2_csv_refuses_a_structural_or_bytes_cell`, `test_h5a_fixture_s_csv_refuses_a_structural_cell_on_either_side_of_the_row_set`, `test_h5a_fixture_n_a_non_mapping_row_refuses_with_the_documented_code`; **all `.parquet` arms (E1, the local pin, Fixture W) stayed green** — confirmed by their absence, proving the two call sites are independent |
| 15 | 9(iii) | `_check_column_types`' normalization `float if actual in (int, float) else actual` → `actual` | FAIL | 4: `test_a_measured_only_unit_is_completed_not_failed`, `test_a_different_unit_may_be_plain_recorded_alongside_a_measured_one`, `test_a_mixed_int_and_float_column_promotes_to_float_deliberately`, and this task's own `test_h5a_fixture_w_parquet_int_beside_float_promotes` |
| 16 | 9(iv) | Delete the `except ContractError` wrapper in `io.write` | FAIL | 2: `test_h5a_arm_e2_csv_refuses_a_structural_or_bytes_cell`, `test_h5a_fixture_s_csv_refuses_a_structural_cell_on_either_side_of_the_row_set` — both on the artifact-name-in-message assertion specifically |
| 17 | 9(v) | Widen the wrapper to the whole body below `path()` (except → `PublishableError`) | FAIL | **4**, exactly reproducing task 9's own corrected count (originally mis-reported as 1, corrected in review `8bc0395`): the step-2 control, `test_an_unregistered_extension_takes_bytes_or_str_verbatim`, `test_write_of_an_unwritable_object_leaves_nothing_behind`, `test_h5a_fixture_n_a_non_mapping_row_refuses_with_the_documented_code`. (Note: bundling `self.path(name)` itself inside the widened `try` — a plausible but different reading of "whole body" — produces **7** failures, three more from `path()`'s own containment/existence `ArtifactError`s being re-coded; I built and ran that variant too and reverted it, since task 9's shipped code keeps `path()` outside the `try`, matching the 4-failure shape rather than the 7-failure one.) |
| 18 | 10(i) | Remove the `str`-by-inheritance branch | FAIL | 9: `test_an_np_str_fact_value_resolves_instead_of_being_refused`, `test_h5a_fixture_w_parquet_round_trip_per_arm`, `test_h5a_fixture_w_csv_round_trip_compares_to_str_of_coerced`, `test_a_numpy_str_coerces_to_exactly_str`, `test_a_str_enum_member_coerces_to_its_declared_value_not_its_repr`, `test_an_estimate_value_that_is_a_str_subclass_now_raises_the_more_precise_code`, `test_an_estimate_ci95_bound_that_is_a_str_subclass_now_raises_the_more_precise_code`, `test_an_estimates_n_retires_the_refusal_a_str_subclass_used_to_draw`, `test_a_resolver_yielding_a_numpy_scalar_attribute_coerces_to_exact_python_float` (this last one only because Fixture R's own fixture yields an `np.str_` `tag` attribute alongside the `np.float64` `score` under test, per task 6's own design) |
| 19 | 10(ii) | Move the branch after the `__len__` guard | FAIL | 9: identical set to #18 — the guard now refuses `np.str_` (it has `__len__`) before the moved branch can run |
| 20 | 10(iii) | Replace `str.__str__(value)` with `str(value)` | FAIL | 1: `test_a_str_enum_member_coerces_to_its_declared_value_not_its_repr` (`'Color.RED'` instead of `'red'`) |
| 21 | 13(i) | `_encode_parquet`'s column-collection loop: `for key in row` → `for key in sorted(row)` | FAIL | 3: `test_h5a_arm_b2_the_parquet_golden_sha256_is_a_tripwire`, `test_h5a_arm_a_a_real_runs_units_parquet_column_order_values_and_types`, **and** `test_h5a_task2_measurements_parquet_carries_no_declared_attribute` — a third, collateral failure beyond the two the design names, because task 2's own fixture also asserts column order. `test_h5a_arm_b1_the_csv_golden_bytes_never_move_in_this_slice` stayed green (confirmed absent), as the design predicts for a fixture whose row happens not to be alphabetical-sensitive at the `.csv` level (unaffected — the mutation is `.parquet`-only) |
| 22 | 13(ii) | Wrap every value in `float()` before building the table | FAIL | **375 failed, 48 errors** — far beyond the design's stated "arm A's type assertion fails for the str and bool columns": `float()` on any `str` cell (the `unit` key column alone guarantees this on every real run) raises `ValueError` inside `_encode_parquet`, crashing essentially every test that writes a real `units.parquet`. Confirmed arm A and arm B2 are both among the 375 (`test_h5a_arm_a_a_real_runs_units_parquet_column_order_values_and_types`, `test_h5a_arm_b2_the_parquet_golden_sha256_is_a_tripwire`), so the design's own claim is not wrong, only far narrower than the measured blast radius |
| 23 | 13(iii) | `_encode_csv`'s `lineterminator="\n"` → `"\r\n"` | FAIL | 1: `test_h5a_arm_b1_the_csv_golden_bytes_never_move_in_this_slice` |
| 24 | 13(iv) | Change one worked-example literal by one digit, `docs/design-principles.md` | FAIL | 1, and **adapted from the design's own wording**: `design-principles.md` carries **no interval literal at all** (grepped `0.581`/`0.488`/etc. against it: zero hits, confirming batch 1's own finding), only three hash lines (`8e21…`, `3d8a…`, `6b1f…`). Changed `8e21…` → `8e22…`; `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text[DESIGN_PRINCIPLES]` failed and `[README]`/`[REFERENCE]` stayed green (confirmed by their absence) |
| 25 | design, "blind" | Empty `_check_column_types`' entire body (distinct from #15 — the whole function, not just the normalization line) | FAIL | 3: `test_a_bool_and_int_column_clash_raises_rather_than_coercing`, `test_a_str_and_int_column_clash_raises_rather_than_coercing`, `test_h5a_arm_c_the_two_shipped_type_clashes_through_a_real_io_write` — **not actually blind**: this task's own Fixture W (NumPy cases) stays green exactly as the design predicts, but task 13's arm C and the two pre-existing direct-call tests catch it. This is the discriminating replacement the brief asks for; no new fixture was needed because one already existed and I grepped for it rather than assuming |

Every "FAIL" above was read from the actual pytest failure-list text, never inferred from a docstring's
claim about what should fail. Every revert was verified by `diff` against a saved copy, never by
`git status` or `git checkout --`.

### Task 6's mutation (i), in its full shape — measured on disk, not asserted from the brief's sentence

The brief's own text predicted: *"the run now executes and raises `ContractError` inside `finalize`."*
**That is not what happens.** With task 9 landed, `.parquet` keeps its structural-cell capability
(the second controller ruling), so `finalize`'s write of `units.parquet` **does not raise at all** — the
structural `tags: [1, 2]` attribute round-trips into the file exactly as a legal value would.

Reproduced with `--basetemp` to keep the run directory past the test: `main(["run", ...])` returns `0`
(not `EXIT_WRONG`); a full `run_*` directory exists under `results/`, with `manifest/`, `environment/`,
and five `seed*/step01_summarize_units/` directories, one per seed repeat; `run.yaml`'s `status` is
`completed`; and `units.parquet` in every one of those five directories decodes (via `_decode_parquet`)
to rows including `{'unit': 'p1', 'tags': [1, 2], 'present': True}` — the structural attribute published
verbatim, with no diagnostic anywhere in the run.

So the mutant's actual end state is **not** "every execution paid for, the record lost" (a mid-run
crash) — it is **every execution paid for, and a structural attribute value silently reaches the
published inference base**, at exit 0, which is arguably closer to the *original* defect Decision 6 was
built to close (§ Where units come from's past-tense claim: *"a resolver-yielded list attribute wrote a
list column into the published inference base"*) than to a late crash. Task 9's own capability change
(honoring the second controller ruling for `.parquet`) is what moved this mutation's failure mode from
"crashes late" to "never refuses at all." This is worth carrying forward rather than silently correcting
the brief's sentence: it is a live example of a decision (Decision 6's coercion) whose *justifying
scenario* changed shape after a later, unrelated decision (the second controller ruling) shipped, without
anyone having to notice unless they ran the mutation and read the disk.

## What I grepped, per the standing rule against reporting zero disagreements

- Grepped `RESERVED_FIELDS` and `RESERVED_COLUMNS` across `src/`, `tests/`, `docs/` before treating
  task 5's constant as fully migrated — confirms task 5's own sweep claim, not re-litigated here.
- Grepped `float if actual in (int, float)` and `_check_column_types` call sites (`grep -n
  "_check_column_types" src/publishable/artifacts.py`) — exactly one caller (`_encode_parquet`), matching
  correction 4's claim.
- Grepped `PublishableError`'s subclass tree in `src/publishable/errors.py` before building mutation
  9(v), to confirm `ArtifactExistsError` is a genuine `ArtifactError`/`PublishableError` descendant (so
  widening the `except` to the shared base is what makes the mutation expressible, per the design).
- Grepped `0.581|0.488|0.661|...` (the full `_H5A_ARM_D_LITERALS` tuple) against
  `docs/design-principles.md` before mutation 24, getting zero hits — confirms batch 1's finding rather
  than assuming it, and is why the mutation is adapted to a hash literal instead of an interval bound.
- Grepped `_YIELDS_TEN_WITH_A_STRUCTURAL_ATTRIBUTE` and `_YIELDS_A_NUMPY_SCALAR_ATTRIBUTE` in
  `tests/test_cli.py`/`tests/test_units.py` before writing the "task 6(i)'s full shape" section, so the
  attribute shapes described above are read from the fixtures actually installed, not assumed.

## Arms without an authorized editor

Arm D (`test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text`) and arm E's `.parquet` half
(`test_h5a_arm_e1_parquet_keeps_a_structural_or_bytes_cell_intact`) were never mutated by any of the 25
runs above, and stayed green through every one of them except mutation 24 (arm D's `[DESIGN_PRINCIPLES]`
arm only, which is the mutation's own intended target — not a finding). **Neither arm fired as an
unintended finding at any point.** Arms A, B1, B2, C were likewise not edited; the plan's own mutations
touch them only as intended catches, listed above.

## Gates

- `uv run ruff check .` — all checks passed.
- `uv run ruff format --check .` — 93 files already formatted.
- `uv run mypy` — success, no issues, 52 source files.
- `uv run pytest` — **2891 passed, 1 skipped, 2 xfailed** (baseline before this task: 2884 passed, 1
  skipped, 2 xfailed). Delta: **+7**, matching the 7 new tests added (Fixture W ×3, Fixture B's
  cross-spelling ×1, Fixture E ×3) with no test edited in place.

## Concerns

- The brief's own prediction for task 6 mutation (i)'s "full shape" does not match the measured disk
  state — see the dedicated section above. Not a defect in any shipped code; a discrepancy between a
  brief's prose (itself dispatched before the interaction with task 9's later-shipped `.parquet`
  capability was traced through) and what actually happens, now recorded so nobody re-derives it from
  the sentence again.
- `docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md`'s own Fixture E wording (*"a column
  whose every value is `None` round-trips as `None` in every row. Both formats"*) is false of `.csv`,
  measured directly. Not corrected in the design document itself (out of scope for this task and for the
  development record's own rule against retro-editing a spec), but stated in the new test's docstring and
  flagged here for task 12, which has not yet landed on this branch, to pick up.
- Mutation 13(ii)'s blast radius (375 failed, 48 errors) is far larger than the two arms the design names
  for it. Not a code defect — every one of those 375 failures is a real run correctly refusing to
  silently corrupt a `str` cell into a crash rather than a diagnostic — but worth carrying so a future
  reader does not read "arm A and arm B2 catch it" as the complete picture.
