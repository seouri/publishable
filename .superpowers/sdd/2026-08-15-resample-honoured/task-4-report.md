## Task 4 report

**Status:** done.

**Commits:**
- `60e7aab` feat: E-STATS-RESAMPLE-METHOD and the 80-draw floor, before anything honours n
- `28c257e` fix: guard resample.method by type, matching n's non-fatal-leaf pattern (post-advisor correction)

**Tests:** `uv run pytest` — 1702 passed, 2 xfailed (baseline 1694 + 2 xfailed; 8 new tests added). `uv run ruff check .` clean. `uv run mypy` clean. Both mutations from Step 5 (`n < floor` → `n < 1`, and `floor = min_honest_draws()` → `floor = 81`) confirmed FAIL then reverted in place. An additional mutation on the `method` isinstance guard (removing `isinstance(method, str) and`) confirmed FAIL then reverted in place.

**Disagreements with the brief, found and fixed:**

1. **The brief's own `method` guard was wrong** — `if method is not None and (not isinstance(method, str) or method not in RESAMPLE_METHODS)` double-reports a wrong-typed `method` (e.g. `method: 5`) under both `E-CONFIG-TYPE` (envelope) and `E-STATS-RESAMPLE-METHOD` (this check), because `5 not in RESAMPLE_METHODS` is `True` for an int. This is inconsistent with the `n` branch two lines below it, which explicitly skips a wrong-typed value "because `E-CONFIG-TYPE` already reported it." Fixed to `if method is not None and isinstance(method, str) and method not in RESAMPLE_METHODS`, dropped the now-dead `shown` formatting, and rewrote the `method: 5` test to assert `E-STATS-RESAMPLE-METHOD` is **absent** (paired with `E-CONFIG-TYPE` and `E-STATS-RESAMPLE-UNSUPPORTED` present, so it isn't an absence-only control). Verified this test fails when the guard is removed.

2. **Two docstring sentences overclaimed a guarantee the code doesn't provide** — "`statistics.resample`, once it is honored rather than refused" (it is not honored at this commit; `E-STATS-RESAMPLE-UNSUPPORTED` still fires wholesale) and "this reads values rather than re-testing types" (false once isinstance guards were added deliberately). Rewrote the docstring to say the block is still refused wholesale by `_check_unimplemented`, and that this check reports shape faults on the block's own terms.

3. **The brief's `_RESAMPLE_UNITS` fixture never resolves a roster.** `index.csv` (from `write_config`) has only a `patient_id` column; `attributes: ["cohort"]` names a column the file does not have, so `resolve_units` raises `E-UNITS-ATTR-MISSING` and `_check_units` returns `roster=None`. Every test in this task's file — task 4's own and, by inheritance, whatever tasks 5/8 build on the same fixture — runs with `roster is None`. Harmless for task 4 (this check never reads `roster`), **not harmless for tasks 5 and 8**, whose declared-attribute check and cluster count need a resolved roster to exercise their real logic; against this fixture as given, both would validate against `None` and their assertions could pass vacuously. Flagging this now since it's their fixture to fix (e.g. add a `cohort` column to `index.csv`, or use a different attributes list).

**Interface delivered, unchanged from the brief:** `_check_resample(doc, roster, c) -> None`, called immediately after `_check_sweep(doc, template, c, fold_basis=basis)` and before `_check_contrasts(doc, c, roster)` in `validate_config`. `RESAMPLE_METHODS = ("bootstrap",)` module-level tuple. Both codes registered in `docs/reference.md` § Errors `validate` reports (alphabetically after `E-STATS-REPORTBY-UNKNOWN`) and the § Validation row added beside *Clusters enough to resample*. No count-phrase near either table needed updating — grepped both tables' surrounding prose in `reference.md` for row-count phrasing and found none.

**Concerns for downstream tasks:** see point 3 above — `_RESAMPLE_UNITS`'s `cohort` attribute does not exist in the fixture's `index.csv`, so `roster` is `None` under it. Tasks 5 and 8 should check this before trusting their own tests.

---

**Coordinator review response (commit `5a61576`):** spec ✅, 1 Important + 5 Minor. Addressed 1–5; left 6 to task 12 per coordinator's routing.

1. **Important — the call-site comment claimed dependencies the placement doesn't create.** `roster` was already available three calls earlier (`_check_fold_stratify_by` reads it too), and `_check_sweep` returns `None`/stores nothing on `doc`, so it hands no comparison family forward for task 6 to read. Rewrote the comment: placement buys grouping with the other `statistics.*` checks and finding order, not roster or family availability, and a later check needing the family must recompute it locally.

2. **Minor — `test_a_resample_n_at_the_floor_is_accepted` was absence-only.** Deleting the `_check_resample` call site left it green because the only other code available, `E-STATS-RESAMPLE-UNSUPPORTED`, fires from `_check_unimplemented` regardless of whether `_check_resample` runs — confirmed by mutating the call site out and watching my first attempted fix (pairing with `-UNSUPPORTED`) stay green. Rewrote the test to pair the `n: 80` acceptance with the `n: 79` refusal in the same test body, the same shape the enum test already used. Mutating the call site out now fails this test.

3. **Minor — the `not isinstance(n, bool)` branch was untested.** Added `test_a_resample_n_of_bool_type_is_a_type_fault_not_a_floor_violation` (`n: true`, asserts `E-CONFIG-TYPE` present and `E-STATS-RESAMPLE-N` absent). Mutation (dropping the `not isinstance(n, bool)` clause) confirmed FAIL, reverted in place.

4. **Minor — `method: null`/absent acceptance was pinned by nothing.** Added `test_resample_method_null_or_absent_takes_the_documented_default`, both spellings. Mutation (`if method not in RESAMPLE_METHODS:`, dropping all guards) confirmed FAIL, reverted in place.

5. **Minor — docstring overclaim, narrowed.** "the same division `_check_report_by` keeps with the envelope: this checks values, not types" → "the same division `_check_report_by` keeps with its own entries," dropping the false "values, not types" framing.

6. **Minor, routed to task 12 per coordinator instruction** — did not touch § The one config file's `resample` expansion line.

All new/changed assertions mutation-tested individually (apply → confirm FAIL → clear `__pycache__` → revert in place → confirm PASS), verified by behavior rather than `git status`. Final: `uv run pytest` 1704 passed + 2 xfailed, `ruff check .` clean, `mypy` clean.
