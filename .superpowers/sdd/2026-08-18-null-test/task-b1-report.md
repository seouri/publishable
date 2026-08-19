# Batch report: tasks 27, 1, 2, 3, 4

**Status: complete.** All five tasks done, in the prescribed order (27 → 1 → 2 → 3 → 4), each its
own commit, gates clean.

## Commits

| Task | SHA | Subject |
|---|---|---|
| 27 | `8a474df` | H4d task 27: the regression pin, captured before any behaviour moves |
| 27 (fixup) | `fb60848` | H4d task 27: ruff format the pin fixture (gates clean) |
| 1 | `ef1d20c` | H4d task 1: fdr_bh ranks on p, and both adjustments defined before any code emits one |
| 2 | `c420227` | H4d task 2: where a p-value lands, and the two homes the document described that no run can produce |
| 3 | `2b7a190` | H4d task 3: the p-value record shape, including the derived level and the weights rule |
| 4 | `65858ff` | H4d task 4: the null_test method enum and the draw floor, with the inequality that fixes its integer |

`fb60848` is a small fixup discovered while checking gates after task 27: `uv run ruff format
--check .` wanted the `_PIN_MEMBERS` fixture in `tests/test_correction.py` reformatted (one
`Member(...)` per line rather than packed). No behavior change, split into its own commit per the
no-amend rule rather than folded into `8a474df`.

## Test summary

Baseline before this batch: 2275 passed, 1 skipped, 2 xfailed. After task 27's three new tests:
**2278 passed, 1 skipped, 2 xfailed** — held at that count through tasks 1–4, which are pure
document edits with no code and no new tests (as their briefs specify). Final full run at HEAD
(`65858ff`) reconfirms 2278/1/2. `ruff check`, `ruff format --check` (80 files, 0 to reformat), and
`mypy` (45 source files) all clean.

Task 27's mutation (`family_members`'s comprehension widened to `[e for e in entries]`) was applied,
run against the full unfiltered suite, and failed as prescribed: both
`test_a_member_with_no_interval_and_no_p_value_is_still_outside_the_family` (family_shape 4 vs 3) and
`test_holms_corrected_bounds_are_unmoved_by_the_p_value_work` (levels changed) failed, plus four
`test_cli.py` tests and two more `test_correction.py` tests as collateral (8 failed, 2270 passed
total) — a real mutation, not one caught only by a crash. Reverted by editing the line back
(`return [e for e in entries if e.ci95 is not None]`), re-run, confirmed green at 2278/1/2.

## Ruling for task 2: where a p-value lands

The landing-site table's ordinary-attribute row now reads **"where the metric is one a template's
`aggregate` derived from it"** and reports **"uncorrected — a per-condition estimate is not a
comparison, so it joins no correction family."** The group-axis row now lands **"On a declared
contrast entry, which is the only cross-arm comparison a run generates"** — never `vs_baseline`.
Grounds: the `vs_baseline` cell was H4c's finding one section over (a baseline fixing a group level
earns the permanent `E-SWEEP-BASELINE-GROUP`, and a parameter-only baseline expands over the group
axis so every generated comparison is within-arm), and the `aggregated:` example's own
`p_value_corrected: 0.0028` sat beside a `ci95` with no `ci95_corrected` — a record cannot correct one
description of a metric and not the other, so it was deleted rather than re-derived (×7 is not
derivable from any family the section describes). The example was re-authored as a derived metric
(`enrichment`, `percentile_over_units`) since a recorded column can carry no p-value at all (the null
would be the observed value repeated `n` times, p ≡ 1.0).

## Ruling for task 3: the record shape

`p_value`/`p_value_corrected`/the resolved `null_test: {method, n, shuffle, level}` echo and
`null_draws` were added on the `resample` echo's exact absent-not-null precedent — first named where
the `resample` echo paragraph already lives (§ Statistical reporting, right after the
`E-DATA-CLUSTER-DERIVED` paragraph, before "Resample methods"), and the contrast-entry pair
(`p_value`/`p_value_corrected`) was added in § Contrasts right after the `n_paired`-is-the-intersection
paragraph, before the `weight_by` paragraph — matching the brief's "the paragraph enumerating a
contrast entry's fields." `level` is recorded as derived-only (never a config input); the weights
rule (a relabelling permutes the label, never the weights) is one sentence, not a construction, since
no weighted contrast cell is reachable to permute.

## Ruling for task 4: the floor

Per the design spec's own appended § Corrections against the code (correction 2), `ceil(1/level) − 1`
gives 19 and 39 against the spec's own stated 20 and 40; `math.floor(1.0/level)` reproduces both and
matches the strict inequality `1/(n+1) < level`. Verified independently: `1/level` = 20.0, 40.0,
60.0 for α, α/2, α/3; `floor` gives 20/40/60 in all three cases, `ceil − 1` gives 19/39/59. Wrote
`math.floor(1.0 / level)` per the brief and the spec's correction, with the one-ulp caveat at
`level = 0.05/7` (brute force answers 139, `floor` answers the exact-arithmetic 140) documented
verbatim.

## Disagreements between the briefs/spec and the actual repo state

1. **Task 27's fourth document-pin literal does not exist in `docs/reference.md`.** The brief
   instructs pinning four literals from `CLAUDE.md`'s worked example, including kendall's
   per-condition CI `[0.347, 0.477]`. Grepped at the branch point (`a207702`, unchanged through HEAD
   before this batch): the first three literals (`ci95: [-0.007, 0.059]`, `[0.488, 0.661]`,
   `[0.517, 0.683]`) are present; `[0.347, 0.477]` is **not** — it appears only in `README.md`'s demo
   table. `docs/reference.md` never spells out kendall's raw per-condition interval, only its
   baseline delta (`[-0.213, -0.125]`, which does appear, matching CLAUDE.md's "kendall's is
   −0.169, [−0.213, −0.125]"). This is the "provably unbuildable" pin failure mode named in the
   task instructions: asserting a string that was never there would pass for the wrong reason (or
   fail immediately, depending on framing) rather than guarding anything. I wrote the pin test with
   only the three present literals and documented the omission in the test's own docstring, verified
   by `grep -c '0.347' docs/reference.md` returning 0 both before and after this batch's edits.

2. **Task 2's "can-fail control" claim is false for two of the four documents.** The brief says to
   prove the `vs_baseline` sweep can fail "by running it against `contrasts`, which is present in all
   four [documents]." Measured: `contrasts` (or any case-insensitive `contrast`) appears zero times
   in `docs/design-principles.md` and zero times in `README.md` — only `docs/reference.md` (62 hits)
   and `docs/experimental-designs.md` (9 hits) carry it. The `vs_baseline` sweep itself worked
   correctly regardless (real hits were found and read in `docs/reference.md`, none routing a
   group-axis p-value into `vs_baseline` after the fix), so this doesn't change the ruling — it's a
   brief inaccuracy in the verification recipe, not a defect in the work.

No other brief/code disagreements found in tasks 1–4 and 27 beyond the two above; all interfaces
(`Member`, `corrected_fields`, `family_members`, `family_shape`, `rank_family`) matched the brief's
consumed signatures exactly, and no code was touched by tasks 1–4 (pure document edits, "no
mutation" as their briefs state).

## Concerns

- None blocking. The two disagreements above are documented in-line (task 27's test docstring
  explains the dropped literal) so a later reader isn't surprised.
- `E-STATS-NULLTEST-UNSUPPORTED` remains alive throughout, as required — nothing in tasks 1–4/27
  touches validate-time behavior or retires any code.
- Final state at `65858ff`: `uv run pytest` → 2278 passed, 1 skipped, 2 xfailed (baseline 2275 + 3
  new task-27 tests); `ruff check .`, `ruff format --check .` (80 files), and `mypy` all clean.

---

## Fix round 1

Review: `.superpowers/sdd/2026-08-18-null-test/task-b1-review.md`, verdicts PASS/PASS with one Major
each. Both credited items (task 27's exact literals + discriminating mutation, and each member's own
α pinned) required no change. Fixed below in review order.

### M2 — the pin guarded member identities, not inner keys, and `holm` alone

Changed: `tests/test_correction.py`. Added `_PIN_INNER_KEYS = {ci95_corrected, correction,
correction_level, family_size, family, thin}` and, for every block returned under `holm`, an
`assert set(fields[key]) == _PIN_INNER_KEYS` alongside the existing per-member value assertions.
Added two new tests, `test_bonferronis_corrected_bounds_are_unmoved_by_the_p_value_work` and
`test_fdr_bhs_corrected_bounds_are_unmoved_by_the_p_value_work`, pinning the same `_PIN_MEMBERS`
family under `bonferroni` (all three at `correction_level` 0.0166…, with their own `ci95_corrected`
literals) and `fdr_bh` (`ci95_corrected: None`, `correction_level: None`, `thin: False` for all
three), each also asserting the inner key set.

Verified by running: computed all three methods' outputs against `_PIN_MEMBERS` directly
(`corrected_fields(ms, method)` for `holm`/`bonferroni`/`fdr_bh`) and confirmed the literals matched
the reviewer's captured baselines exactly before writing them into the test. `uv run pytest
tests/test_correction.py -q` → 47 passed.

**Re-ran the mutation against the widened pin**, per the coordinator's instruction: widened
`family_members`'s comprehension to `[e for e in entries]`, cleared `__pycache__`, ran the full
unfiltered suite. Result: **10 failed, 2270 passed** (up from the original 8 failed) — all three of
`test_holms_corrected_bounds_are_unmoved_by_the_p_value_work`,
`test_bonferronis_corrected_bounds_are_unmoved_by_the_p_value_work`, and
`test_fdr_bhs_corrected_bounds_are_unmoved_by_the_p_value_work` now fail, alongside the same
`test_a_member_with_no_interval_and_no_p_value_is_still_outside_the_family` and the same four
`test_cli.py`/two shipped `test_correction.py` collateral failures as before. Reverted by editing the
line back to `return [e for e in entries if e.ci95 is not None]`; diffed byte-for-byte against a
pre-mutation copy (identical); re-ran, confirmed green.

### M1 — `null_draws` had no example and an undetermined placement

Changed: `docs/reference.md`, two sites. (1) The § Statistical reporting `null_test` echo paragraph
now states placement explicitly: "`null_draws` is what the p-value actually rests on, on
`resample_draws`'s own precedent **and at the same place in the record**: a metric-block sibling of
`null_test`, not a key inside it — `resample_draws` sits beside `resample` rather than inside its
map, and `null_draws` sits beside `null_test` the same way." (2) The § What isn't a repeat `enrichment`
example — the sole p-value-carrying record example in the four documents, and a *derived* metric,
which the prose says is exactly where `null_draws` can differ from `n` — now shows
`null_draws: 4998` beside `resample_draws: 2000` in the metric block (not nested inside the
`null_test: {...}` echo), with a new paragraph explaining the two-short count (two relabelled tables
where the shuffle emptied an arm) and stating a recorded column's `null_draws` equals `null_test.n`
exactly.

Verified by: re-reading both edited paragraphs in full (not just the changed sentence, per
`CLAUDE.md`'s docstring rule); confirming `null_draws` now appears in `docs/reference.md` twice more
than before (`grep -c null_draws` → 3, was 1) with one of the three inside a worked-shape example;
confirming the placement sentence answers the review's exact ambiguity (echo member vs. metric-block
sibling) by naming the `resample_draws`/`resample` pair as the analogy rather than restating "beside
it."

### m6 — positional table-row locator ("by the row above")

Changed: `docs/reference.md:2191` (renumbered after the M1 edit). "`ci95_corrected` is `null` for
every member, by the row above" → "`ci95_corrected` is `null` for every member, which is what the
`correction` table's `fdr_bh` row states" — names the row by what it contains rather than by its
position in the file, per `CLAUDE.md`'s ban on the construct. Verified by re-reading the paragraph in
file order and confirming no other positional locator ("above"/"below"/"the two rows") survives in
the sentence.

### m7 — an insertion pushed "the second row" away from its table

Changed: `docs/reference.md`. "The second row isn't an exception to the first" → "The
[`groups`](#expansion-modes)-axis row isn't an exception to the ordinary-attribute row" — names both
referents instead of counting rows, so a later insertion between this sentence and the table cannot
break it again. Verified by re-reading in file order with the new `null_draws` paragraph and the
re-authored example both now sitting between this sentence and the landing-site table, confirming the
sentence reads correctly regardless of what sits between it and the table.

### m3 — task 28's site list omitted § Between-subjects, which holds the stronger stale clause

Changed: `docs/superpowers/plans/2026-08-18-null-test.md`, task 28 step 4 (not
`experimental-designs.md` itself — the review is explicit that the plan's late-documents task owns
the fix, and this batch's job is only to record the omission where that task will find it). Added
"§ Between-subjects" to the site list beside "§ Bootstrap and permutation, § Matched case-control and
§ Allocation," and a note naming the specific stale clause ("derived from... rather than declared
separately") and why it is the stronger of the two — it is wrong about whether the comparison exists
at all now, not only about its pairing, against `docs/reference.md`'s new "A cross-arm comparison
exists only as a declared `statistics.contrasts` entry." Verified by re-reading task 28 step 4 in full
after the edit to confirm the added sentence doesn't contradict the surrounding "read them, do not
grep for a spelling" instruction it sits beside.

### m4 — the document pin's docstring claimed more than it guards

Changed: `tests/test_validate.py`. Renamed
`test_the_worked_examples_intervals_are_not_narrowed_by_the_null_test_work` to
`test_the_worked_examples_intervals_in_reference_md_are_not_narrowed_by_the_null_test_work`, and
reworded the docstring's second paragraph to open with "Guards `docs/reference.md` only" rather than
stating the omission as an aside. No assertions changed. Verified by running
`tests/test_validate.py -k worked_examples` (still the sole match) and confirming the new name and
opening sentence match exactly what the function's body reads and asserts — `docs/reference.md` and
nothing else.

### m8 and m9 — confirmed, no action owed by this batch

**m8** (forward `[refused]` link to `E-STATS-NULLTEST-REPORTBY`, no row yet): re-read
`docs/superpowers/plans/2026-08-18-null-test.md` Task 5's step 2, which mints the § Errors row for
this exact code as part of task 5's own commit. Confirmed rather than fixed, per the review's either/or.

**m9** (§ Validation's *Null test coherence* row still says "unit attribute," pre-existing tension
with the group-axis landing table): re-read task 28 step 1, which already restates this row's
condition to "name the `sweep.groups` union and the `method`/`n` faults." Already owned and recorded;
no additional edit needed.

**m5** needed no action, per the review (already owned by the plan and `spec-defects.md`).

### Final verification

`uv run pytest` (full, unfiltered, foreground) → **2280 passed, 1 skipped, 2 xfailed** (2278 + 2 new
`bonferroni`/`fdr_bh` pin tests). `ruff check .` → all checks passed. `ruff format --check .` → 80
files already formatted. `mypy` → 45 source files, no issues. `git status` clean after four fix
commits: `96815f9` (M2), `acccda7` (M1, m6, m7), `1273247` (m3), `6a22630` (m4).
