# H4d — whole-branch review (independent, pre-merge gate)

**Branch:** `h4d-null-test`, 29 tasks in five batches, reviewed at tip `095717a`.
**Reviewer scope:** what no per-batch review could see. Findings already closed and verified in a
batch review are not re-litigated.

## Verdict

**DO NOT MERGE** — one Critical, reachable and reproduced through a real `run`, at
`src/publishable/correction.py:517-524`. Everything else on the branch is sound; the fix is small and
has a precedent on this same branch (§ Corrections item 5), so this is a fix-and-re-check rather than
a rethink.

Everything else held under independent re-measurement: the five faults decompose, both batch-2
fail-opens survive the retirement, the retired code is gone from `src/`, `fdr_bh`'s arithmetic
recomputes exactly, batch 1's guard pin is unedited and still discriminating, the worked example is
untouched, the dated measurement is correctly dated and pinned, and six/three are unmoved. Two Majors
and four Minors are document and record work.

## Gates, verified by running

| Gate | Result |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 80 files already formatted |
| `uv run mypy` | no issues, 45 source files |
| `uv run pytest` | **2359 passed, 1 skipped, 2 xfailed** (163 s, then 133 s on re-run) |

`__pycache__` cleared before the first run. Every mutation below was reverted **by editing the file
back**, never `git checkout --`, and each revert was verified by re-running the affected suite;
`src/publishable/validate.py` was additionally confirmed **byte-identical** to a pre-mutation copy.
`git status --porcelain` is empty and `git diff HEAD` is empty at the time of writing. **The tree is
clean.**

---

## Findings

### Critical 1 — `src/publishable/correction.py:517-524`: under `holm`, a p-only member is published an adjusted p-value at a rank it does not have, and two metrics with identical evidence get different numbers decided by column order

**Reproduced end to end in a real `run`, exit 0, zero errors.** A `sweep.groups` axis with one unit
in `arm=of` and five in `arm=against`, two recorded columns, a declared contrast crossing the axis,
`shuffle: arm`, `correction: holm`. Welch needs two units per side so `interval` is `None`, while
`permutation_over_contrast` still has six values to relabel — so `cli.py:1526` builds a member with
`ci95=None` and a real `p_value`, which decision 4's widening admits to the family. `run.yaml`:

```yaml
y: {delta: 87.0,  method: null, n_of: 1, n_against: 5, ci95: null,
    p_value: 0.16976604679064186, ci95_corrected: null,
    correction_level: 0.025, family_size: 2, p_value_corrected: 0.3395320935812837}
z: {delta: 261.0, method: null, n_of: 1, n_against: 5, ci95: null,
    p_value: 0.16976604679064186, ci95_corrected: null,
    correction_level: 0.05,  family_size: 2, p_value_corrected: 0.16976604679064186}
```

**The two raw p-values are bit-identical and the two adjusted ones differ by a factor of two.** The
only thing separating `y` from `z` is `declaration_index` — `rank_family`'s tier key is
`(1, 0.0, declaration_index)` for every member with no interval, so renaming or reordering the two
columns swaps the two published numbers. A reader comparing the two entries reads `z` as twice as
significant as `y` on identical evidence.

**Three reasons this is not a documentation gap.**

1. `reference.md:2176` defines the quantity as *"the p-value expressed at the level **this member's
   interval was corrected at**."* No interval was corrected here — `ci95_corrected: null` sits in the
   same block. And `correction_level: 0.025` is recorded beside it, an α at which nothing was ever
   built. On `main` this state could not arise: `family_members` dropped a `ci95 is None` member, so
   neither key existed for it.
2. **The precedent is on this branch and was not carried across.** § Corrections item 5 found `thin`
   firing for exactly this member and fixed it with `and member.ci95 is not None`
   (`correction.py:506`), on the ground that the warning *"says the resample's draws could not support
   the level, which is false of a member that never had an interval."* The identical sentence is true
   of a level-derived `p_value_corrected`. One field over, the same predicate, the same argument —
   applied to the flag and not to the number.
3. **The affected cell is `holm` alone**, which is the *default* correction. `bonferroni`'s
   `min(1, p x m)` needs no rank and is well-defined for a p-only member; `fdr_bh`'s adjustment is on
   `p` alone and is the method decision 4's widening exists to serve. Only `holm` needs *i*, and *i*
   is fabricated by the tier.

**Unpinned.** `grep p_value_corrected tests/test_correction.py`: the p-only member is pinned under
`fdr_bh` (`test_the_bh_table_is_identical_when_one_member_carries_no_interval`) and its `holm`
behaviour is pinned only for `thin` and `ci95_corrected`
(`test_a_p_only_member_does_not_report_a_thin_correction`, `correction.py` lines asserted at 1479-1480).
Nothing asserts its `p_value_corrected` under `holm` at all, which is why five batch reviews and
task 29 could all pass over it.

**Remedy — either, but it needs a pin.** Withhold the key, mirroring `thin`: `p_value_corrected` only
where `method == "fdr_bh" or method == "bonferroni" or member.ci95 is not None`. Or rule the tier's
level in `reference.md` § Statistical reporting and accept the order dependence in writing. The first
is two lines and matches the precedent; the second needs an argument for publishing an
order-dependent number. Either way the pin is a `holm` family with two p-only members at equal raw p,
asserting the relation between them.

### Major 1 — `docs/reference.md:2189`: a normative sentence that is false against the shipped code, and that contradicts the passage it cites as its own support

§ Statistical reporting's ranking paragraph reads:

> So the ranking statistic is the one quantity every member is guaranteed to have, since
> **[a member with no interval takes no rank](#sweeps-and-repeats)**: the point estimate over half the
> raw `ci95` width, largest first.

**Verified false by running.** `correction.rank_family`'s tuple key
(`src/publishable/correction.py:320-332`) puts a p-only member in tier `1` — it *is* ranked, and
`corrected_for` hands it a `correction_level`:

```
family: ['cond:P', 'cond:A', 'cond:B']      # family_members, widened per decision 4
ranked: ['cond:A', 'cond:B', 'cond:P']      # rank_family — cond:P is rank 3 of 3
holm    cond:P -> correction_level 0.05, p_value_corrected 0.02, ci95_corrected None
```

The linked target — the family-count paragraph this same slice repaired — says the opposite in as
many words: *"A metric carrying a p-value and no interval is counted."* So the sentence and the
anchor it points at disagree, and the sentence is what the ranking rule rests on.

This is the branch's own edit: `main` read *"only metrics carrying an interval are counted"*, which
the widening also falsified, and task 1 replaced it with a second false claim rather than with the
true one — `CLAUDE.md`'s *"a rewrite invents; a deletion cannot"*, one round further on. No per-batch
review could see it: batch 1 wrote the sentence three commits before batch 4 built the tier.

**Remedy:** delete the causal clause (the ranking statistic's definition stands without it), or
state what actually holds — a member with no interval has no evidence ratio and is ranked in a tier
below every member that does.

### Major 2 — `src/publishable/correction.py:320-332`: the ranking rule for a p-only member exists only in code

The mechanism behind Critical 1, recorded separately because it stands even if the Critical is closed
by withholding the key. `rank_family`'s tier puts every member with no interval **after** every member
that has one, ties broken by declaration order. Design decision 4 specified the tuple key and pinned
that no existing corrected bound moves — which task 27's pin does hold, and which I re-verified. What
it never ruled is which rank a p-only member then *has*. `reference.md` § Statistical reporting states
the ranking statistic, the tie-break, and `min(1, p x (m - i + 1))` "at this member's own evidence
rank *i*" — and says nothing about *i* for a member that has no evidence ratio.

Measured directly at `m = 3` with two p-only members and one interval-carrying:

```
A  level 0.01667   p_corr None     # interval, tier 0
P1 level 0.025     p_corr 0.02     # raw 0.01, x2
P2 level 0.05      p_corr 0.02     # raw 0.02, x1 -> uncorrected
```

**Remedy:** state the tier and its consequence in § Statistical reporting, whichever way Critical 1
is closed.

### Major 3 — `.superpowers/sdd/2026-08-18-null-test/task-b5-report.md`: the `bonferroni` `thin` pin gap is "filed" only in a report, with the owner form `CLAUDE.md` forbids

Batch 5's report says of § Corrections item 5's `and member.ci95 is not None` narrowing:

> **Ruling: filed properly rather than fixed here** ... Recorded here with the owner (whoever next
> touches `correction.corrected_for` or its test suite) and the exact check ...

Two faults, both named rules. **"Recorded here" is a report, not a filing** — `grep -n -i 'bonferroni' docs/superpowers/spec-defects.md`
returns two hits, both in an unrelated H7-era entry, and no `thin`-narrowing entry exists. That is
verbatim *"a ledger line saying 'filed' is not a filing."* And **"whoever next touches X" is the
vague-owner form** this same file's H4c entry rejects by name and which batch 3's own fix round was
corrected for — the three genuine H4d filings (`null_draws` on the contrast side, the clustered
derived null, the derived/label-collision corner) all say **"Owner: unassigned"** with the reason,
correctly.

Severity note, in the slice's favour: the *guard itself is pinned*. I mutated
`correction.py:506`, removing nothing but adding a spurious `p_value_corrected: None`, and separately
confirmed by reading that `test_a_p_only_member_does_not_report_a_thin_correction` exercises the
`holm` arm on an expression that is method-independent. So the missing `bonferroni` arm is redundant
coverage, not an unguarded fail-open. The finding is about the record, not the code.

**Remedy:** a real `spec-defects.md` entry with `Owner: unassigned` and the reason, carrying the
check the report already wrote — or add the two-line `bonferroni` arm and drop the filing.

### Minor 4 — `src/publishable/stats.py:1091-1138`: `of_strata`/`against_strata` have zero callers, production or test

`permutation_over_contrast` takes them, and its docstring cites `reference.md` § What isn't a repeat's
*"permuted within cells of every other group axis, so a cross isn't destroyed"* as their ground.
`cli.py:1410` never passes them. Grepped: **no call site anywhere in `src/` or `tests/` supplies
either.** (`permutation_over_units`'s own `strata` is tested at `tests/test_stats.py:5642` but reaches
production only through this dead path.)

Read down, the documented rule is **structurally satisfied rather than unimplemented**: a declared
contrast names conditions by label, and a condition is one cell of the full group cross, so every
other axis is already constant on both sides of any comparison. So this is dead surface plus a
docstring that reads as if the parameters deliver a rule they are not needed for — the spine design's
"constructions with zero production callers" hazard, not a behavioural gap. Worth either deleting the
parameters or saying in the docstring why they cannot be reached.

### Minor 5 — `src/publishable/validate.py:5102`: the parameter-axis disjunct of `W-STATS-CORRECTION-INAPPLICABLE` is still unfailable, and only its message is at stake

Mutation run and reverted: `elif not crossed_by_any_comparison:` → `elif False:` leaves
`tests/test_validate.py` at **750 passed**, and the full suite green. The reason is that the fall-
through branch (`shuffle not in crossed_by_any_comparison`) fires for exactly the same configs when
`crossed_by_any_comparison` is empty, so a code-presence assertion cannot tell them apart — only the
**message** can, and no test asserts either message (grepped: the parameter-axis wording appears in
`tests/test_validate.py:4498` as a docstring only).

Batch 4 raised this and the fix round built `_group_axis_wrong_shuffle_doc` (M3), which pins the
*third* code branch, not this one — the two are numbered differently in the code and in the
docstrings, which is how the confusion survived. Behaviour is correct either way; the disclosure is
what is unpinned. This is the "answering with a proxy" shape at test level, not a defect.

### Minor 6 — task 20's positive path has never been exercised by `run`

The spec's ordering constraints say **"Tasks 19 and 20 by `run`, never by direct call"** and give the
reason (five wrong grounds in that function across two slices). Task 19 got its run — fixture C1.
Task 20's two end-to-end fixtures are C1 (contrast side) and C2, and **C2 pins the *suppressed*
shape**: `assert "p_value" not in metric`. Grepped `tests/test_cli.py`: no run test asserts a
per-condition derived `p_value` **present**.

**I built and ran that config myself** — C2's roster with `cluster_by` dropped, a project-local
template's `aggregate`, `shuffle: label` — and the behaviour is correct:

```
delta_y: value 2.5, method percentile_over_units, resample_draws 2000,
         p_value 0.47910417916416714, null_draws 5000,
         null_test {method: permutation, n: 5000, shuffle: label, level: rows}
         # no p_value_corrected  -> decision 5, uncorrected
seen:    t_over_units, no p_value  -> decision 7, a recorded column gets none
```

So this is a **missing pin, not a defect** — but it is the pin the slice's own binding constraint
names, and the one shape that carries reference.md's documented `aggregated:` example.

### Minor 7 — `docs/superpowers/plans/2026-08-18-null-test.md` was edited in place

`git diff main...HEAD -- docs/superpowers/plans/` shows task 28 step 4's site list rewritten
(commit `1273247`) to add § Between-subjects. The plan is tracked development record. The edit does
name its source (batch 1's review, round 1, m3) and what it replaces, and a plan is the live
checklist rather than a dated measurement, so I do not read this as the retro-edit `CLAUDE.md`
forbids — recorded so a later reader does not have to re-adjudicate it.

---

## What I verified, by running

**End to end, on my own config (not any fixture on this branch).** A `holm` run over an unclustered
`sweep.groups` axis, two recorded columns, a declared contrast crossing the axis, `shuffle: arm`.
`validate` clean (one unrelated `W-ENV-UNLOCKED`), `run` exit 0, and `run.yaml`:

- `p_value: 0.46910617876424715` on both contrast metrics, with the resolved echo
  `{method: permutation, n: 5000, shuffle: arm, level: rows}`.
- `y` at `correction_level: 0.025` → `p_value_corrected: 0.9382123575284943` = `p x 2`;
  `z` at `0.05` → `p_value_corrected` = `p`. **That is `min(1, p x alpha/level)` at the level the
  interval was computed at**, exactly as § The unit table is the inference base requires.
- `family_size: 2`, `family: {comparisons: 1, metrics: 2}` — the p-value **added no place in the
  family**, the `CLAUDE.md` invariant.
- Per-condition `aggregated` blocks carry **no** `p_value`: decision 7's recorded-column rule.
- **`null_draws` is absent from both contrast entries that carry a `p_value`** — the documented-key-
  nothing-writes half of the pair, matching the OPEN unassigned filing exactly. Confirmed rather than
  assumed.

**The five decomposed faults, as exact sets** (each config differing only in the `null_test` block):

| Declaration | Errors reported |
|---|---|
| absent `shuffle` | `E-STATS-NULLTEST-SHUFFLE` |
| `shuffle: ""` | `E-STATS-NULLTEST-SHUFFLE` |
| `shuffle: nope` | `E-STATS-NULLTEST-SHUFFLE` |
| `method: bootstrap` | `E-STATS-NULLTEST-METHOD` |
| `n: 5` and `n: 19` | `E-STATS-NULLTEST-N` |
| `n: 20` | *(none)* |
| `shufle:` typo | `E-CONFIG-KEY-UNKNOWN` + `-SHUFFLE` |
| no `data.units` | `E-STATS-NULLTEST-UNITS` (+ `-SHUFFLE`) |
| `report_by: [label]` + `shuffle: label` | `E-STATS-NULLTEST-REPORTBY` |
| well-formed | *(none)* |

**Both batch-2 fail-opens hold with `-UNSUPPORTED` retired**, which was the entire point: an absent
`shuffle` and `shuffle: ""` are each refused by `E-STATS-NULLTEST-SHUFFLE`, and
`E-STATS-NULLTEST-UNSUPPORTED` appears in no set. The floor is exact at 19/20, matching
`math.floor(1/0.05)` and the *strict* `1/(n+1) < level` inequality reference.md states.

**`level` is derived, never settable.** `null_test: {..., level: rows}` and `level: within_cluster`
each earn `E-CONFIG-KEY-UNKNOWN` at path `statistics.null_test.level` — the closed-one-level-in schema
enforces `CLAUDE.md`'s declared-vs-derived rule for the one value task 3 records *because* it is
derived.

**No verdict rests on a p-value.** Read inside `hypotheses.verdict_for`: `p_value_corrected` reaches
`_observed_block` only; `supported` is computed from `number`/`threshold`, and `verdict_rests_on` is
`obs.rests_on`. Task 21's claim is inert as stated, not merely threaded.

**`CLAUDE.md`'s repeat-kind invariant survives.** All five rejected kinds — `permutation`,
`bootstrap`, `technical`, `biological`, `holdout` — return `E-REPL-KIND` by name.

**Batch 1's guard pin is intact and still discriminating.** `git diff main...HEAD -- tests/test_correction.py`
has **zero deleted lines**. I added a spurious `"p_value_corrected": None` to every block
`corrected_for` returns and got **5 failures**, including all three method arms of the pin
(`holm`, `bonferroni`, `fdr_bh`) on the `_PIN_INNER_KEYS` assertion. Reverted; 60 passed.

**Fixture D recomputed independently**, in a standalone script with no repo imports, BH as
suffix-min over `min(1, m/i x p)` with *i* the ascending-p rank and `m` the whole family:

```
BH:   X 0.0007998400319936012  Y 0.41333333333333333  Z 0.41333333333333333  W 0.9
Holm: X 0.0001999600079984003  Y 0.88  Z 0.9299999999999999  W 1.0
Bonf: X 0.0007998400319936012  Y 0.88  Z 1.0  W 1.0
```

Every value matches the spec table and the shipped literals. Y's suffix-min bind at 0.41333 (its own
`4/2 x 0.22 = 0.44` pulled down to Z's) is present, which is the one assertion that can tell the
two-pass rewrite happened. **Monotonicity is disclaimed, not asserted** (`reference.md:2182`,
*"it is not monotone in the raw p"*, phrased as a "can"), and **no test name claims
non-monotonicity**: `grep -rn 'monoton' tests/ src/` shows the mid-slice defect closed —
`test_holms_adjusted_p_is_the_p_at_this_members_own_evidence_rank` now states in its docstring that
fixture D does *not* instantiate the inversion. Incidentally my own run *does* instantiate it: equal
raw p on `y` and `z`, adjusted 0.938 against 0.469.

**The retired code is gone, enumerated by reading first.** `_check_unimplemented`'s truthy-guarded
emit is the only site the design names; grep over all `*.py`/`*.md` excluding the development record
finds `E-STATS-NULLTEST-UNSUPPORTED` in **no** `src/` file — only in test docstrings, the retired-code
sweep's own literal, the new dated feasibility entry, and one *older dated* feasibility entry which is
evidence and correctly untouched. Can-fail control: the surviving
`E-TEMPLATE-INSTALLED-UNSUPPORTED` returns hits in `src/publishable/validate.py`,
`templates/registry.py`, `generators/experiment.py` and `reference.md`. `E-DATA-CLUSTER-DERIVED` is
likewise gone from `src/` and from `reference.md`, with no orphan § Errors row.

**All six minted codes carry exactly one § Errors/§ Warnings row each**, and each has an emit site:
`-METHOD`, `-N`, `-SHUFFLE`, `-UNITS`, `-LEVEL`, `-REPORTBY`, plus `W-STATS-NULLTEST-FAMILY` and
`W-STATS-CONTRAST-RESAMPLE-THIN`. One row per code, not per emit site, as § Errors requires
(`-SHUFFLE` and `-LEVEL` each have two emit sites and one row).

**`Member.p_value` against every construction site.** `grep -rn 'Member(' src/publishable/*.py`
returns exactly one production site, `cli.py:1526`, which reads
`p_value=metric_block[metric_key].get("p_value")` — absent on the block iff absent here, by `.get`
rather than a second condition. `corrected_for`'s **two** callers are both handled:
`cli.py:3356` via `corrected_fields`, and `hypotheses.py:310` at `size = len(counted)` with a partial
member set. § Corrections 7's narrow claim holds — `hypotheses.evaluate` threads
`p_value_corrected` and `family_size` is still `len(counted)` — and `reference.md:3235` documents
the hypothesis-entry key. Its test discriminates the two readings of `m` (0.1 at `size=2` against
0.15 at the sweep's 3), so it pins a relation and not a bare literal.

**The dated measurement is correctly dated and pinned.** `git show -s --format=%ci d0e9345` →
`2026-08-19 11:50:57`; the entry reads *"Measured on 2026-08-19 against commit `d0e9345`"* and was
committed in `ba47107`, also 2026-08-19. The suite figure it cites (2359) is the count at that
commit. Every refusal in it is named by its code, and **no sentence converts the six into an
execution count** — it says *"H4d unblocks ZERO configs, and both counts stay unmoved: six with no
remaining core-side blocker, three executable."*

**Re-measured myself**, on my own greps rather than the entry's: **eight** `statistics:` blocks in the
feasibility analysis, **all eight** declaring `null_test: null`; `correction:` is `holm` seven times
and `none` once, **zero `fdr_bh`**. I read `_check_null_test`'s guard directly —
`if not isinstance(null_test, dict) or not null_test: return` — so an explicit `null` is undeclared
and none of H4d's five codes can fire for any of them. E1 (lines 206/209) and C1 (lines 562/565)
checked individually. **Six and three, unmoved. Confirmed.**

**Mechanical pass** over the four documents, `CLAUDE.md` and the feasibility analysis, fenced blocks
skipped: every relative link and `#anchor` resolves, no duplicate heading anchors, no trailing
whitespace, no tabs, no invisible unicode. Four table-width reports were false positives from
escaped `\|` inside cells (`reference.md:600, 1645, 3473`, `CLAUDE.md:342`), all pre-existing and
none on this branch.

**The worked example is untouched.** `README.md` and `docs/design-principles.md` have **no diff on
this branch at all**; filtering `reference.md`'s diff for every `cohort-pilot` value —
0.581/0.607/0.412, all six interval bounds, 0.026, the deltas, 0.014, 228/240, and all five hash
prefixes — returns exactly one hunk, and it changes only link *text* in the ranking paragraph. No
interval was narrowed. (That one hunk is Major 1.)

**The three deliberately-open items.** `null_draws` on the contrast side and the clustered derived
permutation are both real `spec-defects.md` entries stating `Owner: unassigned` **with the reason**
(no remaining slice has that surface), each naming what a closer must do — the `null_draws` one names
four steps together, including narrowing `reference.md`'s own "equal by construction" sentence, which
I confirmed is genuinely false for a whole-cluster relabelling that empties an arm
(`permutation_over_units_clustered` `continue`s such a draw while the denominator stays `n + 1`). The
third, the `bonferroni` `thin` pin, is Major 3.

---

## What I could not check

- **`fdr_bh` end to end at `m > 1` with more than one p-carrying comparison.** Fixture C1 runs
  `fdr_bh` at one comparison, where BH's adjustment is the identity — so the suffix-`min` is verified
  only by direct call on fixture D. Building a run with two cross-arm contrasts both carrying
  p-values needs two group axes and was out of budget. The direct-call pin is arithmetically exact
  and I re-derived it independently, so I judge the risk low, but the *threading* of a non-trivial BH
  table onto a real `run.yaml` is untested.
- **Whether the `whole_cluster` level is reachable end to end.** Its construction is pinned by
  direct call in `test_stats.py`, and `units.null_test_level` is pinned in `test_units.py`, but no
  `run` in the suite (or that I built) produces `level: whole_cluster`. This is where the
  `null_draws`-versus-`n` divergence lives, so it is the same surface as the open filing.
- **Batch findings already closed and verified** were read but not re-run, per the brief — except the
  three I re-ran deliberately (batch 1's pin, batch 2's two fail-opens, batch 4's
  `W-STATS-CORRECTION-INAPPLICABLE` disjunct), one of which is Minor 5.
- **`W-STATS-NULLTEST-FAMILY`** is covered two-sided at the 19/20 boundary
  (`tests/test_validate.py:4576, 4584`) which I read but did not mutate.
