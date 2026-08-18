# Batch 3 report: tasks 10, 11, 12, 13 (+17a)

**Status: all four tasks complete, committed separately, full suite green after each.**

## Commits

| Task | SHA | Subject |
|---|---|---|
| 10 | `730551c` | feat: the unpaired key path, n_of/n_against and the per-side cluster counts |
| 11 | `3900661` | feat: Member's third evidence kind, and the exactly-one rule counted over pool/diffs/sides |
| 12 | `f39b40b` | feat: _corrected_bounds' two unpaired arms — the Welch forms rebuilt at a smaller alpha |
| 13 (+17a) | `4c91108` | feat: paired derived at every contrast branch, and the source-text pin replaced by a behavioural one |

## Test summary

Final full suite (after task 13): **2252 passed, 1 skipped, 2 xfailed.** Deltas matched each brief's
stated arithmetic: task 10 +7 (2235→2242), task 11 +4 (2242→2246), task 12 +4 (2246→2250), task 13 +2
net (2250→2252, one test renamed/replaced, two added). All four gates (`pytest`, `ruff check`,
`ruff format --check`, `mypy`) clean at every commit.

## Task 9's mutation (re-applied and verified before any new work)

`contrasts.crossed_group_axes` mutated to bare `return differing_axes(of, against)` (dropping the
`& (of.selectors | against.selectors)` intersection). Ran the full, unfiltered suite: **90 failed**,
2145 passed, 1 skipped, 2 xfailed. It discriminates strongly — task 9's pin is not a no-op. Reverted by
editing the file back (never `git checkout --`), cleared `__pycache__`, re-ran: 2235 passed, 1 skipped,
2 xfailed, matching the stated baseline exactly.

## Task 11 ruling

`UnpairedEvidence` was implemented as a **new evidence kind**, not a fourth modifier: `Member.sides:
UnpairedEvidence | None = None`, and the exactly-one rule was recast as a count over
`pool`/`diffs`/`sides` rather than a second equality. Grounds: a Welch interval's evidence is two
independent per-side value vectors — neither a pool nor a difference vector — so it cannot be
expressed as a modifier on `diffs` the way `weights`/`clusters` are. Both existing modifiers gained a
"never beside `sides`" check in `Member.__post_init__`, checked before the exactly-one rule's early
return. `UnpairedEvidence` owns its own per-side cluster-label alignment invariant in its own
`__post_init__`, because a modifier's length invariant belongs to the object that defines the vectors
it aligns against — a flat cluster pair on `Member` beside `sides` would be one field with two
admissible shapes.

## Brief/code disagreements found and how they were resolved

1. **Task 10's `min_reported_n` placeholder expression was wrong as written.** The brief's literal —
   `len(col_keys) if is_paired else min(len(of_col), len(against_col))` — references `col_keys`, which
   is only ever bound in the recorded-column (non-derived) branch. A derived, paired, `within`-scoped
   metric (exercised by the pre-existing `test_a_thin_within_contrast_warns`, whose contrast metric `r`
   is computed by `aggregate`) hits `is_paired=True` with `is_derived=True`, and `col_keys` is unbound
   there — confirmed by running the suite, which raised `UnboundLocalError`. Deviated to
   `(len(base_keys) if is_derived else len(col_keys)) if is_paired else min(len(of_col),
   len(against_col))`, matching the same expression the record literal itself uses for `n_paired`.
   Documented the deviation inline.

2. **Task 10's record-literal ternary for the derived branch tripped `ruff`'s F821.** The brief's
   snippet — `{"n_paired": len(base_keys) if is_derived else len(col_keys)}` — written inside the
   `if is_derived:` branch (where `is_derived` is always `True` there) makes `col_keys` reachable-in-
   text but never-executed; pyflakes still flags it as an undefined name on that control-flow path
   (confirmed with a minimal repro). Simplified to `{"n_paired": len(base_keys)}` in that branch only,
   since `is_derived` is trivially `True` there; the recorded-column branch keeps `len(col_keys)`
   unconditionally for the same reason.

3. **Task 10 required updating a pre-existing count-based test.**
   `test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch` hardcoded
   `source.count('"paired": True') == 2`; task 10 legitimately adds two more literal sites (the two new
   unpaired arms), so the count became 4. Updated the assertion and docstring rather than leaving it
   red. Task 13 later replaced this whole test with the behavioural pin, as its own brief specified.

4. **Task 12 mutation 1's predicted magnitude did not match the measured one.** The brief predicted the
   clustered-arm-dropped mutation would land the half-width "near 41.9" (implying a ratio of 1.2276 at
   df 8.399); the actual measured value on that fixture was 11.485 (`1.348 mean... ` — see the raw
   Welch interval computed directly). The mutation still correctly **FAILED** the discriminating test on
   the expected assertion; only the specific predicted number was off. Recorded rather than silently
   corrected.

5. **Task 12 mutation 4's predicted discriminating test was not the one that actually failed.** The
   brief named `test_the_five_t_arms_are_each_reached_by_one_member_shape` as the test that would fail
   on the distinctness assertion. Measured: that test stayed **green** (the centre-flip changes the
   `sides_clustered` arm's bounds tuple, but it still lands distinct from the other five, so the `== 6`
   count holds). The mutation was still caught by the full, unfiltered suite —
   `test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts` failed instead,
   via a `zip()` length-mismatch `ValueError` (its fixture's `of`/`against` differ in length, 9 vs 12,
   so swapping them without swapping the label vectors crashes before reaching any centre-flip
   arithmetic). The qualitative claim ("this mutation is caught") held; the specific attribution in the
   brief did not. Followed the brief's own instruction to record this rather than force the named test
   to be the one that fails.

No other brief/code disagreements were found. All prescribed mutations were run against the full,
unfiltered suite in the foreground and reverted by editing the file back; none were left applied.

## Fix round 1 (review at `task-b3-review.md`, reviewed at `908d273`)

Status: all findings closed except none — every Major and Minor addressed. Commit: `2b2674c`.
Baseline reproduced before touching anything: **2252 passed, 1 skipped, 2 xfailed**; same after every
fix and every mutation revert.

**Task 9's mutation, corrected figure (appended, not edited into the original entry above).** Re-ran
the same mutation (`crossed_group_axes` collapsed to bare `differing_axes(of, against)`) at commit
`908d273`/current tree: **126 failed, 2126 passed**, not the 90 recorded when task 9 was first measured
at `9218516`. Both numbers are genuine — the predicate gained a second caller (`cli._comparison_step_blocks`,
tasks 10–13) between the two measurements, so its blast radius grew with the suite. Reverted by editing
the file back; suite returned to 2252/1/2.

### Major 1 — `test_the_five_t_arms_are_each_reached_by_one_member_shape` claimed a guarantee its body did not make

**Changed:** rewrote the test body to call each of the five *t* constructions directly
(`welch_t_over_units_clustered`, `welch_t_over_units`, `paired_t_over_units_clustered`,
`weighted_paired_t_over_units`, `paired_t_over_units`) at `confidence=0.975` and assert
`_corrected_bounds(member, 0.025) == (interval.low, interval.high)` for each, plus the pool arm against
`interval_at(pool, 0.975)`; kept the distinctness assertion as an additional, narrower check. Replaced
both `sides` fixtures' 3-vs-3 geometry with unequal per-side sizes: `sides_clustered` is now 4 (2
clusters) against 3 (2 clusters), `sides_plain` is now 3 against 4.

**Verified by:**
- The rewritten test passes standalone (`uv run pytest tests/test_correction.py -k five_t_arms` → 1
  passed) and in the full suite.
- **Mutation 1 re-run against the repaired test** (`_corrected_bounds`' `sides` branch collapsed to
  always call `welch_t_over_units`, dropping the clustered check): full suite → **2 failed, 2250
  passed** (up from the review's 1 failed) — `test_the_five_t_arms_are_each_reached_by_one_member_shape`
  now fails on `sides_clustered` (`assert (-10.0073…) == (-23.8586…)`) alongside the pre-existing
  `test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts`. This is what
  closes Major 1: the test now fails under exactly the mutation its docstring names. Reverted by editing
  the file back; suite returned to 2252/1/2.

### Major 2 — the clustered `sides` arm's centre was unpinned

**Changed:** added `assert (bounds[0] + bounds[1]) / 2 == pytest.approx(12.833333333333332)` to
`test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts`, and a paragraph
explaining why (half-width alone is blind to a swap that only flips the centre).

**Verified by:**
- **Mutation 4 re-run against the repaired test** (`member.sides.of`/`member.sides.against` swapped in
  the clustered call only, labels left in place): full suite → **2 failed, 2250 passed**, both failures
  the same `zip() argument 2 is longer than argument 1` `ValueError` at `stats.py:550` as the review
  found — because both `sides` fixtures are now (correctly, per Major 1's fix) length-asymmetric, so a
  value-only swap without swapping the label vectors is an invalid call on *either* fixture, not just
  fixture B. The prescribed mutation still cannot reach the new centre assertion by construction; this
  is recorded rather than concealed.
- **A supplementary mutation that isolates the centre**, to prove the new assertion is not vacuous:
  in `stats.welch_t_over_units_clustered`, changed `delta = sum(of) / len(of) - sum(against) /
  len(against)` to `delta = sum(against) / len(against) - sum(of) / len(of)` (sign flip only; half-width
  arithmetic untouched). Full suite → **1 failed, 2251 passed**:
  `test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts` failed on
  `assert (bounds[0] + bounds[1]) / 2 == pytest.approx(12.833333333333332)` (`Obtained:
  -12.833333333333336`), with the half-width assertion still passing — confirming the new line is what
  catches a real centre-only defect. Reverted; suite returned to 2252/1/2.

**Note on disagreement 5's adjudication:** the review's ruling stands — the brief's "tuples DO move, so
it discriminates" reasoning was wrong, and qualitative "this mutation is caught" was not enough because
what caught it was a crash rather than a check. The fix closes the actual gap (centre unpinned); the
prescribed mutation's own crash-vs-check distinction is unchanged by the fix, since it is a property of
that specific value-only-swap mutation on a mandatorily-asymmetric fixture, not of the test.

### Minor 1 — `UnpairedEvidence.__post_init__`'s "every fixture" claim

**Changed:** deleted "the two sides here are deliberately different lengths in every fixture" (false —
three fixtures at the time were 2-vs-2), kept the domain reason (equal sizes make pooled and Welch SEs
coincide), and added one clause noting that a discriminating fixture needs unequal sides as a property
fixtures must choose rather than one the type enforces.

**Verified by:** re-read the paragraph after editing; grepped `test_correction.py` for remaining
2-vs-2 `UnpairedEvidence` fixtures (`test_a_member_carries_exactly_one_of_pool_diffs_and_sides`,
`test_a_member_may_not_carry_a_modifier_beside_sides` — both still legitimately 2-vs-2, since they test
the exactly-one/modifier rules and not the Welch construction, so the claim never applied to them
either). Full suite green.

### Minor 2 — cli.py's "cannot coincide" comment

**Changed:** deleted "Two integers that cannot coincide, which is what makes them a stronger
discriminator than any float here" from the production comment above `n_clusters_of`/`n_clusters_against`;
kept "Per side once the sides are disjoint, and Welch's df reads both." The qualified version of the
claim ("on this fixture") stays in `tests/test_cli.py`'s docstring, where it is true.

**Verified by:** re-read the comment in place; grepped `src/` for `cannot coincide` (zero hits after the
edit). Full suite green.

### Minor 3 — two stale quantifiers in `cli.py`

**Changed:**
- `:829-858` (now shifted): narrowed "A recorded column takes…" and "A derived metric…takes…" to open
  with "On the paired arm (`is_paired`)", and replaced "Both constructions read `n_paired` off
  `stats.paired_keys`" with "Both **paired** constructions read `n_paired` off `stats.paired_keys`",
  adding one closing sentence: "The unpaired arm reads `stats.unpaired_keys` instead, has no
  intersection to report, and records `n_of`/`n_against` in `n_paired`'s place."
- `:1295` (now shifted): "`Member` requires exactly one of `pool`/`diffs`" → "exactly one of
  `pool`/`diffs`/`sides`", with a clause noting `_comparison_step_blocks` never builds `sides` yet (task
  14's), so only `pool`/`diffs` are reachable from this function today.

**Verified by:** re-read both comments' whole paragraphs after editing (per the instruction to re-read
the whole comment, not just the sentence). Full suite green; no test pins either comment's text, so
this is a reading-only check.

### Minor 4 — a caller enumeration re-introduced in `crossed_group_axes`' docstring

**Changed:** replaced "`validate` refuses `weight_by` beside a non-empty answer, and
`cli._comparison_step_blocks` derives the `paired` it records from the same answer" with "read wherever
a comparison's pairing matters", dropping both named call sites while keeping the drift argument
("two spellings of one rule drifting apart is a defect this codebase has already shipped").

**Verified by:** grepped `src/publishable/contrasts.py` for `_comparison_step_blocks` and `validate
refuses` (zero hits after the edit); confirmed no test pins `crossed_group_axes.__doc__` (only
`differing_axes.__doc__` is pinned, by `test_differing_axes_docstring_names_no_caller`, untouched). Full
suite green.

### Minor 5 — the thin-warning message still naming `n_paired`

**Changed:** added one sentence to the existing "Task 16 owns…" comment: "The message text below still
says `n_paired {reported_n}` on the unpaired arm, naming a key that entry does not carry — task 16's to
reword, not this task's, since the message itself is explicitly its scope." Left the message and the
placeholder untouched, per the finding's own instruction not to half-fix it.

**Verified by:** re-read the comment in place; confirmed it now names both the placeholder *and* the
message text as task 16's, rather than only the former. Full suite green.

### Gates and mutation discipline

All four gates clean at the fix commit: `uv run pytest` → 2252 passed, 1 skipped, 2 xfailed; `ruff
check .` → all checks passed; `ruff format --check .` → 80 files already formatted; `mypy` → no issues
in 45 source files. Every mutation in this round (task 12 m1, task 12 m4, the supplementary centre-sign
flip, task 9's re-measurement) was run against the full, unfiltered suite in the foreground and reverted
by editing the file back — never `git checkout --` — with `__pycache__` cleared and the suite re-run to
confirm the revert each time. No sentence added in this round claims a config is unblocked.
