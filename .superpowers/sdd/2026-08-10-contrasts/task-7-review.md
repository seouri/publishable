# Task 7 review: Contrasts reach the record

Reviewed from `.superpowers/sdd/2026-08-10-contrasts/review-a79829d..08ba1eb.diff` (two
commits, `5349b0e` then `08ba1eb`) plus `git show 08ba1eb:<path>` for context the diff
elides. The suite was not re-run; the coordinator's figures are taken as given (673
passed, ruff clean, mypy clean). All line numbers below are at `08ba1eb`, not the
working tree.

## Verdicts

- **Spec compliance: ✅**
- **Task quality: findings** — two Important, four Minor. Nothing blocking a merge on
  correctness of the documented worked example; both Importants are about a reachable
  silent-wrong-number path and a missing test on the codepath Critical 1 lived in.

## The two Criticals, verified

### Critical 1 — the shared `compute` cancelled

**Fixed, and the pairing survived.** `stats.py:252-253` now takes `compute_of` and
`compute_against`. The draw is still *one* draw: `stats.py` builds a single `drawn` key
list per iteration and derives both `table_a` and `table_b` from it, then differences
once (`a = compute_of(table_a)` / `b = compute_against(table_b)` at lines 292-293). The
feared worse-than-the-bug fix — splitting the draw so each side resamples independently
— did not happen, and the existing guards that prove it are untouched and still passing
their own tests: `test_the_paired_interval_is_narrower_than_two_independent_draws` and
`test_a_constant_offset_gives_a_genuinely_zero_width_interval` (a point-mass paired
interval is only reachable when both sides see the same draw).

The call site is genuinely two closures, not one passed twice: `resample_fns_by_key` is
populated inside the per-condition loop from `_make_resample_fn(key, cond_cfg, template)`
(`cli.py:736-740`), so each entry closes over *that condition's* resolved `cfg` — which
is exactly the object a swept `analysis.method` differs on.
`_comparison_step_blocks` reads `(comp.of, step_name)` and `(comp.against, step_name)`
separately (`cli.py:246-252`) with no fallback from one side to the other, and skips the
interval entirely when either side is missing.

The nine `test_stats.py` call sites updated to pass the same callable twice are all cases
where the same statistic on both sides is the genuine intent; none of them lost coverage.

### Critical 2 — declared contrasts validated clean and produced nothing

**Fixed.** `results.contrasts` is built by `_compute_declared_contrasts`
(`cli.py:367-430`) and attached in `run_record.py:152-153` as a sibling of
`results.conditions`, absent (not `[]`) when nothing was declared.

Checked field for field against `docs/reference.md` § Contrasts (the `results.contrasts`
example, ~2076-2085):

| Doc | Implementation |
|---|---|
| `results.contrasts` a list beside `conditions` | `out["contrasts"] = contrasts`, `run_record.py:152` |
| `id: invariance` | `entry["id"] = comp.id` |
| `of: 04_occasions=3` — "recorded with its index; declared without one" | `condition_dir_name(comp.of, label)` → `01_method=spearman`, `cli.py:423-426` |
| `against: 06_occasions=12` | same call for `comp.against` |
| `step03_screen:` as a *sibling* key of `id`/`of`/`against`, not nested under `steps` | `entry.update(block)`, `cli.py:428` |
| `prob: {delta, basis, paired, method, n_paired, ci95, …}` | all present; `correction: null` and no S4c keys |

`condition_dir_name` is `f"{index:02d}_{label}"` (`sweep.py:133`), the same string the
run's own `conditions/` directories use, so the index prefix is the documented one rather
than a second spelling of it.

## Construction chosen by metric origin

Both paths verified in `_comparison_step_blocks`:

- **Recorded column** (`cli.py:288-302`): per-unit differences over `paired_keys`,
  narrowed per column to units where the key is present on both sides, then
  `paired_t_over_units(diffs)` and `cohens_d = cohens_dz(diffs)`.
- **Derived** (`cli.py:244-282`): `paired_percentile_of_derived` with each side's own
  closure, and `"cohens_d": None` as a *literal* at `cli.py:278`.

The choice is `is_derived = metric_key in of_derived or metric_key in against_derived`
(`cli.py:245`) — membership in what `aggregate` returned, i.e. the metric's origin, not a
flag. `cohens_d` cannot become a number on the derived branch: the literal is the only
assignment, and `cohens_dz` is not reachable from that branch. Note the guard is *code*,
not test — see Important B.

`delta` for a derived metric is `of.value − against.value` (the two unresampled
`aggregate` calls), not a resample mean — correct: the point estimate is each side's own
formula on its own full table.

A pleasing consequence worth keeping: with an empty intersection, `mean_of([])` returns
`None` and `paired_t_over_units` returns `None`, so the entry records `delta: null`,
`ci95: null`, `n_paired: 0` — which is `reference.md` § Contrasts' "a contrast whose
intersection is empty is reported as such rather than as a delta of zero", satisfied by
construction rather than by a special case.

## What this slice must not add

Confirmed clean. `grep` over `08ba1eb:src/publishable/cli.py` for `ci95_corrected`,
`correction_level`, `family_size`, `"family"` matches exactly one line — `cli.py:228`, a
docstring saying those are S4c's. Every entry records `"correction": None`
(`cli.py:279`, `cli.py:301`). `validate.py` is not in the diff at all, so
`W-STATS-FAMILY` (`validate.py:938`) and its message are byte-identical.

## The regression guard: no baseline, no contrasts → no `vs_baseline`

Three structural layers, each of which alone would suffice, which is why the report's
fourth test matters:

1. `_compute_vs_baseline` returns `None` when `roster is None`, when
   `_baseline_comparisons` is empty (no baseline → `resolve_contrasts` emits no
   auto-generated comparison, and `_baseline_comparisons` short-circuits on
   `baseline is None`, `cli.py:161-163`), and finally `return out or None`
   (`cli.py:364`) when every comparison produced an empty block.
2. `_comparison_step_blocks` only sets `block[step_name]` `if metric_block`
   (`cli.py:311`), so a step with no differenceable metric contributes nothing.
3. `run_record.py:116-120` attaches the key only `if block`.

`test_a_run_with_no_baseline_has_no_vs_baseline_block` (`test_cli.py:812`) is
over-determined and would pass with layers 1c/2/3 all deleted; the implementer's
self-added `test_a_baseline_sweep_with_no_metric_has_no_vs_baseline_block`
(`test_cli.py:820`) is the one that actually exercises `return out or None` and the
`if block:` guard. Adding it was correct and is the strongest single judgement call in
the submission.

## `min_reported_n`

Real now: `W-STATS-CONTRAST-THIN` (`cli.py:305`) fires when `n_paired < min_reported_n`
(`cli.py:303`), inside the per-metric loop, and applies to `n_paired` specifically —
not to a condition `n`. It is produced by a test, `test_a_thin_pairing_warns`
(`test_cli.py:841`), which runs a real baseline sweep at `units=3` with
`limits: {min_reported_n: 10}`. The identifier is newly minted; nothing existing covered
`min_reported_n` (verified by grepping `src/` and `docs/`). See Minor 1 and Minor 2.

Applying it to every contrast rather than only `within`-restricted ones is the right
reading. `reference.md` says it "applies to a `within` contrast's `n_paired`" in a
section about `within`; restricting it there would leave the warning unreachable in this
build, which is the exact no-op class the task exists to close. The broader reading is
strictly more disclosive and never wrong.

## The two judgement calls

**`_METHOD_VARYING_STEP` genuinely discriminates.** Working the arithmetic:
`pred = i + is_spearman + extra` with `extra = 0.5` when `(i + is_spearman)` is odd. So
pearson gives `i + (0.5 if i odd)`, spearman gives `i + 1 + (0.5 if i even)`, and the
per-unit difference is `1.5` on even units and `0.5` on odd — mean exactly `1.0`, sd
`0.5`, `cohens_dz = 2.0`. That pins three things `_AGGREGATE_STEP` could not: the sign
(`of − against`, since a reversed subtraction gives `−1.0`), a real interval width, and
`cohens_d` as an actual float rather than the `None` a degenerate sd returns. The
implementer's account of why they reverted `_AGGREGATE_STEP` is accurate — `float(i)` is
identical in both conditions, so `delta == 0.0` and `cohens_dz → None` would have passed
against a sign error or a hardcoded `None`. Good call, and the reasoning is recorded in
the fixture's own comment where the next person will find it.

**`run_a_project(units=...)` is additive.** `test_cli.py:30` — keyword-only (after the
bare `*`), defaulted to `10`, and the only behavioural change is
`range(1, units + 1)` where the literal `11` used to be. Every existing caller is
byte-identical in behaviour. It also matches `task-8-brief.md`, which already calls
`run_a_project(..., units=120)`, so this is the keyword the next task expects rather than
a local convenience.

## Tests as evidence

**A reversion to one shared `compute` inside `stats.py`** is caught by
`test_two_different_computes_over_identical_tables_yield_a_real_interval`
(`test_stats.py:1268`): `of` and `against` are the *same* table and the two computes are
different formulas (`total`/`mean`), so a single shared compute cancels to a zero-width
interval at zero and both the `high - low > 0` and the bracketing assertion fail. This is
the right shape — it reproduces the worked example's structure (identical recorded
columns, different formula per condition) in a unit test.

**A reversion at the `cli.py` call site is caught by nothing.** See Important B.

**`results.contrasts` silently disappearing again is caught by nothing.** There is no
test declaring a `statistics.contrasts` entry and asserting the block appears in
`run.yaml`. Deleting `_compute_declared_contrasts`'s call site, or reverting
`run_record.py:152-153` to the unconditional `return {...}`, leaves all 673 tests green.
The report's own end-to-end verification of the `spearman_vs_kendall` block was done by
hand and is not durable. Folded into Important B as one missing-integration-test finding,
since both gaps are on the same two functions and one test file.

---

## Findings

### Important A — a declared contrast can be misfiled into `vs_baseline`, overwriting the real one

`cli.py:168` and `cli.py:188` reconstruct "was this auto-generated?" from
`comp.against == baseline.index and comp.id == label_by_index.get(comp.of)`. Nothing
enforces that only auto-generated comparisons satisfy it: `validate._check_contrasts`
refuses an `id` that another entry's side names (`E-STATS-CONTRAST-NESTED`) and an
unresolvable label, but permits an `id` equal to a condition's own label. So

```yaml
statistics:
  contrasts:
    - {id: "method=spearman", of: "method=spearman", against: "method=pearson", within: {sex: f}}
```

with `method=pearson` as the baseline is kept by `_baseline_comparisons` and dropped by
`_declared_comparisons`. Since `resolve_contrasts` emits auto-generated entries first and
declared ones after, and `_compute_vs_baseline` assigns `out[comp.of] = block`
(`cli.py:363`) rather than merging, the declared entry **overwrites** the genuine
unrestricted baseline block for that condition. The reported numbers are then silently
the `within`-restricted ones, under a key that promises otherwise — and if the stratum
matches no units the block is still non-empty (all-null metrics), so the overwrite is not
even visible as an absence. The declared contrast also never reaches `results.contrasts`.

Reachability requires an unusual `id` choice, which is why this is Important and not
Critical; the consequence when reached is a wrong number with no diagnostic, which is the
class this project treats as worst.

The fix is one field. `Comparison` (`contrasts.py`) should carry its own provenance —
`declared: bool = False`, set `True` in `resolve_contrasts`'s second loop — and the two
filters become `if not comp.declared` / `if comp.declared`. `_baseline_comparisons`'s
docstring explicitly argues against a fourth field on the grounds that "only these two
callers need it"; that argument is what's wrong, because the reconstructed test is not
equivalent to the fact it reconstructs. Cheaper and safer would be `resolve_contrasts`
returning the two lists it already builds separately.

### Important B — the derived contrast path and `results.contrasts` have no integration test

Three claims the brief asked to be true are code-verified and test-unverified, all on
codepaths `08ba1eb` introduced:

1. **`cohens_d` cannot be a number for a derived metric.** True at `cli.py:278`, but
   `test_a_baseline_sweep_reports_a_delta` asserts
   `entry["method"] in ("paired_t_over_units", "paired_percentile_over_units")` — a
   disjunction that pins nothing about construction-by-origin — and its
   `isinstance(entry["cohens_d"], float)` only covers the recorded branch. No test ever
   produces a derived contrast entry through `main(["run", ...])`.
2. **The call site passes each side its own closure.** `cli.py:246-252` does, but
   passing `compute_of` twice positionally would still typecheck, still pass mypy, and
   still pass all 673 tests — reintroducing exactly Critical 1, in exactly the file it
   lived in. `test_stats.py:1268` guards `stats.py`, not `cli.py`.
3. **`results.contrasts` exists.** No test declares a `statistics.contrasts` entry end to
   end, so the whole of Critical 2's fix can be reverted invisibly.

`run_a_project(aggregate_returns=...)` is the existing lever for (1) and (2): a baseline
sweep with a derived metric whose value depends on the swept axis, asserting
`method == "paired_percentile_over_units"`, `cohens_d is None`, and a non-degenerate
`ci95` that brackets its `delta` — the last of which is what a shared closure at the call
site would break. (3) is a few lines on top of the same fixture. Task 8 is the acceptance
task and could absorb these, but its brief names neither, so they will be lost unless
carried forward explicitly.

### Minor 1 — `W-STATS-CONTRAST-THIN` is not in any document

`CLAUDE.md` says the document changes first. The new identifier appears nowhere in
`docs/`. There are four in-tree precedents (`W-ENV-UNLOCKED`, `W-EXEC-BUDGET`,
`W-REPL-FLOOR`, `W-TEMPLATE-VERSION` are all undocumented), so this is consistent with
the codebase rather than a divergence introduced here — hence Minor, and not a
spec-compliance ❌. It is still a line worth adding beside `W-STATS-RESAMPLE-THIN` in
`reference.md` § How a metric becomes a number, where `min_reported_n`'s sibling
disclosures already live.

### Minor 2 — the thin-pairing test doesn't assert the identifier

`test_cli.py:841` asserts `"min_reported_n" in doc["stdout"] or "N_PAIRED" in
doc["stdout"]`. The string `min_reported_n` appears in the warning's `where` field, so
renaming the code to anything at all still passes. The brief supplied this assertion, so
it is not the implementer's invention, but the repo's rule is that every `W-` identifier
has a test *producing it*, and only an assertion on `W-STATS-CONTRAST-THIN` pins that.
One-line fix.

### Minor 3 — key order differs from the documented example

The record writes `delta, basis, paired, method, n_paired, ci95, cohens_d, correction`;
`reference.md`'s examples order `delta, basis, paired, method, ci95, …, cohens_d`.
`yaml.safe_dump(..., sort_keys=False)` preserves insertion order, so a reader diffing
`run.yaml` against the doc sees a reordering. Cosmetic, and `n_paired`/`correction` have
no documented position in `vs_baseline` anyway. Worth aligning when S4c inserts the
correction keys, which is the moment the order becomes visible in the doc.

### Minor 4 — `n_paired` is absent from `reference.md`'s `vs_baseline` examples

All three `vs_baseline` blocks in `reference.md` (≈407, ≈1663, ≈1998) omit `n_paired`,
while § Contrasts says "`n_paired` is the intersection, and it has to be recorded" and
the `results.contrasts` example carries it. This slice writes it in both places, which is
the right behaviour and follows the brief. The doc examples are what's behind — a
one-line addition to each, in whichever slice next edits that region.

### Minor 5 — a degenerate derived resample records nulls with no warning

When `paired_percentile_of_derived` returns `None` (fewer than `min_honest_draws`
survivors), the entry records `method: null, ci95: null` beside a real `delta` and no
`W-` is emitted — the aggregated side warns `W-STATS-AGGREGATE-FAILED` /
`W-STATS-RESAMPLE-THIN` in the same situation. This is the same silent-null species this
slice closed for `min_reported_n`, one level down. Out of scope here; a
`docs/superpowers/spec-defects.md` candidate rather than a fix, and plausibly S4c's,
since that slice is already editing every contrast entry.

### Note on `spec-defects.md`

The report says the declared-contrasts entry was "removed … closed, not deferred." The
file is untracked (`.gitignore:224` ignores `docs/superpowers/`), so it cannot appear in
the diff and the claim is unverifiable from the review package. Checked on disk instead:
no live entry claims declared contrasts compute nothing, so the removal is consistent
with what's there. The pre-existing row noting `min_reported_n` "unread … Assigned to
S4b" is now stale in the other direction; harmless, since those rows are a historical
per-slice record rather than an open list.

## Also checked, no finding

- `paired: true` is hardcoded on every entry. Correct for this build:
  `allocation: between` is refused, so `welch_`/`unpaired_` are unreachable and
  `progress.md` documents them as out of scope. `confounded: true` likewise belongs to a
  design this build cannot express.
- `n_paired` is per-column for a recorded metric (a column present on a subset of
  completed units narrows its own pairing, matching `summarize_step`'s per-column
  counts) and per-step for a derived one (which has no ragged per-unit shape). Both are
  defensible and the choice is documented in the code.
- The `vs_baseline` attachment (`run_record.py:114-120`) runs before the `condition_meta`
  pass, so a condition entry created only by that attachment still gets its `label`,
  `is_baseline`, and `values` filled in afterward — no half-populated condition reaches
  `run.yaml`.
- No `DataFrame`, no new dependency, no `x` where `×` belongs, ruff line-length respected
  throughout the new code.
- `_compute_vs_baseline` and `_compute_declared_contrasts` share
  `_comparison_step_blocks`, so there is one metric-construction codepath rather than two
  to keep in sync — the right factoring, and it is what makes Important B a single test
  gap rather than two.
