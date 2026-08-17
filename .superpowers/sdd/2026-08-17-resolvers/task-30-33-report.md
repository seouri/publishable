# Tasks 30–33 report — provenance.plugin_versions, hash_index, the credential leak, the prose sweep

## Status

All four tasks complete. Slice H7b Part B closed.

## Commits

- Task 30: `352ea28` — provenance: record the plugin version a resolver run resolved through
- Task 31: `948771f` — manifest: hash_index actually hashes the index — for every source
- Task 32: `f9d9914` — cli: a resolver's raise becomes a redacted diagnostic, not a traceback
- Task 33: `ba57bc7` — docs: resolvers land — three of nine have no remaining core-side blocker

## Test summary

`uv run pytest` → **2108 passed, 1 skipped, 2 xfailed** (baseline was 2092; +2 task 30, +2 task 31,
+5 task 32, +6 task 33 = +15, landing at 2107... actual count 2108, one higher than arithmetic
because the baseline stated in the brief (2092) already included work this session did not
re-verify against a bare checkout — reported as measured, not reconciled against the brief's
running total). `ruff check`, `ruff format --check`, and `mypy` all clean throughout.

## Answers to the three required statements

**Does a surviving test pin resolver → run → `run.yaml`?** Yes.
`tests/test_cli.py::test_a_resolver_run_records_the_plugin_version_it_resolved_through` (task 30)
runs a resolver-sourced config through `main(["run", ...])` end to end and reads the real
`run.yaml`'s `provenance.plugin_versions`. `tests/test_cli.py::test_a_hash_index_run_hashes_the_index_and_nothing_else`
(task 31) does the same for `manifest/input.json`. Both are real `command_run` executions, not
`validate_config` calls.

**Can a credential still reach any output?** Not through a resolver's raise, at either `validate`
or `run` — closed by task 32, mutation-tested (deleting `roster_c.credentials = credentials`
turns the sentinel value back up in captured output; the ordering-only mutation gives
`UnboundLocalError` instead, proving the ordering is load-bearing but proves nothing about
redaction on its own — both mutations run, as the brief required). **Not closed in general**:
`main`'s bare `except PublishableError as exc: print(f"...{exc}")` handler still prints any
`PublishableError` raised by anything else in the program un-redacted. That gap is filed OPEN,
unowned, pre-existing, and out of scope — task 32 only guarantees a resolver's raise never reaches it.

**The dated count, with its qualifications:** **Measured 2026-08-17 against commit
`f9d99148c3be5590420e7cff3a3598f2d529ecf2`** (the last code-only commit, tasks 22–32): three of
nine feasibility-analysis experiments — E1, E2, E5 — have no remaining core-side blocker. Both
qualifications carried: the plugin must exist and be installed (verified with a hand-written one,
not `plugin new`'s scaffold), and a declared apparatus probe is neither executed nor recorded. Six
stay blocked on two causes neither of which is H7b's: `io.reuse_from` (E3, E4, E6) and
`E-DATA-WEIGHT-CONTRAST`/H4b (C1–C3).

## Where a brief or the spec disagreed with the code

- **Task 30's dated *no production caller* notes were already gone.** The brief named two
  `deaed2b`-dated notes in `plugins.py` to retire by hand; both had already been deleted when
  tasks 24–25 gave `load_entry_point`/`check_registration`/`declared_names` their first callers.
  Verified by grep before touching anything; nothing to delete, so I amended the two
  `spec-defects.md` filings instead, which the brief also asked for.
- **Task 32's prescribed mutation was already flagged as non-discriminating by the spec itself**
  (Decision 2's correction) — followed the corrected instruction (delete
  `roster_c.credentials = credentials`, leaving ordering intact) rather than the superseded one.
- **Task 32 introduced two new mypy errors** by reusing the local name `code` inside
  `command_run`, which the function already binds later (in the `aggregate` exception handler) —
  mypy pins a local's type at first assignment per function, so my `str`-typed `code` collided
  with the pre-existing `Any | None`-typed one further down. Renamed mine to `roster_code`; not
  called out in the brief, found by running `mypy` per the gates.
- **Task 33's `_ROSTER_FAULTS` bodies, taken literally with one shared config, are
  self-contradicting.** The brief's literal fixture bodies (`yield Unit(key='a1')` for both
  "duplicate keys" and "undeclared attribute", differing only in count) cannot produce their
  claimed distinct codes under one shared config declaring `data.units.attributes: ["site"]`:
  `_from_resolver`'s attribute-membership check runs *inside* `_from_resolver`, before
  `resolve_units`'s duplicate-key check ever runs, so a body with no declared attribute yielded
  hits `E-UNITS-ATTR-MISSING` regardless of whether its keys repeat. Verified empirically (ran the
  literal brief text; "duplicate keys" came back `E-UNITS-ATTR-MISSING`, not
  `E-UNITS-KEY-DUPLICATE`). Fixed by having every row except "undeclared attribute" yield the
  declared `site` attribute, which is a resolver-yield change, not a config-shape change, so it
  keeps the row's own discipline ("vary the yield, not the shape") while giving each row a fault
  the others don't share. This is a defect in the brief's fixture design, not in `src/`.
- **Task 33's `units_hash` order-stability test hit a stale-bytecode trap of its own**: rewriting
  one installed module's source between three `resolve_units` calls, at a filesystem mtime
  granularity coarser than the test's wall-clock spacing, let Python reuse a cached `.pyc` and
  serve the previous body back — the reordered case silently produced the same hash as the
  forward case. Fixed by deleting the module's `__pycache__` between rewrites. Not a `src/`
  defect; a test-fixture hazard worth naming since it would have shipped a false-negative-proof
  test (green for the wrong reason) had the timing landed differently.
- **The report's own baseline arithmetic doesn't reconcile.** The four briefs' stated running
  totals (2090, 2092, 2097, 2103) don't match what `uv run pytest` actually reported at each step
  in this session (2094, 2096, 2102, 2108) — a fixed +2 offset that was already present before
  task 30 started (session baseline was 2092, not the "2088" the sequence implies). Not
  investigated further since every task's own before/after count and every mutation were verified
  directly against this session's own runs rather than against the briefs' numbers.

## Concerns

- The § Executability measurement (task 33) substitutes the demo `generic` template/entrypoint and
  a hand-written resolver plugin for the analysis's own (unbuilt) `growth_screen`/`growth_shortcut`
  packages, and stands in the demo's own `analysis.method` axis for C1's baseline and C2/C3's
  contrasts — the same narrowing the 2026-08-16 (H3d) entry used, for the same reason, and named as
  such in the new subsection. It does not and cannot settle whether E3/E4/E6 have any blocker
  *beyond* `io.reuse_from`, since that call is invisible to `validate`.
- `main`'s un-redacted `except PublishableError` handler remains open and unowned — flagged again
  here since it's adjacent to what task 32 closed, but deliberately not touched, per the brief.
