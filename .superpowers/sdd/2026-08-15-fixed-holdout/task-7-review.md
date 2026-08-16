# Task 7 review — `_check_holdout`, roster half

Reviewed `review-08386ba..880750c.diff` (one commit, `880750c`) against `task-7-brief.md`,
`task-7-report.md`, `CLAUDE.md`, and the task 5 / task 6 reviews.

Working tree was restored to `880750c` after every mutation and verified by re-running the suite,
never by `git status`; backups in the scratchpad, no `git checkout --` on any source file. Baseline
re-measured myself: `uv run pytest` → **1869 passed, 2 xfailed**; `uv run ruff check .` clean;
`uv run mypy` clean.

## Verdicts

1. **Spec compliance: ✅** — the diff is the brief, verbatim, at every site.
2. **Task quality: ❌** — the remedy prescribed by *both* previous reviews of this same function was
   not applied at any of the three new emit sites, and I confirmed by mutation that it costs real
   coverage: an inverted `missing` computation, a rounding-instead-of-largest-remainder split rule,
   and two of the three clauses of the `E-DATA-HOLDOUT-EMPTY` siting guard each survive with the
   whole holdout suite green.

---

## Spec compliance — what I checked

- `units.HOLDOUT_LEVELS`, `units.holdout_sizes`, `units.holdout_values_fault` all present with the
  brief's exact signatures, bodies and docstrings.
- `validate.py` imports `holdout_sizes` and `holdout_values_fault` and **not** `arms_of`. The brief
  contradicts itself here — its *Interfaces* bullet says "`arms_of` added to `validate.py`'s
  `publishable.units` import list", its Step 3(c) says "**not** `arms_of`, which stays behind
  `holdout_values_fault`". The implementer followed 3(c), which is the reasoned one. Not a finding
  against the task; noted so the plan's Interfaces line can be corrected.
- Three new findings, each with its own `roster is not None` guard (read at
  `src/publishable/validate.py` in the three appended blocks). Confirmed.
- Emit order in `_check_holdout` is METHOD, FRAC, NO-DRAW/FROM (mutually exclusive method branches),
  SEED, STRATIFY-UNKNOWN, FOLD, VALUES, STRATIFY-VARIES, EMPTY — **ten distinct codes**, so the
  docstring's grown enumeration and its "an eleventh finding belongs in it" are both correct.
- `stratum_varies_within_cluster`'s corrected docstring: **verified by counting the call sites
  myself.** `grep -rn "stratum_varies_within_cluster(" src/` gives exactly four invocations —
  `validate.py:2066` (`E-DATA-ASSIGN-STRATIFY-VARIES`), `2646` (`E-REPL-FOLD-STRATIFY-VARIES`),
  `2955` (new, `E-DATA-HOLDOUT-STRATIFY-VARIES`), `5579` (`E-STATS-RESAMPLE-STRATIFY-VARIES`). The
  mentions in `stats.py` and `replication.py` are comments, not calls. Four callers, four codes, four
  named § Validation rows — the correction is true.
- **`reference.md` § Errors rows independently verified** against every emit site this diff creates:
  the `E-DATA-HOLDOUT-VALUES`, `E-DATA-HOLDOUT-STRATIFY-VARIES` and `E-DATA-HOLDOUT-EMPTY` rows each
  describe what the code reports, including the EMPTY row's unstratified/unclustered restriction. The
  implementer's "no doc change needed" holds for § Errors. Two document notes below (findings 8, 9)
  are about § Validation and a neighbouring row, not about these three.
- Every new assertion on `E-DATA-HOLDOUT-UNSUPPORTED` is a standalone "appears alongside" line
  (`assert "E-DATA-HOLDOUT-UNSUPPORTED" in found`), never an assertion on the total set of codes, so
  task 17 retires each as a one-line deletion. **No finding** — but see finding 3 for what those
  lines are silently claiming to do.

---

## Findings

### 1. Critical — `E-DATA-HOLDOUT-VALUES`'s two message shapes are unobserved; the remedy from two consecutive reviews was not applied

`holdout_values_fault` builds a message with a conditional clause, so the code has two distinct
renderings — with and without `", and <literals> names no unit"`. All three parametrized rows assert
only `"E-DATA-HOLDOUT-VALUES" in found`. No test in this diff calls `messages_by_code`; the six new
`validate` tests contain zero message assertions.

**Verified by mutation.** In `src/publishable/units.py`, inverted the computation:

```python
missing = [lit for lit in HOLDOUT_LEVELS if lit in seen]   # was: if lit not in seen
```

`uv run pytest tests/ -k holdout` → **67 passed**, and `uv run ruff check src/publishable/units.py`
→ clean (so lint does not catch it either; a plain deletion of the clause does trip `F841`, which is
why I used the inversion). The refusal now tells a reader that the literals which *do* name units are
the ones naming none — the exact inversion of the fault — and nothing fails. Reverted in place;
re-ran, 67 passed.

This is the same defect the task 5 review found across 11 `c.error` sites and the task 6 review found
again, both prescribing `messages_by_code` fragments, which the file's own `_holdout` parametrize
block already uses (`(block, expected, fragment)` rows with comments explaining that "the fragment is
what tells the absent branch from the not-a-string branch"). Task 7 reverted to code-only assertions
at all three new sites. `E-DATA-HOLDOUT-STRATIFY-VARIES` and `E-DATA-HOLDOUT-EMPTY` have one emit
site each, so their exposure is smaller, but their wording is equally unpinned — either message could
be swapped for its `fold` or `resample` sibling's text with the suite green.

Fix: a `fragment` per row via `messages_by_code` — at minimum `"names no unit"` on the
`_SPLIT_ROSTER_ONE_SIDED` and `_SPLIT_ROSTER_AB` rows and its **absence** on `_SPLIT_ROSTER_THREE`,
which is what distinguishes the two shapes.

### 2. Important — `holdout_sizes`' test cannot distinguish largest-remainder from rounding, and its docstring claims it can

`test_holdout_sizes_is_the_single_authority_for_the_split_sizes` says: *"Each row is chosen so a
DIFFERENT wrong rule gives a different answer: truncation, rounding, and largest-remainder disagree
on at least one."* The truncation half is true (the `(4, 0.2)` row separates it). The rounding half is
false.

**Verified by mutation.** Replaced the body with

```python
test = round(n * frac)
return n - test, test
```

`uv run pytest tests/ -k holdout` → **67 passed**. Every row in the test — `(10, .2)`, `(240, .2)`,
`(7, .2)`, `(4, .2)`, `(2, .2)`, `sum(13, .3)` — agrees under banker's rounding. Reverted; re-ran, 67
passed.

Rows that would separate them, measured against the real implementation:
`holdout_sizes(6, 0.25) == (5, 1)` (rounding gives `(4, 2)`) and `holdout_sizes(14, 0.25) == (11, 3)`
(rounding gives `(10, 4)`). Adding one of those makes the docstring's claim true.

The in-test comment on the `(7, 0.2)` row is also wrong on its own terms: *"the train side is what
separates a rule that apportions from one that subtracts a rounded test size"*. In a two-way
apportionment the train side is `n − test` under **every** candidate rule, including
largest-remainder, so the train side separates nothing.

### 3. Important — the three controls' stated safety mechanism does not exist

Each control carries the sentence *"The wholesale refusal is the positive companion — without it this
passes identically if `_check_holdout` never ran at all."* That is false.
`E-DATA-HOLDOUT-UNSUPPORTED` is emitted by `_check_unimplemented`'s
`("holdout", "E-DATA-HOLDOUT-UNSUPPORTED")` loop (`src/publishable/validate.py`, the
`if units.get(field):` block), not by `_check_holdout`, so it cannot witness anything about
`_check_holdout` at all.

**Verified by mutation.** Inserted `return  # MUTATION` as the first statement of `_check_holdout`,
then ran the four controls: `..._holding_exactly_the_two_literals_is_accepted`,
`..._the_same_frac_over_a_larger_roster_is_accepted`,
`..._the_empty_test_partition_refusal_is_not_reported_for_a_clustered_split`, and the
`constant within the animal` row → **all four passed** with the whole function dead. Only
`test_a_holdout_stratum_must_be_constant_within_a_cluster[varies within the animal]` failed. Reverted;
re-ran, 9 passed.

The *suppression* itself is still pinned — the brief's mutation (b) deleting `and not cluster_by`
does fail the clustered control — and the paired negatives do catch a wholly dead check for VALUES
and EMPTY, so this is a comment-honesty finding rather than an unpinned behaviour. The forward
consequence is what matters: **task 17 deletes exactly those `UNSUPPORTED` lines**, and at that point
all three controls become pure-absence assertions with the companion their own docstrings claim they
have. Either correct the sentence now, or task 17 must replace each `UNSUPPORTED` line with a
finding `_check_holdout` actually produces.

### 4. Important — two of the three clauses of the `E-DATA-HOLDOUT-EMPTY` guard are unpinned

The brief's mutation (b) covers `and not cluster_by`. Nothing covers the other two.

**Verified by mutation, twice.** In `src/publishable/validate.py`:

- deleted `and not strata` from the guard → `uv run pytest tests/ -k holdout` → **67 passed**. The
  *stratified* half of the siting rule the brief calls "trap 5's" has no fixture at all; no test
  declares a `holdout.stratify_by` over a roster small enough to apportion an empty test side.
- deleted `and 0.0 < float(declared_frac) < 1.0` → **67 passed**. That clause is load-bearing: it is
  what stops a `frac` already refused as `E-DATA-HOLDOUT-FRAC` (`0`, `1`, `-0.5`, `1.5`) reaching
  `_apportion`, and `frac: 0` would otherwise apportion `(n, 0)` and stack `E-DATA-HOLDOUT-EMPTY` on
  top of the interval refusal. The existing `frac` parametrize asserts membership rather than an exact
  code set, so nothing sees the second finding appear.

Both reverted in place; re-ran, 67 passed each time.

### 5. Minor — an empty attribute value renders invisibly, against this module's own convention

**Verified by probe** (throwaway test, since removed): a roster whose `split` column is `train`/`test`
except one blank cell produces

> the holdout column 'split' has values **, test, train** over this roster — a `by_attribute` holdout
> needs exactly `train` and `test`. …

The offending value is rendered as nothing between two commas. `units.py`'s established rendering for
exactly this case is the literal `no value` — `stratum_varies_within_cluster` uses it
(`seen[cluster].add("no value" if value is None else str(value))`) and `_stratum_groups` uses it, and
`arms_of`'s own raise says `carries no value for it`. `holdout_values_fault` is the one place that
drops it.

Related and **untested rather than unreachable**: the `', '.join(seen) or 'none'` fallback fires when
no unit carries the column at all, which a glob-sourced roster reaches (`units.py:263` builds
`attributes={}` for every unit). I verified the message it produces via the typo'd-column probe in
finding 6; no test exercises it.

`reference.md` § Errors' `E-DATA-HOLDOUT-VALUES` row names three shapes — "carries some other value,
carries none, or one of the two literals names no unit at all". The middle one has no fixture.

### 6. Minor (spec gap, **not this task's to close**) — a `from` naming no attribute at all is reported as a values fault

**Verified by probe**: `holdout: {method: by_attribute, from: splitt}` over a roster declaring
`split` yields

> the holdout column 'splitt' has values **none** over this roster — … and **train, test names no
> unit**. …

No hint that the column does not exist, where `assign.<axis>.from`'s sibling has its own code
(`E-DATA-ASSIGN-UNKNOWN`, with a `difflib` hint). `reference.md` § Errors has no holdout counterpart
and the brief never asked for one, so this belongs in `docs/superpowers/spec-defects.md` with an
owner rather than in this task. (The plural-list-singular-verb "train, test names no unit" is a
wording nit inside the same string.)

### 7. Minor — the "already refused above" guard in the new `stratify_by` loop is behaviourally inert, and its comment says otherwise

The comment claims *"Names already refused above are skipped, so a config with one undeclared and one
varying stratum gets one finding for each rather than two for one."*

**Verified by probe + mutation**: a config declaring `holdout.stratify_by: ["label", "nope", 7]` with
`cluster_by: animal_id` over a roster where `label` varies within the animal produces
`E-DATA-HOLDOUT-STRATIFY-UNKNOWN` ×2 and `E-DATA-HOLDOUT-STRATIFY-VARIES` ×1 — **byte-identically
with and without the guard**, because a name no unit carries is constant within every cluster and
`stratum_varies_within_cluster` returns `None` for it. The doubling the comment says the guard
prevents cannot occur. Deleting the guard also leaves `-k holdout` at 67 passed.

Keep the guard (it matches the resample site at `validate.py:5575` verbatim, and consistency across
the four call sites is worth more than three lines), but the justification is not the reason the
behaviour is right.

### 8. Minor (document) — § Validation's *Holdout leaves a test partition* row omits the siting the check actually has

`docs/reference.md` § Validation, row *Holdout leaves a test partition*, reads as method-independent:
"`holdout.method: random` with `frac: 0.01` over 40 units apportions the test side zero units". Its
explicit model, *Every arm draws units* two tables up, states the restriction inline: "Reported for
the unstratified, unclustered draw only — a clustered draw and either kind of stratified draw are
checked where the run performs them". § Errors' `E-DATA-HOLDOUT-EMPTY` row does carry it, so the
one-row-per-code rule is satisfied; the gap is that a reader consulting § Validation — which is where
CLAUDE.md warns that "several rows read as method-independent while the surrounding prose carries the
gating" — would expect the check to fire for a clustered split. The brief told this task to mirror
*Every arm draws units* "exactly", and the mirroring stopped at the code. **The document is what's
wrong here**, and the fix is one clause in that row.

### 9. Minor (document) — § Errors' `E-DATA-HOLDOUT-STRATIFY-VARIES` row names two of the three other readers

`docs/reference.md`'s `E-DATA-HOLDOUT-STRATIFY-VARIES` row says
`stratum_varies_within_cluster` is "the single authority *Fold strata survive clustering* and
*Resample strata survive clustering* also read", omitting *Allocation strata survive clustering* —
which the function's own docstring, corrected in this diff, now names as the fourth. Not false ("also
read" is not an exhaustive claim) and not introduced by this diff, but the docstring correction is
what makes the partial list visible; worth closing while the four-caller count is fresh.

### 10. Minor — the report's `ruff format` and `stratum_names` claims are both slightly off

- The report says `ruff format --check` reports "63 files would reformat, consistent with this repo's
  standing baseline (not introduced by this task — confirmed by diffing the touched files' reformat
  count against the pre-existing whole-repo baseline)". **I measured 70 files**, and more to the
  point, **lines this diff added are among the would-reformat hunks**: `units.py:1140` (the new
  `seen = sorted(...)`), `tests/test_validate.py:11622, 11644, 11658, 11701` (the new
  `_SPLIT_ROSTER_ONE_SIDED` and three new call sites). The repo is broadly not format-clean, so this
  is not a gate failure — but the specific claim "not introduced by this task" is not supported.
- The report counts six `stratum_names` call sites; I count **seven** invocations —
  `units.py:1586`, `validate.py:1971, 2389, 2865, 5502, 5575`, `cli.py:1122` — against a docstring
  still claiming two. The implementer's decision to leave it stands: this task adds **no** call site
  (its new loop iterates `strata`, produced by the pre-existing call at `validate.py:2865`), so the
  deferral is correct rather than a third dodge. It is now deferred twice and should be re-owned per
  CLAUDE.md's "re-owner a deferral when the slice that filed it finishes".

### 11. Minor — the rewritten "reads `doc`" sentence is now stale in its justification

The replacement sentence reads "**Only `E-DATA-HOLDOUT-FOLD` reads `doc`**; `roster` and `cluster_by`
are both in the signature **anyway**, `units.assignment_for`'s reason: the caller already holds
them". The "in the signature anyway" framing was the point when nothing read them; three checks now
do, and the sentence's own preceding bullet says so. Not false, but it argues for a parameter's
presence that no longer needs arguing.

### 12. Noted, no finding — the `ContractError` → `break` path in the new loop has no test

Matching the three sibling sites (`validate.py:2066`, `2646`, `5579`), none of which tests it either.
Recording it so it is not re-derived.

---

## Mutation ledger

| Mutation | File | Result |
|---|---|---|
| `missing = [lit for lit in HOLDOUT_LEVELS if lit in seen]` (inverted) | `units.py` | 67 passed, ruff clean → **finding 1** |
| `test = round(n * frac); return n - test, test` | `units.py` | 67 passed → **finding 2** |
| `return` as first statement of `_check_holdout` | `validate.py` | 4 controls passed, 1 negative failed → **finding 3** |
| delete `and not strata` from EMPTY guard | `validate.py` | 67 passed → **finding 4** |
| delete `and 0.0 < float(declared_frac) < 1.0` | `validate.py` | 67 passed → **finding 4** |
| delete the `already refused above` guard | `validate.py` | 67 passed, findings byte-identical → **finding 7** |
| `c.error("E-XX-MUTANT", …)` at the VALUES site | `validate.py` | all 3 rows failed → **attribution confirmed**, the code comes from this site and no other |

Roster attribution checked as CLAUDE.md requires: `_SPLIT_ROSTER_THREE`, `_SPLIT_ROSTER_AB` and
`_SPLIT_ROSTER_ONE_SIDED` each earn `E-DATA-HOLDOUT-VALUES` from the new emit site (last row above),
and `_VARYING_HOLDOUT_STRATUM` / `_CONSTANT_HOLDOUT_STRATUM` differ only in roster content under one
config. The `holdout_sizes` rows do pin largest-remainder against truncation (`(4, 0.2)`), just not
against rounding.

Also restored `.superpowers/sdd/.gitignore`, found clobbered to a bare `*` again.
