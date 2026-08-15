# Task 12 report: refuse what has no construction, then retire both codes

**Status:** complete. `uv run pytest` 1391 passed, 2 xfailed; `ruff check` clean; `mypy` clean.
`ruff format` was not run.

## Commits

| Commit | What |
|---|---|
| `870301f` | feat: both retirements, both new refusals, task 6's two pins flipped |
| `23ac64e` | fix: a fold stratum naming the measurement axis — the hole retiring the fold refusal opened |
| `65cd97a` | test: pin `E-DATA-CLUSTER-DERIVED`'s guard shape, including the narrowings `cli` cannot reach |
| `5cd65e4` | docs: registry rows, the run-time `E-DATA-CLUSTER-UNKNOWN` debt, nine → seven |

## Inherited versus added

No report existed for the first half, so this records the split.

**Inherited, kept unchanged:** `src/publishable/replication.py` (the `_fold_k` raise removed,
replaced by the comment explaining the reordering), `src/publishable/stats.py`'s
`E-DATA-CLUSTER-DERIVED` raise and docstring, `tests/test_cli.py` in full (both bypasses
deleted, the derived-refusal end-to-end tests, the shipped-template blast-radius test),
`tests/test_replication.py`. The docstring's argument for why the refusal lives at run time
rather than in `validate` is the answer the brief asked for and I kept it verbatim.

**Inherited, edited by me:** `src/publishable/validate.py` (added the measurement-axis check;
kept the `E-DATA-CLUSTER-CONTRAST` guard as inherited), `src/publishable/cli.py` (the stale
comment), `tests/test_validate.py` (the two pins, five stale present-tense comments, and all
the new probes).

**Added by me:** the measurement-axis refusal and its two tests; the whole
`E-DATA-CLUSTER-CONTRAST` probe set (7 tests — it had **zero**, and an inherited comment named
a test, `test_a_clustered_generated_comparison_is_refused`, that did not exist); 4
`summarize_step` tests in `tests/test_stats.py`; every `docs/reference.md` edit.

## The brief was wrong on item 6, and it blocked

The brief and task 11's `cli.py` comment both said the measurement-axis hole was "unreachable
today". **It is reachable, and this slice is what made it so.** Probed before deciding:

```
{attributes: [rep, val], measurements: {by: rep}}  +  {kind: fold, k: 2, stratify_by: rep}
→ KeyError: 'rep' at cli.command_run's strata comprehension
```

`collapse_measurements` consumes `measurements.by`, so `rep` is a declared attribute no
*resolved* unit carries. It was unreachable only while `E-REPL-FOLD-STRATIFY-UNSUPPORTED`
refused every `stratify_by`. So the brief's "coded refusal or recorded note" choice was
already settled: **coded refusal**, because a slice that opens a bare-traceback path and
writes a note about it has shipped the defect.

**Reported under `E-REPL-FOLD-STRATIFY-UNKNOWN`, not a new code.** That code's own documented
reasoning is that `data.units.attributes` is the reference set *because* a stratum must survive
resolution; a `measurements.by` does not. `E-DATA-CLUSTER-UNKNOWN`'s row already writes the
argument ("a `measurements.by` is consumed at collapse time and dropped from the merged unit")
and the stratify row already inherits from it.

**The asymmetry with `cluster_by` is written down** in code and in the registry row: the same
declaration shape under `cluster_by` reaches `E-DATA-CLUSTER-VARIES` at *run time*, because a
cluster naming the measurement axis varies within every unit by construction and the collapse
is the one place holding the rows that prove it. A stratum's fault needs no rows, so it is a
`validate` check. Recorded so it does not read as drift and get "fixed".

## Blast radius, measured

Every mutation had `__pycache__` deleted before and after; every revert was verified by
re-running the tests, never by `git status`.

| Refusal | Mutation | Caught by |
|---|---|---|
| `E-DATA-CLUSTER-CONTRAST` | guard neutered | 3 tests |
| | gated on the **declaration** instead of `comparisons > 0` (over-fire) | 7 tests |
| `E-DATA-CLUSTER-DERIVED` | raise neutered | 1 test (`test_cli.py`) |
| | per-key `resample` narrowing dropped | **0 → now 2** |
| | `seed is not None` narrowing dropped | **0 → now 1** |
| measurement-axis | check neutered | 2 tests |
| | fires on any stratum beside a `measurements` block (over-fire) | 1 test |

**The two undetected mutations were a real gap.** Traced it: `cli` builds a resample callable
for *every* derived key and only when `derived` is truthy, so neither narrowing is reachable
through `cli` — the narrowing is defensive, and removing it changed nothing any test could see.
Pinned directly on `summarize_step` (`65cd97a`): one test producing the identifier plus three
parametrized under-firing controls, each also asserting the recorded column beside it stays
`t_over_units_clustered`, so the clustering is demonstrably still in force and the guard simply
does not apply. Both mutations are now caught.

**Controls that must report** are present throughout: the contrast set mirrors H3a's weighted
set one for one — bare `sweep.baseline` stays legal *with* a crossed sibling that is refused,
`report_by` stays legal, an unclustered sweep is untouched, an empty `cluster_by` draws only the
name check. The measurement-axis test carries an identical config stratifying on the other
declared attribute.

## Documentation

- `E-DATA-CLUSTER-CONTRAST` → § Errors `validate` reports (validate-only), **plus** a codeless
  sibling in § Validation's checks table, "Clustered deltas aren't computed". The brief was
  right that the table carries siblings an identifier grep cannot see: "Weighted deltas aren't
  computed" is the precedent.
- `E-DATA-CLUSTER-DERIVED` → § Errors core raises **only**. Not dual-listed: it is run-time-only
  by construction, which is the entire argument in its docstring, so a validate row would
  contradict it. `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` is dual-listed because both surfaces really
  do report it.
- `E-DATA-CLUSTER-UNKNOWN` → the missing § Errors core raises row (the tasks 2 / 8 debt).
- Nine → seven was **three** edits: the prose count, the two inline `NOT BUILT` markers, and the
  closing clause's future tense about `.cluster_by`. The fenced block now carries exactly seven
  markers, matching the prose.
- `E-REPL-FOLD-STRATIFY-UNKNOWN`'s registry row and the "Stratification attribute exists" check
  row both gained the measurement-axis case.

**Mechanical pass** diffed against the branch point (`cefaba3`): finding set identical, only
line numbers shifted. The pre-existing findings are my slugger's `&` handling and multi-line
table rows, not regressions. Both retired codes: **zero** occurrences across every tracked
`*.md`; grep proved live against `E-DATA-CLUSTER-UNKNOWN` (5 hits, same file). Nothing about
`cohort-pilot` moved — checked by grepping the docs diff for every worked-example value.

## Cross-document pass: two things checked and deliberately not changed

The `*.md` grep for retired identifiers cannot see a stale claim that names no code — the
"Nine declarations" prose was exactly that class — so both were checked by phrasing.

1. **No generated project ships a falsified comment.** `git grep "NOT BUILT" -- src/ templates/`
   returns only two `validate.py` comments *citing* the doc list. Nothing in
   `src/publishable/generators/` mentions `cluster_by`, `weight_by` or `stratify_by` at all, so
   `publishable init` never wrote a `NOT BUILT` for either and there is no generated comment for
   this slice to have falsified.
2. **`docs/experimental-designs.md` § Case-control (matched) line 328 says core reports "each
   arm and their contrast with intervals clustered on `match_set`" — which
   `E-DATA-CLUSTER-CONTRAST` now refuses. Left unchanged, on H3a's precedent.** That document
   annotates **no** temporary refusal or unbuilt state anywhere — `git grep -E "not (yet )?
   (built|implemented)|this build"` over it returns nothing — and H3a shipped
   `E-DATA-WEIGHT-CONTRAST` without touching its own weighted-samples row (line 351) for the same
   reason. It is the designs-as-specified document; the temporary refusal is recorded in
   `reference.md`'s registry row, which is the placement that row argues for. Changing line 328
   would state the build where the document states the design.

## Comment triage

The brief flagged one falsified comment (`cli.py`). There were **six**. `tests/test_validate.py`
carried five more present-tense claims that `E-DATA-CLUSTER-UNSUPPORTED` "is still live" /
"cannot reach" (around the empty-`cluster_by`, non-string, direct-call, and cluster-bound
tests), one of which made an `assert ... not in found` pass for the wrong reason — now an exact
set assertion. Historical framing ("was live when these were written", recording the flip) was
kept deliberately; present-tense falsehoods were removed.

## Concerns

1. **Two `src/` comments still name `E-REPL-FOLD-STRATIFY-UNSUPPORTED`** — `cli.py` and
   `validate.py` — as historical explanation for why a check exists where it does. Deliberate,
   and consistent with the house reason-giving style, but it means a future "grep for retired
   codes" sweep over `src/` will hit them. The `*.md` grep the brief specified is clean.
2. **`E-DATA-CLUSTER-DERIVED` fires per step, and drops the whole `derived` mapping.** Inherited
   behaviour, matching the derived-key-collision containment exactly. Worth noting that a
   clustered run with a deriving template now silently loses every derived metric with only a
   `W-STATS-AGGREGATE-FAILED` to say so. That is the ruled design, but it is a warning where a
   reader might expect a refusal before the run spends its budget — and it cannot be moved to
   `validate` for the reason the docstring gives.
3. **The measurement-axis refusal is a `validate` check with no run-time backstop.** `cli`'s
   subscript is still bare; it is safe because `command_run` validates first and refuses. Left
   as is because a second guard would need its own code and row, but flagged.
4. **H4 owes three lifts, not two:** the `_clustered` contrast family
   (`E-DATA-CLUSTER-CONTRAST`), the clustered derived draw (`E-DATA-CLUSTER-DERIVED`), and — if
   it wants stratification on a measurement axis to mean anything — a decision about whether a
   `measurements.by` should be retainable as an attribute at all.
