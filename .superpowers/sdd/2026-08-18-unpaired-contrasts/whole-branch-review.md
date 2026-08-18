# H4c — whole-branch review

**Reviewed at** `2e6786c` (branch `h4c-unpaired-contrasts`), against `main`.

**Verdict: MERGE.** One Major and one Minor were found, **both fixed in this review** and verified by
a full green suite; the working tree now carries those two fixes as uncommitted changes for the
merger to commit. Nothing else blocks. The slice delivers what it claims: `E-DATA-ALLOCATION-CONTRAST`
retired, four unpaired constructions built and reachable through a real `run`,
`E-DATA-WEIGHT-ALLOCATION-CONTRAST` minted and airtight, `paired` derived, and **both counts unmoved
at six and three** — re-measured, not carried.

Tree was clean at start (`git status --short` and `git diff` both empty). At finish it holds exactly
the two comment fixes below (`src/publishable/cli.py`, 3 insertions / 11 deletions, comments only) and
nothing else. **No mutation is left applied** — each of the three was reverted by editing the file
back, `__pycache__` cleared, and verified by a green 2275 **and** by inspecting `git diff`.

---

## Gates — all verified by running

| Gate | Result |
|---|---|
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 80 files already formatted |
| `uv run mypy` | Success, 45 source files |
| `uv run pytest` | **2275 passed, 1 skipped, 2 xfailed** — exactly the expected count |

Run in the foreground, unfiltered, twice: once at start to establish the baseline and once at the end
to verify the mutation revert **by behaviour** rather than by `git status`.

---

## Findings

### Major 1 — FIXED — a comment asserting the unpaired arm is unreachable, 50 lines above where it runs

**`src/publishable/cli.py:1382-1383`**, inside `_comparison_step_blocks`' `Member`-construction
commentary:

> `# computed from. This function never builds `sides` yet — that is`
> `# task 14 — so only `pool`/`diffs` are reachable from here.`

**This is false at HEAD.** Line 1438 of the same function builds `sides=UnpairedEvidence(...)`. The
comment is a batch-3 artifact that batch 4 (task 14) did not update when it added the very code the
comment denies. It also leaks a plan-task number (`task 14`) into production source.

Verified by: reading lines 1378–1453 in final state, and by
`grep -n "never builds \`sides\` yet" src/publishable/cli.py` → one hit at 1382, against
`grep -n "UnpairedEvidence(" src/publishable/cli.py` → one hit at 1441, same function.

**Why Major rather than Minor.** It is not merely stale description — it asserts a **negative
reachability guarantee** ("only `pool`/`diffs` are reachable from here") about the precise corner the
spec records as having been given *four wrong grounds in four commits*. A future reader tracing
`_corrected_bounds`' `sides` arm back to its construction site finds a comment telling them that arm
is dead code, which is the "reader greps for exactly that name and stops looking" failure mode
`CLAUDE.md` names. It is the first entry in § Habits that cost real work, and the previous slice spent
two review rounds on this exact class.

**Fix applied:** the two-sentence claim **deleted** (not rewritten — `CLAUDE.md` prefers a deletion,
which cannot invent), leaving the surrounding paragraph, which is correct, intact.

### Minor 2 — FIXED — a seven-line comment duplicated verbatim, back to back

**`src/publishable/cli.py:1424-1430` and `1431-1437`** are byte-identical:

> `# The single decision, read once for all four fields now:` …through… `# corrected_from_pool decision the paired arm reads.`

Verified by `grep -n "The single decision, read once for all four fields now"
src/publishable/cli.py` → hits at **1424 and 1431**. A copy-paste in task 14's edit; `ruff format`
does not collapse comments, so no gate catches it.

**Fix applied:** the second copy deleted.

### Both fixes verified by running

`uv run pytest` → **2275 passed, 1 skipped, 2 xfailed** — unchanged, as comment-only edits must be.
`ruff check` clean, `ruff format --check` 80 files, `mypy` 45 source files clean. `git diff` shows
exactly two hunks in `src/publishable/cli.py`, comments only, 3 insertions / 11 deletions.

---

## What I verified by running (not by reading)

**1. The spec's discriminating fixtures reproduce exactly against shipped code.** Direct computation,
not reading:

| Quantity | Spec literal | Shipped |
|---|---|---|
| Fixture A half-width | 3.039125537798091 | exact match |
| Fixture A `cohens_ds` | 2.1251185925162073 | exact match |
| Fixture A Bonferroni ratio (df 13.714286) | 1.1706821500146336 | exact match |
| Fixture B half-width (CR1, df over `G_s`−1) | 34.14810237373095 | exact match |
| Fixture B Bonferroni ratio (df 2.095031) | 1.4227764722656022 | 1.4227764722656024 (last-ulp) |
| Fixture B IID Welch on identical data | 9.647234756296374 | exact match |

The two Bonferroni ratios differ by 21 %, so the corrected bound is pinned to the **unpaired
construction at its own α and df** — a bound built at a paired, IID or unclustered df would be
visibly different. Method strings returned were `welch_t_over_units` and
`welch_t_over_units_clustered`.

**2. My own end-to-end `run`, on my own config** — `groups × grid`, `allocation: between`,
`assign.arm.by_attribute`, `cluster_by: site`, per-arm cluster counts **4 and 3** (not the documented
"both 3" unfailable shape), declaring **both** a cross-arm and a within-arm contrast in one family.
`validate` clean, `run` → `EXIT_OK`. The `run.yaml` on disk carried:

- **Unpaired entry:** `paired: false`, `method: welch_t_over_units_clustered`, `n_of: 5`,
  `n_against: 7`, `n_clusters_of: 4`, `n_clusters_against: 3`, `cohens_d: -0.5154…` (the *d*s value),
  and **`n_paired` absent — not null**.
- **Paired entry, same run:** `paired: true`, `n_paired: 7`, `n_paired_clusters: 3`,
  `method: paired_t_over_units_clustered`.

**`n_paired`'s absence was asserted on the raw `run.yaml` text**, not the parsed dict — the only
`n_paired` lines in the file belong to the paired entry. Key **order** was also checked on raw text:
`n_of`/`n_against` are written **in place** (after `method`, before `ci95`), per correction 12, not
appended after `correction`.

**3. The corrected bound threads end to end at a smaller α.** Re-ran the same config under
`correction: bonferroni` so the unpaired entry landed at `correction_level: 0.025` rather than 0.05.
Raw half-width 4.548314238705341 → corrected 5.774778280365419, ratio 1.2696524420461295. Inverting
that ratio through the shipped `_t_critical` gives an implied **df of 3.735** — a non-integer
Welch-Satterthwaite combination bounded by the two per-side `G_s`−1 values, and decisively **not**
`n_of + n_against − 2` = 10 (ratio 1.182) nor any of the three rejected readings the spec's decision 4
names. This is decision 4's df rule confirmed through a real run, not by direct call.

**4. Mixed-pairing correction family.** In that one run both entries shared `family_size: 2`,
`family: {comparisons: 2, metrics: 1}`, and Holm ranked the paired entry first (0.025) and the
unpaired last (0.05) on point-estimate-over-half-raw-width — the `CLAUDE.md` invariant preserved
across a family holding both pairings for the first time.

**5. A discriminating mutation on the one observable branch inside the `sides` arm.** Correction 10
establishes that `_corrected_bounds`' arm *order* is unobservable; it does **not** cover the
`sides.clusters` branch inside that arm, which is very observable (34.148 vs 9.647). I changed
`if member.sides.clusters is not None:` to `if member.clusters is not None:` — always false, since
`__post_init__` forbids the two together — silently downgrading every unpaired clustered corrected
bound to the IID form. **Full unfiltered suite, foreground: 2 failed, 2273 passed.**

```
FAILED test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts
       - assert 11.484952890215286 == 48.58511662986156
FAILED test_the_five_t_arms_are_each_reached_by_one_member_shape - AssertionError: sides_clustered
```

The branch is pinned by two independent tests. Reverted **by editing the file back**, `__pycache__`
cleared, and verified both by a green 2275 and by an empty `git diff`.

**5b. A second mutation, on the batch-3/batch-4 seam itself** — the `Member` field selection that
decides `sides` versus `diffs`, which is where batch 3's new evidence kind meets batch 4's wiring and
the first thing the brief names under "the seams between batches". At `cli.py:1409` I removed the
`not is_paired` disjunct, so an unpaired non-pool member would carry `diffs` instead of only `sides`.
**Full unfiltered suite, foreground: 19 failed, 2256 passed**, across `test_cli.py`'s unpaired run,
derived, clustered, correction-family, `report_by`/`Estimate` and both-pairings tests. The seam is
heavily pinned, and the failure mode is a loud `UnboundLocalError` rather than a silent wrong number
— `diffs` is genuinely unbound on the unpaired arm rather than stale from a previous metric, which
also confirms the "bound here, before either branch" discipline at `cli.py:971-983` is doing real
work. Reverted by edit; `git diff` confirmed empty before the fixes below were applied.

**6. Re-measured the dated count myself.** § Executability's new section is headed *"Measured on
2026-08-18 against commit `6b9bf119a9706aeb34be7e10a4311280e1b9e5d9`"*;
`git show -s --format=%ci 6b9bf11` → `2026-08-18 18:42:13 -0400`. **Date matches the commit.**
Its greps (`allocation: within` → 3, `allocation: between` → 1) reproduce **exactly at the pinned
commit** and read 4/2 at HEAD only because the section's own prose contains both strings — the
section was written one commit later (87d1706), which is correct practice, and the pin is what the
rule asks for. The substantive claim is independently confirmed at HEAD: `grep -n 'groups:'` → two
hits, **both `groups: []`**.

Two configs re-measured by extracting their YAML and reading the resolved fields: **E1** —
`allocation: within`, `groups: []`, no `weight_by`, no `cluster_by`, `contrasts: []`; **C1** — no
`groups` declaration at all, `contrasts: []`. Neither refusal can reach either. **Six / three,
unmoved**, confirmed.

---

## What I verified by reading

- **`E-DATA-ALLOCATION-CONTRAST` is gone.** Enumerated the emit sites by reading `_check_sweep` first,
  then confirmed by grep over `src/ docs/ tests/ README.md`. No emit survives. The single `src/` hit
  is `cli.py:899`, a docstring saying the code *is retired*; test hits are docstrings and negative
  assertions (`assert "…" not in section`); development-record and older dated feasibility hits are
  exempt evidence.
- **The four `method` spellings match what the documents name**, checked as emitted **string
  literals** rather than function names: `stats.py:495` `welch_t_over_units`, `stats.py:571`
  `welch_t_over_units_clustered`, `stats.py:1802` default `unpaired_percentile_over_units`,
  `cli.py:1273/1275` the clustered/plain percentile pair. `unpaired_percentile_of_sides` is a function
  name and never reaches a `method`.
- **The suffix rule still licenses the two undocumented clustered spellings.** `reference.md:2441`
  reads *"each of the **unweighted** forms above takes a `_clustered` suffix"*, and both unpaired
  forms sit in that table (2436, 2437). Task 1's narrowing of the two `weighted_paired_*` rows (2438,
  2439, now *"A **paired** column metric"*) did not touch the quantifier. The two `_clustered`
  unpaired spellings having **no rows of their own is the correct state** — I did not file it.
- **Record-key cross-tabulation, both directions.** Every key the code writes is named in
  `reference.md` and every documented key is written: `n_of`, `n_against`, `n_clusters_of`,
  `n_clusters_against`, `n_paired_clusters`, `n_paired_effective`, `weighted_by`. No orphan either
  way.
- **`Member.sides` against every construction site.** `grep -rn "Member(" src/publishable/` returns
  exactly one production site (`cli.py:1402`), and it passes `sides`. The other hits are
  `RepeatMember`/`RepeatLevel` in `replication.py`, a different type. Nothing else builds a `Member`
  that should now pass `sides`.
- **`_corrected_bounds` is five *t* arms plus `pool`** — six return paths, per correction 4. The
  `sides` arm branches on `sides.clusters` the right way round.
- **The weighted unpaired boundary.** `validate.py:5041-5079` runs the guard **inside** the
  per-comparison loop, gated on `crossed_group_axes` being non-empty, so it catches every cross-arm
  shape carrying `weight_by`. Its sibling `E-DATA-WEIGHT-CLUSTER-CONTRAST` (5001) fires independently
  on `comparisons > 0`, so a config declaring `weight_by` + `cluster_by` + a group axis draws **both**
  — coherent, and `validate` collects rather than aborting. `cli.py:918` and `cli.py:939` mirror both
  as `ValueError` bookkeeping guards, so neither combination can reach an unbuilt construction even if
  `validate` were bypassed.
- **The shared predicate is one expression with exactly two callers** — `contrasts.crossed_group_axes`
  (119), read by `cli.py:930` and `validate.py:5046`. No second spelling.
- **Correction 1 is honoured at both emit sites.** `validate.py:5332-5335`'s message now reads *"this
  comparison's own denominator over the two sides' completed units"* — the key name **deleted**, not
  rewritten into a claim false of an unpaired contrast. `cli.py:1480-1494` fires per side when
  **either** is below the floor, one finding per entry.
- **`n_paired`'s readers re-measured at HEAD** (not carried from `6a1ece1`): two writes in `cli.py`
  (1076, 1220), one local variable, one warning denominator. Nothing in `attrition` or `_entry_for`
  reads it, so the conditional absence breaks no reader.
- **The worked example is untouched.** `git diff main...HEAD` over `README.md`,
  `design-principles.md` and `reference.md`, filtered for every `cohort-pilot` literal (0.581, 0.488,
  0.661, 0.607, 0.412, 0.026, −0.007, 0.059, −0.169, 0.014, 228, 240, and all five hash prefixes) —
  **no hit on a removed line**. `README.md` and `design-principles.md` are not in the diff at all.
- **§ Allocation's repaired block** (`reference.md:1352-1367`) carries `abs_error`, `delta: 0.041`,
  `ci95: [0.012, 0.070]`, `method: welch_t_over_units`, `paired: false`, `n_of: 116` + `n_against:
  112` = **228**, the worked example's completed count, and **no `n_paired`**. Its `cohens_d: 0.27`
  is a value, matching what the unpaired recorded-column arm actually writes (key `cohens_d`, value
  from `cohens_ds`). The `03_`/`01_` label prefixes are the pre-existing documented convention
  (`reference.md:2613`, *"recorded with its index; declared without one"*), not this branch's doing.
- **Nothing dangles from the two deleted rows.** The one positional locator in the region
  (`reference.md:296`, *"the … rows above, between them"*) names both siblings **by name** and both
  are still at 288/289 unmoved; the deleted § Validation row was at 309, **below** it. Swept for the
  **claim** rather than the code string — `unpaired estimators`, `no unpaired construction`,
  `refuses to compute that delta`, `no construction computes an unpaired`, `refused outright rather
  than reported paired` — across `src/`, `tests/` and the four documents **named individually**:
  no survivor. `E-SWEEP-BASELINE-GROUP`'s message is restated on the peers ground (`validate.py:4689,
  4699`), not the expired temporal one.
- **`experimental-designs.md` § Mistakes core prevents** reads coherently after the deletion: the
  three-code enumeration is narrowed to two, the crossed-arms clause removed, a positive statement
  appended, and the *"two more close the routes"* count phrase still holds. No dangling conjunction.
- **No sentence converts the six into an execution count.** Swept the feasibility analysis,
  `reference.md`, `spec-defects.md` and the batch records for `unblocks N`, `newly execut`,
  `executable count goes/moves/rises` and `six … execute`, excluding the zero/unmoved forms. Only hit
  is a batch-3 review line recording that it ran the same sweep.

**Mechanical pass — clean.** Wrote a throwaway checker over the four documents plus the feasibility
analysis, skipping fenced blocks: every relative link resolves, every `#anchor` resolves (after
correcting my slugger to match GitHub's per-space hyphenation — the first run's 22 "dead anchors" were
all my bug, not the docs'), no duplicate anchors within a file, every table row matches its header's
column count, and no trailing whitespace, tab, or invisible unicode.

---

## Could not check / out of scope

- **`CLAUDE.md` has no H4c § Repository status entry, and this is not a finding.** I ran the
  discriminating check the convention question needs: `git log -- CLAUDE.md` shows H4b-2's entry is
  `051600c`, which the spec itself pins as *"`main` … after H4b-2 merged"* — so the entry is written
  **post-merge on `main`**, not on the slice branch. Flagging it only as a **required follow-up**:
  after merge, `CLAUDE.md`'s *"Order of the slices that remain: H4c → the rest"* and H4b-2's
  forward-reference re-ownering a `report_by` filing "to H4c" both go stale and need the usual entry.
- **`docs/feasibility-llm-growth-studies.md:959`** still lists `E-DATA-ALLOCATION-CONTRAST` in a
  refusal table. It sits inside an **older dated** § Executability subsection, which the spec's task
  19 rules is *"re-dated rather than edited"* and `CLAUDE.md` protects as evidence. Correctly left.
- **`validate.py:5148`'s docstring** still says *"so `n_paired` is bounded above by this number"*,
  directly above the message that was correctly generalized away from that key. Not false of a paired
  contrast, merely narrower than the code it now describes. Noted rather than filed — below the bar,
  and a rewrite here would invent where the message's own deletion did not.
- I did not re-litigate any finding already closed and verified in the four batch reviews.
- The `_clustered` run-side half-width literal in
  `test_a_clustered_cross_arm_contrast_runs_and_records_a_cluster_robust_interval` is self-captured
  (*"from this test's first green run"*) rather than independently derived. The two integer cluster
  counts beside it (4 and 3, which cannot coincide) carry the discrimination, and I verified the
  construction itself independently against fixture B, so this is acceptable rather than a finding.
