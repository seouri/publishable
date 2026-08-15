# Task 16b report — A contrast whose two sides share no units is refused

## What was done

- **`src/publishable/validate.py`** (`_check_sweep`): kept the resolved `resolve_contrasts`
  list (`resolved_contrasts`) instead of discarding it after `len()`, and added a new,
  per-comparison guard beside `E-DATA-WEIGHT-CONTRAST`/`E-DATA-CLUSTER-CONTRAST`. For each
  resolved comparison it computes `cli._differing_axes(of, against)` (imported locally to
  avoid the `cli`↔`validate` circular import — `cli` imports `validate` at module scope) and
  intersects it with `of.selectors | against.selectors`. A non-empty intersection — the two
  conditions differ on a `sweep.groups` axis — reports `E-DATA-ALLOCATION-CONTRAST`, naming
  both conditions' indices, labels, and the differing group axis/axes. Guarded per comparison,
  **not** on `comparisons > 0` like its two siblings, per the addendum: a `groups × grid`
  design's within-arm comparisons are paired and computable and must not be refused alongside
  its cross-arm ones.
- **`src/publishable/cli.py`** (`_comparison_step_blocks` docstring): rewrote the paragraph
  that justified the hard-coded `"paired": True` by naming `E-SWEEP-GROUPS-UNSUPPORTED` and
  `E-DATA-ALLOCATION-UNSUPPORTED` (task 17's retirement targets). It now names
  `E-DATA-ALLOCATION-CONTRAST` and states that `True` is a true claim about what survived
  validation ("`cli` always validates before running") rather than a placeholder for an
  unreachable case — per the addendum's instruction to say which of the two claims survives.
- **`docs/reference.md`** § Errors `validate` reports: inserted the `E-DATA-ALLOCATION-CONTRAST`
  row immediately before `E-DATA-ALLOCATION-NO-ARMS` (sorted: CONTRAST < NO-ARMS < WITHIN-ARMS),
  modelled on the `E-DATA-CLUSTER-CONTRAST` row's structure and stating the guard's
  per-comparison shape explicitly so it doesn't read as a copy of its `comparisons > 0` siblings.
- **`tests/test_validate.py`**: added a new section ("a contrast whose two sides differ on a
  group axis has no unpaired construction") with the three controls the addendum asked for —
  (1) groups axis alone, no baseline, no contrasts → no new finding, exact set asserted; (2)
  ordinary parameter baseline+grid, no groups at all → genuinely paired, untouched, empty set;
  (3) a `groups × grid` design whose baseline fixes the group axis to one arm, generating 4
  resolved comparisons of which exactly 2 cross arms — asserted by count and by which
  conditions' labels are named in the messages, not just that the code appears — plus a fourth
  test for the declared-`statistics.contrasts`-across-arms route. Two **pre-existing** tests
  (`test_a_baseline_may_fix_a_group_level`,
  `test_a_baseline_may_not_fix_a_group_level_while_ablate_is_declared`) turned out to already
  contain configs that generate genuine cross-arm comparisons (a baseline fixing the group axis
  to one specific arm value, rather than per-cell) — their expected code sets and docstrings
  were updated to include the new, correct finding, since the guard's firing there is not a
  false positive.

## Verification

- `uv run pytest tests/test_validate.py` — 476 passed.
- `uv run pytest` (full suite) — 1490 passed, 2 xfailed (pre-existing, unrelated).
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — no issues, 40 source files.
- Mutation testing (apply → run named test → confirm FAIL → delete `__pycache__` → revert →
  confirm PASS, verified by behavior each time):
  1. Disabled the entire per-comparison loop (`continue` as the first statement) — both the
     count test and the declared-contrast test failed (0 found where 2/1 expected). Reverted,
     both pass.
  2. Skipped only `comp.declared` comparisons (`if comp.declared: continue`) — only the
     declared-contrast test died (0 found where 1 expected); the baseline-generated count test
     was unaffected. Reverted, both pass.
  3. Skipped only non-declared comparisons (`if not comp.declared: continue`) — only the
     baseline-generated count test died (0 found where 2 expected); the declared-contrast test
     was unaffected. Reverted, both pass.
  4. Removed the `group_axes` selector-intersection (fired on *any* differing axis, matching
     the siblings' unconditional shape) — both the count test (4 found where 2 expected, since
     the two within-arm, method-only-differing comparisons were now wrongly flagged) and the
     "genuinely paired, unaffected" control test failed. Reverted, full suite green.

Each mutation was confirmed to die to the intended test and to no other, and the final
`git diff` state matches what `pytest`/`ruff`/`mypy` were run against.

## Scope decisions

- Did **not** touch `docs/superpowers/spec-defects.md`. It has a `RESOLVED (S4c task 8)` entry
  (§ `confounded: true`...) whose closing note repeats the same stale "unreachable in this
  build" claim naming the two codes task 17 retires. Neither the brief nor the addendum lists
  that file in scope, and the addendum explicitly says "Task 17's addendum has been told to
  verify [16b landed before it] and to check the `_vs_baseline_block` docstring as part of its
  own grep sweep" — task 17 already owns retiring those two codes everywhere they're named, and
  fixing a closed historical defect entry that only becomes stale once those codes are actually
  gone reads as that slice's job, not this one's. Flagging it here in case task 17's grep sweep
  doesn't reach `spec-defects.md`'s prose (its own grep is for the two live code strings, which
  this entry does contain, so it should be caught).
- Used `cli._differing_axes` via a **function-local** import inside `_check_sweep` rather than a
  module-level one, since `cli.py` imports `publishable.validate` at module scope — a
  module-level `from publishable.cli import _differing_axes` in `validate.py` would be a true
  circular import. Verified both import orders (`import publishable.validate` first, and
  `import publishable.cli` first) succeed.

## Notes on the brief and addendum

- The brief's file list names `cli._vs_baseline_block`, but no such function exists — the
  hard-coded `"paired": True` and its docstring live in `cli._comparison_step_blocks` (the
  function `_compute_vs_baseline` and `_compute_declared_contrasts` both call). The addendum's
  own "Verified interfaces" table confirms the quoted docstring text and code names verbatim,
  so this is a naming slip in the brief rather than a wrong premise — the described site,
  content, and fix are all correct once `_vs_baseline_block` is read as
  `_comparison_step_blocks`.
- Everything else in the brief and addendum checked out against the code: `_differing_axes`
  exists exactly as described (union-of-both-sides, declaration order), `Condition.selectors`
  is a `frozenset[str]` from task 3, `stats.paired_keys` returns `[]` over disjoint arms, and
  `grep -rn 'unpaired_\|welch_' src/` returns exactly the one docstring hit the addendum named
  (now rewritten).

## Addendum: coordinator review follow-up

The coordinator's review found five items after the first pass; all five addressed.

1. **§ Validation check table had no row for the new check.** Added *Allocation deltas
   aren't computed* to `docs/reference.md`'s check table, between *Allocation strata exist*
   and *Cluster attribute exists* as instructed, modelled on the sibling *Clustered deltas
   aren't computed* / *Weighted deltas aren't computed* rows but stating explicitly that it
   reads per comparison rather than the whole design. Re-checked the "Six things deliberately
   absent from that table" sentence and found it counts unrelated run-time/dry-run facts, not
   rows in this table, so it needed no change; found no other row-count phrase on that surface.
2. **The rewritten `paired: True` docstring had no expiry.** Added one sentence to
   `cli._comparison_step_blocks`: retiring `E-DATA-ALLOCATION-CONTRAST` must also turn
   `paired` into a derived value (`differing_axes(...) ∩ (of.selectors | against.selectors)`
   non-empty — the same test the refusal runs today), not leave `True` hard-coded once
   validation stops rejecting the case it's hard-coded against.
3. **Layering: moved `differing_axes` (formerly `cli._differing_axes`) to `contrasts.py`.**
   `contrasts.py` sits below both `cli.py` and `validate.py` and already defines an equivalent
   `_MISSING` sentinel, reused rather than duplicated. Renamed without the leading underscore
   since it is now a genuine cross-module helper (matching `resolve_contrasts`/`baseline_for`/
   `units_matching`, the other public names in that module) rather than a single module's
   private detail. Updated both production call sites (`cli.py`'s own `differs_on = ...` line,
   `validate.py`'s guard) to import it from `contrasts` at module scope — this also removed the
   function-local import Important 3 flagged, since there is no cycle to break anymore. Updated
   every remaining reference: two explanatory comments in `validate.py`, one in
   `cli._comparison_step_blocks`'s docstring, and the test-side imports/call-sites in
   `tests/test_contrasts.py` (module-level import) and `tests/test_validate.py` (the two
   function-local imports), plus one prose mention in `tests/test_cli.py`. Left the historical
   mentions in `docs/superpowers/spec-defects.md`, `docs/superpowers/H3c-SCOPING.md`, and
   `docs/superpowers/plans/*.md` alone — planning/historical artifacts outside the four
   documents, accurate as descriptions of the state when written, the same class of thing
   already left alone for the `spec-defects.md` codes deferral.
4. **Message wording narrower than the guard.** Changed "`allocation: between` means the two
   conditions hold disjoint sets of units" to "a declared `groups` axis means the two
   conditions hold disjoint sets of units" in the runtime message, and added a comment
   explaining the guard fires regardless of the declared (or undeclared/default `within`)
   `allocation` value — a config missing `allocation` entirely still co-reports
   `E-DATA-ALLOCATION-WITHIN-ARMS`, so nothing incorrect escapes, but the premise as originally
   worded was narrower than what actually gates the check.
5. **Which row owns which route.** Added one sentence to the *Contrast has units in common*
   check-table row: it covers the case *Allocation deltas aren't computed* does not — two
   same-arm conditions (or any pair) left disjoint by a `within` stratum or by
   `resolve_units`, with no differing group axis between them — and named the two
   constructions each row reads (`differing_axes ∩ selectors` vs. `stats.paired_keys`'s own
   intersection) so a reader lands on the right one once task 17 makes the group-axis case
   reachable.

### Verification (second pass)

- `uv run pytest` — 1490 passed, 2 xfailed, after fixing the three test files
  (`tests/test_contrasts.py`, `tests/test_validate.py`, `tests/test_cli.py`) that imported or
  named `_differing_axes` from `cli` — the move broke their imports first, caught immediately
  by `pytest`'s collection error naming the exact site.
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — no issues, 40 source files.
- Re-ran the whole-guard-disable mutation (the first and strongest one from the original pass)
  against the moved/renamed code: applied, confirmed both `test_a_generated_cross_arm_...` and
  `test_a_declared_contrast_across_arms_is_refused` FAIL (0 found where 1/2 expected), deleted
  `__pycache__`, reverted, confirmed the full suite (1490 passed) and both targeted tests PASS
  again. Did not re-run the other three mutations from the original pass — the guard's logic
  is unchanged by the move (only its import path and the sentinel's home changed), and this one
  mutation is sufficient to confirm the move didn't silently disconnect the check from its
  tests.
- Mechanical pass over every row edited or moved: table column counts checked for the new row
  (285), the edited *Contrast has units in common* row (297), and a neighboring untouched row
  (424) — all 4 pipe-delimited fields, consistent; no trailing whitespace or tabs introduced;
  the "Six things..." count sentence re-verified as unrelated to this table's row count; the
  worked example's pinned hashes/values (`8e21`/`1a2b`/`3d8a`/`6b1f`, r = 0.581/0.607/0.412,
  `repeat_spread`) grepped and confirmed unmoved.

## Status

DONE.
