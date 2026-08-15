# Task 11 report

**Status:** Complete.

**Commit:** `98fe62d` — feat(validate): refuse blocked beside a declared cluster_by

**Tests:** `uv run pytest` → 1574 passed, 2 xfailed (full suite). New tests
(`test_blocked_beside_a_declared_cluster_by_is_refused`,
`test_random_beside_a_declared_cluster_by_is_not_blocked_clustered`,
`test_blocked_with_no_cluster_by_is_not_blocked_clustered`) pass; `ruff check .`
and `mypy` both clean.

**Mutation testing performed (apply → run → FAIL → revert → PASS, `__pycache__`
cleared between, reverts verified by re-running the suite rather than
`git status`):**
- Guard removed (`if usable_cluster is not None:` → `if True:`): failed
  `test_blocked_with_no_cluster_by_is_not_blocked_clustered` as expected
  (extra `E-DATA-ASSIGN-BLOCKED-CLUSTER`); reverted, full `test_validate.py`
  green.
- Method scope widened (`if method == "blocked":` →
  `if method in DRAWN_ASSIGN_METHODS:`): failed
  `test_random_beside_a_declared_cluster_by_is_not_blocked_clustered` as
  expected; reverted, full `test_validate.py` green (524 passed).

Each mutation died to exactly the control built for it; neither died to the
other's.

**Both layers agree on the refusal.** `validate._check_assign` now reports
`E-DATA-ASSIGN-BLOCKED-CLUSTER` for `method: blocked` beside a non-empty
`data.units.cluster_by`, before any of the `block_size` checks run for that
axis (a `continue` skips them once this fires — they'd be moot). This is
exactly the shape `units.assignment_for`'s `blocked` branch already raises
`NotImplementedError` for (`clusters is not None`), so a config that reaches
`run` can never hit that raise — `validate` refuses it first. No gap between
the two surfaces was found.

**Files touched:**
- `src/publishable/validate.py` — `_check_assign`: added `usable_cluster`
  local (same "present, non-empty str" narrowing as `validate_config`'s own),
  the new check inside the `blocked` branch, and a docstring paragraph for
  *Blocked draw excludes clustering*; bumped the row count in the function's
  docstring from "ten" to "eleven".
- `tests/test_validate.py` — three new tests (the refusal plus the two
  controls), both as direct `_check_assign` calls and end-to-end through
  `write_config`/`validate_config`, asserting exact finding sets throughout.
- `docs/reference.md` — one row added to § Errors `validate` reports (sorted
  alphabetically between `E-DATA-ASSIGN-BLOCK-SIZE` and `E-DATA-ASSIGN-DRAWN`)
  and one row added to § Validation (after *Block size fills the arms*). The
  two existing forward references to `E-DATA-ASSIGN-BLOCKED-CLUSTER` in §
  Allocation and § Clustered units needed no change — they already state the
  rule correctly and are now backed by a registered code.

**Concerns:** None outstanding. The message names both honest routes
(`random`, `by_attribute`) as the brief required, and the exact-set assertions
on all three fixtures (refusal + two controls) are the anti-regression teeth
requested.
