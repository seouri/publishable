# Review — H4b-1 tasks 1–5 (decisions and documents)

Reviewed at `3530ff1` on branch `h4b-weighted-contrasts`, against
`docs/superpowers/specs/2026-08-17-weighted-contrasts-design.md` (including its appended
corrections), the five task briefs, and `CLAUDE.md`.

## Verdicts

**Spec compliance: CONDITIONAL PASS — the five rulings comply, the `reference.md` edits do not.
Blocking before tasks 6+ proceed: Findings 1 and 2.** Both are edits to shipped normative prose and a
shipped comment, and Finding 1 blocks hardest because task 2's own new paragraph is one half of the
contradiction. Findings 4–9 do not block.
Decisions 1, 3, 4 and 5 are implemented as the design rules them, `E-DATA-WEIGHT-CONTRAST` is alive
(emit at `src/publishable/validate.py:5023`, two `validate` tests exercising it pass), nothing reads
`Member.weights` yet as task 4's brief requires, and every new test asserts *alongside* the code
rather than on a total code set. What fails is the mandatory cross-document pass: task 2's two new
rows leave a count phrase and a quantifier above and below them describing the four-row table they
replaced, one of which now contradicts the paragraph task 2 itself added (Finding 1), and task 1's
narrowing sweep stopped one file short of the claim it was chartered to remove (Finding 2).

**Task quality: CONDITIONAL PASS — good mutation discipline on tasks 1–4, unpinned on task 5.
Blocking before task 7: Finding 3.** Task 7 builds the weighted closure on top of this stratified
draw, and the draw's pool ordering currently has no pin at all, so a task-7 regression in it would
ship green. Finding 4 (the false remediation claim in the tracked report) should be corrected in the
same pass.
Four of the five prescribed mutations I re-ran myself reproduced the report's outcomes exactly. But
task 5's ordering guarantee is pinned by **nothing**: I proved the prescribed mutation blind for a
stronger reason than the report gives, and proved the test that claims to pin it cannot detect *any*
of the three candidate orderings on its fixture (Finding 3). The report's stated remedy for that
blindness is false, and it is now in the tracked record (Finding 4).

## Gates (all verified by running, foreground)

| Gate | Result |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 80 files already formatted |
| `uv run mypy` | no issues, 45 source files |
| `uv run pytest` | **2132 passed, 1 skipped, 2 xfailed** in 129 s — matches the report exactly |

## Findings

### Critical

None.

### Major

**1. `reference.md:2424` still says "Which of the four below applies follows from two facts" above a
six-row table, and `reference.md:2445` contradicts the paragraph task 2 added at 2435–2443.**
Verified by reading the current file, not the diff. Task 2 appended
`weighted_paired_t_over_units` and `weighted_paired_percentile_over_units` to the contrast
construction table (now six rows) and left the sentence introducing it unchanged. Two defects in one
sentence: the count ("the four below") is stale, and the *determination rule* is stale — weighting is
a third fact, so "two facts" no longer selects among the rows. This is `CLAUDE.md`'s named trap
verbatim: "when you insert or remove a row, check every row it moved, **and every count phrase near
it**."

The contradiction is worse. Line 2445 (unchanged): "When `cluster_by` is declared **each** takes a
`_clustered` suffix and reads the cluster as the draw" — now quantifying over six rows — while the
new paragraph two lines above says "The `_clustered` suffix does not compose with either weighted
form in this build." Two sentences, one file, ten lines apart, one over-claiming over the other's
exception; that is the shape that shipped Criticals last slice. The same quantifier problem recurs in
the normative § Errors row for `E-DATA-CLUSTER-CONTRAST` (`reference.md:514` region), which reads
"gives **each contrast construction** a `_clustered` suffix … none of **those five** exists in this
build" — a count computed when the table had four rows.

Contributing: task 2's brief said to place the new paragraph "immediately **after** the paragraph
that states the `_clustered` suffix rule"; it was placed immediately **before** it, so the exception
is now stated before the rule it excepts. Two separate defects, so two required fixes, not an either/or: **(a)** re-word 2424 regardless of
anything else ("Which of the six below applies follows from three facts: … and whether `weight_by` is
declared"), and **(b)** narrow 2445's "each" to the unweighted forms. Moving the new paragraph after
2445, as briefed, improves the reading order but resolves neither on its own.

**2. `tests/test_validate.py:7277` still carries the exact over-broad claim task 1 existed to
narrow.** The section comment above the weighted-contrast tests reads: "the one combination that
would publish a wrong delta is refused under its own code **until the paired estimators weight**."
Decision 1's whole content is that the *derived* paired estimators will never weight; task 1 deleted
that promise from the emit message (`validate.py`) and from the § Errors row (`reference.md`) and
left it standing in a third file — which the brief listed under **Files: Modify**, two lines above
where the new test was inserted. Verified by `grep -rn "paired estimators" README.md docs/*.md src/
tests/`, which returns this line plus the new test's own quoting of it. `CLAUDE.md`: "Sweep for the
claim, not for the file the claim was first noticed in — three sweeps in one slice stopped one file
short." Delete or narrow the comment.

**3. `tests/test_stats.py::test_a_relabelled_stratum_draws_the_identical_sequence` pins nothing —
it cannot detect *any* of the three candidate orderings, including the one its docstring claims to
rule out.** Verified by running two mutations, reverting each by editing the file back and
re-verifying by behaviour:

- Prescribed mutation (content order → insertion order, `stats.py:1214`): test **passed**, matching
  the report.
- **My additional mutation — label order**: `pools = [sorted(group) for _lab, group in
  sorted(grouped.items())]`. The test **passed too**. The docstring says "the two orderings this must
  rule out are exactly two — insertion order and label order — and swapping the two labels reverses
  one and not the other." It reverses label order and the test does not see it.

Root cause, and it is not the one the report gives: `_PAIRED_STRATA`'s two strata are **equal-sized
(3 and 3) and their values differ by a constant 8** (1,2,3 against 9,10,11), so reversing the pool
order merely swaps which group consumes which RNG value — and every drawn difference shifts by the
same +24/6, i.e. not at all. That is the operative reason, and the unequal-size fixture below
confirms it by discriminating. A **second** reason the assertion is weak, worth stating so nobody
tries to repair the test by keeping this fixture and comparing sequences instead:
`PairedResample.pool` is `sorted(values)` on **both** return paths (`stats.py:1247`, `stats.py:1252`),
so `first.pool == second.pool` is a multiset comparison and a genuine resequencing of draws is
invisible on top of the translation symmetry. A test whose docstring asserts a guarantee no assertion
makes is a documented failure shape here.

**The discriminating fixture, built and verified.** Unequal-sized strata break the translation
symmetry: `A = {u0:1, u1:2}`, `B = {u2:3, u3:4, u4:100, u5:200}`, keys sorted, 100 draws. Under the
label-order mutation the relabelled call's pool **differs** (assertion would fail); after reverting to
the shipped `sorted(sorted(group) …)` the two pools **compare equal**. That fixture should replace or
join the current one.

### Minor

**4. The report's remediation claim for the blind mutation is false, and it is in the tracked
record.** `task-1-5-report.md` lines 87–105 say the mutation is blind because the strata are
contiguous, and that "a discriminating fixture would need the two strata interleaved (e.g.
alternating rather than contiguous membership)". Falsified exhaustively: over **all 729** label
assignments of three labels to six sorted keys — interleaved assignments included — content order and
insertion order produce **identical** pools, 0 differences. The reason is structural: `grouped`'s
label order is first-occurrence order over the `keys` walk, the first element of each `sorted(group)`
is `min(group)`, groups are disjoint, so lexicographic order of the sorted groups *is* first-occurrence
order whenever `keys` is ascending. The outer `sorted(...)` is a **mathematical no-op under the
sorted-`keys` contract** — `CLAUDE.md`'s "a mutation whose two branches cannot differ", which means the
brief's step 5 prescribed an unrunnable proof, not that the fixture was too small. The only input that
separates the two is an **unsorted** `keys` list (verified: `["u3","u4","u5","u0","u1","u2"]` gives
content `[[u0,u1,u2],[u3,u4,u5]]` against insertion `[[u3,u4,u5],[u0,u1,u2]]`), and no production call site can
produce one today for two separate reasons, only the first of which I verified by reading both sites:
**neither `cli.py:905` nor `cli.py:958` passes `strata` at all yet** (task 7 owns that wiring), and
both pass a sorted key list — `base_keys` from `paired_keys`, which returns `sorted(keys)`, and
`col_keys` an order-preserving filter of it. Correct the report's paragraph; a future reader will otherwise build the
interleaved fixture and find it equally blind.

**5. The sorted-`keys` contract is a genuine divergence from the sibling construction, and it lives
only in a comment.** `stats.percentile_of_derived` does `keys = sorted(collapsed)` itself
(`stats.py:1026`); `paired_percentile_of_derived` takes `keys` from the caller and its new comment
asserts "which `paired_keys` returns sorted" (`stats.py:1200`-ish). That unenforced contract is
exactly why finding 3/4's guarantee is unpinnable. Everything else about the dialect is **consistent**,
which I checked directly: the signature `strata: dict[str, str] | None = None` in last position
matches `percentile_of_derived` exactly (the `Sequence`-aligned form in `percentile_over_units` is the
value-based construction and correctly not copied); `strata` is indexed rather than `.get`-ed, same as
the sibling; and one drawn key list feeds both sides — verified by mutation, an independent second
draw for `table_b` is caught by `test_a_stratified_paired_draw_still_draws_once_for_both_sides`.
The one substantive difference is that the new code sorts each group defensively where the sibling
relies on pre-sorted keys — harmless.

**6. `Member`'s class docstring was not extended with the new field**, contrary to task 4's brief step
3 ("Extend the class docstring with the field's argument"). `correction.py:20-32` still enumerates
`pool`/`diffs` as "the evidence it was built from" with no mention of `weights`; the rule lives only
in `__post_init__`'s docstring. Also `weights: tuple[Any, ...]` is looser than the `Sequence[float]`
its eventual consumer (`stats._weighted_mean`) takes — a `tuple[str, ...]` constructs cleanly today.
Both are as-briefed for the type, so this is a note for task 9.

**7. `_section_text`'s control assertion is implied by another assertion in the same test.**
`tests/test_cli.py::test_the_weighted_contrast_record_keys_are_documented` asserts `"n_paired" in
section` as "the control", then `"n_paired_effective" in section` two lines down — the first is a
substring of the second, so the control cannot distinguish "the section was located" from "the slice
contains only the new paragraph". (I confirmed the section genuinely holds 8 bare `n_paired`
occurrences, so it is true, just not discriminating.) `CLAUDE.md`: "an assertion implied by another in
the same test". The sibling control in the same commit, `test_the_interval_construction_tables_are_parsed_at_all`,
is by contrast **genuinely discriminating** — I ran the parser and confirmed its four names span both
`| The interval | Is |` tables (13 names, 2 tables found), so losing either table fails it.

**8. `reference.md:2585` reuses the contrast `id: sensitivity` on a different axis.** The section's
existing examples declare `sensitivity` over `shift=abnormal`/`shift=normal`; the new results block
records `sensitivity` with `of: 02_arm=abnormal` / `against: 01_arm=normal`. A reader takes the two
blocks for one run. The block's internal arithmetic is sound (`family_size: 4` = 2 × 2,
`correction_level: 0.0125` = 0.05/4, Holm's tightest rank).

**9. The pre-existing `spec-defects.md` entry at line 5544 still names its owner "H4b"**, which this
slice has just split into H4b-1/H4b-2; the new entry at 6292 correctly names H4b-2 and cross-references
it. Re-owner the older entry when H4b-1 finishes, per `CLAUDE.md`.

## Verified by running, and what that covered

- **Full suite and all four gates**, foreground, clean (table above).
- **Mutations I re-ran myself**, each reverted by editing the file back, `__pycache__` deleted, and
  the revert verified by re-running the tests *and* an out-of-band probe — never `git checkout --`;
  `git status` clean at the end:
  - task 5, `pools = sorted(...)` → `pools = None`: `test_a_stratified_paired_draw_preserves_each_stratums_key_count`
    **FAILED** on the forced floor, as prescribed.
  - task 5, content order → insertion order: **PASSED** (blind), reproducing the report.
  - task 5, content order → **label order** (mine, not prescribed): **PASSED** — finding 3.
  - task 4, delete the length branch: `test_weights_of_a_different_length_than_the_differences_is_refused`
    **and** `test_weights_are_checked_even_when_ci95_is_none` both **FAILED**, as prescribed.
  - task 1, emit message reverted to the over-broad wording:
    `test_the_weight_refusal_does_not_promise_the_derived_estimators_will_weight` **FAILED**, as prescribed.
- **Exhaustive ordering proof** (729 label assignments) and two out-of-band probes of
  `paired_percentile_of_derived` with unsorted keys and with unequal-sized strata — findings 3, 4.
- **Mechanical pass over `docs/reference.md`**: no duplicate anchors, no trailing whitespace or tabs,
  no ragged table in any region this diff touched, every `#anchor` in the new prose resolves. The
  three ragged tables and the anchor misses my checker reported are pre-existing and outside the diff
  (my slugger's handling of `&`).
- **Claim checks in code**: `E-DATA-WEIGHT-CONTRAST` emit alive; `Member.weights` read by nothing but
  `__post_init__` (`grep -rn "\.weights\b" src/`); the new `spec-defects.md` entry's claims about the
  three siblings' content-based degenerate refusals confirmed in `stats.py:635`, `stats.py:891`,
  `stats.py:1037`; its "already recorded as deferred" cross-reference confirmed at
  `spec-defects.md:5544` (Finding 2 of that entry); the emitted string
  `"paired_percentile_over_units"` at `stats.py:1251` matches the new prose's claim about a derived
  metric's `method`; the narrowed `validate.py` comment's claim that a column contrast's closure
  "takes the plain collapsed row" confirmed against `_column_mean` at `cli.py:955`.

## What I read but could not check by running

- **Review point 2 — the corrected-bound trap — is unreachable at this stage, by design.** Task 4's
  brief explicitly excludes `_corrected_bounds` ("task 9 reads the field") and states the two-commit
  window where the field is written and read by nothing. So no test today would fail if
  `_corrected_bounds` dropped the weights, and none can: nothing passes weights to a `Member` yet, and
  the weighted raw interval does not exist until task 10. The field is pinned only by the three
  `__post_init__` tests, whose discriminating power I did verify. **Task 9 owns the raw-vs-corrected
  agreement**, and it must be a construction-level pin, not a field-presence one.
- The design's discriminating-fixture arithmetic (unweighted delta 6.0 / weighted 8.0, `cohens_d`
  1.3416… / 2.0, Kish 6 / 4.8) is not exercised by tasks 1–5 — nothing computes a weighted contrast
  yet. It appears only as `Member` constructor arguments in `test_a_member_may_carry_weights_alongside_its_differences`,
  which asserts field round-tripping and no arithmetic.
- Whether `n_paired_effective` and `weighted_by` reach any full `run.yaml` schema example elsewhere in
  `reference.md` — they are documented in § Contrasts prose and its own fenced block only, which is
  correct until task 8 emits them, but the completeness question belongs to task 8's review.
