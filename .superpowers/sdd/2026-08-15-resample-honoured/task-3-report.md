## Task 3 report

**Status:** done
**Commits:** 3c8c941 (initial), d9bed97 (review fixes)

**Test summary:** `uv run pytest` — 1694 passed, 2 xfailed (baseline 1691 + 3 new resample tests); `uv run mypy` clean (42 source files); `uv run ruff check .` clean.

**Concerns:** none. Precedent verified before relying on it: adding the three `LEAF_TYPES` entries alone made `statistics.resample` both leaf and container, so `_check_unknown_keys`'s existing container-before-leaf ordering produced `E-CONFIG-KEY-UNKNOWN` for `stratifyy_by` with no closed key set needed, exactly as the corrected precedent (`data.units.measurements`) predicted. Mutation performed: deleted the `stratify_by` leaf entry, confirmed `test_the_three_resample_leaves_are_typed` FAILED (path set shrank to two) while `test_a_misspelled_resample_key_is_reported_rather_than_ignored` still PASSED (closure survives on the other two children); cleared `__pycache__`, edited the line back in place (no `git checkout`), reran to confirm PASS.

**Review follow-up (d9bed97):** Coordinator review found 2 Important + 2 Minor.

- Important 1 (would have caused task 4 to build a crash): the `test_the_three_resample_leaves_are_typed` docstring falsely claimed the `E-CONFIG-TYPE` backstop "lets `_check_resample` read each value without its own isinstance ladder." `validate.py` treats a leaf fault as deliberately non-fatal (e.g. `_check_metadata`'s guard on `metadata.name`), so validation continues past a bad `n` and task 4 still needs its own guard before reading a value for comparison. Rewrote the docstring to say what the backstop actually buys — a reported fault, not a stopped pass — and pointed at `_check_metadata`'s guard by behaviour.
- Important 2: the `LEAF_TYPES` comment claimed the block "is no longer refused wholesale," which is false at this commit — `E-STATS-RESAMPLE-UNSUPPORTED` still fires; task 12 retires it. This also contradicted the `holdout` comment a few lines above (which says a still-refused block stays whole). Rewrote both the inline comment and the module docstring's `resample` sentence to give the true reason: validate-before-honour — the shape is closed now so the checks exist before the refusal retires later in the slice.
- Minor 1: added an assertion on the difflib hint text itself (`"stratify_by" in msg`) in `test_a_misspelled_resample_key_is_reported_rather_than_ignored`, rather than only asserting the finding's presence.
- Minor 2: added missing `-> None` annotations to the three new tests.

Re-verified after the fix: mutated (removed `stratify_by` leaf entry), confirmed all three resample tests FAIL, cleared `__pycache__`, reverted in place (no `git checkout`), confirmed PASS. Full suite/mypy/ruff re-run clean at 1694 passed + 2 xfailed.
