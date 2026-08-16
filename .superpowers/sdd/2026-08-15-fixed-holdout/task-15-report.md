# Task 15 report: the denominators — six sites narrowed, two deliberately not

## Status

DONE

## What was built

`src/publishable/cli.py`: added `_evaluation_roster(roster, holdout)` immediately after
`_resolved_holdout`, verbatim from the brief (docstring included). In `command_run`, added
`eval_roster = _evaluation_roster(roster, holdout_plan)` immediately after `holdout_plan` is
realized, with the brief's comment about `roster` staying whole below that line. Changed exactly six
call sites from `roster` to `eval_roster`: `execute_plan(units=...)`, `_condition_beside_n(...)`,
`_condition_counts(...)`, `_condition_report_by_levels(...)`, `_compute_vs_baseline(roster=...)`,
`_compute_declared_contrasts(roster=...)`. Added the brief's comment at the `provenance["units"]`
write site explaining why `240` there and `48` in a metric's `n` are both true. Added one line beyond
the brief: `assert eval_roster is not None` immediately inside `if roster is not None:` (before the
per-condition loop), with a comment — `mypy` cannot see that `eval_roster is None` iff `roster is
None` (an invariant of `_evaluation_roster` itself), and without it three of the six narrowed call
sites failed `arg-type` (`UnitList | None` where `UnitList` is required).

`tests/test_cli.py`: added `_evaluation_roster` and `HoldoutPlan` to the top-level imports (the
latter placed in import-sorted position, not beside its use, to satisfy `ruff`'s import-order check).
Appended the brief's two given tests verbatim
(`test_the_evaluation_roster_is_the_test_partition_and_preserves_roster_order`,
`test_the_narrowed_roster_is_what_attrition_counts_against`, the latter using `_repeat_result` —
already imported from `tests.test_stats` at the top of this file — rather than a new
`_completed_results_for` helper, since `_repeat_result(step, repeat_label, condition_index,
rows_by_unit)` already builds exactly the `list[ExecutionResult]` needed) and a module-level
`_HOLDOUT_PLAN_8_2`. Added four more tests for the four sites the brief left unpinned:
`test_condition_report_by_levels_omits_a_level_confined_to_training_units`,
`test_compute_declared_contrasts_within_is_narrowed_by_the_test_partition`,
`test_compute_vs_baseline_roster_argument_never_affects_the_auto_generated_family` (a documented
non-pin — see below), and `_condition_beside_n` is covered only by the finding in the table, not a
test (also below).

## The six sites: pinning status

| # | Site | Pinned? | By |
|---|---|---|---|
| 1 | `execute_plan(units=eval_roster)` | No | Unpinnable at this commit. `E-DATA-HOLDOUT-UNSUPPORTED` refuses every config declaring a holdout before `command_run`'s body runs, so no test reaches this call site end-to-end. Task 18's `n.resolved` and `max_failed_fraction` pins are what close it (brief's own mutation (c), confirmed below). |
| 2 | `_condition_beside_n(beside_n, eval_roster, cond.index, arm_members_map)` | No — and not just "no test yet" | **Structurally inert**, verified empirically (see finding below): `_condition_beside_n`'s return depends only on `beside_n`'s own content and on whether `arm_members_map is None`, never on which roster object or content is passed. No task-18 pin closes this either, since the fact being tested (identity of `_cond_roster`'s return against its own input) doesn't change with which roster is fed in. |
| 3 | `_condition_counts(results, eval_roster, step_name, ...)` | **Yes** | `test_the_narrowed_roster_is_what_attrition_counts_against` (brief's own test). Mutation confirmed below. |
| 4 | `_condition_report_by_levels(eval_roster, cond.index, arm_members_map, attribute)` | **Yes** | `test_condition_report_by_levels_omits_a_level_confined_to_training_units`. Mutation confirmed below. |
| 5 | `_compute_vs_baseline(..., roster=eval_roster, ...)` | No — and not just "no test yet" | **Structurally inert**, verified empirically (see finding below): `resolve_contrasts` never sets `within` on an auto-generated (`declared=False`) comparison, so `units_matching(roster, None)` always returns `None` regardless of which roster is passed. `test_compute_vs_baseline_roster_argument_never_affects_the_auto_generated_family` records this rather than asserting a pin that doesn't exist. |
| 6 | `_compute_declared_contrasts(..., roster=eval_roster, ...)` | **Yes** | `test_compute_declared_contrasts_within_is_narrowed_by_the_test_partition`, using a declared `within` (which *can* be non-`None`, unlike site 5). Mutation confirmed below. |

Sites 2 and 5 are a real disagreement with the brief's framing (see "Where the brief disagreed with
the code"), not an oversight — I made the six-site change as instructed for both (correctness of
`cond_roster`'s eventual *content*, and consistency with sites 1/6/3/4, in case a future change makes
either function's roster argument observable), but no test can distinguish `eval_roster` from
`roster` there, and neither will task 18's pins.

## The three key-indexed sites, checked rather than restated

Verified `unit_attributes` empirically (`Unit`/`_attributed` reached directly): built the mapping from
a 10-unit whole roster and again from a 2-unit narrowed roster, ran `_attributed` against a table
holding rows for only the narrowed unit's keys, and the two outputs were byte-for-byte identical —
`_attributed` looks up `attributes.get(row["unit"], {})` only for keys the table's rows actually carry,
so the eight surplus training keys in the whole-roster mapping are never read. `weights` and
`resample_strata` follow the same shape by inspection (both are consumed by key from `attrition`'s /
`stats`'s per-completed-unit loop, never iterated over on their own), and I did not find a case where
narrowing either changes anything. This matches the brief's claim; I did not find a case where it is
wrong.

## Mutations run

All reverted by editing the file back (never `git checkout --`), `__pycache__` deleted between runs,
each revert verified by re-running the affected test(s), and a final `diff` against a pre-mutation
backup confirmed byte-identical restoration of `src/publishable/cli.py` before committing.

**Brief's three, on `_evaluation_roster` and the `execute_plan` site:**

**(a)** Changed the early return to `return UnitList(list(roster)) if roster is not None else None` (a
copy instead of the same object). Result: **FAIL** —
`test_the_evaluation_roster_is_the_test_partition_and_preserves_roster_order` failed directly on
`assert _evaluation_roster(roster, None) is roster` (this test, added this task, asserts the identity
claim directly — stronger than the brief's fallback prediction that nothing would fail and the
docstring would need weakening). Reverted; both `-k "evaluation_roster or narrowed_roster_is_what"`
tests pass again.

**(b)** Changed the narrowing to `test = set(holdout.train)`. Result: **FAIL** — both
`test_the_evaluation_roster_is_the_test_partition_and_preserves_roster_order` and
`test_the_narrowed_roster_is_what_attrition_counts_against` failed (`8 == 2` on the latter's
`narrowed["resolved"]` assertion). Reverted; both pass again.

**(c)** Reverted `execute_plan(units=eval_roster)` to `execute_plan(units=roster)`. Result: **nothing
failed** — `uv run pytest` still reports 1942 passed, 2 xfailed. The honest result at this commit,
exactly as the brief predicts: no config can declare a holdout and reach `command_run`, so no test
exercises this call site end-to-end. Task 18 is what closes it. Reverted back to `eval_roster`.

**Mine, one per pinned site (3, 4, 6), confirming the direct-call tests are mutation-sensitive:**
rather than re-mutating `command_run`'s source (which none of these four tests reach at all — they
call the extracted functions directly, the same pattern task 13/14 established, since command_run
itself can't be exercised past `validate`'s refusal), I fed each test's "should be narrowed" call the
wrong (whole) roster and confirmed the assertion that pins the fix fails:

- Site 3 is the brief's own test; its `whole["failed"] == 8` assertion already *is* this check
  (confirmed live before implementing, per the brief's step 2).
- Site 4: called `_condition_report_by_levels(roster, 0, None, "cohort")` (whole, where `eval_roster`
  belongs) and re-asserted `"early" not in mutated` — **AssertionError**, confirming `"early"` is
  present when the wrong roster is fed.
- Site 6: called `_compute_declared_contrasts(..., roster=roster, ...)` (whole, where `eval_roster`
  belongs) and re-asserted `n_paired == 1` — got `n_paired == 2`, confirming the mismatch.

I additionally reverted all six `command_run` call sites to `roster` at once (a single script edit)
and ran the full suite: **1942 passed, 2 xfailed — nothing failed**, the same "honest result" as
mutation (c), for all six sites simultaneously. This confirms that command_run's own *wiring* (as
opposed to the narrowing functions' own behavior, which sites 3/4/6 pin directly) is unverifiable
end-to-end for any of the six sites at this commit, not only for `execute_plan`. Reverted back to the
six `eval_roster` call sites; full suite green again.

## Test summary

`uv run pytest` — 1942 passed, 2 xfailed (1937 baseline + 5 new tests: two of the brief's own, plus
`_condition_report_by_levels`, `_compute_declared_contrasts`, and the `_compute_vs_baseline`
non-pin finding). `uv run ruff check .` and `uv run mypy` clean (42 source files). `uv run ruff
format --check .` shows only pre-existing drift in 63 files, none of which are `cli.py` or
`test_cli.py` (confirmed by grepping the reformat list for both filenames — neither appears).

## Where the brief disagreed with the code

Two disagreements, both about which of the six sites are actually observable, found by testing rather
than assumed from the brief's framing:

1. **Site 2, `_condition_beside_n`.** The brief lists it as one of six sites whose narrowing matters
   for the denominators. Empirically, its return value depends *only* on `beside_n`'s own content and
   on whether `arm_members_map is None` — never on the roster argument's identity or content, because
   `_cond_beside_n`'s only use of its two roster-derived arguments is the identity comparison
   `cond_roster is roster`, and both sides of that comparison are always derived from the *same*
   passed-in value in one call. Feeding `_condition_beside_n` the whole roster versus `eval_roster`
   produces byte-identical output in every case I constructed, with and without a non-`None`
   `arm_members_map`.
2. **Site 5, `_compute_vs_baseline`.** Same shape, different cause: `resolve_contrasts` never
   populates `within` on an auto-generated `vs_baseline` comparison (`Comparison(..., declared=False)`
   omits the keyword, taking the dataclass default `None`), and `units_matching(_, None)` is `None`
   regardless of which roster is passed. `_compute_vs_baseline`'s only other use of `roster` is the
   `if roster is None: return None, []` guard, and `eval_roster is None` iff `roster is None`, so even
   that guard can't distinguish them.

Both are real findings that outrank the brief's implicit assumption that all six sites are equally
pinnable, not oversights in my testing — I checked both with actual constructed inputs (see the code
snippets run during this task), not by reasoning alone. I still made the change at both sites, since
it is the correct, defensive answer (in case a future change gives either function's roster argument
teeth — e.g., `within` becoming settable on an auto-generated comparison), but neither is testable now
and neither will be closed by task 18's two named pins (`n.resolved`, `max_failed_fraction`), which
don't touch `_condition_beside_n`'s or `_compute_vs_baseline`'s own return values.

## Process notes

`.superpowers/sdd/.gitignore` was clobbered to a bare `*` (the standing `scripts/sdd-workspace` /
`task-brief` behavior CLAUDE.md documents) when this task's brief was read. Restored via `git
checkout -- .superpowers/sdd/.gitignore` before committing — safe here because that file had no
uncommitted content of its own; `git diff` showed no remaining changes to it afterward.
