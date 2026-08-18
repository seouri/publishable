# H4b-2 — whole-branch review

**Reviewed:** `h4b2-clustered-contrasts` (46 commits, `d1ac52a`..`c44f527`) against `main`.
**Read:** `whole-branch.diff`, the design spec **including § Corrections against the code**, the
ledger, the four task reports and reviews, `CLAUDE.md`.

**Verdict: DO NOT MERGE.** One Critical, reproduced through a real `run` on my own config. It is a
narrow fix (one statement plus a docstring and a filing correction), not a redesign — everything
else on this branch holds up, including under two of my own mutations on the full suite.

## Gates — verified by running, foreground

| Gate | Result |
|---|---|
| `uv run pytest -q` | **2199 passed, 1 skipped, 2 xfailed** (119s) — matches the expected figure |
| `uv run ruff check .` | clean |
| `uv run ruff format --check .` | 80 files already formatted |
| `uv run mypy` | no issues, 45 source files |

Re-run after every mutation was reverted: identical. Tree left clean (`git status --short` empty),
`__pycache__` cleared, ~500MB of stale `pytest-of-joon` temp dirs removed before starting (no
`ENOSPC` hit).

---

## Critical

### C1 — A clustered run can still publish an **unclustered** contrast interval, and the record says nothing

**File:** `src/publishable/cli.py:940-987` (the `is_derived` branch of `_comparison_step_blocks`),
reachable because `src/publishable/cli.py:2294-2295` assigns `derived_by_key` **and**
`resample_fns_by_key` *before* the `summarize_step` call whose `except ContractError` retry
(`cli.py:2309-2330`) clears neither.

**Verified by running** — a real project, my own config, through `main(["run", ...])`, reading
`run.yaml` off disk. 10 units in 3 clusters (3/3/4), `cluster_by: site`, one declared contrast, and a
template whose `aggregate` returns a key colliding with the recorded column `pred`:

```
per condition:  pred: method: t_over_units_clustered      ci95: [-3.91, 16.71]   (half-width 10.31)
vs_baseline:    pred: delta: 6.4  method: paired_percentile_over_units
                      ci95: [4.4, 8.4]  (half-width 2.0)  n_paired_clusters: 3
results.contrasts[0]: the same entry, same method, same interval
```

The delta's interval is a percentile drawn over **units** on a run that declared a cluster — five
times narrower than the cluster-robust per-condition interval sitting beside it — its `method`
carries no `_clustered` suffix, and `n_paired_clusters: 3` is written beside it, which reads as if the
cluster *was* honoured. This is verbatim the failure decision 2 names as the reason the retirement had
to come last ("publishing `method: paired_t_over_units` beside per-condition values that *are*
`t_over_units_clustered`, with nothing in the record saying which is which") and verbatim what
`E-DATA-CLUSTER-CONTRAST` refused ("the delta's interval would be narrower than the design
supports while the values beside it are cluster-robust"). **`validate` reports zero errors on this
config; the run completes and the number ships.**

**A normative row is falsified, so this is a code defect and not a filing gap.** `reference.md:1040`,
`E-DATA-CLUSTER-DERIVED`'s § Errors row, states the containment as "**the whole `derived` mapping is
dropped**, the code disclosed through `W-STATS-AGGREGATE-FAILED`, and the run keeps its record and its
recorded columns". At HEAD, in the collision case, the mapping is **not** dropped: it survives in
`derived_by_key` and its closures survive in `resample_fns_by_key`, and both are used to compute and
publish a contrast `delta` and `ci95`. "The corner is disclosed as open in § Contrasts" does not answer
that — § Contrasts defers the *branch choice* to `spec-defects.md`, while this row states the
containment unconditionally.

**Newly reachable on this branch — verified by running, not inferred.** The identical probe against
`main` (`82310b9`) exits **1** with no run directory: `E-DATA-CLUSTER-CONTRAST` refuses the config at
`validate`. Switched back and re-verified the tree clean afterwards.

**Why no per-task review saw it.** The corner *was* routed here — `spec-defects.md`'s H4b-2-task-4
entry says "task 14 **must** re-check this corner" — and task 14's re-check (fix round 1) recorded
this state:

```
{'delta': None, 'basis': 'units', 'paired': True, 'method': None, 'n_paired': 12, 'ci95': None, ...}
```

on the stated grounds that `resample_fns_by_key` holds "nothing for it — the state the collision's
uncleared retry leaves". **That premise is false.** `cli.py:2246` builds `resample_fns` for *every*
key in `derived` under `if derived:`, before the raising call, so the colliding key's two closures
**do** exist and the derived branch computes a real point estimate and a real draw. The same false
claim is asserted as fact in the docstring of the test that pins the decision —
`tests/test_cli.py:3489-3500` ("`resample_fns_by_key` holds nothing callable for it, since the
collision means no derived closure was ever built for this run") — which is the
*comment-claiming-a-guarantee-the-code-does-not-provide* shape, and it is what made the fixture model
a state that does not occur end to end. `reference.md` § Contrasts discloses the corner as "open" and
defers to `spec-defects.md`; the filing it defers to describes the wrong branch outcome, so the
disclosure does not cover the number that actually ships.

**The fix I recommend, and the one I do not** (not applied — the finding is the deliverable). The
recorded intent, already documented in `reference.md` § Contrasts, in the filing and in the test, is
that this corner publishes `delta`/`method`/`ci95` as `null` beside `n_paired_clusters`. **Take the
clusters-guarded suppression**: when `clusters is not None`, the derived branch computes no delta and
no draw — `E-DATA-CLUSTER-DERIVED`'s own rule, that no clustered draw exists for a recomputed metric —
which is confined to this branch's regression and matches all three places that already claim it.
**Do not clear both maps in the `except ContractError` retry** as the remedy: that also changes the
**unclustered** collision path, which is pre-existing on `main` and outside this branch, and it should
be filed separately rather than bundled into this fix. Whichever is chosen, the test docstring at
`tests/test_cli.py:3489` and the `spec-defects.md` re-check paragraph must be corrected rather than
rewritten around, and the end-to-end shape (not a direct call with the maps hand-built) is what needs
pinning: **the direct-call fixture cannot see this, which is why four reviews missed it.**

**The fix perturbs none of the dated counts.** No config in
`docs/feasibility-llm-growth-studies.md` declares `data.units.cluster_by` (two hits, both
`cluster_by: null`, re-checked here with a can-fail control), so the § Executability entry dated
2026-08-18, its table, and `CLAUDE.md`'s H4b-2 entry all stand unchanged after it — zero configs
unblocked, six with no remaining core-side blocker, three executable. The measurement question does
not re-open; only the suite count moves, by whatever the new pin adds.

---

## Minor

### M1 — The new § Executability entry's prose and its own table assign "no remaining core-side blocker" to different sets

**File:** `docs/feasibility-llm-growth-studies.md:1215-1248`. The prose says "**six** with no
remaining core-side blocker, three executable"; the table three paragraphs below annotates its three
`Yes` rows as "**Yes** — no remaining core-side blocker" while C1–C3 (which have no core-side blocker
either, per H4b-1) read "No — blocked on `io.reuse_from`". A reader taking the table at face value
gets three, not six. **Verified as inherited**: H4b-1's own dated section (`:1168-1181`, on `main`)
carries the identical annotation, where 3 == 3 made it unambiguous. Not the item-7 failure mode — no
sentence converts six into an execution count, and no count is wrong — but the annotation is this
slice's own text in this section and could be one clause longer. Do **not** retro-edit H4b-1's or Part
B's dated sections to match.

---

## What I verified by running (as distinct from read)

- **My own clustered contrast, end to end, with my own arithmetic.** 10 units, clusters 3/3/4,
  per-unit differences 2/6/10 — a fixture that meets all four of the spec's discriminating
  constraints and is *not* the branch's 2/4/6. `run.yaml` carries
  `method: paired_t_over_units_clustered`, `n_paired: 10`, `n_paired_clusters: 3`, and a raw
  half-width of **10.313450515635465**, which equals a CR1 half-width I computed from the formula
  (`G/(G−1)·ΣS_g²/n²`, df = `G−1`, `scipy.stats.t.ppf`) independently of `stats.py`, digit for digit.
  The **corrected** bound's half-width is **14.874204669728154**, which is that same construction at
  the entry's own `correction_level: 0.025` and df = 2 — so the corrected bound is the clustered
  construction, not a clustered field on an unclustered number.
- **The percentile arm, end to end.** The same project with `statistics.resample` declared records
  `paired_percentile_over_units_clustered` with `n_paired_clusters: 3` on both `vs_baseline` and
  `results.contrasts`. Both spellings the `_clustered` suffix rule licenses are therefore written by
  code, and no `method` string in `run.yaml` is undocumented.
- **The weight × cluster boundary.** My own transplant of C1's `data.units`/`statistics` blocks with
  `cluster_by: record_source` added earns exactly `E-DATA-WEIGHT-CLUSTER-CONTRAST` at
  `data.units.weight_by`; the same block without `cluster_by` validates with zero errors. The core
  side of the boundary is belt-and-braces (`cli._comparison_step_blocks` raises `ValueError`,
  `Member.__post_init__` refuses both modifiers), and `Member` has exactly **one** construction site
  (`cli.py:1206`), so nothing else needed teaching about `clusters`.
- **My own re-measurement of two feasibility configs at HEAD**, rather than accepting the figure: E1's
  and C1's `data`/`statistics` blocks transplanted onto a scaffolded project over a 60-unit banded
  table roster both validate with **0 errors** and only `W-DATA-CLUSTER-UNDECLARED` — matching the
  dated entry's "(none)" rows and its own stated warning. The zero-configs claim re-checked with a
  can-fail control: `cluster_by` has two hits in the analysis, both `cluster_by: null`, against 13
  `weight_by` hits.
- **Two mutations, full unfiltered suite, foreground, reverted by editing and re-verified:**
  - `interval = paired_t_over_units(diffs)` in place of `paired_t_over_units_clustered` →
    **5 failures** (`test_a_clustered_column_contrast_takes_the_cluster_robust_t`, the
    `[False-True-False-paired_t_over_units_clustered]` cell of the six-cell method test,
    `..._entry_carries_its_cluster_count`, `..._runs_end_to_end_and_records_the_clustered_delta`,
    `..._leaves_a_summary_estimate_alone`).
  - the clustered draw grouping replaced by per-key items in `paired_percentile_of_derived` (draw
    units while still calling it `_clustered`) → **4 failures**, including
    `test_a_clustered_resampled_contrast_really_drew_clusters` and the stratum-composition refusal
    test.
  Both seams between batch 2's constructions and batch 3's threading are therefore pinned, not merely
  present.
- **`E-DATA-CLUSTER-CONTRAST` is gone.** Enumerated by reading `_check_sweep`'s replaced block and the
  three `src/` comment sites in the diff first, then confirmed by grep: **zero** hits in `src/`, zero
  in `docs/reference.md`; the survivors are `tests/` assertions saying it is gone and two lines inside
  `docs/feasibility-llm-growth-studies.md`'s **dated 2026-08-15** section, which is evidence and
  correctly untouched.

## What I verified by reading

- **The invariants** (`CLAUDE.md` § Invariants). The clustered path computes over `col_keys`, the
  intersection of both sides' completed units, and records it as `n_paired`; the interval is its own
  construction over that intersection (`paired_t_over_units_clustered` / a joint clustered draw), never
  a difference of the two sides' intervals; `correction.py`'s Holm ranking is untouched by this branch
  and still ranks on the point estimate over half the **raw** `ci95` width; `cohens_d` is deliberately
  unclustered and § Statistical reporting says so.
- **No dangling locator or count phrase.** Both the § Errors and § Validation rows were **replaced in
  place**, not deleted, so no row below them moved; the sibling row *Allocation deltas aren't
  computed* had its by-name citation of the deleted row re-worded rather than left dangling. Grepped
  README, `design-principles.md`, `experimental-designs.md`, `reference.md` and `CLAUDE.md`
  individually for "Clustered deltas", "five construction", "none of those five", "row above",
  "further up": the only hits are locators naming *other* tables' rows by content.
- **The deleted df-provenance claim did not return a fifth time.** Read for the claim rather than
  grepping one spelling: the only surviving df attributions are to the *t* forms
  (`reference.md:2433`, `cli.py:1159`), and no comment, docstring or document attributes a df to a
  percentile draw.
- **The worked example is untouched.** `README.md` and `docs/design-principles.md` are not in the
  diffstat at all, and `reference.md`'s diff touches no `cohort-pilot` number, interval or hash.
- **Mechanical pass over `reference.md`'s additions**: every `#anchor` resolves, no trailing
  whitespace, no tab or non-breaking space, every added table row matches its header's column count.
- **`CLAUDE.md`'s new H4b-2 entry**, claim by claim: the retirement, the mint and its grounds, both
  `method` spellings, `n_paired_clusters`, the zero-configs figure with both counts correctly labelled
  (six / three, in the post-H4b-1 sense), the degenerate-draw closure worded as "every stratum's rows
  identical" (which is what the `all(...)` guard actually tests), and the `report_by` gap declined in
  writing and re-owned to H4c — all check out. "H4c inherits the composition itself" is stated in the
  `spec-defects.md` mint filing, so the composition is owned rather than a silent gap. The only
  perishable claim is "merged on 2026-08-18", true once this merges today.

## What I could not check

- **The degenerate-draw refusal's own numbers** were taken from batch 2's tests and the suite rather
  than recomputed by hand; I verified only that the code's condition matches the documented wording.
- **`E-DATA-WEIGHT-CLUSTER-CONTRAST` against a `weight_by`/`cluster_by` declaration arriving in a
  shape other than a non-empty string** — a non-string is `E-CONFIG-TYPE`'s by the surrounding rows,
  read but not exercised.
- **Whether the unclustered derived-key-collision case** (the same branch without `cluster_by`, which
  publishes a derived contrast for a metric dropped from `aggregated`) is correct: it is pre-existing
  on `main` and outside this branch's diff, so I did not pursue it beyond noticing that C1's fix will
  touch the same code.
