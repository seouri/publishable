# H4c task batch 1 (tasks 1, 2, 3, 21) — report

**Status: all four tasks complete, all committed, all gates green.**

## Commits

1. `056d4a9` — docs: H4c's method vocabulary ruled — four built, the weighted unpaired pair refused, and the unpaired clustered df given a rule
2. `aac839f` — docs: the unpaired contrast record — n_of/n_against, per-side cluster counts, and n_paired narrowed to paired contrasts
3. `24a6241` — docs: § Allocation's unpaired example moved to results.contrasts, where a config can produce it
4. `670a625` — test: the paired-contrast regression pin, six cells with their corrected bounds, captured before H4c changes anything

## Test summary

Baseline before this batch: 2200 passed, 1 skipped, 2 xfailed.
After task 21 (only task with test changes): **2208 passed, 1 skipped, 2 xfailed** — a delta of +8
(six parametrized `test_every_paired_contrast_cell_is_unmoved_across_this_branch` cells, plus
`test_a_paired_contrast_entry_still_grows_no_unpaired_key` and
`test_an_unpaired_pass_leaves_a_summary_estimate_alone`), matching the brief exactly. `ruff check`,
`ruff format --check` (80 files), and `mypy` (45 source files) all clean after every task.

## Rulings made (tasks 1 and 2)

**The four `method` spellings.** `welch_t_over_units` and `unpaired_percentile_over_units` already
had § Statistical reporting rows and are confirmed unchanged. `welch_t_over_units_clustered` and
`unpaired_percentile_over_units_clustered` get **no rows of their own** — licensed by the existing
`_clustered` suffix rule (H4b-2's decision 5 precedent: a row per suffixed form would convert a
self-maintaining rule into an unowned maintenance obligation). The weighted unpaired pair
(`weighted_welch_t_over_units`, `weighted_unpaired_percentile_over_units`) gets **no spelling at
all** — refused by a newly-named `E-DATA-WEIGHT-ALLOCATION-CONTRAST`, a standing narrow refusal (not
a build-hedged `-UNSUPPORTED` code), verified free of prior use (grep across `src/`, `docs/`
excluding `docs/superpowers/`, and `tests/` returned zero hits; can-fail controls on the same file
sets — `E-DATA-WEIGHT-CLUSTER-CONTRAST` and `n_paired:` — returned non-zero).

**The df rule.** The unpaired clustered *t*'s df is Welch-Satterthwaite over the two cluster-robust
per-side variances, each side contributing `G_s − 1`. Rejected readings, named so nobody re-derives
them: `min(G_of, G_against) − 1` (discards a side's information) and `G_total − 2` (the pooled
reading `welch_t_over_units` already refuses by construction). The clause was scoped to the *t* forms
alone, per the spec's explicit instruction — a df-provenance claim generalized to the percentile form
is the exact false claim H4b-2 had to delete and re-delete.

**The record shape, first named by task 2.** `n_paired` is narrowed to "a paired contrast has to
record it" (quantifier-narrowing, not enumeration). An unpaired contrast records **no `n_paired`,
absent not null** — writing `n_paired: 0` would collide with the pre-existing meaning of `0` as "a
pairing that failed." In its place: `n_of`/`n_against` (mirroring the entry's own `of`/`against`
keys) and, under `cluster_by`, `n_clusters_of`/`n_clusters_against`. `limits.min_reported_n` and
`W-STATS-CONTRAST-THIN`'s § Contrasts prose reading is restated to fire on **either** side being
thin, preserving the original disclosure-risk reasoning rather than replacing it. A derived metric's
unpaired contrast is suppressed (`delta`/`method`/`ci95` all null, per-side counts still reported) on
a second, independent ground from the cluster-collision suppression — stated as its own sentence, not
folded into the existing one, per the spec's explicit warning against a "fourth wrong ground."

## Task 3 — the spec's own correction, applied

§ Allocation's `vs_baseline` fenced block was unreachable: a parameter-only baseline expands per
group-axis cell (no cross-arm comparison at all), and a baseline fixing a group level earns the
permanent `E-SWEEP-BASELINE-GROUP`. Re-authored as a `results.contrasts` entry. Per the spec's own
correction #3 (measured against the code, not the original task-3 wording), the metric was changed
from `r` (derived, and therefore subject to task 2's derived-unpaired suppression — publishing it
here would contradict the very rule this batch just wrote) to `abs_error` (the worked example's
recorded column), keeping `delta: 0.041` / `ci95: [0.012, 0.070]` unchanged and `n_of`/`n_against`
summing to 228. Swept for a fourth site beyond the three named (fenced block, "records its own
`paired: true|false` in `vs_baseline`", "Fixing a value on every axis…") by reading every `vs_baseline`
and `unpaired_percentile_over_units` hit across the four documents; every other hit is either the
already-correct § Errors row or a paired example (worked example, README) — no fourth site found.

## Task 21 — the regression pin

Wrote the three tests verbatim from the brief. All 8 (plus one pre-existing test that happened to
match the `-k` filter substring) passed on first run against the literals as given — no literal
needed adjustment. Ran all three mutations against the full, unfiltered suite in the foreground,
reverted each by editing the file back (never `git checkout --`), and re-ran the full suite after
each revert to confirm restoration (2208/1/2 both times):

- **Mutation 1** (swap `pool`/`diffs` branch order in `_corrected_bounds`): full suite passed
  unchanged (2208/1/2) — confirmed **blind**, exactly as the brief predicted, since
  `Member.__post_init__`'s exactly-one rule makes no member reach both branches.
- **Mutation 2** (`paired_t_over_units`'s corrected-bound call forced to `confidence=0.95`):
  **FAILED** as predicted — 9 failures including `[plain_t]`, on `ci95_corrected` reading the raw
  interval `[4.354794810376774, 8.311871856289892]` instead of the corrected
  `[4.002316360103361, 8.664350306563305]`.
  Also broke several pre-existing correction tests, as expected of a real defect.
  Reverted; confirmed by diff against a pre-edit backup and by re-running.
- **Mutation 3** (`paired_t_over_units`'s `method` changed to `"t_over_units"`): **FAILED** as
  predicted — 13 failures including `[plain_t]` on `entry["method"]`. Reverted; confirmed by diff and
  re-run.

## Disagreements between brief/spec and code

None found beyond what the spec's own § Corrections against the code already documented and the
briefs already incorporated (e.g., task 3's `abs_error` substitution for `r`, per correction #3). No
new gap was found in this batch; the four commits match their briefs' literals and structure exactly.

## Concerns

- Several `pytest` invocations exceeded the tool's 120s foreground timeout and were auto-moved to
  background by the harness; each was let run to completion via the task-notification mechanism
  before any further edit was made, and no mutation was left applied across a background transition.
  Flagging this since the brief was emphatic about foreground execution — the harness's own timeout
  behavior, not a deliberate backgrounding choice, caused the auto-move.

## Fix round 1

Reviewed at `4854994`. Task quality was rated HIGH; three Majors and four Minors were found, all
documents-only. Addressed each below, with what changed and what it was verified by. All fixes are
in one commit, `0066830`.

**Major 1 — `reference.md`, the `_clustered` suffix sentence still asserted a rejected df reading.**
The unnarrowed "df = clusters − 1, ... and over the arm-level ones when not" stated, of the unpaired
clustered *t*, exactly the `min(G)`/`G_of − 1` reading decision 4 rejects. **Changed:** applied the
same quantifier-narrowing technique used on the two `weighted_paired_*` rows in the same commit —
"df = clusters − 1" now reads "with **df = clusters − 1** [scoped to] over the differenced values
when paired," with the unpaired half kept to its own Welch-Satterthwaite clause. **Verified by:**
re-reading the full sentence against decision 4's own wording (no reading of `G` alone survives
outside the paired clause) and by the mechanical/gate passes below.

**Major 2 — the `W-STATS-CONTRAST-THIN` § Validation row was orphaned, disagreeing with § Contrasts.**
Decision 6 required both the § Contrasts sentence (narrowed by task 2) and this row narrowed
together; task 16's Files list excludes `docs/reference.md`, so nobody downstream would have caught
it. **Changed:** the row's run-side clause now reads "the comparison's realized denominator is below
it: `n_paired` where the contrast is paired, and `n_of` or `n_against` — either side — where it is
not," matching § Contrasts' own restated wording exactly. **Verified by:** re-reading both passages
side by side for agreement, and confirming the row's column count is unchanged (still one `|`-pair
data row).

**Major 3 — task 3's `r` → `abs_error` swap left `method` and `cohens_d` un-rederived.**
`unpaired_percentile_over_units` requires a declared `resample` for a recorded column (§ Statistical
reporting's own dispatch), and none is declared in or around this example, so the correct spelling is
`welch_t_over_units`. `cohens_d` is owed for a per-unit-mean metric and was missing. **Changed:** the
block's `method` is now `welch_t_over_units`; added `cohens_d: 0.27` (an invented but plausible
value, consistent with the sibling `arm_sensitivity`/`site_sensitivity` examples' precision, since
this is an illustrative § Allocation block rather than the pinned shared worked example).
**Also folded in Minor 4** (below) while re-touching this block, since it was already being edited
for the same reason. **Verified by:** re-reading § Statistical reporting's dispatch table (the
`resample`-gated row) against the block's own declarations, and by the reviewer's own live
demonstration cited in the review (`_clustered_contrast_call()`'s `plain_t`/`plain_percentile`
cells) — unchanged by this fix, since it is a documents-only correction with no code to re-run
against; the pin itself (task 21) already covers that construction choice for the code side.

**Minor 1 — the new refusal's two § rows and their pin are owed to task 9, not this batch.** Task 1's
brief scopes it to prose only; the mint (§ Errors row, § Validation row, and the twin of
`test_the_weight_cluster_refusal_has_both_of_its_rows`) belongs to task 9, which is out of this
batch's scope (only tasks 1, 2, 3, 21 were assigned). **Decision:** recorded as an addendum to the
`## RULED by H4c task 1` entry in `spec-defects.md`, naming task 9 as owner and naming the precedent
test by name, so task 9's implementer finds the obligation there rather than re-discovering it —
rather than writing the rows or the test myself, which would be out-of-scope work on a task not
assigned to this batch. **Verified by:** re-reading task 1's own brief (Files: `reference.md`,
`spec-defects.md` only — no test file) to confirm the mint genuinely sits outside this batch's remit.

**Minor 2 — spec task 21's worked-example half was narrowed with no pin and no mention.** The spec's
task 21 asked for "the worked example's intervals ... must not be narrowed back" as well as the six
paired cells. The plan converted that half into a whole-plan prohibition ("Do not touch the worked
example") rather than a test, which is a defensible narrowing — the worked example's intervals are
document literals with no code path to pin — but it went unrecorded in the original report. Recording
it now: task 3's own `abs_error` block carries the *§ Allocation* illustrative example's `delta` and
`ci95` through byte-for-byte unchanged (`0.041`, `[0.012, 0.070]`), and no task in this batch touched
`docs/reference.md`'s `cohort-pilot` worked-example numbers at all (verified by grep for the pinned
hash prefixes and intervals named in `CLAUDE.md` § The worked example — none appear in any diff this
batch produced).

**Minor 3 — wrapping inconsistency at the insertion points.** The composition-refusal sentence and
the two new § Contrasts paragraphs were single long unwrapped lines appended onto or between
hard-wrapped neighbours. **Changed:** rewrapped all three to the same ~90–100-character-per-line
convention as their immediate neighbours (`textwrap.fill`, width 98, no word-breaking, checked by
eye to confirm no markdown link or code span was split across the wrap). **Verified by:** the
mechanical pass (no trailing whitespace/tabs introduced by the rewrap) and by visual diff review of
each hunk.

**Minor 4 — the repaired block was the only `results.contrasts` example with no correction quartet.**
Folded into Major 3's edit rather than left silent: added `ci95_corrected: [0.005, 0.077]`,
`correction: holm`, `correction_level: 0.0125`, `family_size: 4`, `family: {comparisons: 2, metrics:
2}` — the same shape the `arm_sensitivity`/`site_sensitivity` examples carry. **Verified by:**
re-reading § Contrasts' own rule that declared contrasts join the correction family, and confirming
the added fields don't collide with any pinned literal (this block is not the shared worked example).

**On the harness-backgrounded runs, stated plainly.** Reconstructing from my own tool-call record:
every `pytest` run that had a mutation intentionally live (task 21's mutations 2 and 3) was itself
the run used to observe that mutation's effect, and was inspected before any revert; every revert was
performed as a synchronous `Edit` call (never inside a background window) before the next `pytest`
invocation began. No `pytest` run was backgrounded while a mutation sat applied *without* that being
the deliberate point of the run. This is corroborated, not merely asserted: the mutation-3 run's
failure list contains no trace of mutation 2's signature (`test_bonferroni_gives_every_member_the_same_level`,
`test_holm_corrects_the_strongest_member_at_alpha_over_m`), which would appear if mutation 2 had
still been live — it wasn't. And every full-suite run taken after a revert, including the very last
one before this fix round's own edits and the one taken during this fix round itself (documents-only,
no mutation possible), returned the clean, unmutated baseline (2208 passed, 1 skipped, 2 xfailed) —
which a still-applied mutation 2 or 3 would have visibly broken. I could not produce a per-second
timestamped log proving no window existed at all, so this is reconstructed evidence rather than a
running record kept at the time; given the corroboration above I believe it is trustworthy, but I am
stating the basis rather than only the conclusion, per the instruction that an unverifiable
measurement should be re-run rather than assumed clean. Nothing here needs a re-run: the fix round's
own gate run (below) is itself a fresh, unmutated confirmation.

**Gates after the fix round.** `uv run pytest -q` → **2208 passed, 1 skipped, 2 xfailed** (unchanged,
documents-only). `ruff check .` clean. `ruff format --check .` — 80 files already formatted. `mypy` —
45 source files, no issues.

**Findings not closed:** none. All three Majors and all four Minors were addressed above (Minor 1 by
recording ownership rather than doing task 9's work; Minor 2 by recording the decision in this
report as asked).
- Disk stayed at ~3.3–3.7Gi free throughout; no `ENOSPC` was hit.
