# Task 14 report — `allocation.json`

## Status: DONE

Commit: `b15ef37` — "feat: write allocation.json recording realized arm assignment"

## What was built

- `src/publishable/artifacts.py`: `build_allocation_document(roster, group_axes)` builds the
  `allocation.json` payload — `{"seed": {}, "arms": {axis: {level: [unit keys...]}}, "strata": {}}`,
  `None` when `group_axes` is empty. Calls `units.arms_of` directly, once per axis — the single
  authority task 10 built, not `arm_members` (built for a condition's cross-axis intersection, the
  wrong shape here) and not a fresh derivation. `allocation_hash(document)` mirrors
  `manifest.manifest_hash`'s canonical-JSON-then-sha256 construction.
- `src/publishable/cli.py`: `command_run` writes `allocation.json` beside `sweep.yaml` (before
  `execute_plan`, "settled before the first execution"), and adds `provenance.allocation` /
  `provenance.allocation_hash` (path + hash, or `None`/`None` together when nothing was written).
- Tests: `tests/test_artifacts.py` — unit tests for `build_allocation_document`/`allocation_hash`
  (empty-axes → `None`; exact per-axis-per-level unit keys in roster order using a 4/9/13 fixture
  with deliberately out-of-order keys, so sorted output would fail; `seed`/`strata` == `{}`,
  `holdout` absent; hash determinism/content-sensitivity). `tests/test_cli.py` — two end-to-end
  tests following `test_a_group_axis_actually_narrows_end_to_end`'s discipline (monkeypatch only
  `validate._check_unimplemented`): one runs a real `groups` + `between` + `by_attribute` config to
  a real `run.yaml` and asserts the file's exact contents and `provenance` fields; the other runs a
  plain project with no group axis and asserts absence, paired with a positive check that the same
  run's `run.yaml` exists and completed.

## Decisions the addendum required, and what was picked

- **`holdout` omitted, never written `null`** — named precedent: `manifest/input.json`'s "absent
  rather than null, so 'not hashed' can't be misread as 'hashed to nothing'". `holdout` is
  unreachable in this build regardless (`E-DATA-HOLDOUT-UNSUPPORTED` still refuses every
  declaration), so in practice the key is always absent today; H3d adds it once that refusal lifts.
- **`seed` and `strata` are always empty mappings (`{}`), not omitted keys** — `by_attribute` is the
  only reachable `assign.method` and it draws nothing and stratifies nothing, so no axis ever
  qualifies for either. Kept as present-but-empty rather than omitted, matching the document's "keyed
  by axis name" framing regardless of whether any axis currently qualifies. Tests assert this
  explicitly (`alloc["seed"] == {}` and `"arm" not in alloc["seed"]`), per the addendum's warning that
  this is the assertion most likely to be missing.
- Documented the `allocation.json`/`provenance.allocation*` gap as now closed in
  `docs/superpowers/spec-defects.md` § "Six `provenance` and `results` keys ... that no code writes"
  (this file is git-ignored/untracked, so the note is local bookkeeping only, not part of the commit).

## Verification

- `uv run pytest` — 1481 passed, 2 xfailed (was 1476 passed before this task; +5 new tests).
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — success, no issues in 40 source files.
- Mutation testing (brief step 5, "write row indices rather than keys"): mutated
  `arms[axis] = {level: [u.key for u in units] ...}` to `{level: list(range(len(units))) ...}`,
  deleted `__pycache__`, ran `test_build_allocation_document_maps_axis_to_level_to_unit_keys_in_roster_order`
  and `test_allocation_json_is_written_with_exact_arm_keys_when_declared` — both FAILED on the exact
  keys (as designed: `{'control': [0,1,2,3], ...}` vs the expected key strings). Reverted, deleted
  `__pycache__` again, re-ran both — both PASSED. Verified by test behaviour, not `git status`.

## Concerns / things worth a second look

- No requirement in either brief or addendum turned out to be unsatisfiable or resting on a false
  premise, as best I could tell. The one place I had to make a call the documents didn't fully spell
  out: whether `provenance.allocation`/`.allocation_hash` needed wiring at all, since the brief's file
  list didn't mention `run.yaml`'s provenance block explicitly. `reference.md` § Allocation and § A
  fixed holdout split both state the hash "lands in `provenance.allocation_hash` beside the path" as
  a normative consequence of writing the file, and the config example (§ The one config file) already
  reserves both provenance keys with a comment naming this exact file — so I wired it in as part of
  this task rather than leaving it for a later one; flagging this in case the task split intended it
  to land elsewhere. No config/schema changes were needed since both keys were already reserved.
- I did not find an inconsistency between the brief and the addendum, or between either and the
  interfaces from tasks 10/12/13 — `arms_of`'s single-authority contract and roster-order promise
  lined up cleanly with what this task needed.

## Post-review fixes (coordinator review of task 14)

Commit: `f7a02db` — "fix: correct allocation_hash's claimed digest and document by_attribute's empty seed/strata"

Review verdict: spec ✅, quality strong; every invented mutation caught (forced `seed`, forced
`"holdout": None`, sorted keys, nulled `provenance.allocation_hash`, removed the `group_axes` gate).
Three items raised, all addressed:

1. **`allocation_hash`'s docstring described a guarantee the code doesn't have.** It claimed to hash
   "exactly the bytes written," but it hashes the *canonical* form (`sort_keys=True`, compact
   separators) of the same dict `build_allocation_document` returned — a different digest from
   `json.dumps(doc, indent=2)`, the encoding `allocation.json` is actually written as (confirmed by
   hand: for a 2-unit fixture the file-bytes hash and `allocation_hash`'s return differ, as the
   reviewer found). Rewrote the docstring to say which digest it is and the exact re-canonicalization
   a reader must perform by hand (`json.dumps(json.load(...), sort_keys=True, separators=(",", ":"))`)
   rather than hashing the file directly.
2. **`reference.md` had no normative statement for what a `by_attribute` axis writes into `seed`/
   `strata`.** The rule — omit the axis from both, because `by_attribute` reads an arm rather than
   drawing one — existed only in a docstring and two tests, leaving H3d (which edits the same file
   for `holdout`) nothing to follow. Added one sentence to § `allocation.json` — who went where,
   directly after the existing "unit keys, never row numbers" paragraph, tying the reasoning to
   § Allocation's existing statement that a `ratio` under `by_attribute` "describes a draw that
   didn't happen."
3. **Added a comment, no behavior change**, at `build_allocation_document`'s `if not group_axes:
   return None` gate: `_resolved_group_axes` warns callers against gating on its own truthiness (a
   non-`str`-`levels` axis is silently dropped), but that silent-skip case cannot reach this function
   in practice because `cli.command_run` already calls `units.arm_members` on the identical
   `group_axes` mapping earlier, outside the run directory, and `arm_members` raises `KeyError` the
   moment a condition selects an axis or level missing from it. Recorded as non-local safety rather
   than changing the gate.

Not addressed here (per the coordinator's note, these are task 15's scope): the discriminating
swap-two-units hash assertion, a stated reason `allocation_hash` lives in `artifacts.py` rather than
`hashes.py`, and the "§ Resuming's read-rather-than-re-drawn rule has no reader" statement.

### Verification after the fixes

- `uv run pytest` — 1481 passed, 2 xfailed (unchanged from before the fixes — these were
  documentation/comment corrections, no test or behavior change).
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — success, no issues in 40 source files.
- Manually verified the corrected `allocation_hash` docstring's claim: for a 2-unit fixture, the
  `indent=2` file-bytes hash and `allocation_hash`'s canonical-form hash are indeed different digests
  (`sha256:009f3081...` vs `sha256:2877206b...`), matching what the docstring now says rather than
  what it said before.
- Mechanical pass over the edited `reference.md` section: no trailing whitespace, no tabs, the
  `#allocation-within-subjects-or-between-subjects` anchor referenced in the new sentence resolves
  (grepped and confirmed against existing uses of the same anchor elsewhere in the file).
