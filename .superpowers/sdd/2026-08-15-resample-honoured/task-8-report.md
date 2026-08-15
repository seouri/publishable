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

`cf9f022` was the branch tip at start; this task's commit is on top of it:
`feat: W-STATS-RESAMPLE-CLUSTERS, and fix the docstring citing limits.min_clusters as
statistics.min_clusters` (see `git log -1` on `h4a-resample-honoured` after this report lands —
committed in the same pass as this report).

## Concerns

- None outstanding on the check itself: both the roster-is-`None` and the
  `E-DATA-CLUSTER-UNKNOWN` paths are guarded and tested for silence, matching the "leaf faults are
  non-fatal" and "collects rather than raises" rules this slice has repeated.
- The `write_config` dotted-override fixture's inability to auto-vivify missing top-level keys is a
  latent trap for the next task that needs a `limits.*` (or any other currently-absent top-level
  block) override written as a dotted string — worth a one-line note in a future task's brief
  rather than a silent surprise like this one.
