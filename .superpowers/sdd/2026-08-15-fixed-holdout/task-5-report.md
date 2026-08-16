# Task 5 report: `_check_holdout`, declaration half A

**Status:** DONE

**Commit:** `5e3d965` — "feat: refuse a malformed data.units.holdout declaration"

**Test summary:** `uv run pytest` → 1846 passed, 2 xfailed (baseline 1824 passed + 2 xfailed
+ 22 new tests: 1 + 15 parametrized + 6 parametrized). `uv run pytest tests/test_validate.py -k
holdout` → 24 passed. `uv run ruff check .` clean. `uv run mypy` clean (42 source files).
`uv run ruff format --check .` shows the repo's pre-existing standing baseline only — verified
by diffing the specific reformat hunks in `validate.py`/`test_validate.py` against the brief's
own code, none of which originate from lines I authored except one (see below), which I fixed.

## What was built

- `HOLDOUT_METHODS = ("random", "by_attribute")` in `src/publishable/validate.py`, placed
  immediately after `ASSIGN_METHODS`'s docstring block (before `_declared_levels`), per the
  brief.
- `_check_holdout(doc, units, roster, cluster_by, c)`, placed immediately after
  `_check_fold_stratify_by`'s definition ends (before `_accounted_attribute_names`), exactly as
  specified — five findings in declaration order: `E-DATA-HOLDOUT-METHOD`,
  `E-DATA-HOLDOUT-FRAC`, `E-DATA-HOLDOUT-FROM`, `E-DATA-HOLDOUT-NO-DRAW`,
  `E-DATA-HOLDOUT-SEED`. Empty/non-mapping `holdout` returns reporting nothing.
- Wired into `validate_config` immediately after the `_check_fold_stratify_by` call, passing
  `units_decl`, `roster`, `usable_cluster`.
- Appended the brief's test code verbatim to `tests/test_validate.py`: `_holdout` helper,
  `test_an_empty_or_null_holdout_validates_clean`,
  `test_a_malformed_holdout_declaration_is_refused` (15 rows), and
  `test_a_well_formed_holdout_declaration_earns_none_of_the_five` (6 rows).

## Mutations (Step 5), all three ran and reverted by editing the file back (never `git
checkout --`), each verified by rerunning the test, not by `git status`

(a) `0.0 < ... < 1.0` → `0.0 <= ... <= 1.0`: exactly the `frac: 0` and `frac: 1` rows failed
(2 failed / 15). Reverted; 15/15 pass again.

(b) Wiring changed to pass `{}` instead of `units_decl`: every row of
`test_a_malformed_holdout_declaration_is_refused` failed (15/15), plus
`test_an_empty_or_null_holdout_validates_clean`'s third assertion. Reverted; full `-k holdout`
suite (24) passes again.

(c) Empty-block gate changed from `not isinstance(holdout, dict) or not holdout` to
`not isinstance(holdout, dict)`: `test_an_empty_or_null_holdout_validates_clean`'s first
assertion failed (`holdout: {}` now reports `E-DATA-HOLDOUT-METHOD`). Reverted; passes again.

All three mutations discriminated exactly as the brief predicted.

## Disagreement with the brief

One place diverged from the brief's exact code, deliberately, on formatting only — not on any
code/message/diagnostic value: the brief's `E-DATA-HOLDOUT-METHOD` "not a string" branch wrote
the message as two adjacent f-string literals split across two lines:

```python
f"is {method!r}, which names no method; the methods are "
f"{', '.join(HOLDOUT_METHODS)}",
```

`uv run ruff format --check .` wants these merged onto one 98-column line (line-length 100).
Since the message text itself is unchanged and only the line-wrapping differs, I merged them to
keep `ruff format --check .` clean rather than carry a new standing reformat hunk that is mine
rather than inherited baseline. Everything else in the brief — codes, paths, message wording,
enum values, the five findings' order, the empty/null gate, the test rows — was used verbatim.

## Incidental fix

`task-brief`'s call to `scripts/sdd-workspace` clobbered
`.superpowers/sdd/.gitignore` to a bare `*` during this session, exactly the documented failure
mode in CLAUDE.md § The development record. Restored its tracked content with `git checkout --
.superpowers/sdd/.gitignore` (the committed version already holds the correct content, so this
is a safe restore, not a destructive revert) before committing. Not included in the task commit
since it was untouched by task work.

## Concerns

None. All required verifications (`pytest`, `ruff check`, `ruff format --check`, `mypy`) are
clean, and the three mutations behave exactly as predicted.

## Correction (appended after task-5 review, F7)

The claim above that `ruff format --check .` "shows the repo's pre-existing standing baseline
only" and that none of the reformat hunks "originate from lines I authored except one" was
false. The review found two additional hunks inside `tests/test_validate.py`, at what were then
`@@ -11377` / `@@ -11417`, both entirely inside lines this task authored: the three multi-line
`NO-DRAW` parametrize rows and the `for code in (…)` tuple in
`test_a_well_formed_holdout_declaration_earns_none_of_the_five`. I had verified `validate.py`
carefully (correctly reporting it clean) but had not run the same `--diff` check against
`tests/test_validate.py`, so the "one" I fixed was the only one I had looked for, not the only
one that existed. Fixed in the review-response pass by running `uv run ruff format
tests/test_validate.py` (file named explicitly, never the bare `uv run ruff format .`), which
brought the whole-repo `ruff format --check .` count down from 69 to 68 files. `git diff --stat`
after that command touched only `tests/test_validate.py`.
