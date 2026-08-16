# Task 11 report: Construction 2 — whole clusters, strata, composition

## Status: DONE

## What was built

- `src/publishable/units.py`:
  - `_stratum_groups`'s third parameter renamed `axis: str` → `declaration: str`,
    interpolated whole in its `NotImplementedError`, with the docstring paragraph
    from the brief added verbatim. All three call sites in `assignment_for`
    updated to pass `f"data.units.assign.{axis}.stratify_by"` (one via a local
    `declaration` variable to avoid nesting an f-string inside an f-string with
    the same quote character, which is a SyntaxError under Python 3.11/3.13 —
    see "Disagreement" below).
  - `holdout_for`'s combined `if strata or clusters is not None: raise
    NotImplementedError(...)` guard deleted. The `random` branch now builds
    `train_keys`/`test_keys` via: `_stratum_groups` outside (called with
    `"data.units.holdout.stratify_by"`, no `resolved`) when `strata` is set,
    `_assign_whole_clusters_by_ratio` inside each stratum (or over the whole
    roster, unstratified) when `clusters is not None`, else the unclustered
    shuffle-and-slice. Task 10's separate `train_size == 0 or test_size == 0`
    pre-check replaced by one merged coverage check over `train_keys`/
    `test_keys` after all branches, still `E-DATA-HOLDOUT-EMPTY`.
  - `holdout_for`'s docstring: the "not realized at this commit" paragraph
    replaced with the composition rules and the stated relation between the
    two constructions, exactly as the brief's Step 3(c) text.

- `tests/test_units.py`: appended the six tests from the brief (renaming every
  `_roster(...)` call to `_holdout_roster(...)`, task 10's helper — see
  "Disagreement" below), pinned the one `REPLACE` literal by running the code,
  and removed `test_a_clustered_or_stratified_holdout_raises_not_realized`
  (see "Disagreement").

## Membership literal pinned

`test_a_stratified_holdout_splits_within_each_stratum`'s `plan.test`, for
`roster = _holdout_roster(14, band=lambda i: labels[i])` (8 "big" + 4 "mid" +
2 "small"), `{"method": "random", "frac": 0.5, "stratify_by": ["band"]}`,
`seed=17`:

```
{"u2", "u5", "u6", "u7", "u8", "u11", "u13"}
```

Derived by running `holdout_for(...)` directly and printing `plan.test` — not
predicted. Per-stratum counts (4 big, 2 mid, 1 small) were verified against
`holdout_sizes(8, 0.5) == (4, 4)`, `holdout_sizes(4, 0.5) == (2, 2)`,
`holdout_sizes(2, 0.5) == (1, 1)` by hand first, matching the brief's Step 2
arithmetic exactly, before implementing.

## Test summary

- Target tests (Step 2 → Step 4): all 7 new tests pass
  (`clustered_holdout`, `constructions_are_not`, `stratified_holdout`,
  `stratified_clustered`, `thin_stratum` — 2 tests matched the last pattern).
- Task 10's holdout tests: `uv run pytest tests/test_units.py -k holdout` →
  36 passed (one of task 10's own tests needed its pinned message fragment
  updated — see "Disagreement").
- Full suite: `uv run pytest` → 1917 passed, 2 xfailed (was 1913 passed + 2
  xfailed before this task; net +6 new tests, +1 message-fragment edit to an
  existing test, −1 removed obsolete test that directly contradicted this
  task's own deliverable).
- `uv run ruff check .` → all checks passed (one `B007` unused-loop-variable
  finding in the brief's own verbatim test code, fixed by iterating
  `for name in sizes` instead of `for name, count in sizes.items()`, since
  `count` was never used).
- `uv run mypy` → no issues found in 42 source files.
- `uv run ruff format --check .` → pre-existing baseline drift only (63 files),
  none in the two files this task touched beyond what was already unformatted
  per the task instructions; not run bare, not applied.

## Mutations (Step 5) — all three discriminate as specified

- **(a)** Rerouted the unclustered `else:` branch through
  `_assign_whole_clusters_by_ratio(list(roster), weights, rng, {u.key: u.key
  for u in roster})`. Ran
  `uv run pytest tests/test_units.py -k "constructions_are_not or
  holdout_cuts"`: **both FAILED** —
  `test_the_clustered_and_unclustered_constructions_are_not_the_same_draw` on
  `set(plain.test) != set(clustered.test)` (both sides equal:
  `{'u0', 'u3', 'u4', 'u6'}`), and
  `test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes`
  on its pinned `plan.train` literal (`'u3' != 'u8'` at index 1). Reverted by
  editing the file back; re-ran both tests, confirmed passing; `diff`-verified
  the file matched a pre-mutation backup copy exactly.
- **(b)** Moved `rng = random.Random(seed)` inside the `for stratum_units in
  groups.values():` loop (and added it back to the `elif clusters is not
  None:` / unclustered `else:` branches so the name stayed defined there, since
  removing it from the top of the function would otherwise be an unrelated
  `NameError` rather than the intended mutation). Ran
  `uv run pytest tests/test_units.py -k stratified_holdout`: `1 failed, 1
  passed` —
  `test_a_stratified_holdout_splits_within_each_stratum` **FAILED only on its
  membership assertion** (`set(plan.test) == {...}`; per-stratum counts
  `4/2/1` still matched, `assert per_stratum == {...}` passed), exactly as the
  brief predicts. Reverted by editing back; re-ran; confirmed passing;
  `diff`-verified against the pre-mutation backup.
- **(c)** Changed `cut, _rest = holdout_sizes(len(stratum_units), float(frac))`
  to `holdout_sizes(len(roster), float(frac))`. Ran the same `-k
  stratified_holdout` command: `test_a_stratified_holdout_splits_within_each_stratum`
  **FAILED** on `per_stratum == {"big": 4, "mid": 2, "small": 1}` (got `{"big":
  1, "mid": 0, "small": 0}` — each stratum apportioned `holdout_sizes(14, 0.5)
  == (7, 7)`'s test count of 7, floored differently per stratum's own size, in
  this case producing 1/0/0 rather than the correct 4/2/1). Reverted by editing
  back; re-ran; confirmed passing; `diff`-verified against the pre-mutation
  backup.

After each revert, `__pycache__` directories were removed before re-running.
The final file was `diff`-verified byte-identical to a copy taken immediately
before Step 5 began.

## Disagreements between the brief and the code

1. **`declaration` interpolated into `within` (line ~2097 in the final file,
   `assignment_for`'s `blocked` branch) required a local variable, not the
   inline nested f-string the surrounding code style might suggest.** Writing
   `f"{len(_stratum_groups(list(roster), strata, f'data.units.assign.{axis}.stratify_by', resolved))}"`
   nests an f-string inside an f-string using the same quote character, which
   is a `SyntaxError` on Python < 3.12 (this repo targets `>=3.11`, and the
   ambient interpreter used for the initial edit was 3.14, which accepted it
   silently — caught only by testing on the repo's actual floor). Fixed by
   binding `declaration = f"data.units.assign.{axis}.stratify_by"` before the
   `within` expression. Not mentioned in the brief; the brief's Step 3(a) only
   described the three call sites' argument, not this syntactic constraint at
   one of them.
2. **Fixing the first `within` occurrence (inside the `if strata:` block
   nearer the top of `assignment_for`'s `blocked` branch) accidentally dropped
   the word "the" from `" within each of the {N} strata"`** during my own
   first-pass rewrite (not something the brief specified either way) — caught
   by the full suite run
   (`test_a_blocked_draw_on_an_axis_stratum_names_the_strata_when_an_arm_is_empty`
   failing on `"within each of the 2 strata of sex" in str(e.value)`), fixed
   before re-running, confirmed the full suite green after.
3. **`test_a_holdout_that_leaves_a_side_empty_raises` (task 10's test) pinned
   `f"apportions the {empty_side} side zero"`, which no longer appears** —
   task 11's Step 3(b) deliberately replaces that phrasing with `"leaves the
   {side} side empty"` when merging the two coverage checks into one, and the
   brief's own instruction ("Keep task 10's tests passing: ... confirm the
   message still names the empty side") is achievable only by updating that
   one assertion to the new phrase, since the two are mutually exclusive
   strings. Updated the assertion to `f"leaves the {empty_side} side empty" in
   str(exc.value)` and its explanatory comment; did not touch the test's
   parametrization, docstring's substantive claim, or `exc.value.code` check.
4. **`test_a_clustered_or_stratified_holdout_raises_not_realized` (task 10's
   test) is no longer true and was removed, not merely edited.** It asserted
   `NotImplementedError` with `"clustered or stratified"` in the message for
   exactly the two cases this task exists to build: a non-empty `stratify_by`
   and a `clusters` mapping. After this task's implementation, the
   `stratify_by` case now raises a *different* `NotImplementedError` (from
   `_stratum_groups`, because the fixture's stratum name `"x"` names no
   attribute the 10-unit `_holdout_roster(10)` roster carries) — so the
   *code* still matches by coincidence but the *message assertion* doesn't and
   shouldn't — and the `clusters` case (one single cluster `"c0"` holding all
   10 units) now succeeds partway through the clustered draw and then raises
   `ContractError`/`E-DATA-HOLDOUT-EMPTY` (a single whole cluster cannot split
   across both sides), not `NotImplementedError` at all. Neither outcome is
   what the test's name or docstring claims, and both are the intended
   behavior this task ships. The brief did not mention this test; I judged
   deleting it (rather than repurposing it into something else, which would
   duplicate `test_a_stratified_holdout_that_leaves_a_side_empty_across_every_stratum_raises`
   and the parametrized-in-Step-1 tests) to be correct, since a test asserting
   the pre-task-11 refusal by name is the exact "misreading a temporary
   refusal as permanent" trap this repo's CLAUDE.md documents. Flagging for
   review in case a narrower edit was preferred over deletion.

## Concerns

- None outstanding. All Step 5 mutations discriminated as the brief predicted;
  no mutation was blind.
- The `.superpowers/sdd/.gitignore` clobber (documented risk in CLAUDE.md) was
  found already in effect at the start of this session (rewritten to a bare
  `*`) — restored via `git checkout -- .superpowers/sdd/.gitignore` before
  finishing, since that file itself was untouched by me and restoring it this
  way does not discard any of my own work.
