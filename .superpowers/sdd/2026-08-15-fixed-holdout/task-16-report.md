# Task 16 report: `W-STATS-RESAMPLE-CLUSTERS` against the test partition

## Status

DONE

## Commit

`30f18b2` — `fix: count a resample's clusters over the holdout's test partition`

## What was built

`src/publishable/validate.py`: added `clusters_of`, `holdout_for`, `holdout_seed_for` to the
`publishable.units` import list and `design_digest` from `publishable.hashes` (new import, no
cycle — `hashes.py` imports only the standard library). Added `_holdout_test_roster(doc,
units_decl, roster, cluster_by) -> UnitList | None`, verbatim from the brief, immediately before
`_check_resample`. In `validate_config`, resolved `holdout_test = _holdout_test_roster(doc,
units_decl, roster, usable_cluster)` immediately after `basis` is resolved (before
`_check_fold_stratify_by`), and changed the `_check_resample` call to pass
`holdout_test=holdout_test`. In `_check_resample`, added the `holdout_test` keyword parameter and
changed the `W-STATS-RESAMPLE-CLUSTERS` count from `fold_basis(roster, cluster_by)` to
`fold_basis(holdout_test if holdout_test is not None else roster, cluster_by)`. Left
`E-STATS-RESAMPLE-STRATIFY-VARIES` reading `roster` unchanged, with a docstring sentence saying
why (constancy over the whole roster implies it over any subset; the narrower read would let a
config validate whose training half is incoherent).

`tests/test_validate.py`: appended the brief's two tests verbatim
(`test_the_resample_cluster_warning_counts_the_holdout_s_test_partition`,
`test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn`) and its third,
`test_the_stratum_constancy_check_still_reads_the_whole_roster` — but corrected that third test's
docstring, which made a false claim about its own fixture (see below).

`docs/reference.md` § Errors: updated the `W-STATS-RESAMPLE-CLUSTERS` row to say the count is
"over `data.units.holdout`'s realized test partition when one is declared, the roster otherwise" —
the check's behavior changed, so the row had to change with it. The two
`E-STATS-RESAMPLE-STRATIFY-VARIES` rows needed no edit; they already describe a whole-roster read
and stay true.

## The under-warning fixed, on a concrete fixture

100 units in 50 clusters of 2 (`cluster_by: animal_id`), `limits.min_clusters: 20`,
`data.units.holdout: {method: random, frac: 0.2}`. Old check: `fold_basis(roster, ...)` = 50 (the
whole roster), `50 >= 20` → silent. New check: `fold_basis(holdout_test, ...)` = 10 (the realized
test partition at this seed, confirmed directly against `holdout_for`), `10 < 20` → fires. That is
a 5x under-count in the direction the brief names — roughly `1/frac`. The companion fixture
(`frac: 0.8`, test side ~40 clusters) stays silent under both old and new code, confirming the fix
is attributable to the partition read, not to "warn whenever a holdout is declared."

## Mutations run

All reverted by editing the file back (never `git checkout --`), `__pycache__` deleted between
runs, each revert verified by re-running the affected test(s). A final `diff` against a
post-implementation backup of `validate.py` confirmed byte-identical restoration before committing.

**(a) Brief's — revert the `fold_basis` argument to `roster`.** Result: **FAIL** —
`test_the_resample_cluster_warning_counts_the_holdout_s_test_partition` failed on `assert
"W-STATS-RESAMPLE-CLUSTERS" in with_holdout` (nothing fired, since 50 ≥ 20 again).
`test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn` still passed. Reverted; both pass
again.

**(b) Brief's — change `_holdout_test_roster`'s return to select `plan.train`.** Result: **FAIL —
both tests**, not the one the brief predicted. `test_a_holdout_wide_enough_to_keep_the_clusters_does_not_warn`
failed as the brief said (train side at `frac: 0.8` is ~10 clusters, below 20, so it now warns).
But `test_the_resample_cluster_warning_counts_the_holdout_s_test_partition` also failed: at `frac:
0.2` the train side is ~40 clusters (verified directly: `clusters_of` + `holdout_for` at this
digest/seed gives test=10, train=40), which is *above* 20, so the warning goes silent exactly where
the test expects it to fire. **This is a real disagreement with the brief**, which claimed this
test "must PASS" under mutation (b) and reasoned that "a single-config fixture cannot tell 'counts
the test side' from 'counts the smaller side'" — true of a single config, but the frac-0.2 fixture
by itself already distinguishes "test" from "train" (10 vs. 40), so it fails under the train
mutation same as the frac-0.8 one does under the reverse. Both companion tests are needed, as the
brief says, but for a stronger reason than stated: each one independently rules out the *opposite*
partition, not just the smaller-side reading. Reverted; both pass again.

**(c) Mine — narrow the `E-STATS-RESAMPLE-STRATIFY-VARIES` check to the test partition too.**
Result: **PASS — an honest negative, not a failure.** Narrowing
`stratum_varies_within_cluster(roster, ...)` to `holdout_test` left
`test_the_stratum_constancy_check_still_reads_the_whole_roster` passing unchanged. I verified this
wasn't a mistake in my mutation by computing the fixture's realized partitions directly
(`clusters_of` + `holdout_for` at seed 1234): the 40-unit fixture's label column is `'y'` for even
`i` and `'x'` for odd `i`, and each cluster is `{2k, 2k+1}` — so **every** cluster carries one `x`
and one `y`, not only the training-side ones the test's docstring claimed. `stratum_varies_within_cluster`
reports an offender on the whole roster (`a0`), on the training side alone (`a0`), and on the test
side alone (`a2`) — a violation exists on both partitions, so this fixture cannot distinguish "reads
the whole roster" from "reads the test partition only." Reverted the mutation; the test still
passes on the un-mutated code, as it did before.

Given the check itself is correctly unchanged (per the brief's own argument, which stands
independently of this fixture), I did not invent a new fixture to force a discriminating case.
Instead I corrected the test's docstring, which asserted a false guarantee about its own fixture —
exactly the recurring defect shape CLAUDE.md names ("A comment or docstring claiming a guarantee the
code does not provide"). The corrected docstring states what the fixture actually does (every
cluster varies), what mutation (c) showed (narrowing here is a no-op for this fixture), and that the
test's real content is narrower than its name: it proves the check still fires once a holdout is
declared, not that it reads the whole roster specifically. That claim rests on the code and this
report, not on an assertion in the test file.

## Test summary

`uv run pytest` — 1945 passed, 2 xfailed (1942 baseline + 3 new tests). `uv run ruff check .` and
`uv run mypy` clean (42 source files). `uv run ruff format --check .` shows only pre-existing drift
(63 files), none introduced by this task's own new lines.

## Where the brief disagreed with the code

One disagreement, found by running mutation (b) rather than trusting its predicted outcome: the
brief asserts `test_the_resample_cluster_warning_counts_the_holdout_s_test_partition` (frac 0.2)
would still **pass** under the train-side mutation. It does not — see mutation (b) above. The
frac-0.2 and frac-0.8 fixtures each independently rule out the opposite partition reading, which is
a *stronger* justification for needing both tests than the brief gave, not a weaker one; the fix
itself, and both tests as written, are correct.

A second, smaller disagreement: the brief's third test's docstring claimed a false fact about its
own fixture (only training-side clusters vary). Corrected in `tests/test_validate.py` rather than
left standing; see mutation (c) above for the verification.

## Process notes

`.superpowers/sdd/.gitignore` was clobbered to a bare `*` (the standing `scripts/sdd-workspace` /
`task-brief` behavior CLAUDE.md documents) when this task's brief was read. Restored via `git
checkout -- .superpowers/sdd/.gitignore` before committing — safe here, since that file carried no
uncommitted content of its own and `git diff` showed nothing remaining against it afterward.

## Concerns

None outstanding. `E-DATA-HOLDOUT-UNSUPPORTED` is still asserted alongside the new warning in both
brief tests, never in place of it, and the assertion is a one-line deletion when task 18 retires
that code.
