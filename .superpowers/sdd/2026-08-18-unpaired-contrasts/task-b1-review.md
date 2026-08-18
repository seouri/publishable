# H4c batch 1 (tasks 1, 2, 3, 21) — whole-batch review

**Reviewed at `4854994` on branch `h4c-unpaired-contrasts`, 2026-08-18.** Baseline re-measured in the
foreground before any mutation: `uv run pytest -q` → **2208 passed, 1 skipped, 2 xfailed** (108.79s),
`ruff check` clean, `ruff format --check` **80 files already formatted**, `mypy` **45 source files**.
Tree left clean; `src/publishable/correction.py` restored to md5 `7fee4fc477935b6cd1721dff03b9b70f`
and the suite re-run after the last revert → 2208/1/2.

---

## The two verdicts

**Spec compliance: FAIL — three Majors, all documents-only, all one-to-three-line fixes, no code.**
Two are obligations the binding spec assigned by number and the batch did not discharge (decision 4's
rejected df readings are named as rejected only in the development record and the normative document
still *asserts* one of them; decision 6's § Validation row narrowing was dropped by task 2 and is
excluded from task 16's file list, so nobody owns it). The third ships, in the block whose entire
purpose was to stop being unproducible, a record § Statistical reporting's own dispatch table forbids.
Nothing here requires rebuilding: fix the three sentences and re-verify.

**Task quality: HIGH.** Task 21's literals were correct on first run, all six cells discriminate their
corrected bound at *its own df* (verified numerically and by mutation), all three prescribed mutations
were run in the foreground against the full unfiltered suite, and the reverts were by editing the file
back. The mutation-1 blindness claim is not merely repeated — it is now established twice over (see
below), which is stronger than the implementer claimed. Deducted for the two orphaned document
obligations and for a metric swap whose two downstream fields nobody re-derived.

---

## Findings

### Major 1 — `reference.md:2438` still asserts a df rule decision 4 rejects

The `_clustered` suffix sentence reads *"the *t* forms are cluster-robust (CR1) with **df = clusters −
1**, over the differenced values when paired and **over the arm-level ones when not**"*, and only then
does the newly inserted clause say the unpaired *t*'s df is Welch-Satterthwaite over `G_s` − 1. The
first clause's quantifier was never narrowed, so the normative document states, of the unpaired
clustered *t*, a df that is `min(G_of, G_against) − 1` or `G_of − 1` — **precisely one of the two
readings decision 4 names as rejected**, and on fixture B those give 35.65 and 26.37 against the
correct 34.15.

This is also the answer to the brief's item 4: the rejected readings are named as rejected **only in
`docs/superpowers/spec-defects.md`** (the `## RULED by H4c task 1` entry, item 4), which is the
development record and not normative. The four documents name neither, and one of them is still
implied. **Verified by reading** `docs/reference.md:2438` beside the spec's decision 4 and its own
grounds ("`min(G_of, G_against) − 1` … contradicts 'df = clusters − 1' on the side it discards").

The fix is the same two-word quantifier narrowing task 1 applied, **in the same commit**, to both
`weighted_paired_*` rows (`docs/reference.md:2435`, `:2436` — "A **paired** column metric under
`weight_by`"): make it *"with df = clusters − 1 when paired"*. The technique was in hand and was not
applied here.

### Major 2 — decision 6's § Validation row narrowing is orphaned

`docs/reference.md:385`, the `W-STATS-CONTRAST-THIN` row, still reads *"and at `run`, when the
comparison's realized **`n_paired`** is below it"*. Decision 6 states in terms: *"The row and the
§ Contrasts sentence are both narrowed in task 2, before task 16 reads them."* Task 2 narrowed the
§ Contrasts sentence (`:2595`, now per-side and "either") and left the row.

The ownership is not recorded where the fixer will find it. **Verified by reading** the plan's task 16
in full: its **Files** list is `src/publishable/cli.py`, `src/publishable/validate.py`,
`tests/test_cli.py`, `tests/test_validate.py` — `docs/reference.md` is absent, and its Produces names
only "a validate-side message that no longer names a key an unpaired contrast does not record". So
after task 16 the row will still key the run-side point on a key an unpaired contrast will not carry,
while § Contrasts three sections away says the opposite. Note the tension with the spec's correction
#1, which says *"the row is right and the message is what drifted"* — that sentence is about the row
naming **both emit points**, and it does not retract decision 6's narrowing; read either way, the row
and § Contrasts now disagree.

### Major 3 — task 3's metric swap left `method` and `cohens_d` un-rederived

`docs/reference.md:1359-1363`. The block now records `abs_error` — a **recorded column**, per
`:2538` *"with `abs_error` recorded per patient"* — with `method: unpaired_percentile_over_units` and
no `cohens_d`. Both fields were correct **because the metric was `r`, which is derived**, and both
became wrong when the metric changed:

- **`method`.** § Statistical reporting's own row (`:2434`) defines `unpaired_percentile_over_units` as
  *"the unpaired counterpart of the second"*, and the second (`:2432`) applies to *"Every derived
  metric, and a column metric **under `resample`**"*. Nothing in or around this example declares
  `statistics.resample`, and `:2477` states the worked example *"declares nothing"*. A recorded column
  with no declared `resample` takes the *t* row (`:2433`), so the method here must be
  `welch_t_over_units`. **Verified by running as well as reading**: `_clustered_contrast_call()` with
  `resample_columns` unset yields `paired_t_over_units` and with `resample_columns=True` yields
  `paired_percentile_over_units` — the pin's `plain_t`/`plain_percentile` cells, both passing, are a
  live demonstration that a column metric's percentile spelling requires a declared resample.
- **`cohens_d`.** `:2473` (*"unpaired ones report *d*s, over the pooled within-condition standard
  deviation"*) and `:2538` (*"`cohens_d` is reported only for a per-unit mean … with `abs_error`
  recorded per patient … *d* is exactly the right summary"*) both make it owed for this metric, and it
  is absent. The brief's ground — "inventing a number this task has no source for" — was not the
  batch's own standard four commits later: task 2's new unpaired block at `:2706` invents
  `cohens_d: 0.31` for the same class of metric.

So the block whose repair was justified as *"where a config can produce it"* still shows a record no
config can produce. `delta: 0.041`, `ci95: [0.012, 0.070]`, `differs_on` and `confounded: true` all
carry over correctly and `n_of: 116 + n_against: 112 = 228` matches the worked example's completed
count — those halves are right.

### Minor 1 — the new refusal has neither of its two rows, and no test will notice

`E-DATA-WEIGHT-ALLOCATION-CONTRAST` is now cited in two normative sentences (`:2450`, `:2693`), both
linking `#errors-validate-reports`, and it has **no § Errors row and no § Validation row**. Task 1's
brief argues the window deliberately and task 9 is ordered before 18, so this is not a defect of the
ruling. What is missing is the pin: `tests/test_cli.py:10880
test_the_weight_cluster_refusal_has_both_of_its_rows` is the H4b-2 precedent for exactly this claim,
the plan's task 9 Step 5 **cites** it as *"the shape of the pin that says so"*, and **verified by
reading task 9 in full, it writes no such test** — its five new tests are the `crossed_group_axes`
trio and three guard tests. Task 9 or task 22 should add the twin.

### Minor 2 — spec task 21's second half is unpinned and unmentioned

Spec task 21 asks for the paired cells **"and the worked example's intervals, which `CLAUDE.md`
§ The worked example says must not be narrowed back"*. The plan converted that into a whole-plan
prohibition (*"**Do not touch the worked example.**"*, plan lines 283-288) rather than a test, and
task 21's brief and report carry no trace of it. That is a defensible narrowing — the intervals are
document literals with no code to pin — but the report should have said so. **Verified by reading** the
plan and by diffing: task 3 did carry the block's `delta` and `ci95` through unchanged.

### Minor 3 — wrapping inconsistency at three insertion points

`:2450` appends a ~450-character sentence onto the last line of a paragraph hard-wrapped at ~90
characters (`:2440-2450`); `:2693` and `:2711` are unwrapped paragraphs inserted between wrapped
neighbours (`:2683-2689`). Cosmetic, but it is the region's own convention.

### Minor 4 — the repaired block is the only `results.contrasts` example with no correction quartet

`:1359` carries no `ci95_corrected`/`correction`/`correction_level`/`family_size`, while `:2639`,
`:2681` and `:2706` all do, and § Contrasts' own rule (`:2597`) is that declared contrasts join the
correction family. **Not a regression** — the `vs_baseline` original omitted them too — but the block
changed shape and this was the moment to add them.

---

## What I verified, by running

- **Baseline and restoration.** 2208/1/2 before mutations and again after the last revert; `ruff
  check`, `ruff format --check` (80 files), `mypy` (45 files) all clean at HEAD.
- **Mutation 1 is genuinely blind, and I could not overturn it.** Moved the `pool` arm above the
  `diffs` arm in `correction._corrected_bounds` (`src/publishable/correction.py:241`, `:259`); full
  unfiltered foreground suite → **2208 passed, unchanged**. The overturn attempt then fails at the
  source rather than at the fixture: `Member.__post_init__` (`:132`) raises on both-set and
  `family_members` (`:150`) drops the `ci95=None` members before `_corrected_bounds` is ever called, so
  every member reaching the function carries exactly one of the two and **no legitimate fixture can
  discriminate the order**. The implementer's claim stands, and its ground is stronger than stated.
- **The pin covers the corrected bound at its own α *and* its own df** — the H4b-1 hole is closed.
  Mutating the `clusters` arm's corrected-bound call to the unclustered `paired_t_over_units`
  (`correction.py:250`) failed **exactly** `test_every_paired_contrast_cell_is_unmoved_across_this_branch[clustered_t]`
  (plus `test_correction.py::test_a_clustered_members_corrected_bound_is_the_clustered_construction`),
  2 failed / 2206 passed. Independently, each *t* cell's corrected half-width equals its raw one times
  `t(df, 0.975)/t(df, 0.95)` at **its own df**, computed against the shipped `stats._t_critical`:
  `plain_t` 1.178150916034073 at df 11, `clustered_t` 1.4422141888574018 at df 2, `weighted_t`
  1.1829342728467618 at Kish's df 9.8. Three distinct ratios — so a bound built at the wrong df is
  caught in every cell, including `weighted_t` vs `plain_t` (0.4 % apart, ≈0.0102 absolute on a 2.128
  half-width, far outside `pytest.approx`). The three percentile cells' corrected literals all differ
  from their raw ones, so α is pinned there too.
- **`0` really is taken.** `tests/test_cli.py:4185` asserts `entry["n_paired"] == 0` beside a null
  delta for a *paired* contrast over an empty stratum — live, passing, and it is why absence is the
  only free encoding for the unpaired case. Decision 5 is right.
- **`E-DATA-ALLOCATION-CONTRAST` is alive.** `tests/test_validate.py:8115` asserts the **exact set**
  `{"E-DATA-ALLOCATION-CONTRAST"}` and passes; ten allocation-selected validate tests pass. No test in
  this batch exercises an unpaired shape, so there was nothing to assert alongside it.
- **The identifier really was free, and the exclusion is legitimate rather than the filter-the-output
  trap.** Re-ran the sweep: `E-DATA-WEIGHT-ALLOCATION-CONTRAST` occurs in `src/`, the four documents
  and `tests/` **only** at the two sentences this batch added; `weighted_welch|weighted_unpaired` hits
  `docs/superpowers/{H4c-SCOPING.md, plans/…, spec-defects.md, specs/…}` and nothing else. The filter
  was applied to the **file list** (a directory that is evidence), not to grep's output, and the
  spec's own § Corrections declares the development record exempt.
- **Task 3's fourth-site sweep could have found one.** `grep -n vs_baseline` over the four documents
  returns 17 hits and `unpaired_percentile_over_units` returns 2 — both non-vacuous. I read all 17:
  `:309`, `:483`, `:1821` are correct as written (a declared contrast is the route; a generated
  `vs_baseline` reaches it only beside `E-SWEEP-BASELINE-GROUP`), `:396` is `grid`-only and explicitly
  says a groups × parameter confound is warned about by nothing, and the rest merely mention the block.
  **No fourth site exists.** The enumeration of three is complete.
- **Mechanical pass, both files.** No trailing whitespace, tab or invisible unicode outside fences in
  `docs/reference.md` or `docs/superpowers/spec-defects.md`; no duplicate heading anchors; every one of
  the eight anchors the new text uses resolves to a real heading (`#errors-validate-reports`,
  `#errors-core-raises`, `#allocation-within-subjects-or-between-subjects`, `#clustered-units`,
  `#statistical-reporting`, `#contrasts-claims-that-arent-condition-vs-baseline`, `#expansion-modes`,
  `#weighted-samples`); no table row's column count changed (no rows added or removed); `×` used
  throughout, no stray `x`.
- **No sentence claims a config unblocked.** Every `unblock`/`executable count` line added across the
  four commits and the development record asserts **zero**, six and three unchanged.

## What I verified by reading

- **Every reader of `n_paired`, enumerated by reading rather than by one grep.** Writes at
  `cli.py:1001` and `:1138`; reads at `:984` and `:1032` (the `>= 2` gates) and `:1254` (the
  `min_reported_n` warning); a message at `validate.py:5337`. I then read the two candidates a grep
  cannot see: `cli._entry_for` (`:1466`) returns the entry dict and the caller `entry.update(values)`s
  it — no key inspection — and `hypotheses._observed_block` (`:109`) copies a **fixed four-key
  allowlist** `("delta", "value", "ci95", "method")`, so no generic pass over a contrast entry's keys
  exists anywhere. Decision 5's "the readers are those two writes and `tests/` alone" holds.
- **The suffix rule does license the two clustered spellings.** *"each of the **unweighted** forms
  above"* over a six-row table whose first four rows are the unweighted ones names
  `welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered` by construction, so
  ruling 2 (no new rows) is right and its mechanical tripwire is real —
  `tests/test_cli.py:3349 test_a_clustered_contrast_method_is_one_the_document_defines` over
  `_interval_method_names()` (`:7491`) asserts `f"{stem}_clustered"` is *not* a row, and
  `test_the_interval_construction_tables_are_parsed_at_all` (`:7514`) is its can-fail control. The rule
  needs no narrowing to license the spellings — what it needs is Major 1's narrowing of its *df* claim.
- **The § Contrasts insertion moved nothing that pointed across it.** Swept the whole section for
  positional locators and count phrases; the only `above`/`below` hits (`:2595`, `:2713`) are semantic
  ("below the floor", "above the mean"), not locators.
- **`differs_on` is a real key** written for both record shapes (`cli.py:1202`), so keeping it in the
  re-authored block is correct.

## What I could not check

- **Whether task 16 or task 22 will in fact repair `reference.md:385`.** I read task 16's brief-source
  in the plan and it excludes the file; I cannot rule out task 22's consistency pass catching it, but
  no numbered task owns it and § Contrasts and § Validation disagree in the meantime.
- **The percentile constructions' df-provenance tripwire** (task 1 Step 4's deferral to task 22's
  re-read). Those constructions do not exist yet, so there is nothing to re-read; the tripwire is
  unverifiable until task 22.
- **The implementer's report of pytest runs auto-moved to background by the harness timeout.** I can
  confirm the tree is clean and the suite green now, but not that no mutation was ever live across a
  background transition. All three mutations I ran were foreground with an explicit long timeout.
- **`weighted_t`'s corrected arm by mutation.** Settled arithmetically instead (the Kish-vs-df-11
  ratios above); I did not spend a fourth full-suite run on it.
