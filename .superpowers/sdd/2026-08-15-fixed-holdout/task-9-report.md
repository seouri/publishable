# Task 9 report: `holdout.from`'s constant-column accessor

## Status: DONE

## What was built

- `src/publishable/units.py`:
  - Added `_holdout_constant_column(holdout_decl) -> dict[str, str]`, gated on
    `method == "by_attribute"`, returning at most `{"holdout.from": <column>}`.
  - Added the `"holdout"` entry to `CONSTANT_COLUMN_RULES`, carrying
    `E-DATA-HOLDOUT-VARIES`, inserted after `"assign"`.
  - `resolve_units` now calls `constant.update(_holdout_constant_column(units_decl.get("holdout")))`
    between `_assign_constant_columns`'s entries and the flat-pair comprehension —
    the documented severity order (`assign` worst, then `holdout`/`cluster_by`
    tied by fiat, then `weight_by` last).
  - Rewrote the two present-tense "not reachable" comments/docstring passages
    (in `resolve_units` and in `CONSTANT_COLUMN_RULES`'s docstring) to describe
    the accessor that now exists.
  - Also updated `CONSTANT_COLUMN_RULES`'s opening docstring sentence, which
    said "**Three codes, not one**... each says a different thing about what
    breaks" — literally false the moment a fourth code was added whose damage
    description is deliberately identical to `cluster_by`'s. Rewrote to "Four
    codes, not one" and carved out `holdout` as the stated exception (same
    damage as `cluster_by`, separate code only because one identifier would
    send a reader naming the other to the wrong section).
- `src/publishable/validate.py`: replaced the falsified `_check_units`
  docstring sentence ("`cluster_by`, `weight_by`, and `holdout` are not read by
  `resolve_units` at all") with the brief's corrected text distinguishing
  `allocation`/`assign`'s method (truly unread) from the three that are read
  only where a `measurements` collapse could file a unit by row order.
- `tests/test_units.py`: added `_assign_constant_columns`/`_holdout_constant_column`
  to the import list, and appended the brief's five tests verbatim
  (`test_a_holdout_from_column_varying_within_a_unit_is_refused`,
  `test_a_constant_holdout_from_column_collapses_cleanly`,
  `test_the_holdout_accessor_resolves_no_column_for_these` (8 parametrized
  cases), `test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair`).
  Also added one test the brief did not ask for — see "Disagreement" below.

## Step 5 mutations, run as instructed

**(a)** Deleted the `method == "by_attribute"` gate in `_holdout_constant_column`.
Ran `uv run pytest tests/test_units.py -k holdout_accessor`:

```
FAILED tests/test_units.py::test_the_holdout_accessor_resolves_no_column_for_these[random with a stray from]
AssertionError: assert {'holdout.from': 'split'} == {}
1 failed, 7 passed, 167 deselected
```

FAIL as predicted. Reverted by editing the file back (re-added the gate line),
re-ran: `8 passed, 167 deselected` — confirmed revert by re-running the test,
not `git status`.

**(b)** Moved `constant.update(_holdout_constant_column(...))` in `resolve_units`
to after the flat-pair `constant.update({...})` block. Ran
`uv run pytest tests/test_units.py -k holdout_rule`:

```
tests/test_units.py::test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair PASSED [100%]
1 passed, 174 deselected
```

**This is a PASS, not the FAIL the brief predicts** — see Disagreement below.
I also ran the full `tests/test_units.py` file under this mutation: `175 passed`,
zero failures anywhere in the suite. Reverted by editing the file back (restored
original insertion order), diffed against a pre-mutation backup copy
(`/private/tmp/.../scratchpad/units.py.bak`) to confirm byte-identical revert,
then re-ran `tests/test_units.py`: `176 passed` (176, not 175, because of the
test I added to close the gap — see below).

## Disagreement with the brief (verified, not assumed)

`test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair`, copied
verbatim from the brief, builds its `constant` mapping **by hand** in the test
body (`_assign_constant_columns(...)`, then `.update(_holdout_constant_column(...))`,
then `.update({"cluster_by": ...})`) and passes that mapping straight to
`collapse_measurements`. It never calls `resolve_units`. So Step 5(b)'s mutation
— reordering `resolve_units`'s own `constant.update` calls — cannot touch this
test's outcome, and empirically does not: with the mutation in place the test
still passes, and so does every other test in `tests/test_units.py` (175/175).
The dispatching agent's "Verified before dispatch" note claims this mutation
discriminates; it does not, because the pinned test only proves
`collapse_measurements` stops at the first key of whatever dict it is handed —
an already-covered property — not that `resolve_units` builds that dict in the
documented order. This is the exact "seam named in the brief and instantiated
by no fixture" shape `CLAUDE.md` warns about.

I closed the gap rather than leaving it, by adding
`test_resolve_units_checks_holdout_after_assign_and_before_cluster` (placed
after `test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code`,
which is the existing precedent for this exact style — it does the same thing
for `assign` vs. `cluster_by` alone via a real `resolve_units` call). The new
test declares `assign`, `holdout`, and `cluster_by` together over one
`measurements`-collapsing unit whose `arm`, `split`, and `site` columns all
disagree between its two rows, calls `resolve_units` directly, and asserts
`E-DATA-ASSIGN-VARIES`; then again without `assign` declared, asserting
`E-DATA-HOLDOUT-VARIES`. I verified this new test **does** discriminate: with
mutation (b) reapplied, it fails on its second assertion exactly as the brief
predicted for the original test (`E-DATA-CLUSTER-VARIES` instead of
`E-DATA-HOLDOUT-VARIES`), and passes clean after reverting.

No other disagreements found — the reference.md § Errors row for
`E-DATA-HOLDOUT-VARIES` (already present, presumably from task 1) already
described exactly what this task's emit site does, so no document change was
needed there.

## Verification

- `uv run pytest tests/test_units.py -k "holdout_from or holdout_accessor or holdout_rule"` — 11 passed (Step 2/4).
- `uv run pytest` — 1891 passed, 2 xfailed (baseline 1879 + 12 new: 11 from the
  brief's tests plus the 1 integration test I added).
- `uv run ruff check .` — All checks passed.
- `uv run ruff format --check .` — 3 files would be reformatted
  (`units.py`, `validate.py`, `test_units.py`), all pre-existing baseline
  non-conformance per the brief's own warning; confirmed none of my new lines
  are additional reformats beyond that baseline shape (the same style as
  surrounding untouched code in each file). Did not run bare `ruff format .`.
- `uv run mypy` — Success: no issues found in 42 source files.
- Sweep: `grep -rn "not read by" src/publishable/*.py` — one hit, the corrected
  sentence in `validate.py`. `grep -rn "holdout.from" src/ docs/` — every
  present-tense "unreachable" claim is gone from `src/`; the historical
  "not reachable" quotes remain only in the tracked development record
  (`docs/superpowers/plans/`, `docs/superpowers/specs/`, `docs/superpowers/H3d-SCOPING-2.md`),
  which CLAUDE.md says must not be retro-edited. Proved the sweep can fail: it
  returns hits for `_holdout_constant_column` itself (`units.py` accessor
  definition, its docstring, its call site, its return statement).

## Commit

`bf27897` — `feat: give holdout.from its own constant-column accessor`

Files touched: `src/publishable/units.py`, `src/publishable/validate.py`,
`tests/test_units.py`. Also restored `.superpowers/sdd/.gitignore`, which
`scripts/task-brief` had clobbered to a bare `*` before this task started
(noticed via `git status`, restored via `git checkout .superpowers/sdd/.gitignore`
— the tracked, correct content — not a mutation of my own work).

## Correction (2026-08-16, closing review findings)

The closing line above — "the reference.md § Errors row for `E-DATA-HOLDOUT-VARIES`
… already described exactly what this task's emit site does, so no document change
was needed there" — overstates what task 1's row covered. The task-9 review found
two gaps that row left: (1) `"holdout"`, once added as a `CONSTANT_COLUMN_RULES`
key, also admitted a bare-string `data.units.holdout` through `resolve_units`'s flat
comprehension, an emit path (message spelling `data.units.holdout`, no `.from`) the
row never described and no test pinned — closed by excluding `holdout` from that
comprehension rather than documenting a second route, since the accessor was built
to be the only one; (2) the row omitted that `validate` also reports this code
through the resolution it performs, unlike its three dual-listed siblings — a gap
this task's own emit site made real and so this task's to close. Both are fixed as
part of closing that review. The row did describe the `holdout.from` accessor path
correctly; it did not describe the flat-comprehension path this task's registry
entry also opened, nor the `validate`-reporting fact.
