# Task 17 review — echo the resolved `method`/`n`/`stratify_by` into `run.yaml`

Reviewed `584a24a..9d2f8d4` on `h4a-resample-honoured`.

**Spec compliance: ❌** — the values reach the record as *data* but not as *text*: every metric block
after the first is emitted as `resample: *id001`, so the deliverable does not yet honour the sentence it
just wrote into the specification. The cause is the shared `beside_n` carrier the brief mandated — it
pre-dates this task, `technical_n` aliases identically today — and one fix closes both. See C1.

**Task quality: findings** — 1 Critical, 5 Important, 8 Minor. The two open decisions are both right on
the merits; the *reasoning* for one of them is not (I3), the sweep this task owed stopped one file short
again (I4), and the report's own claim about the `report_by` path is unguarded (I5).

---

## Critical

### C1 — the echo is emitted as a YAML alias in every metric block but one

`resample_beside`'s inner dict is a single object, merged by reference into `weighted_beside`
(`cli.py:1667`) and into every `cond_beside_n` (`cli.py:1757-1760`), and `summarize_step` spreads
`beside_n` verbatim into each block (`stats.py:1795`, `:1890`). `yaml.safe_dump` therefore anchors it
once and aliases it everywhere else. Verified against a real run's `run.yaml` (config declaring
`method`/`n: 500`/`stratify_by: [cohort]`):

```yaml
        pred:
          resample: &id001
            method: bootstrap
            n: 500
            stratify_by:
            - cohort
          ...
        mean_pred:
          resample: *id001
```

Observed, not inferred. A run with `report_by: [cohort]` emits **six** metric blocks and exactly one
anchor: `resample: &id001` followed by five `resample: *id001` — two top-level metrics and four
`by.cohort` level blocks. Across conditions it follows by object identity (the same inner dict is
spread into every `cond_beside_n`).

This is the one failure mode the task exists to prevent. The sentence being settled is "the resolved
values are recorded in `run.yaml` beside the interval **so the number is never the result of an
undocumented default**"; beside `mean_pred`'s interval there is no number, there is a pointer. The repo
has already ruled on exactly this, in `hypotheses.py` `_observed_block`: it copies with `list(...)`
because sharing "makes `yaml.safe_dump` anchor the interval where the comparison writes it (`&id002`)
and emit an alias (`*id002`) in the verdict, so the number a hypothesis was decided on is no longer
readable where it is written — in the file this project describes as what a reviewer opens in ten
years." Same file, same standard.

Neither new test can see it: both go through `yaml.safe_load`, which resolves aliases transparently. A
test that guards this must assert on the raw `run.yaml` **text**.

Attribution and fix scope: this is a latent defect of the `beside_n` carrier, not a slip unique to this
task — `technical_n` aliases identically today (verified: `technical_n: &id001` / `technical_n: *id001`
in a measured-roster run), so it dates to H3a task 6. But task 17 is the task that makes an unreadable
record contradict a sentence it just wrote into the specification, and the fix is one place: copy each
container value of `beside_n` per block where `summarize_step` spreads it, which closes `technical_n`
and `resample` together. `list(...)` on `stratify_by` alone does not help — the shared object is the
outer `resample` dict.

## Important

### I1 — the doc cross-reference is wrong in both halves

`reference.md:2355`: "See the second `r` block below for the shape." The block added is named
`mean_pred:`, and it is at line 1939 — **above**, and in a different subsection (§ What isn't a repeat,
not § Statistical reporting where the sentence lives). Wrong identifier and wrong direction, in the one
sentence the whole slice deferred to. It is also the positional-locator class `CLAUDE.md` names
explicitly. Fix by naming it: "the `mean_pred` block in § What isn't a repeat".

### I2 — the new sentence appeals to an absent-not-null rule for `resample_draws` that is stated nowhere above it

Same sentence: "the same absent-not-null rule `resample_draws` follows above." **No statement of an
absent-vs-null rule for `resample_draws` exists anywhere above 2355** — the examples at 1925/1939 show
the key with a value and say nothing about either state. Its only semantics are given at 2365 and 2367,
both *below*: 2365 says "the field is `null` when resampling was never attempted", and 2367 says a
column's is "**absent** entirely — not `null` — when no `resample` is declared".

Which end is wrong matters more than which is newer, so: the emitted behaviour matches **2367**
(absent on an undeclared column) and the new sentence, and it is **2365** that overreaches by stating
`null`-when-never-attempted as if it covered both metric shapes. So the fix is at 2365 — scope it to the
derived metric, which 2367 already implies — and the new sentence should point at 2367 by name rather
than at "above".

### I3 — decision 2's stated reasoning carries no evidence (the outcome is right; the argument isn't)

The report's case for absent-not-null is "matching task 1's pin exactly … needed no amendment and passed
unmodified." `_assert_undeclared_resample_shape` asserts individual keys and is not a dict-equality pin;
it never asserts `"resample" not in ...`. Confirmed by mutation — with `if resample_spec["declared"]`
replaced by `if True`, `__pycache__` cleared: **both task-1 pins PASS**, only
`test_no_resample_block_is_recorded_when_none_was_declared` fails. So the pin was green under either
choice, and its greenness is exactly the non-evidence the brief warned about. (Reverted in place;
`cli.py` byte-identical to pre-mutation, verified by `diff`.)

Weighing the choice myself: **absent-not-null is right**, and for a reason the report doesn't give.
`run.yaml` embeds the config — task 1's own pins read `run["config"]["statistics"]["resample"]` — so a
reader of an undeclared run sees `resample_draws: 2000` in the block and `statistics.resample` absent
(or `null`) one level up, in the same file. The "can't tell a default from a choice" cost the brief
posits is not real. It is also the rule `by`, `contrasts` and `corrected_fields` already follow, for the
identical reason. The choice stands; the argument for it should be that, not the pin.

### I4 — the sweep stopped one file short, at the file the brief itself named

`stats.py:1539-1540`: "`beside_n` is core-supplied context copied verbatim into every metric block —
**`technical_n` today**." That enumeration is now wrong by two (`weighted_by` was already there;
`resample` is new). The brief cites this exact docstring as the interface being consumed, and the
sweep covered `cli.py` and `docs/reference.md` and stopped before it. This is the third incomplete sweep
in the slice and the second of the "fixed the sentence, missed the function it describes" shape.

Everything else in the sweep is clean: `grep` for `future task` / `not yet recorded` /
`beside the interval` across `src/`, `tests/`, `docs/*.md`, `README.md` turns up only accurate prose;
`cli.py:1687`'s stale sentinel comment was correctly rewritten and correctly distinguishes the composed
`|`-label from the attribute names; `test_cli.py:6941`'s "a future task threading `method` or
`stratify_by`" is still true as a description of what that test guards.

### I5 — the report asserts the `report_by` path and nothing guards it

The report claims the merge into `weighted_beside` means "the `report_by` level call at the existing
`beside_n=weighted_beside` site carries it too". It does — I verified it (a `report_by: [cohort]` run
puts the block in all four `by.cohort` level blocks) — but **no test covers it**, and no existing test
combines `report_by` with a declared `resample`. This is the slice's twice-recurring "a seam named in a
brief is not a tested seam" class, here on a seam the *report* affirmatively claims rather than one the
brief merely mentions. Related: both new tests read `conditions[0]` only, despite the name
`..._beside_every_interval`, so the per-condition `cond_beside_n` path is exercised for one condition.

## Minor

- **M1 — a seam named in the brief that no fixture instantiates.** The brief asks that the echo carry
  *resolved*, not declared, values. Both new tests declare all three fields, so nothing distinguishes
  the two. Verified by hand end-to-end: a config declaring only `n: 500` echoes
  `{method: bootstrap, n: 500, stratify_by: []}` — correct, and untested. One extra config in the
  existing test closes it.
- **M2 — the second example doesn't say which run it is from.** 40 units, `failed: 0`, and a metric name
  (`mean_pred`) that appears nowhere else in the four documents and comes from the test fixture. Label
  it as a separate illustrative run so it can't be read as a worked-example variant.
- **M3 — key order in the example doesn't match the record.** `beside_n` is spread first, so core emits
  `resample` *before* `value`/`basis`/`n`; the example places it between `method` and `resample_draws`.
  Pre-existing looseness (`technical_n` has the same mismatch), but this is the block a reader will diff
  against a real file.
- **M4 — the two new sentences are near-duplicates.** "requested vs. rests on" and "`stratify_by` reads
  back as a list" now exist at 1949 and again at 2355 in almost the same words: two copies to keep in
  sync, in a repo whose named drift class is exactly that.
- **M5 — the one place the new rule reaches an existing `run.yaml` example.** I ran the named
  cross-document class (`grep` for every `resample`/`resample_draws` occurrence in the four documents).
  Only one metric-block example is affected: § Weighted samples' `r: {value: 0.607, ...}` at
  `reference.md:1329` sits eleven lines above a `statistics: resample: {method: bootstrap, n: 2000,
  stratify_by: [dx_status, count_stratum]}` snippet in the same section, and carries no `resample`
  sibling. Nothing says the two are the same run — the block is abridged and has no `method` key either
  — but under the rule this task just wrote, a reader who takes them as one run sees a violation. Say
  which run the block is from, or add the sibling. Everything else checks out: `init` writes
  `resample: null` (`reference.md:147`), so the worked example declares none and correctly carries no
  sibling; `README.md`'s two metric blocks (214, 216) are under the same undeclared config;
  `experimental-designs.md` shows configs only, no `run.yaml` metric blocks.
- **M6 —** the committed `progress.md` entry ends with a dangling fragment, "for implying it was already
  met."
- **M7 —** `cli.py:401` and `:1387` say "task 17 retired …", meaning a *different* slice's task 17; the
  same file now also says "H4a task 17" at `:1687`. Pre-existing, newly ambiguous within one file.
- **M8 — registered, not owed here:** `vs_baseline` and `results.contrasts` entries carry an interval
  whose construction the declaration changed (`paired_percentile_over_units`) and get neither a
  `resample` echo nor `resample_draws`. The amended sentence scopes the promise to "every metric block",
  so nothing written is false — but a reader of a delta still cannot see the draw count. Same owner as
  task 16's M6/M7 (H4 contrast-side hardening).

## Verified correct

- **Decision 1 (per-metric, not run-level) is well argued and cannot imply variation.** The deciding
  reason in the report is the right one: presence marks exactly the metrics a resample under the
  declaration reached, and absence marks `basis: repeats` metrics and ones dropped by
  `E-DATA-CLUSTER-DERIVED` — a run-level block would claim over both. It is a reinterpretation of
  "beside the interval" (metric blocks only, not contrast entries), and the document now says so
  explicitly, which is the right disposition.
- **`weighted_beside.update()` is not order-dependent.** Written at `cli.py:1245`/`:1254`, updated at
  `:1667`, read once at `:2250` (`beside_n=weighted_beside`). No read between declaration and update.
  Functionally identical to declaring it merged.
- **Once-ness still bites.** Mutation: a second `_resolved_resample(doc)` call feeding the echo →
  `test_the_resample_block_is_resolved_exactly_once` fails `assert 2 == 1`. Reverted in place.
- **All three `summarize_step` call sites are covered** (`:1895`, `:1943` via `cond_beside_n`; `:2250`
  via `weighted_beside`), including the `report_by` level call.
- **`resample_draws` semantics unchanged** — `stats.py` untouched, suite green, `_assert_undeclared_
  resample_shape` and the declared-`n` tests unmoved.
- **Worked example untouched** — `0.517, 0.683`, `0.014`, `−0.007, 0.059` unchanged across
  `reference.md`, `README.md`, `design-principles.md`.
- **Mechanical pass on `reference.md`** — every `#anchor` resolves, no duplicate heading anchors, no
  trailing whitespace, tabs or invisible unicode, no table or `×` touched.
- **Tree left clean at `9d2f8d4`**: `1797 passed, 2 xfailed`; `ruff check` and `mypy` clean; only the
  pre-existing `progress.md` modification in `git status`.
