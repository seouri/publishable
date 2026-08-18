# Whole-branch review — H4b-1, weights through contrasts

Branch `h4b-weighted-contrasts` @ `b15281e`, against `main` @ `d11f40a`. 15 tasks, 4 batches, all
task-reviewed and fixed. Reviewed 2026-08-17.

## Verdict

**DO NOT MERGE** — until Major 1 and Major 2 are closed. Both are one-clause document edits and
neither is a correctness defect in the shipped arithmetic, so this is a short hold, not a rejection.
But at the last gate a conditional verdict is the thing that gets skimmed: as the branch stands, one
normative section of `reference.md` contradicts the code, and `CLAUDE.md` states as a live blocker a
refusal this branch retires. Close those two and **merge** — the slice's substance is sound. The
payoff path, the corrected path, the general path and the retirement are all verified by running,
and the dated count reproduces under a substitution different from either the implementer's or the
task reviewer's.

## Gates — verified by running, twice (before and after my mutations/probes)

| Gate | Result |
|---|---|
| `uv run pytest` | **2159 passed, 1 skipped, 2 xfailed** — matches expectation exactly |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 80 files already formatted |
| `uv run mypy` | Success, 45 source files |

Tree is **clean**: `git status --porcelain` empty, both throwaway probe files deleted, all
`__pycache__` cleared, gates re-run after cleanup rather than trusted. No `git checkout --` was used
at any point; I added and deleted my own files rather than mutating tracked ones.

---

## Findings

### Major 1 — `reference.md` § Contrasts asserts a four-way obligation the derived path breaks

**File:** `docs/reference.md:2618-2621` (the paragraph closing the weighted-contrast record shape).

> "All four move together or none of them does: a weighted delta beside an unweighted interval, an
> unweighted `cohens_d`, or an `n_paired` with no effective size beside it, is a declaration
> accepted whose effect is half delivered"

**Verified by running.** A derived metric under a declared `weight_by`, driven end to end through
`main(["run", ...])` and read back off the `run.yaml` on disk:

```
step01_summarize_units.score: {"delta": 0.0, "method": "paired_percentile_over_units",
  "cohens_d": null, "weighted_by": "sampling_weight", "n_paired_effective": 4.8, ...}
```

`weighted_by` and `n_paired_effective` travel beside an **unweighted** `method`, an unweighted
`delta` and `cohens_d: null` — precisely "all four" not moving together. The same run's recorded
column (`pred`) correctly shows `weighted_paired_percentile_over_units`, so this is the derived
exception, not a bug.

**The behaviour is right and the sentence is wrong.** § Statistical reporting
(`docs/reference.md:2440-2447`, added by this branch) documents the split correctly and explicitly —
"Its `method` therefore stays `paired_percentile_over_units` … while `weighted_by` and the effective
size travel beside it regardless" — as does the feasibility analysis's C1 paragraph
(`docs/feasibility-llm-growth-studies.md:515`) and the shipped test
`tests/test_cli.py:9940` (`test_a_weighted_derived_contrast_carries_the_record_keys_without_a_weighted_method`).
So one document section contradicts another document section, a shipped test, and the code.

**This is exactly a batch seam.** The § Contrasts paragraph is **task 3**'s (commit `06b52f0`),
written before the derived/column split was built out; the derived exception is **tasks 9–12**'s.
Task 14's prose sweep swept for *"a contrast is unweighted"* claims — which it closed completely, I
confirmed — and this sentence makes the opposite over-claim, so the sweep could not see it. No
per-task review could either: task 3's review saw a paragraph true of everything then built.

**Remedy — one clause, and only one.** The paragraph's three *enumerated* faults are all still true;
none of them is the derived case. What the derived path breaks is only the opening clause, **"All
four move together or none of them does"** — two travel, two don't. Narrow that clause to the
recorded-column case and leave the rest of the paragraph alone. `CLAUDE.md`'s *prefer deleting a
claim to rewriting it* applies: a rewrite of the whole paragraph would invent, and the enumerated
faults it already states are worth keeping.

---

### Major 2 — `CLAUDE.md` still names `E-DATA-WEIGHT-CONTRAST` as a live blocker, and has no H4b-1 entry

**File:** `CLAUDE.md:69`.

> "Six stay blocked on two causes neither of which is H7b's: `io.reuse_from` (unbuilt, unowned) for
> E3, E4, E6, and **`E-DATA-WEIGHT-CONTRAST` (H4b) for C1–C3**."

**Verified by grep and by running.** `CLAUDE.md` is untouched on this branch (`git diff --stat
main...HEAD` lists no `CLAUDE.md`), while the code is gone: `grep -rn E-DATA-WEIGHT-CONTRAST src/`
returns nothing, and my own re-measurement (below) shows C1 validating with **zero errors**. The
sentence is false the moment this merges.

Two reasons this is the branch's and not the merge's:

1. `CLAUDE.md`'s own mechanical pass names itself in scope: *"After removing or renaming any string,
   grep the four documents, **this file**, and any feasibility analysis for what should no longer
   exist."* Task 14 was the owned prose sweep; it swept `README.md`, the three other documents, `src/`
   and `tests/`, and stopped one file short — which is `CLAUDE.md`'s own *"Sweep for the claim, not
   for the file the claim was first noticed in"* rule, recorded as having fired three times in one
   prior slice.
2. Every prior slice recorded its own § Repository status entry (H7b Part A, H7b Part B, H7c, H4a,
   H3d all have one). H4b-1 has none, so the file's running narrative stops before the slice that
   produced the project's first weighted contrast.

**Remedy:** add the H4b-1 § Repository status entry and correct line 69's second cause. If the
repo's convention is that the entry is written in the merge commit, the *stale* half of line 69 still
must not survive the merge.

---

### Minor 3 — the dated measurement's pin is one commit behind, and does not say so

**File:** `docs/feasibility-llm-growth-studies.md:1131` — "Measured on 2026-08-17 against commit
`0f15c3f9…`".

`git diff 0f15c3f..HEAD -- src/` shows `validate.py` moved by 4 lines after the pinned commit. I read
the diff: it is **comment-only** ("its two siblings' helpers" → "its sibling's helpers"), so no
executable code moved and the measurement still describes the build it names. But the same file sets
the precedent for saying so out loud — its 2026-08-16 correction at line 1001 states *"The only
change to `src/` after the commit this section pins is a docstring in `artifacts.py`, so no
executable code moved and the measurement still describes the build it names."* One sentence of the
same shape would close it. **Not blocking**; the claim is true as it stands.

---

### Minor 4 — `weighted_by` is gated on truthiness where everything else is gated on `is not None`

**File:** `src/publishable/cli.py:2694-2701` (`weighted_by=weight_by if weights else None`) against
`src/publishable/cli.py:1103` (`if weights is not None:`).

`weights` is built at `cli.py:1552-1559` only when `weight_by` is a non-empty string **and** the
roster resolved, so `{}` requires an empty roster — under which `aggregated` is empty and the metric
loop never runs, so no record is written. **I could not construct a reachable case** and am recording
it as a consistency note, not a defect: the two guards read the same variable and answer differently,
which is the kind of asymmetry that becomes load-bearing under an unrelated refactor. `is not None`
at both sites would cost nothing.

---

## What I verified by running

**1. The payoff path end to end, on a branch nothing had exercised through `run`.** The advisor's
observation was right and it changed what I tested: the shipped end-to-end test
(`tests/test_cli.py:10029`) declares `resample`, so it takes the percentile branch, where
`corrected_from_pool` is `True` and `Member.weights` is therefore set to `None`
(`cli.py:1148-1149`). **The `diffs` branch — `weighted_paired_t_over_units`, a non-`None`
`Member.weights`, and `_corrected_bounds`' weighted arm — had never reached `run.yaml`.** That is
the branch tasks 4 and 9 exist for and the one the 9–12 review's Major 1 said would "ship live at
task 13".

I built it: `weight_by` + baseline sweep + **no** `statistics.resample`, six units weighted
1/1/1/3/3/3, driven through `main(["run", ...])` and read off disk.

| | weighted | unweighted counterpart |
|---|---|---|
| `method` | `weighted_paired_t_over_units` | `paired_t_over_units` |
| `delta` | 0.9166666666666666 | 1.0 |
| `ci95` | [0.1996660364822509, 1.6336672968510824] | [0.4252004273791009, 1.5747995726208992] |
| `cohens_d` | 1.6543593206751552 | 1.8257418583505538 |
| `weighted_by` | `sampling_weight` | *absent* |
| `n_paired_effective` | 4.8 | *absent* |

All four documented facts reach `run.yaml`, the weighting genuinely moves every number (this is not
a uniform-weights no-op), and `weighted_by`/`n_paired_effective` are **absent rather than null** on
the unweighted run, as § Contrasts specifies. `n_paired` stays 6 while `n_paired_effective` is 4.8 —
the invariant that `n` counts units.

**1b. The weighted *corrected* bound, at a family size where α actually bites.** The run above has
`family_size: 1`, so `correction_level` is 0.05 and `ci95_corrected == ci95` exactly — which is
precisely the case where a wrong α on the weighted corrected branch would be invisible. Since
`correction.py:211-213` (the `weighted_paired_t_over_units(member.diffs, member.weights,
confidence=1.0 - level)` arm) is what spec decision 4 exists for and what the 9-12 review's Major 1
said would "ship live at task 13", I re-ran the same config with a **two-level** grid — two
comparisons, Holm level 0.025 on the second:

| | raw `ci95` | `ci95_corrected` @ 0.025 |
|---|---|---|
| weighted | [2.1996660364822507, 3.6336672968510824] | **[2.0083207765765585, 3.8250125567567745]** |
| unweighted | [2.425200427379101, 3.574799572620899] | [2.2926464039600276, 3.7073535960399724] |

Both properties hold. The corrected interval is strictly **wider** than its raw counterpart, which
proves the α was threaded rather than defaulted; and it differs from the unweighted run's corrected
bound, which proves `member.weights` reached the *recomputation* and not merely the raw interval.
Decision 4's "a counterpart in name only" risk is closed end to end, not just by direct call.

**2. The dated count, re-measured independently.** Item 7's load-bearing half. I did **not** reuse
the implementer's resolver plugin or the task reviewer's fixture — I transplanted C1's and E1's real
`data.units`/`statistics` blocks from the analysis verbatim onto a scaffolded `generic` project with
a **table roster** substitution (`from: index.csv`, 60 synthetic units), and called `validate_config`
directly.

| Config | codes reported |
|---|---|
| **C1** (`weight_by: sampling_weight`, baseline sweep, `resample.stratify_by: [consensus_label, count_stratum]`, `report_by` ×5) | *(no errors)* — only `W-DATA-CLUSTER-UNDECLARED` |
| **E1** (`holdout` random/0.2/`stratify_by: [truth]`, `resample`) | *(no errors)* — only `W-DATA-CLUSTER-UNDECLARED` |
| **can-fail control** (C1 with `resample.n: 3`) | `E-STATS-RESAMPLE-N` |

**The figure reproduces.** C1 has no remaining core-side blocker, E1 unchanged, and the measurement
is discriminating rather than silently vacuous. `W-DATA-CLUSTER-UNDECLARED` is the same fixture
artifact the analysis's own table excludes, and I reproduced it from a completely different roster —
which corroborates that exclusion rather than merely repeating it.

**3. No sentence converts six into an execution count.** I read the whole new § Executability entry
(`docs/feasibility-llm-growth-studies.md:1130-1206`). The Critical the task-13-15 review caught is
properly closed: the *Would execute?* column reads `No — blocked on io.reuse_from` for **C1, C2 and
C3**, identical to E3/E4/E6, and only E1/E2/E5 read **Yes**. "**The executable count stays at
three**" stands unqualified in the prose, and the closing qualification explicitly separates the
table's column from the prose's no-remaining-core-side-blocker reading. The section is dated and
pinned. Spec decision 6 is honoured.

**4. The `_clustered` interaction lands coherently.** `cluster_by` + `weight_by` + a resolved
comparison, through `validate_config`:

```
['error:E-DATA-CLUSTER-CONTRAST', 'warning:W-STATS-RESAMPLE-CLUSTERS']
```

Exactly the surviving refusal, no `E-DATA-WEIGHT-CONTRAST`, and not zero codes — the combination does
not fall through the hole its sibling's retirement left. `reference.md:2450` ("The `_clustered`
suffix does not compose with either weighted form in this build") agrees with the code, and I checked
the § Errors row text itself rather than trusting `test_the_sibling_refusal_rows_state_their_own_reading`:
both surviving rows now state their own family-reading property and neither cites the retired code.

**5. A newly reachable input that could not be reached before.** `weight_by` naming an attribute
absent from `units.attributes`, beside a contrast — a combination the retired refusal used to
intercept. Through `run` it produces a clean named diagnostic, `E-DATA-WEIGHT-UNKNOWN`, at exit 1.
No traceback, no fabricated number.

**6. The derived-metric contrast shape**, through `run` rather than by direct call — the evidence
behind Major 1, above.

---

## What I verified by reading

- **`Member.weights` has exactly one construction site** in all of `src/` (`cli.py:1135`), so nothing
  else needed teaching about the new field. The field is appended with a default, and `Member` is
  never serialized by field enumeration — `grep` for `asdict`/`astuple`/`dataclasses.fields` over
  `src/` returns **nothing**, and `correction.corrected_fields` builds an explicit dict. The
  docstring's "neither may reach `run.yaml`" survives the third field.
- **`base_keys` is bound at `cli.py:898`**, outer to the metric loop, so the
  `base_keys if is_derived else col_keys` selector at `cli.py:1106` cannot hit an unbound name on any
  path. `col_weights` is likewise bound before both branches at `cli.py:916` with a comment saying
  why — the right instinct.
- **The `CLAUDE.md` invariants hold.** The contrast is computed over `col_keys`, the intersection of
  both sides' completed units, and `col_weights` is derived from *that same list in that same order*
  (`cli.py:980`), so the point estimate, the effect size and the interval cannot weight a unit the
  difference beside it did not come from. The interval is its own construction over the intersection
  in both weighted forms — never a difference of two intervals. Holm still ranks on
  `abs(member.delta) / half` over the raw `ci95` half-width (`correction.py:146-150`), untouched and
  still correct under weighting, since `delta` and `ci95` are both the weighted pair.
- **The seam vocabulary agrees across all three batches.** The `method` strings minted in task 2 are
  the strings task 8 emits and task 15 describes: `weighted_paired_t_over_units` and
  `weighted_paired_percentile_over_units` each appear in `reference.md`'s construction table
  (2430-2431), in `stats.py`/`cli.py`, and in `run.yaml` as I read it off disk. No record key is
  written that no document names, and no documented key goes unwritten — I checked both directions.
- **The retirement left nothing dangling.** `grep -rn E-DATA-WEIGHT-CONTRAST` over `src/` and
  `docs/superpowers/spec-defects.md` is empty; the only survivors are two absence assertions in
  `tests/test_cli.py:10104-10105` (correct — that is their job), earlier **dated** measurement
  sections of the feasibility analysis (correct — those are historical records that must not be
  retro-edited), and `CLAUDE.md:69`, which is Major 2.
- **Positional locators and count phrases survive the two row deletions.** I grepped `reference.md`
  for `rows above|rows below|two siblings|three siblings|both siblings` and read every hit: all name
  their sibling rows by *what the row does* rather than by position, and none sits adjacent to either
  deletion. The two count phrases the deletions did invalidate were both fixed on the branch — "none
  of those **five** constructions exists" → "none of those", and "Which of the **four** below
  applies" → "Which row below applies".
- **The prose sweep held — checked twice, the second time by claim rather than by spelling.** My
  first sweep grepped four specific phrases (`no construction in this build weights`, `the three
  paired estimators`, `does not weight a contrast`, `contrast is unweighted`) over the four documents
  and `src/`, and returned nothing. That is a grep for *spellings*, which is the substitution
  `CLAUDE.md` § Answering a question with a proxy says shipped a credential leak — and zero diff on
  the other three documents is not zero stale claims, since a retirement can falsify a sentence no
  commit touched. So I re-swept by reading every `weight` hit in `README.md`,
  `docs/design-principles.md` and `docs/experimental-designs.md`. There are exactly three, and all
  three survive the retirement: `design-principles.md:42` ("core weights the estimate and says so in
  the record") is now *more* true than before; `experimental-designs.md:354` ("`weight_by` weights
  the estimate and records `weighted_by` beside it") is exactly what I read off `run.yaml`; and
  `README.md:97` is the word "Lightweight" in a comparison table. Neither § What core will not do for
  you nor § Mistakes core prevents ever claimed core refuses a weighted comparison.
- **No table-level count was invalidated by the two row deletions.** Separately from the positional
  locators, I swept `reference.md` for `NOT BUILT` and for both numeric and spelled-out
  `N rows|checks|codes` phrases. No statement anywhere counts the rows of § Errors or § Validation,
  so deleting one row from each invalidates no total. The `NOT BUILT` hits are all about the config
  block list and the CLI `Status` column, neither of which `E-DATA-WEIGHT-CONTRAST` was ever part of
  — the deleted code comment said so explicitly, and `weight_by` itself was already built.
- **A thin weighted contrast still carries both keys.** `min_reported_n` could have suppressed the
  records where an effective size matters most, so I checked rather than assumed: its only use inside
  `_comparison_step_blocks` is at `cli.py:1159`, which is *after* the `if weights is not None:` block
  at `cli.py:1103` and emits a warning rather than `continue`ing. There is no `continue` anywhere in
  the metric loop (lines 890-1140). A weighted contrast on a below-threshold intersection publishes
  `weighted_by` and `n_paired_effective` normally.
- **The filings are real filings.** `paired_percentile_of_derived`'s new docstring claims the
  degenerate-draw sweep is "filed rather than built, with a named owner"; the entry exists
  (`spec-defects.md`, *OPEN — a stratified paired draw can publish a zero-width contrast interval —
  **Owner: H4b-2***), and **H4b-2 is a real, unbuilt slice**, not a closed one. Every H4b deferral
  was genuinely re-ownered from the now-split `H4b` to `H4b-2`, including the sorted-pool
  precondition, the finiteness gap, and the `report_by`-under-`resample` gap, which the feasibility
  entry correctly holds open against C1–C3's own "no remaining core-side blocker" claim rather than
  rounding it away. The commit message's "every H4b filing re-ownered" is accurate.
- **The worked example is untouched.** `README.md`, `docs/design-principles.md` and
  `docs/experimental-designs.md` have **zero** changes on this branch. `reference.md`'s only diff
  line matching any `cohort-pilot` figure is the § Weighted samples paragraph whose "228 units"
  appears identically on both sides of the diff. No interval, hash prefix or count moved.
- **Mechanical pass.** I ran a link/anchor/whitespace checker over the four documents, the
  feasibility analysis and `CLAUDE.md`. No trailing whitespace, no tabs, no duplicate anchors. All 22
  reported "bad anchors" are false positives of my own slugger on `&`- and `.`-containing headings
  (`#secrets--credentials`, `#executionsjsonl--…`), every one of them **pre-existing** and none on a
  line this branch touched.

---

## What I could not check

- **Whether C1–C3 actually depend on `io.reuse_from`.** Unsettleable by construction — it is a
  step-level call invisible to any config, and `growth-shortcut`'s steps do not exist. The analysis
  says so in its own words and does not claim otherwise; I am recording that I inherited the
  limitation rather than closed it. This is the sole reason the executable count stays at three, and
  it is correctly *stated* rather than assumed in either direction.
- **C2 and C3 end to end.** I measured C1 and E1 (the brief asked for at least two, one of each
  kind, which separates "no core-side blocker" from "blocked on `io.reuse_from`"). C2/C3 differ from
  C1 only in contrasting a recorded column rather than a derived metric, which I exercised directly
  through my own weighted-column runs instead.
- **The real `growth_screen`/`growth_shortcut` plugins.** They do not exist; every measurement in
  this section, mine included, rests on a substitution, and mine used a *different* substitution from
  the two before it precisely so agreement means something.
- **`aggregate`-side weighting by a template.** § Weighted samples says a template weights its own
  derived metric from the weight column handed to it as a unit attribute. I confirmed the column
  reaches `aggregate` (there is a shipped test for it) but did not write a template that uses it.

---

## Note on process

I ran the suite in the **foreground** both times, and every measurement above is against the **full,
unfiltered** suite or a fresh throwaway module of my own — never a `-k`-narrowed subset of the
existing suite. The one narrowing I did use (`-k` over my own two probe files) selects among tests I
wrote in this session and makes no silence claim about the shipped suite. The branch's own history
records that shortcut producing a false blind-spot claim twice; it seemed worth being explicit that
it was not repeated.
