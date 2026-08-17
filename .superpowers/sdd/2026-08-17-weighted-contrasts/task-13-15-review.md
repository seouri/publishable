# Tasks 13–15 review — the retirement batch

Reviewed at `03242c5` on `h4b-weighted-contrasts`. Gates re-run in the foreground:
`uv run pytest` → **2159 passed, 1 skipped, 2 xfailed**; `ruff check` clean; `ruff format --check`
**80 files**; `mypy` clean over 45 source files. All four match the report.

## Verdicts

**Spec compliance: FAIL on one point, otherwise met.** The retirement itself (task 13) is complete and
correct — one emit deleted, both rows gone, the `run`-through half genuinely wired and pinned, and the
zero-error `validate` result reproduces under an independent re-measurement I ran myself. But spec
**decision 6** and task 15's own explicit instruction ("do not write six of nine execute") are
violated by the new dated table, which answers **Yes** in a column headed *Would execute?* for six
configs three lines below the sentence "The executable count stays at three", and answers **No —
blocked on `io.reuse_from`** for three other configs carrying the identical dependency. That is the
one deliverable the whole task existed to get right, and it reverses an adjudication this same section
already recorded. Two further prose claims (M1b) misstate **decisions 1 and 2** — the dated entry
credits C1 with a weighted `cohens_d` its derived AUROC cannot have, and § Shortcut names the weighted
paired *t* on a path decision 2 says C1–C3 never take.

**Task quality: FAIL.** Two mutation failures of the kind `CLAUDE.md` names by hand. The
`strata=None` mutation the implementer recorded as a "stated blind spot" is **not blind** — I applied
it and the suite fails; it was scoped to a single test of the implementer's choosing rather than run.
And `test_the_sibling_refusal_rows_state_their_own_reading` lost **both** of its discriminating
assertions and now asserts only its controls; I reintroduced the dangling citation it is named for and
the test passed. Offsetting credit: the implementer's two reported disagreements with the brief are
both **correct and verified by me** — the prescribed `codes(path) == set()` strengthening really is
blind against a live warning, and the brief's exit grep really did leave stale citations behind.

---

## Findings

### Critical

**C1. The dated table converts the six into an execution count, and answers one column by two
different standards.** `docs/feasibility-llm-growth-studies.md:1167–1177`.

Verified by reading, against the Part B entry's own convention at lines 1095–1105 of the same file.
The column is headed `Would execute?`. In the Part B entry the "Yes" rows are exactly the three
`CLAUDE.md` reports as the executable count; the column's Yes *is* that count, which is why Part B
marked E3/E4/E6 `No — blocked on io.reuse_from`. The new entry keeps that spelling for E3/E4/E6 and
gives C1/C2/C3 `**Yes** — no remaining core-side blocker` — while its own prose at line 1138 says
"C1–C3's `io.reuse_from` dependency is unsettled", § Shortcut at line 519 says the confirmation run
"reads the fitted artifact with `io.reuse_from`", and the spec's own headline says the same. Same
blocker, opposite answer, same column, same table.

Three separate things are wrong and each is sufficient on its own:
- A reader counting Yeses gets **six executable**, which is the exact sentence step 10 and decision 6
  forbid. A table cell states a claim as loudly as a sentence.
- The column now answers *"is there a core-side blocker"* for C1–C3 and *"would it execute"* for
  E3/E4/E6. Two standards, one column, no marker distinguishing them.
- The entry marks C1–C3 **Yes** on the "no remaining core-side blocker" standard **eleven lines after
  falsifying that standard's own second clause for exactly those three** (lines 1150–1155: "'every
  field they declare is honoured' … is … not [true] of their `statistics.report_by`").

Task 15's brief prescribed `| C1 | *(none)* | No — blocked on io.reuse_from |` verbatim, for all three.
The implementer changed it and did not record the change in the report's *Disagreements* section, so
nothing flags it for a reader of the record either.

**This reverses a recorded adjudication in the same section.** `docs/feasibility-llm-growth-studies.md:1003`
(the 2026-08-16 entry) already ruled on exactly this case: "**Under the table-roster substitution, the
generous count is three, not six.** … E3, E4 and E6's transplanted blocks validate equally clean under
the same substitution — the same zero-error result — **but still cannot run** … So 'six of nine, one
substitution away' is not the number this measurement supports." And `CLAUDE.md`'s standing Part B
paragraph counts `io.reuse_from` as a blocker in as many words: "**Six stay blocked** on two causes …
`io.reuse_from` (unbuilt, unowned) for E3, E4, E6, and `E-DATA-WEIGHT-CONTRAST` (H4b) for C1–C3." The
new table treats the same dependency as not-a-blocker for three of those six, without argument.

Remedy: restore the brief's three rows (the "no remaining core-side blocker" claim already lives in the
prose above the table, where it is correctly qualified), or split the column into two so the two
standards are separately answerable.

### Major

**M1b. The dated entry states a false build fact about the record C1 writes, and the § Shortcut
paragraph names a construction C1–C3 never reach.** `docs/feasibility-llm-growth-studies.md:1146–1148`
and `:515`.

Verified by reading the configs against the code, and corroborated by the slice's **own** test
docstrings.

- The dated entry says of all three: "Their weighted contrasts record `weighted_by`, an
  `n_paired_effective` …, **a weighted `cohens_d`**, and a corrected bound built from the same weighted
  evidence." C1's headline metric is **derived** — `:525` says "AUROC is derived from the per-unit
  `prob`/`consensus_label` columns by the template's `aggregate`", and its hypothesis names
  `step03_screen.auroc`. Decision 1 settled that core does not weight a derived metric:
  `src/publishable/cli.py:932–964` takes the derived branch, `method` stays the unweighted spelling and
  `cohens_d` stays `None`, pinned by
  `tests/test_cli.py:9940` (`…_carries_the_record_keys_without_a_weighted_method`, asserting
  `entry["cohens_d"] is None`). So the sentence is true of C2/C3 (whose metric, `step03_screen.prob`,
  is a recorded column) and **false of C1's own primary metric** — in a section whose entire purpose is
  that build facts be accurate on their date. This is the higher-graded half: it is a claim about a
  record a reader would go looking for.
- § Shortcut's rewritten paragraph at `:515` says "**the weighted paired *t*** and the weighted closure
  in `paired_percentile_of_derived` weight the delta and its interval". All three declare
  `statistics.resample`, so `resample_columns=True` and the *t* branch at `src/publishable/cli.py:1050`
  is never entered — raw or corrected. Spec decision 2 states this flatly ("`paired_t_over_units` is
  **never called** on C1–C3"), and the slice's own
  `test_a_weighted_column_contrast_with_no_resample_takes_the_weighted_t` opens its docstring with
  "The general case, **off the payoff path**: C1-C3 all declare `statistics.resample`, so
  `resample_columns` is True for them and this branch [is not reached]"
  (`tests/test_cli.py:9984–9986`). The prose the slice shipped re-asserts the exact confusion decision 2
  and the spec's trap table were written to prevent.

**M2. The `strata=None` mutation is not blind; it was scoped to one test rather than run.**
`.superpowers/sdd/.../task-13-15-report.md` "Task 13, mutation 2"; `src/publishable/cli.py:2698` and
`:2714`.

Verified by running. I set both `command_run` call sites to `strata=None` and ran the **whole** suite:
`tests/test_cli.py::test_a_declared_stratify_by_reaches_a_contrasts_interval_through_run` **FAILS** on
`assert 1.6249999999999998 < 1.6249999999999998` (`tests/test_cli.py:7511`); 2158 passed, 1 failed.
Reverted by editing the file back, `__pycache__` cleared, revert verified by re-running that test to a
pass.

The implementer ran the mutation against only `test_a_weighted_run_publishes_a_weighted_delta_end_to_end`
— their own new test — saw it pass, and wrote it up as a blind spot with a paragraph of justification.
This is `CLAUDE.md`'s *reading a mutation's silence as confirmation* combined with *a mutation applied
to a proxy*: silence in one chosen test is evidence about that test. The irony is that the test which
does catch it is one the report itself names two sentences later, built in fix round 1 for precisely
this purpose.

The residual the report claims stays unpinned — "`command_run`'s threading of `strata` specifically
into a *weighted* contrast" — has **no code seam**. `src/publishable/cli.py:1034–1048` passes
`strata=strata` into `paired_percentile_of_derived` on one call for both weighted and unweighted; only
the `method=` string branches on `weights`. There is no separate weighted threading to leave unpinned.
The stated blind spot is not a blind spot at all, and the report's justification for it (the
`_METHOD_VARYING_STEP` fixture argument) answers a question nobody needed answered.

Remedy: strike the blind-spot paragraph from the report and record the real result. Left standing it
reads as a considered engineering judgement with a named alternative pin, and a later slice grepping
for unpinned surface finds a claim that is simply false.

**M3. `test_the_sibling_refusal_rows_state_their_own_reading` no longer tests what its name and
docstring claim.** `tests/test_cli.py:10083–10100`.

Verified by mutation. The two `assert "E-DATA-WEIGHT-CONTRAST" not in ...` lines were deleted
(review-13-15.diff:970–971), leaving only the two comments labelled `# the control`. I edited
`docs/reference.md`'s `E-DATA-CLUSTER-CONTRAST` row to read "Temporary, exactly like
`E-DATA-WEIGHT-CONTRAST` above: …" and the test **passed**. Reverted; `grep -c` on `reference.md` back
to 0.

The docstring still asserts the guarantee in prose — "a row that argued 'unlike that one' would now be
a dangling reference" — with no assertion behind it. This is verbatim `CLAUDE.md`'s *a test whose name
claims the guarantee*. `git log -S` puts the test's origin at `982b9b8`, **task 11's own commit** —
this slice wrote the absence assertions and this slice deleted them. The absence assertions were still
meaningful after the retirement (the code can be
re-introduced into those rows, as my mutation shows) and should not have been dropped.

**M4. A stale count phrase survived in `src/publishable/validate.py`, in the file the implementer
edited, while the identical phrase was correctly fixed in the tests.**
`src/publishable/validate.py:5059` and `:5066`.

Verified by reading both files. `E-DATA-ALLOCATION-CONTRAST`'s comment block still says "Imported at
module scope, the same as **its two siblings'** helpers" and "Like **its two siblings** it refuses a
*combination* rather than a declaration, so it carries a row in § Validation's registry". With
`E-DATA-WEIGHT-CONTRAST` retired there is **one** sibling. The implementer made exactly this correction
in `tests/test_validate.py:7522–7531` and again at `:10431`-region ("It differs from **its sibling** in
the one way that matters: **that one** fires on `comparisons > 0`") — and missed the mirror image in
`src/`, eight and nineteen lines below a comment block in the same function that they *did* edit
(review-13-15.diff:727–729 shows the edit landing at line 5047 of the same block). This is
`CLAUDE.md`'s *sweep for the claim, not for the file the claim was first noticed in*, and *check every
count phrase near a deletion* — both named in the review charter.

### Minor

**m5. Task 13's stated exit gate is unmet and the report does not disclose it.**
`tests/test_cli.py:10031`.

Verified by running the brief's own grep: `grep -rn "E-DATA-WEIGHT-CONTRAST" src/ docs/reference.md
tests/` returns one hit — the new end-to-end test's docstring, "Until this task `command_run` returned
before running on `E-DATA-WEIGHT-CONTRAST`". Can-fail control on the identical file list:
`grep -rn "E-DATA-CLUSTER-CONTRAST" src/ docs/reference.md tests/ | wc -l` → **21**. Neither sweep
filtered its output.

The sentence is *true as history* and the brief itself planted it verbatim in the prescribed test body,
so this is a defect in the brief as much as in the work. But the brief says the grep "must be empty at
the end of this task" and the report's disagreement #3 argues the grep "would have caught [the stale
citations] had it been run to completion" — implying it was run to a clean end. It was not clean.
Either the docstring should be reworded (it can say "before this task's retirement" without the code)
or the residual hit should be declared.

---

## What I verified by running (as distinct from read)

- **Gates.** Full foreground `pytest` twice (before and after all mutations): 2159/1/2 both times;
  `ruff check`, `ruff format --check` (80 files), `mypy` all clean.
- **Mutation 1 (`weights=None` at both `command_run` sites).** `test_a_weighted_run_publishes_a_
  weighted_delta_end_to_end` **FAILS** on `assert 'paired_percentile_over_units' ==
  'weighted_paired_percentile_over_units'`. Reverted by file restore; verified by re-running to a pass.
  The `run`-through half is genuinely pinned.
- **The α on the weighted corrected branch, now the path is live.** Dropping `confidence=1.0 - level`
  from `src/publishable/correction.py:213` makes
  `test_a_corrected_bound_over_weighted_differences_is_weighted_too` fail at exactly the bounds
  `progress.md` recorded — `2.8239563251976074` against `1.4426305905416408`
  (`tests/test_correction.py:614`). **The pin still holds.** Reverted; verified by re-running
  `tests/test_correction.py` to 33 passed.
- **The `strata=None` mutation** — see M2, whole suite.
- **The sibling-row mutation** — see M3.
- **The report's disagreement #2 (the brief's prescribed strengthening was blind).** Confirmed: I
  replaced the assertion at `tests/test_validate.py:7378` with the brief's `codes(path) == set()` and
  it **FAILS**; the implementer's `{"W-DATA-WEIGHT-UNDECLARED"}` is the accurate stronger claim.
  Reverted; verified by re-run.
- **Independent re-measurement of the dated count.** I did **not** reuse the implementer's plugin. I
  transplanted the real `data`/`statistics` blocks into `tests/`'s own `write_config` harness against a
  60-unit table roster carrying every attribute the nine configs name — a different substitution
  (table source rather than resolver), so the source kind is an independent variable:
  - **E1** (`holdout`, `resample.stratify_by: [truth]`, `report_by`, no weight) → errors: **none**
    (`W-DATA-CLUSTER-UNDECLARED`, `W-DATA-WEIGHT-UNDECLARED` only, both roster artifacts of my
    all-attributes CSV).
  - **C1** (`weight_by: sampling_weight` + `sweep.baseline` + `resample.stratify_by:
    [consensus_label, count_stratum]` + five-level `report_by`) → errors: **none**.
  - **C2** (the same weights with a declared `statistics.contrasts` entry) → errors: **none**.
  - **Can-fail control:** the same E1 block with `holdout.frac: 0` reports `E-DATA-HOLDOUT-FRAC`, and
    reverting the field restores the zero-error result.

  The report's zero-error result reproduces. The **numbers** are sound; C1 is what the table says of
  it. The **framing** is C1 above.
- **Task 14's four sweeps**, over the four documents named individually plus `src/` and `tests/`,
  unfiltered output, can-fail control `grep -rn "paired_t_over_units" …` → **67 lines**. Sweep 1's only
  survivors are the `E-DATA-ALLOCATION-CONTRAST` and `E-DATA-CLUSTER-CONTRAST` rows, where the claim is
  still true and doing correct work for those codes. Sweeps 2–4 leave no falsified weight claim. Also
  swept for "`Member` has no weights field", "takes no weights", and `cohens_dz` claims — none stale.
- **The mechanical pass**, scripted over `README.md`, `docs/design-principles.md`,
  `docs/experimental-designs.md`, `docs/reference.md` and `docs/feasibility-llm-growth-studies.md`, and
  **diffed against the pre-batch commit `28aba16` in a throwaway worktree**: duplicate anchors, table
  column counts against each header, trailing whitespace, tabs, invisible unicode, every relative link
  and `#anchor`. Result: **no new mechanical issue** (the handful of hits are my slugger's handling of
  em-dash headings and are identical at both commits). No `x`-for-`×` in the new material. The worktree
  was removed and pruned.
- **`E-DATA-WEIGHT-CONTRAST`'s emits, enumerated by reading then confirmed by grep** — in that order.
  Read `_check_sweep` in full at `src/publishable/validate.py:4965–5100`: the guard, its comment block
  and the feeding `weight_by = units_here.get("weight_by")` line are gone, `units_here` is retained for
  the cluster guard with its comment repaired. Read `_check_unimplemented` at `:3990–4010`: the
  docstring list and the placement-precedent comment no longer name it, and the replacement text is
  accurate. Then confirmed by grep: **zero** in `src/`, **zero** in `docs/reference.md`, one historical
  docstring in `tests/` (m5).
- **§ Errors and § Validation.** `E-DATA-WEIGHT-CONTRAST`'s § Errors row is gone (`grep -c` on
  `reference.md` → 0). § Validation's *Weighted deltas aren't computed* is gone. The sibling row
  *Allocation deltas aren't computed* (`docs/reference.md:309`) is **still true**: it now cites only
  *Clustered deltas aren't computed*, which survives at `:317`, and its claim — read per comparison,
  unlike the clustered row's whole-design reading — matches the code at
  `src/publishable/validate.py:5070–5081`. `Contrast has units in common` at `:321` cites *Allocation
  deltas aren't computed* "above"; 309 < 321, so the positional locator still resolves.
- **§ The one config file** still reads "**One declaration above is not yet built**" naming
  `statistics.null_test` (`docs/reference.md:193`), and `NOT_BUILT_COMMANDS` passes in the green suite.
- **`CLAUDE.md`'s contrast invariant.** Honoured. `src/publishable/cli.py:966–980` computes `col_keys`
  as the intersection of both sides' completed units, `n_paired = len(col_keys)`, and `col_weights` as
  that intersection's own weights in `col_keys` order. `:1105–1107` computes `n_paired_effective` from
  Kish over `col_keys` (or `base_keys` for a derived metric) rather than over the roster-wide mapping,
  and the comment says so. The interval is its own construction over that same intersection
  (`paired_percentile_of_derived(..., col_keys, ...)` at `:1034`), never a difference of two sides'
  intervals. The spec's three-distinct-answer fixture exists and is exercised:
  `tests/test_cli.py:9936–9937` pins `n_paired == 4` against `n_paired_effective == 3.0` over an
  8-unit roster.
- **`spec-defects.md` re-ownering.** `grep -n "H4b" docs/superpowers/spec-defects.md` leaves no bare
  "H4b" owner; the single remaining bare mention (`:6298`) is a **quotation** from `H4-SCOPING`, not an
  ownership line.
- **The other three documents.** `experimental-designs.md:354` and `design-principles.md:42` are the
  only weight claims outside `reference.md`; both are still true and neither needed to move.
  `README.md` has none. § Weighted samples' "Four interactions worth knowing"
  (`docs/reference.md:1429`) still enumerates exactly four after task 11's edit.

## Read but not run

- The re-ownering **text** in `spec-defects.md` — I confirmed each entry now names H4b-2 and that the
  three claims about what H4b-1 did or did not touch match the code I read (`checked_weights` /
  `usable_weight` gating on the weighted paired forms), but I did not independently re-derive the
  finiteness argument.
- The seven earlier dated subsections in the feasibility analysis: confirmed unedited by the diff, not
  re-measured.
- The `report_by`-under-`resample` gap the new entry qualifies itself against: read the filing and the
  `command_run` call site, did not build a config to observe the unresampled level interval.

## Could not check

- Whether C1–C3's `io.reuse_from` dependency is genuinely identical to E3/E4/E6's. Both § Shortcut and
  the spec say the confirmation run reads a fitted artifact through it, which is why C1 is a finding
  rather than a question — but nothing in this repo can settle the dependency itself, exactly as both
  the spec and the entry say.
- The weighted corrected bound **through `run`** on the *t* path. The payoff path takes the pool
  branch, and the e2e test asserts only `ci95_corrected is not None`. The α pin (above) lives at a
  direct `correction.py` call; a weighted config with no declared `resample` would reach
  `weighted_paired_t_over_units` through `run` and nothing exercises that combination end to end. Not
  raised as a finding — the construction is pinned where it lives — but it is the one path the batch's
  "run-through half" does not cover.

## Tree state

**Clean.** Four mutations were applied (`src/publishable/cli.py` twice, `src/publishable/correction.py`,
`docs/reference.md`, `tests/test_validate.py`) and one throwaway probe file created
(`tests/test_zzz_reviewer_probe.py`). Every one was reverted by restoring the file's content — never
`git checkout --` — `__pycache__` cleared after each, the probe file deleted, and the throwaway git
worktree removed and pruned. Each revert was verified **by behaviour** (re-running the test the
mutation had broken), and the final state confirmed by a full green suite (2159/1/2) plus
`git status --porcelain` returning nothing — that check was run before this review file was written,
so the tree is clean apart from this file itself.
