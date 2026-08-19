# Review: batch 1 (tasks 27, 1, 2, 3, 4) — `h4d-null-test`

Reviewed at HEAD `f0f300a`, against the branch point `a207702`. `docs/superpowers/spec-defects.md`
and the implementation plan were both read before filing anything, and two of my draft findings moved
because they are already owned there.

## Verdicts

**Spec compliance: PASS with one reservation.** Every ruling in the design spec's decisions 1–3, 5–7
and 9, plus § Corrections against the code 2, is in `docs/reference.md` in the form the spec fixes.
No `CLAUDE.md` invariant is contradicted: the p-value **adds no place in the family** and is corrected
**at the level the interval was computed at** at every new site; `E-STATS-NULLTEST-UNSUPPORTED` is
alive (`src/publishable/validate.py:4030`) and `null_test: null # NOT BUILT` still stands at
`docs/reference.md:156`; **no sentence claims a config was unblocked** — the zero/six/three counts are
untouched in the four documents, and the only "unblocks" strings in the branch's `docs/` diff are the
plan's and progress ledger's *"H4d unblocks ZERO configs"*. The reservation is M1: `null_draws` is
normative prose with no example anywhere and an undetermined placement.

**Task quality: PASS with one Major.** Task 27's literals are exact (verified by running the brief's
own script), its mutation genuinely discriminates on assertions rather than a crash (verified by
running the full unfiltered suite), and each member's **own** correction level is pinned — the hole
H4b-1 left is closed here. The Major is what the pin does *not* constrain: the inner key set, and
every method but `holm`.

Gates, all run: `uv run pytest` → **2278 passed, 1 skipped, 2 xfailed** (before my mutation and again
after reverting it); `ruff check .` clean; `ruff format --check .` → 80 files already formatted;
`mypy` → 45 source files, no issues. **The tree is clean** (`git status` empty apart from this file).

---

## The five items, answered

**Item 1 — does task 27 discriminate, and how far does it reach?** Its literals match today's code
exactly: I ran the brief's step-1 script and got `(3, {'comparisons': 3, 'metrics': 1})`, rank order
`['cond:2','cond:1','cond:3']`, and levels 0.05/3, 0.025, 0.05 with bounds identical to the digit.
Each member's **own** level is pinned by three separate assertions, so the H4b-1 α hole is covered.
The mutation is real — see M2 for what it still does not reach.

**Item 2 — the dropped literal.** The implementer's claim is true: `[0.347, 0.477]` (and `0.412`)
appear only at `README.md:64`; `docs/reference.md` spells out only kendall's *delta*
`[-0.213, -0.125]`. **The distribution is legitimate and its absence is not a defect** — `CLAUDE.md`
requires a value be changed "everywhere **it appears**", and it already records deliberate per-file
differences between README and `reference.md`. See m4 for the smaller thing that is owed.

**Item 3 — the two unproducible homes.** Both repaired. The group-axis row now lands "On a
[declared contrast] entry, which is the only cross-arm comparison a run generates"
(`docs/reference.md:1971`), with the `vs_baseline` word gone and the reason stated beneath the table
(`:1974`). I confirmed the ruling against the code, not just the prose: `resolve_contrasts`
(`src/publishable/contrasts.py:194`) states and implements "A run with no baseline and no
`statistics.contrasts` compares nothing", and `E-SWEEP-BASELINE-GROUP` is emitted at
`src/publishable/validate.py:4686`. The per-condition row reads "and **uncorrected** — a per-condition
estimate is not a comparison, so it joins no correction family" (`:1970`), and the example's
`p_value_corrected: 0.0028` is **deleted with no replacement number** (`:1994–1997` now shows
`p_value: 0.0004` and no corrected key at all). Third-site sweep: I read for the claim across all four
documents, not for one spelling — two hits in `experimental-designs.md` (m3), none in
`design-principles.md` or `README.md` (positive control per file: `statistics` → 4 and 5 hits, so the
sweep can find text in both).

**Item 4 — the Bonferroni cell.** The cell now reads "`p_value_corrected` when a [`null_test`]
supplied a p-value" (`docs/reference.md:2152`), matching the `holm` row. It agrees with
§ Statistical reporting's new definition and with `CLAUDE.md`'s correction invariant: the p-value adds
no family place (`:2535` unchanged: "**It does not add a place in the family**") and is expressed at
the level the interval was computed at. **Verified by running** that the documented general form
reduces to both cell expressions on the pin family: under `bonferroni` all three members carry
`correction_level` 0.0166…, so `p × α/level` = `p × 3` = `p × m` ✓; under `holm` cond:1 carries 0.025,
so `α/level` = 2 = `m − i + 1` at rank 2 of 3 ✓. The **monotonicity disclaimer is present and correctly
scoped** (`:2165–2171`): "**This is not Holm's step-down adjusted p-value, and it is not monotone in
the raw p.** There is no prefix maximum: a member with a smaller raw p can carry a larger adjusted
one", with `fdr_bh` explicitly carved out to its own paragraph — and that paragraph is the one place
an accumulation is described ("a running minimum from the largest *i* down").

**Item 5 — the floor.** I recomputed it: `floor(1/level)` → **20 / 40 / 60** at α, α/2, α/3, against
`ceil(1/level) − 1` → 19 / 39 / 59, and a brute-force scan of the strict inequality → 20 / 40 / 60,
with the documented one-ulp caveat reproduced exactly (`level = 0.05/7`: brute force 139, `floor`
140). The document states the **strict** form — "can fall **strictly below** the level being tested:
`1/(n + 1) < level` gives `n > 1/level − 1`, so `n ≥ ⌊1/level⌋`" (`:2581–2586`) — and no `ceil` or `⌈`
residue survives anywhere in `reference.md`. `min_honest_permutations` is **not** conflated with
`min_honest_draws`: the paragraph opens by distinguishing them, and `min_honest_draws`' only other
occurrence (`:2156`) is the resample family bound, unchanged.

---

## Findings

### Critical

None.

### Major

**M1. `null_draws` is named in prose and appears in no example in any document, and its placement is
undetermined.** `docs/reference.md:2546`: "`null_test.n` is what was *requested*; **`null_draws`
beside it is what the p-value actually rests on**". *Verified by running:* `grep -rn 'null_draws'
docs/*.md README.md` → **one** hit, prose only. The batch re-authored the one p-value-carrying record
example in the same batch (`:1994–1997`) as a **derived** metric — precisely the case the prose says
can differ from `n` — showing `resample_draws: 2000` and the `null_test` echo but no `null_draws`.
This is `CLAUDE.md`'s *Schema fields in prose* class, and it is the one place this batch fails its own
premise that the record shape lands before code emits it: the echo is enumerated `{method, n, shuffle,
level}` and `null_draws` is "beside it", so whether it is a **member of the echo** or a **metric-block
sibling** (which is what `resample_draws` is) is not decided. Tasks 19/20 will guess. Fix: add
`null_draws` to that example at the placement intended, in one line.

**M2. Task 27's pin covers each member's level but not the inner key set, and only `holm`.**
*Verified by running* the brief's script: each member's block is
`{ci95_corrected, correction, correction_level, family_size, family, thin}`. The test asserts
`set(fields) == {...}`, which pins the **outer** keys (member identities) — nothing constrains the
inner key set, so tasks 17/18 can begin emitting `p_value_corrected` into every member's block,
including a spurious `None` under `holm`, with this pin green. And `corrected_fields` is exercised
under `holm` alone, while decision 3 changes Bonferroni's behaviour and task 18 rewrites
`corrected_for` two-pass for BH — the same function. The unpinned baselines, which I captured while
verifying: `bonferroni` → all three at `correction_level` 0.0166…; `fdr_bh` → `ci95_corrected: None`,
`correction_level: None`, `thin: False`. Fix, before task 16: add
`assert set(fields[("cond:1","s","m")]) == {...}` and a `bonferroni`/`fdr_bh` arm to the same pin.

### Minor

**m3. Two `experimental-designs.md` passages now contradict a normative absolute this batch minted,
and the later task chartered to sweep them does not name one of the two sites.**
`docs/experimental-designs.md:79` (§ Between-subjects / parallel-arm trial): "The arm-to-arm comparison
is unpaired, **derived from** the fact that the two conditions differ on the `groups` axis **rather
than declared separately** … `statistics.null_test` with `shuffle: arm` tests that contrast directly …
core attaches the p-value to the contrast". `docs/experimental-designs.md:332` (§ Matched
case-control): "Core reports each arm and their contrast … the p-value attaches to the case-vs-control
contrast". Neither design's YAML declares `sweep.baseline` or `statistics.contrasts`, and
`resolve_contrasts` compares nothing in that state (*verified by reading*
`src/publishable/contrasts.py:194`) — so against `docs/reference.md:1974` ("A cross-arm comparison
exists only as a declared `statistics.contrasts` entry") the first sentence is wrong about the
comparison itself, not merely about its pairing. **Not filed against this batch's tasks**: the plan's
late documents task (step 4) already owns "Check § Bootstrap and permutation, § Matched case-control
and § Allocation for sentences the retirement makes stale". The finding is that **§ Between-subjects
is not on that list**, and it holds the stronger of the two clauses. Add it to that task's site list.
The ground is `CLAUDE.md`'s **cross-document** pass, which runs on the four documents after any `.md`
edit; task 2 step 5 asked only for the mechanical pass on the edited file, and a brief does not
outrank `CLAUDE.md`.

**m4. The document pin's docstring claims more than the pin guards.** `tests/test_validate.py`'s
`test_the_worked_examples_intervals_are_not_narrowed_by_the_null_test_work` is named for "the worked
example's intervals" and guards three of the four, and README's copy of the fourth is pinned nowhere.
The omission is correctly explained in the docstring, so this is a naming/coverage nit, not a false
claim: read `README.md` in the same test, or narrow the name and docstring to `reference.md`'s subset.

**m5. `W-STATS-CORRECTION-INAPPLICABLE`'s condition is momentarily stated three ways — owned, and
verified as owned.** Task 1 gave the paragraph (`docs/reference.md:2176–2181`) **three** disjuncts;
the § Validation row (`:333`) still carries **two**, and the § Warnings row (`:387`) a **different
two**. *Verified by reading* the diff (the paragraph previously matched row 333 verbatim), and
*verified as scheduled* by reading the plan's late documents task, step 3: "confirm …
`W-STATS-CORRECTION-INAPPLICABLE`'s row states the **three-disjunct** condition rather than the old
one", and `docs/superpowers/spec-defects.md` (the `fdr_bh` warning entry), which already names the
three-disjunct row and its owner. Filed here only so the divergence is visible on the branch in the
meantime; **no action owed by this batch**.

**m6. Positional table-row locator introduced.** `docs/reference.md:2186`: "`ci95_corrected` is `null`
for every member, **by the row above**" — the `fdr_bh` row is five paragraphs up after this batch's
insertions. `CLAUDE.md` bans the construct outright ("Name what a sibling row *does*"); it came from
task 1's brief, which does not outrank `CLAUDE.md`. *Verified by* reading the section in file order.

**m7. An insertion moved a referent.** `docs/reference.md:1999` — "The second row isn't an exception to
the first so much as its consequence" — is pre-existing, but three inserted paragraphs and the
re-authored YAML block now sit between it and its table, so it follows a fenced example where "the
second row" can be read as a row of that example. *Verified by* reading in file order. This is the
"check every paragraph an insertion moved" class that produced Majors on three consecutive slices.

**m8. A forward `[refused]` link whose row is not written yet.** `docs/reference.md:1991` routes the
`report_by` + `shuffle` combination to § Errors; the anchor resolves, but `E-STATS-NULLTEST-REPORTBY`
has no row yet — task 5's, by design. *Verified by running:* `grep -rn 'E-STATS-NULLTEST' ` over the
four documents returns **zero**, which is two facts: no `-REPORTBY` row yet (this note), **and**
`E-STATS-NULLTEST-UNSUPPORTED` correctly absent from the documents, as `CLAUDE.md` requires of the
`-UNSUPPORTED` build family. Recorded so task 5's review confirms the row lands rather than assuming
it did.

**m9. Pre-existing tension the batch presses on, unchanged by it.** § Validation's *Null test
coherence* row (`docs/reference.md:253`) still says `shuffle` must "name a unit attribute", while the
landing table one section over admits a `groups` axis attribute — which task 7 must accept as
attributes ∪ axis names. Task 7's, and the design spec already rules it.

### Observation, not a finding

Task 27's second test overlaps two shipped tests — under my mutation
`test_a_member_with_no_interval_is_not_in_the_family` and
`test_a_member_with_no_interval_may_carry_sides_and_is_not_corrected` failed alongside it. Its
distinct contribution is the `family_shape` count.

---

## Verified by running vs. read

**Ran:** the full suite three times (baseline **2278 passed, 1 skipped, 2 xfailed** → mutation **8
failed, 2270 passed** → after revert **2278/1/2**); `ruff check`, `ruff format --check` (80 files),
`mypy` (45 files); the brief's step-1 literal script, plus the same family under `bonferroni` and
`fdr_bh`; the floor arithmetic and a brute-force scan of the strict inequality; a link/anchor,
duplicate-heading, whitespace/tab/invisible-unicode and table-width pass over the four documents with
a **proven can-fail control** (a fabricated anchor reported missing) — every anchor this batch added
resolves and both new tables' rows match their headers' three columns; the claim sweep across all four
documents with a per-file positive control; the `0.347`/`0.412`/`null_draws`/`E-STATS-NULLTEST*`/
`unblock` greps.

**The mutation, re-run myself, unfiltered:** widening `family_members` to `[e for e in entries]`
(`src/publishable/correction.py:253`) gave 8 failed / 2270 passed. Both named tests failed on
**assertions**, not a crash — `..._is_still_outside_the_family` on the `where`-list assertion one line
before the `family_shape` assertion the brief predicted (same fault, earlier assertion), and
`..._bounds_are_unmoved_by_the_p_value_work` on the levels — plus four `test_cli.py` end-to-end tests
and two shipped `test_correction.py` tests as collateral. **Reverted by editing the line back**, never
`git checkout`; `__pycache__` cleared; byte-compared against a pre-mutation copy (identical); suite
re-run green; `git status` empty.

**Read, not run:** the design spec including § Corrections against the code, the five briefs, the batch
report, `contrasts.py`, `spec-defects.md`'s `null_test`/`report_by`/`fdr_bh` entries, the plan's late
documents task, and § Statistical reporting / § What isn't a repeat / § Contrasts in file order rather
than as diff hunks.

## Could not check

- Whether task 5's rows land (m8) and whether tasks 19/20 resolve `null_draws`' placement (M1) —
  outside this batch.
- The four `test_cli.py` collateral failures under the mutation were not individually attributed; they
  are the expected end-to-end consequence of a widened family.
