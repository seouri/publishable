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
- Disk stayed at ~3.3–3.7Gi free throughout; no `ENOSPC` was hit.
