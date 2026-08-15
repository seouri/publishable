# Task 17 report — The three retirements

## What was retired, and where

Three sites, exactly matching the addendum's correction (not one loop):

- `E-SWEEP-GROUPS-UNSUPPORTED` — the one-entry `for mode, code, why in (...)` loop in
  `validate._check_unimplemented` — deleted outright.
- `E-DATA-ALLOCATION-UNSUPPORTED` — the standalone `if units.get("allocation") not in (None,
  "within")` in `_check_unimplemented` — deleted outright.
- `E-DATA-ASSIGN-UNSUPPORTED` — the `("assign", "E-DATA-ASSIGN-UNSUPPORTED")` entry in the
  two-entry `("assign", ...), ("holdout", ...)` loop — the entry removed, leaving a one-entry
  loop (`holdout` only), with a "was here" comment matching the `cluster_by`/`weight_by`/
  `measurements` precedent already in that loop.

## A behavioral gap found and closed before retiring (not just documentation)

Removing `E-DATA-ALLOCATION-UNSUPPORTED` outright would have left an out-of-enum `allocation`
value (`allocation: sideways`) checked by nothing — this exact gap was pre-recorded in
`docs/superpowers/spec-defects.md` by task 12's reviewer, with the proposed resolution and code
name (`E-DATA-ALLOCATION-METHOD`) already specified. I implemented it: `ALLOCATION_MODES =
("within", "between")` plus a check in `_check_assign`, run before either *Allocation needs arms*
or *Arms need allocation*, so both can assume `allocation` is already one of the two. Marked
`RESOLVED (H3c, task 17)` in spec-defects.md.

**A second, previously-undocumented gap surfaced empirically while checking off masked item
GROUPS-10 ("Axis names are distinct").** `reference.md` § Validation already names this row
(`sweep.groups` declares `arm` twice), but no code backed it — because `E-SWEEP-GROUPS-UNSUPPORTED`
made the shape unreachable. I verified by direct `sweep.expand()` call that `groups: [{by: arm,
levels: [a,b]}, {by: arm, levels: [c,d]}]` crosses two same-named axes into **4 conditions
rendering only 2 distinct labels** (`arm=c`, `arm=d` — the second axis silently overwrites the
first's cell value on every combination), which `selector_paths`' own dedup hides from every
existing check. This is the exact "retirement makes a latent defect live" pattern the brief
warns about, occurring a fourth time. I added a check in `_check_sweep` (reusing
`E-SWEEP-PATH-DUPLICATE`, the adjacent sibling code, rather than minting a new one) that reads
`sweep.groups` entry-by-entry (not through the deduping `selector_paths`) and reports a `by` name
declared more than once. Added `test_two_group_axes_may_not_share_a_name`, which pins the
`sweep.expand` defect directly (4 conditions, 2 labels) plus the new validate finding, with a
two-distinct-axes control. Mutation-tested (see below).

## The 24 masked items — checked off

Per `docs/superpowers/H3c-SCOPING.md` § 1, re-verified against the code as it stands now, not
assumed from the (pre-task-7-16) scoping snapshot.

**`E-SWEEP-GROUPS-UNSUPPORTED` masked 11 things** — all 11 closed:
1. `sweep.expand` ignores `groups` — closed, tasks 2–5 (`_axes`/`PRODUCT_MODES`).
2. Execution budget undercounts — closed (budget reads `len(expand(doc))`, which now includes
   group cells).
3. `E-SWEEP-EXPANDS-EMPTY` double-report on `groups`-only — closed (task 2–5's expansion).
4. **The phantom parameter** — closed, task 4 (`resolve_condition_cfg` skips `condition.selectors`
   paths); re-verified by reading the code directly, not assumed, per the addendum's explicit ask.
5. `_swept_paths`/`AXIS_MODES` split — closed, task 5 (`PRODUCT_MODES`/`PARAMETER_AXIS_MODES`).
6. No swept-value legality check for group levels — closed (`E-SWEEP-VALUE-UNNAMEABLE` fires for
   `groups` levels; verified live in `validate.py`).
7. `check_swept_value` docstring's stale exemption argument — already correctly includes `groups`
   in the current source; no edit needed (verified, not assumed).
8. `sweep.expand`'s stale docstring claim — was never actually false in the current source; the
   `PRODUCT_MODES` docstring claim about validate-time refusal *was* stale and is fixed (see below).
9. `design_digest` covering `sweep.groups` — was already true; now observable for real.
10. **Axis names are distinct** — was NOT closed (see "gap found" above); closed in this task.
11. `AXIS_MODES` three-predicate split — closed, task 5.

**`E-DATA-ALLOCATION-UNSUPPORTED` masked 6 things** — 5 closed, 1 open (reported, not fixed):
1. `paired` hard-`True` in `cli.py` — closed by task 16b's `E-DATA-ALLOCATION-CONTRAST`; verified
   the docstring (cli.py ~595–611) still holds and does **not** name any of the three retired
   codes, so no edit was needed there.
2. No unpaired interval construction — unchanged; `E-DATA-ALLOCATION-CONTRAST` (task 16b) still
   refuses the one combination that would need one, so this stays correctly refused, not silently
   wrong.
3. `confounded`/`differs_on` parameter-axes-only — closed; `differing_axes` reads group axes too.
4. Folds drawn over the whole roster, never within a cell — closed (H3c's fold-within-cell work,
   tasks not owned by this slice's number but landed before task 17 per the interfaces table).
5. `resolved` is the whole roster per condition, never an arm — closed, tasks 12–13
   (`_cond_roster`, `_condition_counts`).
6. **No cell-population warning** (`limits.min_units_per_cell` unread) — **still open**, see
   "Findings" below.

**`E-DATA-ASSIGN-UNSUPPORTED` masked 7 things** — 6 closed, 1 open (reported):
1. `data.units.assign` bare-`dict` leaf, no per-key closure — **still open**, see "Findings" below.
2. `assign.<axis>.from` unreachable by `CONSTANT_COLUMN_RULES` — **closed, task 11**
   (`_assign_constant_columns`). My first draft of this report incorrectly flagged this as open,
   trusting the pre-task-11 scoping snapshot rather than reading `units.py` directly; caught on
   re-check and corrected before finalizing (a spec-defects.md entry was written and then deleted
   once the contradiction with the actual code was found).
3. No `E-DATA-ASSIGN-VARIES` row — **closed, task 11** (exists in `units.py`, and in
   `docs/reference.md` § Validation/registry/§ Allocation — 5 hits, not 0). Same correction as
   above.
4. `design_digest` covering `assign.seed` — closed, task 16.
5. No `assign` seed construction — closed (part of the assign/allocation build-out, tasks 12–16).
6. `allocation.json` not written — closed, task 14.
7. `W-DATA-CLUSTER-UNDECLARED`'s `assign.from` exclusion untestable — now testable and exercised
   end-to-end (`test_a_group_axis_actually_narrows_end_to_end` and neighbors reach real `assign`
   configs).

## Findings not closed by this task (reported, not silently retired on top of)

1. **`limits.min_units_per_cell` is declared, typed, and read by nothing.** § The one config file
   states the warning in the present tense with no `NOT BUILT` marker, and § Validation carries
   two rows for it (*Cells are populated*, *Allocation is coherent*) — neither has a code
   anywhere. Before this task this was inert (every `between` config that could exercise it also
   carried the now-retired blanket refusal); after this task, `allocation: between` runs for real
   and a thin cell completes with no warning, contradicting the document's own present-tense
   claim. Recorded in `docs/superpowers/spec-defects.md` with a proposed resolution.
2. **`data.units.assign`'s per-axis blocks have no unknown-key closure.** `envelope.py` still
   types `data.units.assign` a bare `dict` with no `assign.<axis>.*` entries, so a misspelled
   field inside an axis block (`stratifyy_by`, `assign.arm.form`) is silently ignored rather than
   reported — the "did you mean" treatment every other block gets. `reference.md`'s own
   `.holdout`/`.assign` "inherit the same treatment when their slices land" sentence was true
   before `.assign`'s slice landed and is not true now that it has; the sentence is corrected in
   this task's edit (§ The one config file), and the gap is recorded in spec-defects.md. Severity
   minor: the misspelled key's default still applies, so the run is well-formed under the
   default rather than wrong — not a silent-behavior-change class defect.

## Mutation testing (apply → run named test → FAIL → revert → confirm PASS, `__pycache__` cleared each time)

- `_cond_roster` forced to always return the whole roster →
  `test_a_group_axis_actually_narrows_end_to_end` FAILED (wrong `resolved`/`failed` counts);
  reverted, both group-axis end-to-end tests PASS.
- `E-DATA-ALLOCATION-METHOD`'s `if` gated `False and ...` →
  `test_an_out_of_enum_allocation_is_refused_by_its_own_check` FAILED; reverted, PASS.
- The new `sweep.groups` `_check_shape` guard removed entirely →
  `test_a_malformed_groups_entry_is_a_shape_fault` FAILED; reverted, PASS.
- The new duplicate-`by` threshold changed from `> 1` to `> 999` →
  `test_two_group_axes_may_not_share_a_name` FAILED; reverted, full suite PASS (1488 passed, 2
  xfailed).

## `docs/reference.md`

- § The one config file: count sentence "Seven declarations … NOT BUILT" → "Four", enumeration
  reduced to `holdout`, the `{resolver:}` form, `resample`, `null_test`; `NOT BUILT` markers
  removed from the `allocation`, `assign`, and `groups` inline comments; the `.holdout`/`.assign`
  closure sentence corrected to say `.assign`'s slice landed without the closure (see Finding 2).
- § Errors `validate` reports: new row for `E-DATA-ALLOCATION-METHOD` (alphabetically before
  `E-DATA-ALLOCATION-NO-ARMS`), `E-DATA-ALLOCATION-WITHIN-ARMS`'s row edited to point at the new
  code instead of the retired blanket refusal, `E-SWEEP-PATH-DUPLICATE`'s row extended to name
  its new entry-by-entry group-axis use.
- § Validation: new row *Allocation is a known value* before *Allocation needs arms*.
- The `W-STATS-REPORTBY-THIN` "recorded gap" paragraph (§ What isn't a repeat) updated from
  "unreachable while … draws `E-SWEEP-GROUPS-UNSUPPORTED`" to "reachable now" — this one was
  outside the addendum's own code-name grep (it named the concept, not the code, in one spot the
  addendum's sweep didn't check) and would have been missed by a grep-only pass.
- The worked example (`cohort-pilot`) is untouched — it declares no `groups`/`allocation`/`assign`,
  and none of its numbers moved.

## Tests

- `tests/test_cli.py`: the two `monkeypatch.setattr(validate_mod, "_check_unimplemented", ...)`
  end-to-end tests simplified per their own docstrings' request — patch removed, docstrings
  rewritten to say why it's no longer needed; both re-verified to still fail under the
  `_cond_roster` mutation. Three unit-level tests on extracted functions
  (`_wide_swept_paths`, `_resolved_group_axes`, `_report_by_levels`) had their "untestable because
  refused" docstrings corrected to state what they actually are now (focused unit tests beside
  the end-to-end coverage) without deleting them — they still pin exact behavior more directly
  than a full run's aggregated output would.
- `tests/test_validate.py`: ~40 assertions naming one of the three codes updated. One-row
  parametrize tables that documented only the retired family were removed
  (`test_each_unimplemented_mode_is_refused_on_its_own`,
  `test_every_sweep_refusal_message_defers_rather_than_scolds`) or converted to a plain function
  (`test_each_unimplemented_units_subfield_is_refused_on_its_own` → `test_holdout_is_refused_on_its_own`,
  the one row left). New tests added:
  `test_groups_is_accepted_and_expands_for_real`,
  `test_an_out_of_enum_allocation_is_refused_by_its_own_check`,
  `test_a_malformed_groups_entry_is_a_shape_fault`,
  `test_two_group_axes_may_not_share_a_name`. No exact-set assertion was weakened to a membership
  test; where a set now empties (`test_by_attribute_assignment_is_accepted` and
  `test_between_allocation_with_a_group_axis_draws_neither_arms_row`'s second half), it is
  checked and correct that the config validates clean, with the adjacent test
  (`test_assign_levels_is_reported_through_a_real_validate_config`) serving as its can-fail
  control.

## Verification

- `uv run pytest`: 1488 passed, 2 xfailed.
- `uv run ruff check .`: all checks passed.
- `uv run mypy`: no issues found (40 source files).
- Tracked-`*.md` grep for the three codes returns exactly one hit
  (`docs/reference.md`'s `W-STATS-REPORTBY-THIN` paragraph), which is a retrospective "no longer
  draws" mention, not a live refusal claim — demonstrated against the positive control
  `E-DATA-HOLDOUT-UNSUPPORTED` (still present, still live) to prove the grep itself can fail.

## Files touched

- `src/publishable/validate.py` — the three retirements, `E-DATA-ALLOCATION-METHOD`,
  `sweep.groups` `_check_shape` guard, duplicate-`by` check, docstring corrections.
- `src/publishable/sweep.py` — one stale docstring claim fixed (`PRODUCT_MODES`).
- `src/publishable/cli.py` — four stale unreachability claims fixed/rewritten.
- `docs/reference.md` — count/enumeration, two new registry rows' worth of edits (one new row,
  one extended row), one new § Validation row, `NOT BUILT` markers removed, `W-STATS-REPORTBY-THIN`
  paragraph corrected.
- `tests/test_cli.py`, `tests/test_validate.py` — as described above.
- `docs/superpowers/spec-defects.md` (gitignored, not part of the commit) — out-of-enum-allocation
  entry marked RESOLVED; the mistaken CONSTANT_COLUMN_RULES/VARIES entry written then corrected to
  a CONFIRMED-CLOSED note; two new open findings recorded (`min_units_per_cell`,
  assign unknown-key closure).

## Addendum — coordinator review, second pass (commit `b7af7a5`)

The coordinator's review confirmed the retirement, the `seven → four` edit, the grep-with-control,
and the ~40 exact-set assertions, and independently re-verified both "ship silently" masked items
by probe. It also confirmed the duplicate-`by` catch was **worse** than my first report said — the
first axis's levels are entirely erased (`['arm=c','arm=d','arm=c','arm=d']`, two byte-identical
label pairs, not just "collapsed to fewer labels") — and that the fix survives a stronger mutation
(deleting the whole `by_names` accumulation) than the one I ran. No code change was needed for
that; only my report's description of severity undersold it.

One methodological gap it named: I ran a concept-level sweep on the *docs* (which is how
`W-STATS-REPORTBY-THIN` was caught) but only a code-name grep on `src/`, missing three
grep-invisible items. All three fixed, commit `b7af7a5`:

**Required 1 — `materialize.py` scaffolded a falsified claim into every new project.** `init` wrote
`allocation: within  # within  (between: later slice)`, and `tests/test_materialize.py` locked that
string in via `_MARKED_LATER_SLICE`/`_MARKED_FIELD_PATHS` — a mechanism that parses `(x: later
slice)` markers out of the rendered config and asserts each marked value is genuinely refused.
`H3c-SCOPING.md` § 6 listed this as owed work with no task claiming it. Fixed: the comment now
reads `within | between`; `allocation` removed from `_MARKED_FIELD_PATHS` (its marker is gone
because the claim is gone, not because the marker mechanism regressed — the dict's remaining entry,
`kind`, still round-trips through the same test). `test_the_generated_units_block_carries_its_comments`
updated to match. Verified: `test_materialize.py` — 19 passed.

**Required 2 — hedge `min_units_per_cell`, don't implement it.** Per the coordinator's ruling: the
warning was never built for `within` designs either, so this task makes a pre-existing gap
*reachable*, not one it introduces — implementing a `W-` code is out of scope (limits family).
Hedged three places the way `Assignment method isn't drawn`/`Allocation deltas aren't computed`
already are ("specified, not built in this build"): the `min_units_per_cell` inline comment, and
both § Validation rows (*Cells are populated*, *Allocation is coherent*). Checked, not assumed,
that this doesn't perturb the "Four declarations… NOT BUILT" count: that sentence marks *refused
declarations*, and `min_units_per_cell` is a `limits` value that is never refused (any int
validates), only its promised *warning* is unbuilt — a different category, confirmed by grep
(`min_units_per_cell` is not among, and was never among, the four enumerated).

**Required 3 — replaced a false `cli.py` comment with the real divergence.** The claim that
`levels: []` would silently skip arm narrowing was probed and found vacuous:
`expand({"groups": [{"by": "arm", "levels": []}]})` returns **zero** conditions, so
`E-SWEEP-EXPANDS-EMPTY` already refuses it — the clause was never reachable. Substituted the
live case the coordinator identified and I confirmed by direct probe: `by: ""` passes
`selector_paths`'s `isinstance(by, str)` (so `expand` renders real conditions,
`Condition.selectors == {""}`, labelled `=a`/`=b`) but fails `_resolved_group_axes`'s `not axis`
check (empty string is falsy), so `command_run`'s gate-on-`selector_paths`-not-`group_axes` design
is what catches the disagreement as `arm_members`'s own `KeyError` rather than a silent
whole-roster fallback. The conclusion the comment reached was already correct; only its example
was invented rather than probed. Left the neighboring `_resolved_group_axes` docstring's
`levels: [1, 2]` example untouched — confirmed still literally true, not a false claim, per the
coordinator's own read.

**Recommended (non-blocking), all done:**
- Two stale `tests/test_validate.py` docstrings claiming a config avoids "the refusal `groups`
  still gets" (`test_paired_is_accepted_and_expands_for_real`,
  `test_ablate_is_accepted_and_expands_for_real`) — `groups` lost that refusal in this task, so
  both rewritten to say so. A third, adjacent stale docstring found by the same
  `grep groups tests/` sweep (`test_the_four_refused_modes_are_known_keys_not_unknown_ones`,
  claiming all four modes "are refused by `_check_unimplemented`") fixed too.
- The new `E-DATA-ALLOCATION-METHOD` registry row's "checked before either row below runs" —
  a positional table-row reference — renamed to name the two codes directly
  (`E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ALLOCATION-WITHIN-ARMS`).
- `E-CONFIG-SHAPE`'s registry row's container enumeration (pre-existing incomplete — omits
  `paired`/`ablate`/`sample` already, unfixed, out of scope) extended to name the new
  `sweep.groups` walk this task added, so as not to make the existing incompleteness worse.

Re-verified after these changes: `uv run pytest` — 1488 passed, 2 xfailed; `ruff check .` — all
checks passed; `mypy` — no issues (40 source files); tracked-`*.md` grep for the three codes —
still exactly the one retrospective `W-STATS-REPORTBY-THIN` mention, control (`E-DATA-HOLDOUT-
UNSUPPORTED`) still non-empty.

Commits: `f71b1d4` (original retirement), `b7af7a5` (review fixes).
