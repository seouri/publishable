# Task 15 review — stratum membership from `cli` into `summarize_step` (both paths)

Reviewed against the **amendment** (both the column and the derived path honour `strata`), not the
brief. Range `a6fe234..d715e08`. Tree at `d715e08`: **1787 passed + 2 xfailed**, `ruff check` clean,
`mypy` clean, working tree carrying only the coordinator's `progress.md` edit.

## Verdicts

- **Spec compliance: ✅** — the amendment is delivered. One declared `stratify_by` composes one
  roster-wide label mapping in `cli.command_run`, reaches `percentile_over_units`/
  `percentile_over_units_clustered` for a recorded column and `percentile_of_derived` for a derived
  metric, and moves both in the same table. `W-STATS-RESAMPLE-STRATIFY-UNHONOURED` is fully retired.
  One scope note so the ✅ is not over-read later: `run.yaml` still records **nothing** saying an
  interval was stratified — same `method`, same `resample_draws`, declared or not — and the `cli.py`
  comment hands that disclosure to the later task that records the attribute names. What this task
  closes is the *asymmetry* between the two paths, not the record's silence.
- **Task quality: approved with findings** — 2 Important, 5 Minor, no Critical. Neither Important
  blocks the construction's correctness; both are honesty/coverage gaps this task's own wiring
  created, and each should be closed or filed with a named owner before the merge gate rather than
  left in a docstring or in an untested branch.

## The statistics — verified independently

Built a reference implementation and ran it against the shipped code (banded fixture: 20 units in
[0,1), 8 in [10,11), 2 in [100,101)).

1. **Per-stratum key counts are preserved.** Instrumented `compute` over 50 replicates: every
   replicate's composition is exactly `{high: 2, low: 20, mid: 8}` with `len(table) == 30`, a single
   distinct value across all replicates.
2. **The stratified derived interval is distinguishable and correct.** Shipped code returns
   `Interval(290.45, 296.55)`; an independent reference draw reproduces `290.45 / 296.55` **to the
   digit**. Pooled is `(82.8, 602.2)`; mean-of-stratum-means × 30 is `1111.6`. The three answers are
   nowhere near each other, so the fixture cannot hide a wrong construction. Mutating the draw to
   equal counts per stratum (`n // len(pools)` per pool) **fails**
   `test_percentile_of_derived_draws_within_the_strata_it_is_given` at `1108.5 < 293.5` — the
   containment assertion is doing real discriminating work.
3. **Both paths move in one run.** Confirmed at the stats level
   (`test_summarize_step_stratifies_a_column_and_a_derived_metric_together`), at the CLI level
   (`..._reaches_the_column_and_the_derived_interval_together`), and independently by me end-to-end:
   with `report_by: [site]` crossed against `stratify_by: [cohort]`, the top-level column width goes
   30.20 → 0.092 and the top-level derived width 30.18 → 0.090 under one declaration.
4. **Label invariance holds** (`low→zzz, mid→mmm, high→aaa` returns a byte-identical `Interval`), so
   `sorted(pools.values())` delivers what the new docstring claims — untested, see Minor 2.

## Findings

### Important

**I1. The derived path publishes a zero-width 95 % interval where the column path refuses — one
table, one declaration, reachable from a config that validates clean.**
`percentile_over_units` refuses (`None`) when every stratum's pairs are identical;
`percentile_of_derived` has no such refusal (its docstring says so). All-singleton strata is reached
by a plausible declaration — any near-unique attribute. Run end-to-end through `command_run` with
`stratify_by: [tag]` where `tag` is unique per unit, 40 units:

```
COL: {'method': None,                  'ci95': None,               'resample_draws': None}
DER: {'method': 'percentile_over_units','ci95': [50.4875, 50.4875], 'resample_draws': 2000}
```

No warning fires. That is the **same asymmetry the amendment existed to prevent**, one corner over,
and it additionally violates `reference.md` § Statistical reporting's own standard — "reporting a
point with no interval is honest; a zero-width 95 % interval is not" — while `resample_draws: 2000`
asserts 2000 draws of evidence behind it. The docstring discloses the missing refusal; `run.yaml`
does not, and `spec-defects.md` has no entry.
*Not Critical*: it needs a degenerate declaration and the code does not lie in its own docstring.
*Fix*: mirror the structural refusal (every pool of size 1 ⇒ every drawn table is the input table
⇒ the metric is constant by construction, not by data coincidence) returning `None, 0`; or file a
`spec-defects.md` entry with a named owner. One or the other before the merge gate.

**I2. The clustered × stratified wiring is invisible to the whole suite.** This diff added
`strata=column_strata` to `summarize_step`'s `percentile_over_units_clustered` call — a new
production branch. Replacing that argument with `strata=None` and running the **entire** suite gives
**1787 passed + 2 xfailed**, unchanged. No test passes both `clusters=` and `strata=` through
`summarize_step`, and no config exercises `cluster_by` beside `stratify_by` end to end. The
construction itself is well covered at the function level (`tests/test_stats.py` has ~10 clustered +
stratified cases, including the constancy refusal); it is the *wiring* that no assertion can see —
the repo's own "a dimension no assertion can see" shape, and the reason the unclustered half got a
mutation and this half did not. *Fix*: one `summarize_step` test passing `clusters=` and `strata=`
together and pinning a width or an exact interval, mutation-confirmed. Cheap, and it is the only
thing standing between this branch and a silent regression.

### Minor

**M2. The new docstring's label-invariance claim has no test.** `percentile_over_units` pins its
version; `percentile_of_derived`'s "a relabelled stratum must draw the identical sequence of tables"
rests on nothing. I verified it holds by hand — so this is an unpinned guarantee, not a false one.

**M3. A docstring sentence describes `.get`, not the code beside it.** `percentile_of_derived`:
"`strata` must be total over `collapsed`'s keys, or a unit the caller could not otherwise stratify
would **silently draw as if it were unstratified**." The code indexes and raises `KeyError` — loudly,
which is the whole point and is what `test_percentile_of_derived_stratum_vector_is_indexed_not_defaulted`
pins. The standing "a docstring claiming a guarantee the code does not provide" class, in its
inverted form (claiming a weakness the code does not have).

**M4. The sentinel's collisions are undiscussed.** The `cli.py` comment justifies `<absent>` on
PyYAML NUL-safety only. A genuine attribute value `"<absent>"` is indistinguishable from a missing
one, and `|` as the joiner makes `["a|b", "c"]` and `["a", "b|c"]` produce the same label. Both are
tolerable today (labels reach no artifact) — but the comment is where a reader would look for the
answer, and the task that records stratum names in `run.yaml` inherits it. It also makes one
`reference.md` claim stale: `E-STATS-RESAMPLE-STRATIFY-VARIES`'s row says the dual-listed run-time
check in `percentile_over_units_clustered` is "normalized the identical way that function is
(`"no value"` for `None`, `str()` otherwise)" so the two checks "cannot disagree". After this task
`cli.py` composes the labels itself and **never passes a raw `None`** — a missing attribute arrives
as `"<absent>"`, so that run-time normalization is unreachable from production and the two renderings
differ. Verdicts still agree except in one corner: a cluster holding one unit with no value and one
whose value is the literal string `"no value"` validates clean and then raises
`E-STATS-RESAMPLE-STRATIFY-VARIES` at run time (contained — `summarize_step`'s `ContractError` is
caught into `W-STATS-AGGREGATE-FAILED`). A `spec-defects.md` line, and either a doc correction or a
shared sentinel.

**M5. The retry `summarize_step` (`cli.py`, after `W-STATS-AGGREGATE-FAILED`) omits `strata` with no
comment.** The comment immediately above justifies only the `resample_columns` omission at length.
Inert today (that call passes no `seed`), and the same reasoning applies — but a reader has to
re-derive it, which is exactly what the `resample_columns` paragraph exists to prevent.

**M6. The report names a method string that exists nowhere.** `percentile_over_units_derived` appears
in `task-15-report.md`; `grep` over `src/`, `docs/`, `tests/` returns zero hits — the derived
interval reports `percentile_over_units`. Report-only, no code or doc impact.

## Confirmations requested

- **Warning retirement is complete.** Emit site removed; `reference.md` § Warnings core reports row
  removed; the two `test_cli.py` pins replaced by real behaviour tests; `spec-defects.md` heading
  marked `— CLOSED` with a dated closing paragraph. `grep` across all tracked `*.md` finds the string
  only in that (historical, closed) entry and in the gitignored sdd ledger/reports. The paragraph
  after the table — "`W-ENV-UNLOCKED` is the one row above whose *firing condition* is a gap in this
  project" — is **true again** after the removal (it was arguably false while task 14's row stood);
  no count phrase near the deletion needed changing. Mechanical pass on `reference.md`: no duplicate
  anchors, every `#anchor` resolves, no trailing whitespace/tabs/invisible unicode; three table rows
  flagged by a naive column counter are escaped `\|` inside cells, pre-existing.
- **Task 1's pin stays green and reaches the changed code.** Both pins pass; a mutation defaulting
  `strata` to `{k: k}` inside `percentile_of_derived` fails both, so the pinned derived `ci95` is
  genuinely guarding the new branch.
- **`resample_draws` valuedness is unchanged by stratification.** Column two-valued: key absent when
  `resample_columns` is off (verified absent in level blocks), and **present-with-`null`** under a
  refused interval — verified by key membership, not `.get`, on the new stratified refusal
  (`'resample_draws' in block` is `True`, value `None`) — else the requested `n`. Derived
  three-valued, unchanged.
- **A `report_by` level still mints no `Member`s.** Level blocks carry no `family`, `family_size` or
  `correction` key. Positive companion in the same run: the level's derived metric carries
  `resample_draws: 2000` and a real `ci95`, so the absence is not "nothing ran".
- **`resample_strata` is gated on `declared and stratify_by` and composed once** from the roster,
  outside the condition loop; task 13's once-ness test still passes. The second conjunct is inert
  today (dropping `declared` from the gate changes no test, because an empty `stratify_by` yields one
  stratum, which reproduces the unstratified draw digit-for-digit) — and the code comment says
  exactly that rather than overclaiming.
- **A unit missing an attribute joins a stratum of its own.** The implementer was right to reject the
  brief's blank-cell fixture: `csv.DictReader` yields `""`, not `None`. The shipped fixture uses a
  genuinely short row so `attributes.get("cohort")` is really `None`, which is what makes the
  drop-mutation raise `KeyError`. `n.completed == 40` — the draw drops nobody.
- **Keys are indexed, not `.get`-ed**, on both paths; the derived path has its own `KeyError` pin.
  The column path's indexing is exercised only indirectly (the ragged-column alignment test), which
  is acceptable — the mutation the brief specified (whole-table vector) does fail there.

## `report_by` level call site — recommendation: **legitimate deferral, not a merge blocker**

Confirmed live (`report_by: [site]`, `stratify_by: [cohort]`, declared `resample`): inside one level
block, `pred` is `t_over_units` width 48.26 with no `resample_draws` key, beside `mean_pred` at
`percentile_over_units` width 0.12 with `resample_draws: 2000`. Real, and worth scheduling. But it is
not task 14's case:

1. **It is disclosed in `run.yaml`, and task 14's case was not.** Task 14 declined a stratified column
   beside an unstratified derived metric — both report `method: percentile_over_units`, and
   stratification is recorded nowhere, so nothing in the record separates them. Here the two carry
   **different method strings** and differ on the presence of `resample_draws`, which is precisely
   what § Statistical reporting's `method` field is for. A reader comparing a level's interval to the
   parent's sees `t_over_units` against `percentile_over_units` and can tell. The implementer's "same
   defect class, one layer down" is false in the load-bearing respect, and that is the reason the
   escalation does not carry.
2. **It predates the slice.** A derived metric resamples whenever `resample`/`seed` allow, declared or
   not; a level's columns have always been `t_over_units`. Every `report_by` run on `main` already
   holds that mixed table. Task 15 deepened one side; it did not create the split.
3. **The fix is a task, not a line.** Passing `resample_columns` at the level call turns a level's
   columns into percentile intervals over the level's own thinner table, pulling in
   `min_honest_draws` per level, the two-valued `resample_draws` scheme per level, and the
   `report_by`/`Member` boundary in tests. That argues for scheduling it, not for holding the gate.

**Required with the deferral:** a `spec-defects.md` entry with a named owner, alongside (or merged
with) the I1 entry — the two are the remaining honesty gaps this construction leaves.
