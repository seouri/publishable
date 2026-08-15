# Task 8 report: `limits.min_clusters` made real

**Status:** Done.

**Test summary:** `uv run pytest` → 1726 passed, 2 xfailed (baseline was 1722 passed + 2 xfailed;
4 new tests added, all pass). `uv run ruff check .` clean. `uv run mypy` clean (42 source files).
Both mutations applied per the brief's Step 5 — `fold_basis(roster, cluster_by)` → `len(roster)`,
and `groups < min_clusters` → `groups < 10` (after confirming `<=` alone doesn't distinguish the
fixture, as the brief predicted) — each reverted in place after confirming the named test FAILed.

## What changed

- `src/publishable/validate.py` — `_check_resample` now reads `limits.min_clusters` and warns
  `W-STATS-RESAMPLE-CLUSTERS` when a declared `resample` sits beside `data.units.cluster_by` and
  the roster resolves to fewer clusters than the floor. Cluster count comes from `units.fold_basis`,
  the same derivation `_check_replication`/`_check_sweep` already share, not a second counting
  expression. `E-DATA-CLUSTER-UNKNOWN` from an unresolvable cluster attribute is caught and treated
  as "unresolved" (this module collects rather than raises), leaving that fault to whatever check
  already reports it.
- `src/publishable/stats.py` — `percentile_over_units_clustered`'s docstring citation fixed from
  the nonexistent `statistics.min_clusters` to `limits.min_clusters`. Confirmed no other
  miscitation in `src/` or the four documents (`grep -rn "statistics.min_clusters" src/ docs/` now
  matches only historical SDD-workspace planning docs, out of scope for this task).
- `docs/reference.md` § Warnings core reports — new row for `W-STATS-RESAMPLE-CLUSTERS`, inserted
  alphabetically directly before `W-STATS-RESAMPLE-FAMILY`. § Validation's *Clusters enough to
  resample* row needed no edit, as the brief said.
- `tests/test_validate.py` — four new tests: fires below the floor, counts clusters not units
  (12-unit/4-cluster fixture straddling the floor of 10), silent above the floor (positive
  companion), and silent with no declared `resample` (scope check).

## A conflict between the brief and the code, found and resolved

The brief's Step 1 test code uses dotted overrides like `"limits.min_clusters": 10` against the
`write_config` fixture. That fixture's override mechanism (`tests/test_validate.py::write_config`,
around line 53) walks `node = node[h]` for each dotted path segment *without creating missing
keys* — it only ever assigns the final leaf. `base_config()` (same file, ~line 23) declares no
top-level `"limits"` key at all, unlike `"data"`, which is why `"data.units": {...}` overrides work
fine elsewhere in this same file. Using `"limits.min_clusters"` verbatim throws `KeyError: 'limits'`
inside the fixture itself, before `_check_resample` ever runs — not a missing-check failure, a
fixture failure.

Every other place in this file that overrides `limits` uses the nested-dict form,
`"limits": {"max_executions": ...}` (e.g. lines 238, 1098, 1231), which works because `"limits"`
*is* the leaf when the dotted string has no further segments. I followed that existing convention:
the four tests use `"limits": {"min_clusters": 10}` / `{"min_clusters": 3}` in place of the brief's
`"limits.min_clusters": 10` / `3`. The floor values themselves (10, 3) are exactly as specified;
only the override's shape changed, to the shape every other `limits` override in this file already
uses. I did not touch `write_config` itself — auto-vivifying missing dict paths there is a
broader, riskier change against a shared fixture that this task's scope doesn't call for.

## Commit

`21214d8` on `h4a-resample-honoured` (parent `cf9f022`, the branch tip at start of this task):
`feat: W-STATS-RESAMPLE-CLUSTERS, and fix the docstring citing limits.min_clusters as
statistics.min_clusters`. Superseded on the review points below by `f75078b` and the follow-up
commit addressing this section.

**Correction to this report's own earlier claim:** the line above said both the roster-`None` and
the `E-DATA-CLUSTER-UNKNOWN` paths were "tested for silence." Review caught that this was false —
neither had a test that would fail if its guard were deleted; the suite stayed green under three of
the four guard clauses removed, including the one whose removal is an actual crash. Fixed below.

## Review response (3 Important, 5 Minor — no behavioural defect shipped)

**Important 1 — three of four guard clauses were untested, one hides a crash.** Added
`test_an_unresolved_roster_does_not_crash_the_cluster_check` (`data.units.from` names a
nonexistent file, so `roster` is `None` while `cluster_by`/`resample`/`limits.min_clusters` are all
otherwise valid — the exact combination that, with `roster is not None` deleted, sends a `TypeError`
out of `units.clusters_of`'s `for unit in roster` and out of `validate`, which is contracted to
collect, never raise). Confirmed by mutation: deleting the guard turned the test into an uncaught
`TypeError`, not an assertion failure. Also added
`test_no_cluster_warning_when_cluster_by_is_undeclared` (mutation-confirmed: deleting the
`cluster_by` guard fires the warning on an unclustered 1-unit roster) and
`test_a_wrong_typed_min_clusters_is_a_type_fault_not_a_warning` (parametrized over `"ten"`, `True`,
`10.0`; mutation-confirmed for the string and float cases — `True` alone doesn't distinguish this
particular mutation because `1` isn't below the fixture's 4-cluster count, but the guard mirrors the
already-established `n`/bool pattern and the other two parameters do prove it's read). All three
mutations applied, confirmed FAIL, `__pycache__` cleared, reverted in place, confirmed PASS.

**Important 2 — the "`roster` is unused by every check below" comment was false as of this task's
own commit**, and its enumeration omitted the new check — the same shape of drift task 7's review
flagged in the same function. Rewritten to name which checks read `resample`/`doc` alone
(`method`, `n`, the family bound, `stratify_by`) and to say explicitly that the cluster-floor check
is the one exception that reads `roster`, guards itself independently, and that the sentence's job
is only to justify the missing `return` — not to promise every check below is roster-independent.

**Important 3 — the new `except ContractError` comment claimed the fault was "already reported
beside this," measured false** for `cluster_by: measurements.by` (resolves the roster cleanly,
and neither `_check_cluster_by` nor `_check_units` says anything about it). Rewritten to name the
one reachable case with no companion finding and say plainly that the fault is swallowed here
because the check cannot proceed without a readable grouping and `validate` collects rather than
raises. Per review's explicit instruction, also fixed the sibling comment upstream (the `basis`
computation's own `except ContractError`, `validate.py` around line 602) that the new comment had
been copied from: its claim that "nothing downstream needs the basis" is no longer true in general
now that this task's check independently resolves the same roster/`cluster_by` pair — narrowed to
say that only the `basis` local itself goes unused when no `fold` level is declared.

**Minors, all five taken:**
- The miscitation survived at `tests/test_stats.py:2206` (`test_two_clusters_still_report_a_percentile`'s
  docstring) — my original sweep filtered to `src/` and `docs/`, missing `tests/`. Fixed; re-swept
  `grep -rn "statistics\.min_clusters" --include="*.py" .` across the whole tree, zero matches.
- `_check_resample`'s docstring enumeration was stale (five checks named, six now real). Updated to
  name the `limits.min_clusters` check and flag it as the one that reads the roster.
- The cluster count was walked twice (`fold_basis` here, `fold_basis` again for `basis` in the
  caller) while the comment claimed a single derivation. Did not thread `basis` through as a
  parameter — judged a larger, riskier cross-function change than this response calls for — instead
  corrected the comment to say plainly that this is a second call to one derivation, not a shared
  value, and that the two `try`/`except ContractError` blocks must be kept in agreement by hand.
- Test redundancy inherited from the brief: `test_the_cluster_warning_counts_clusters_not_units`
  called `write_config` twice with an identical override dict, once for `codes()` and once for
  `messages_by_code()`. Collapsed to one `write_config` call read both ways.
- No test varied the cluster count at a fixed floor (all four original tests varied the floor
  against one roster). Added
  `test_the_cluster_warning_tracks_the_cluster_count_at_a_fixed_floor`: `min_clusters: 10` held
  constant across two rosters, 4 clusters (warns) and 12 clusters (silent).

Suite after fixes: 1732 passed, 2 xfailed (1726 + 6 new tests). `ruff check .` and `mypy` clean.

## Concerns

- The `write_config` dotted-override fixture's inability to auto-vivify missing top-level keys is a
  latent trap for the next task that needs a `limits.*` (or any other currently-absent top-level
  block) override written as a dotted string — worth a one-line note in a future task's brief
  rather than a silent surprise like this one.
- `basis`/cluster-count-for-`min_clusters` is still computed twice (once in `validate_config` for
  `fold_basis`, once again inside `_check_resample`). Not threaded through as a parameter in this
  response, per the minor's own "either reuse it or drop the claim" — I dropped the claim rather
  than reusing. If a future task touches this area again, threading `basis` through as
  `_check_resample`'s own `fold_basis=` keyword (matching `_check_replication`/`_check_sweep`'s
  existing pattern) would remove the duplication for good.
