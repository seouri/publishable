# H5b — whole-branch review

Reviewed at `14b816e` on branch `h5b-non-numeric-downstream` (41 commits ahead of `main` at `d70b11e`),
2026-08-22. **This was a real-command review**: every behavioural claim below was established through the
**installed console script** (`uv run --project <repo> publishable run|report|diff …`) against projects
scaffolded by `publishable new` + `generate experiment` **outside this repo**, or by a **mutation applied
at the call site and the suite re-run**. Where a claim rests on reading, it says so. Every mutation was
reverted **by editing the file back** and the revert verified by **re-running**; `git status --porcelain`
is empty and the final full-suite run below was taken after the last revert.

## Verdict: **HOLD** — three Majors, no Critical. All three are claim defects; nothing in `src/` computes a wrong number.

The precedent is H7d Part A, whose whole-branch gate held the merge on two Majors closed the same day.
Two of the three below are **false or incomplete claims about shipped behaviour**, which is the category
this repo grades hardest, and one of them is this slice's own signature defect in a **fifth** home.

## Gates

| Gate | Result |
|---|---|
| `uv run pytest` (HEAD) | **2931 passed, 1 skipped, 2 xfailed** in 191s — matches the expected figure exactly |
| `uv run pytest` (`main` at `d70b11e`, in a throwaway worktree) | **2891 passed, 1 skipped, 2 xfailed** |
| Delta | **+40 tests**, xfail count `2 → 3 → 2` (batch 2's strict `xfail` minted, batch 3 converted it). Accounted: +4 / +25 / +6 / +5 / +0 across the five batches, which is the ledger's own arithmetic |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 93 files already formatted |
| `uv run mypy` | Success, 52 source files |

---

## Findings

### Major 1 — `W-STATS-CONTRAST-RESAMPLE-THIN` is a **fifth** thing a shipped run newly earns, and it appears in no enumeration this slice wrote

**Established by behaviour, console script, one project run twice — once against this branch and once
against a `main` worktree, same project, same commit of the project, same seed.** Two conditions
(`baseline: pearson` / `grid: [spearman]`), six units of which four record `score`, all six record a bool
`flag`, project-local template returning `n_rows`/`n_flag`/`mean_score`:

```
main  stdout warnings:  W-ENV-UNLOCKED
HEAD  stdout warnings:  W-ENV-UNLOCKED
                        W-STATS-RESAMPLE-THIN            (×2, condition 0 and 1, metric 'mean_score')
                        W-STATS-CONTRAST-RESAMPLE-THIN   condition 1 ('method=spearman') vs baseline,
                                                         step 'step01_summarize_units' metric
                                                         'mean_score': 1996 of 2000 resample draws
                                                         produced a value
```

The mechanism is item (iv)'s exactly — admitting units that carry no numeric column creates degenerate
draws — but it fires at a **different emit site** (`cli.py:1659`, the contrast arm) under a **different
code** from the site item (iv) names (`cli.py:3257`). `reference.md`'s own row for it already rules the
two are two facts: *"The contrast-side sibling of `W-STATS-RESAMPLE-THIN`, on the same disclosure ground,
**since neither the `n_paired` denominator nor a thin pool are the same fact**."*

**The omission is mechanical, not a judgement call.**
`grep -rn "CONTRAST-RESAMPLE-THIN"` over `CLAUDE.md`, `docs/feasibility-llm-growth-studies.md`, the design
spec, the plan, `H5b-SCOPING.md` and every file under `.superpowers/sdd/2026-08-22-non-numeric-columns-downstream/`
returns **zero lines**. The can-fail control — `grep -rc "W-STATS-RESAMPLE-THIN"` over the same set —
returns `CLAUDE.md:1`, `feasibility:1`, `design:2`, so the sweep hits when the string is there. **Three
surfaces each say "four things newly stop or newly warn" and the correct number is five**: the design's
§ The behaviour change, `CLAUDE.md`'s H5b entry, and the feasibility § Executability entry dated
2026-08-22 against `56aad22`.

This is the design's own stated obligation — *"name what actually stops covers a warning a shipped run
newly earns, not only a refusal"* — and item (iv) was written up as *"the item a three-item list would
have read as excluded."* A four-item list read this one as excluded the same way.

**Route: close in a fix round now.** `CLAUDE.md`'s "Four things newly stop or newly warn" → five, edited
in place. The feasibility § Executability entry gets an **appended** correction, which is that section's
own convention for a published figure. **The design spec and `progress.md` are development record and
must not be retro-edited** — the ledger may gain an appended note.

### Major 2 — the slice's signature two-case sentence has a **fifth** home, in `spec-defects.md`, and it is wrong on two of the three mixtures

`docs/superpowers/spec-defects.md:8693-8695`, in the OPEN entry *whether `E-STEP-RETURN-TYPE` should ever
be forgiving*:

> on the **read** side, a column reaches `aggregate`'s table regardless of the mixture, and is published
> as a metric **only when every value carried for it is a real number** — one `str` costs that column its
> own metric block and nothing else.

It fails twice:

1. **The all-or-nothing clause is the batch-1 Critical verbatim.** Measured through the console script,
   six units of which three record `{"score": float(i)}` and three record `{"score": None}`:
   `run.yaml` publishes `score: {value: 1.0, n: {resolved: 6, completed: 3, …},
   ci95: [-1.484…, 3.484…], method: t_over_units}`. A column not every value of which is a real number
   **is** published.
2. **The `str` clause describes an unreachable state as reachable.** Ruling 1's amendment table rules
   that `str` beside a number *cannot occur*, and *"a document that states one invites a later reader to
   build against it."* Measured: exit **4**, `status: failed`, every execution
   `E-STEP-RETURN-TYPE ContractError: units.parquet: column 'score' recorded both a float (unit 'p1') and
   a str (unit 'p4')`. It does not cost "that column its own metric block and nothing else" — it costs
   the whole run.

**The mechanism is the named habit, and it is visible in the commit graph.** `2e9f5e4` (task 3) wrote
this sentence **and** the `reference.md` copy that became batch 1's Critical. Fix round `020ddf6` touched
`docs/reference.md` and the plan — `git show --stat 020ddf6` → two files — and never swept
`spec-defects.md`. *Sweep for the claim, not for the file the claim was first noticed in*, with both
copies written by one commit.

**Route: close in a fix round now**, in place (`spec-defects.md` is the live-list exception). **Delete**
the false clause rather than rewriting it — the entry's residual (whether the *write* should ever be
loosened) is correct and stands on its own; the read-side paragraph can simply point at Ruling 1's
amendment table, which the batch-3 ledger already made the single authority every site links to instead
of restating.

### Major 3 — `report.py::_is_metric_entry`'s ground is a two-case account of the same three-case rule, and its second case is false of the reachable middle one

`src/publishable/report.py`, `_is_metric_entry`, edited by this slice (task 14, `a855f91`):

> a recorded column named `by` whose every value is a number keeps that value on the write side, as a
> real metric entry. **(A NON-numeric one keeps no metric block at all**, so the record can hold either
> shape under this key and a structural test is what reads both.)

**Measured, console script, six units, step recording `{"score": float(i), "by": float(i) if i < 3 else None}`:**

```
aggregated.step01_summarize_units keys: ['score', 'by', 'n_rows', 'n_flag', 'n_cols']
by: {value: 1.0, n: {resolved: 6, completed: 3, …}, ci95: [-1.484…, 3.484…],
     method: t_over_units, repeat_spread: {...}}
```

and `publishable report <run.yaml>` renders it as a full metric row. A `by` column that is *not* numeric
for every unit keeps a complete metric block. The parenthetical's *"A NON-numeric one"* most naturally
covers that column and is false of it.

The conclusion (*the record can hold either shape, so a structural test reads both*) **survives** — the
code is right, and this slice's whole point in that file was to stop answering a structural question with
a name. It is the **ground** that is wrong, and this is the third time on this slice a guard's
justification has been wrong while its conclusion held; the batch-3 ledger's own instruction for that
case was *write a true ground or delete the sentence rather than add a third layer.*

**Route: close in a fix round now — delete the parenthetical's second clause.** *A rewrite invents; a
deletion cannot.*

### Minor 1 — arm G's docstring calls `1927` both the "fourth" and the "third" distinct `resample_draws` literal

`tests/test_cli.py::test_arm_g_the_report_by_stratum_path_moves_with_the_widened_collapse`: the docstring
says *"the **fourth** distinct such literal measured in this slice, beside arm B's `1998` …, plan
correction 7's `1999`, and the batch 2 review's own `1997`"*; the inline comment above the assertion says
*"The third distinct `resample_draws` literal of this slice."* **`1927` is the fourth** (1998, 1999, 1997,
1927), and `CLAUDE.md`'s H5b entry names all four, so the inline comment is the wrong one. Deliberately
left by batch 5 for this gate — a records task may not edit a pin arm's docstring, which was correct
restraint.

**Route: fix now, with this gate named as the editor in the commit message.** No literal and no assertion
moves; only the ordinal word in a comment.

### Minor 2 — the consolidated RE-OWNED note's stated verification grep reaches three of the five entries it names

`spec-defects.md`'s *RE-OWNED 2026-08-22, as H5b completes* says the five were *"all verified with
`grep -n "H5b, H6, H9, H3c-3's remaining 14" docs/superpowers/spec-defects.md` plus the spine-citing
variant."* Run at HEAD, that grep returns lines **8613, 8643, 8674** and **8877** (the note quoting
itself). The fifth entry it names first — the `Estimate.method` coercion one — sits at **line 1951**,
where the phrase is **line-wrapped** after `H3c-3's`, so the stated command cannot see it;
`grep -n "H5b, H6, H9"` finds it. The count of five is **correct** (1951, 8613, 8643, 8674, plus the
spine-citing entry at 8572) — it is the stated verification that under-finds.

This is precisely batch 5's own recorded lesson (*a `grep -rF` cannot match a line-wrapped phrase*)
recurring in batch 5's own output, one paragraph away from the entry that records it.

**Route: fix in place** — narrow the quoted command to one that can find all four parenthetical hits.

### Minor 3 — `W-STATS-COLUMN-THIN` multiplies one fact by the column count on any roster smaller than the floor. **File, do not fix.**

**Measured, console script, six units, step recording three fully covered numeric columns, scaffold floor
`min_reported_n: 10`:**

```
warning W-STATS-COLUMN-THIN  limits.min_reported_n
        condition 0, step 'step01_summarize_units': recorded column 'a' carries a number for 6 unit(s),
        below limits.min_reported_n (10)
   … identically for 'b' and 'c'
```

Three warnings, one fact: the *roster* is below the floor, and no column is partially covered. The
emit site's own comment refuses per-column-per-level on exactly this ground — *"per-column-per-level
would multiply one fact by the number of columns"* — and Ruling 5's own argument for narrowing the
warning was that *"an unconditional warning would fire on runs with nothing wrong."*

**But it is literally what Ruling 5 ordered** (one warning per condition, step and column below the
floor), the § Warnings row is honest about it (*"carries a real number for fewer units than
`limits.min_reported_n`"*, not *"is partially covered"*), and narrowing a controller ruling's
just-minted warning inside this gate would be a behaviour change with no argument behind it. **Route:
file in `spec-defects.md`, owner unassigned with the reason** (no remaining slice — H6, H9, H3c-3's
remaining 14 — has this loop as its surface), for whoever next sweeps it.

---

## What was verified, and how

### The behaviour change: is every moved key one of the nine? **Yes, for the config exercised — and the classes that config could not reach are covered by arms F and C.**

One project, run against `main` and against HEAD from the **same project commit** (so `code_hash`,
`parameters_hash` and `input_manifest_hash` are identical between them), the two `run.yaml`s flattened to
leaf paths and compared key by key by script. Config: two conditions with a declared baseline,
`correction: holm`, `report_by: [cohort]`, six units in two cohorts, four recording `score`, all six
recording bool `flag`, template returning `n_rows`/`n_flag`/`mean_score`.

**No key name appeared and none vanished** (the only `ONLY-*` lines were `ci95: null → [x, y]`, a value
shape, not a key). Every moved leaf fell in one of:

| Class | Moved keys observed |
|---|---|
| arm B's seven (derived metric over a widened table) | `n_rows.value` `4.0→6.0` and `.ci95`, `n_flag.value` `0.0→6.0` and `.ci95`, `mean_score.n.completed` `4→6`, `mean_score.ci95`, `mean_score.resample_draws` `2000→1996` |
| arm E (the correction family) | `vs_baseline…mean_score.n_paired` `4→6`, `n_flag.n_paired`, `n_rows.n_paired`, `mean_score.correction_level` `0.025→0.05` **and** `score.correction_level` `0.05→0.025` — a column carrying no non-numeric value anywhere — with both `ci95_corrected` pairs moving in their last digits |
| class 9, arm G (the `report_by` stratum path) | every `by.cohort.b.*` key: `n_rows.value` `1.0→3.0`, `.method` `null→percentile_over_units`, `.ci95` `null→[3.0, 3.0]`, `.resample_draws` `0→2000`, and `mean_score.resample_draws` `0→1413` |

**Nothing moved outside the nine.** Volatile keys only: `run_id`, `started_at`, `wall_seconds`,
`provenance.git.commit`, `config.data.output_dir`.

**Scope, stated rather than implied.** This one config does not reach class 8 (`null_test`'s
`p_value`/`p_value_corrected`) or the `by` classes; those are covered by pin arm F's direct call
(`0.846307385229541 → 0.812375249500998`, and a recorded column getting no p-value at all) and by arm C
plus Fixture F respectively, each of which I mutation-tested below.

### Ruling 1's three mixtures, end to end, on a project outside the repo. All three behave as ruled.

| Mixture | `run.yaml` |
|---|---|
| Non-numeric for **every** unit (bool `flag` beside numeric `score`) | `flag` earns **no metric block**; the template's `n_cols` reads **`2.0`** and `n_flag` **`6.0`** — the column reaches `aggregate`'s table |
| A number for some units, `None` for others (3 of 6) | `score: {value: 1.0, n: {resolved: 6, **completed: 3**, ineligible: 0, failed: 0}, ci95: [-1.484…, 3.484…]}` — **the contributing count beside a condition-wide `resolved: 6`** |
| `str` beside a number | **Cannot occur.** Exit **4**, `status: failed`, every execution `E-STEP-RETURN-TYPE ContractError: units.parquet: column 'score' recorded both a float (unit 'p1') and a str (unit 'p4')` |

### Ruling 5's blind spot: the honest `n` is still published, which is the whole justification.

`limits.min_reported_n: 1`, one unit of six carrying a number: **no `W-STATS-COLUMN-THIN`** on stdout
(the accepted blind spot), and `run.yaml` publishes
`score: {value: 7.0, n: {resolved: 6, completed: 1, …}, ci95: null, method: null}`. The honest count and
the null interval are both there, so the downside really is bounded by the pre-warning status quo, as
Ruling 5 argued and batch 3 measured.

### Cross-batch interactions: no earlier guard is dead, and every one is pinned by a discriminating test

Nine mutations, each at the **call site** rather than in a helper body, each reverted by editing back and
the revert re-run:

| # | Mutation | Result |
|---|---|---|
| A | Undo the empty-record admission (`gathered.setdefault(key, {})` removed, `setdefault` chain restored inside the loop — the exact pre-task-4 shape) | **1 failed** — `test_a_unit_that_recorded_no_column_at_all_is_still_admitted_as_a_row` |
| B | `_repeats_disagree`'s `(is-numeric, value)` tuple → plain `v != first` | **1 failed** — `test_a_bool_in_one_repeat_and_a_float_in_another_disagrees_in_both_orders` |
| C | Delete the **paired** contrast guard's two `_is_numeric` clauses | **2 failed** — `…_no_longer_crashes` and `test_fixture_g_the_paired_contrast_guard_skips_a_str_column_instead_of_raising`, the second with the real `TypeError: unsupported operand type(s) for -: 'str' and 'str'` at `cli.py:1211` |
| D | `if "by" in recorded_columns` → `if "by" in step_summary` (the proxy task 9 removed) | **1 failed** — `test_a_non_numeric_recorded_by_column_warns_and_suppresses_the_strata` |
| E | Ruling 1's gate → the all-or-nothing `if not raw or not all(_is_numeric(v) for v in raw)` | **1 failed** — `test_ruling_1_a_column_numeric_for_some_units_and_none_for_others_keeps_a_block` (`KeyError: 'score'`) |
| F | The second empty-level gate → `if True:` | **1 failed** — `test_fixture_h_the_all_non_numeric_level_is_absent_the_numeric_one_present` |
| G | Delete the **unpaired** arm's `of_col`/`against_col` guard | **1 failed** — `test_fixture_g_the_unpaired_contrast_guard_narrows_of_col_so_n_of_matches_the_vector` |
| H | `W-STATS-COLUMN-THIN`'s emit condition → `if False:` | **1 failed** — `test_a_thin_recorded_column_warns_column_thin_naming_the_column_and_the_count` |
| I | `_across_repeats`'s disagreement return → `values[0]` | **2 failed** — including `test_fixture_e_a_disagreeing_collided_column_still_refuses`, the collision consequence mutation 4 was written for |
| J | `repeats_disagreeing` → `return {}` | **6 failed** across both files, including both Fixture D arms and the two-columns-warn-twice test |
| K | The contributing count → `{**counts}` (condition-wide `completed`) | **8 failed**, arm B among them |

**No guard added in an earlier batch is dead, and no comment written in batch 2 or 3 is false of the
shipped code.** Three claim-shaped comments were checked *by making the thing happen* rather than by
reading:

- The contrast guard's *"an all-dropped metric publishes `n_paired: 0` and `ci95: null`, a shape a reader
  can already read."* Built the state end to end (condition 0 numeric on units 0–2, condition 1 on units
  3–5, so the numeric intersection is empty): `run.yaml` publishes
  `score: {delta: null, method: null, n_paired: 0, ci95: null}` at **exit 0** beside three healthy
  derived contrasts. **True.**
- The `by` widening's *"`by` in `step_summary` implies `by` in `recorded_columns`, because a DERIVED `by`
  is refused by `RESERVED_METRIC_NAMES`."* Read at `stats.py:34` and `stats.py:3256` — the refusal exists
  and raises `E-STEP-KEY-COLLISION`. **True.**
- `_repeats_disagree`'s *"Measured, both orders: `_across_repeats([True, 1.0])` and
  `_across_repeats([1.0, True])` both return `1.0`."* Ran both: `1.0 1.0`. And Fixture D's pair:
  `_across_repeats([None, None])` → `None` with no disagreement, `_across_repeats([None, True])` → `None`
  **with** disagreement — bit-identical cells, opposite answers. **True.**

### The guard pin: every arm moved only where authorized, and the three with no editor never moved

By `git log -L :<function>:<file> main..HEAD`, and for arm C by extracting both test bodies at `main` and
at `HEAD` and diffing them:

| Arm | Authorized editor | Commits that touched its body |
|---|---|---|
| A (`test_a_numeric_only_run_is_untouched_by_h5b_no_editor`) | **NONE** | `23b79a9` only (the capture) — **never edited** |
| B (`test_a_bool_only_column_widens_exactly_seven_moving_keys`) | task 4 | `23b79a9`, **`06fdd3d` (task 4)** |
| C (the two existing numeric-`by` tests) | **NONE** | **0 diff lines** in both bodies, `main` → `HEAD`. `git log -L` reports `b276704` for the second only because task 9 **appended** a new fixture block below it |
| D (the two narrowed-around refusals) | **NONE** | not edited |
| E (`test_the_correction_family_measurement_arm_e_no_editor_except_task_4`) | task 4 | `23b79a9`, **`06fdd3d` (task 4)** |
| F (`test_a_derived_metrics_permutation_p_value_widens…`) | task 4 | `23b79a9`, **`06fdd3d` (task 4)** |
| G (`test_arm_g_the_report_by_stratum_path_moves…`) | added by the batch 2 fix round | `a9b6340`; `29d0a0d` shows only because task 12 appended below it — arm G's body is unchanged |

**No pin was weakened, and no arm was edited by an unauthorized task.**

### The strict xfail conversion asserts strictly more (verified by diffing the bodies across batches)

At `252774b` the `xfail(strict=True)` body carried exactly two assertions:
`assert doc["run_dir"] is not None` and `assert (doc["run_dir"] / "run.yaml").exists()`. At HEAD the
converted test carries **those two byte-identical** plus `assert entry["n_paired"] == 3`. Decorator gone,
`reason=` moved into the docstring, name `…_crashes` → `…_no_longer_crashes`. **Strictly more**, and
mutation C above shows both halves still fail when the guard is removed.

### § Errors / § Warnings: one row per code, re-derived by grep over every emit site

| Code | Emit sites (grepped in `src/`) | Row |
|---|---|---|
| `W-STATS-REPEATS-DISAGREE` | **1** — `cli.py:2934` | minted, granularity *per (condition, step, recorded column)* — matches the loop, which iterates `repeats_disagreeing`'s columns (Ruling 6's fix holds) |
| `W-STATS-COLUMN-THIN` | **1** — `cli.py:3333` | minted, same granularity, and honest about the fully-covered-but-thin case (see Minor 3) |
| `W-STATS-STRATUM-SHADOWED` | **1** — `cli.py:3603` | reworded to be total over the three mixtures |
| `E-STEP-KEY-COLLISION` | **8** — 2 in `stats.py`, 6 in `artifacts.py` | unchanged, correctly: one site sees a wider input, no site is added, and the row is unqualified |
| `E-STEP-COLUMN-UNKNOWN` | **1** — `stats.py:3430` | unchanged, correctly |

### The filings

- **`OPEN — whether E-STEP-RETURN-TYPE should ever be forgiving`** — its own evidence reproduces exactly:
  at `ee8085e`, `grep -cE 'more forgiving|mixed column'` → **0**, control `grep -c 'E-STEP-RETURN-TYPE'`
  → **4**. Its read-side paragraph carries Major 2.
- **`OPEN — diff's uv.lock row prints two digests and never names the package` (Owner: H9)** —
  **reproduced from scratch rather than trusted.** Two runs of one config, the second after moving one
  pin in `uv.lock` and committing:
  ```
  code_hash          identical    sha256:5b32…
  input_manifest     identical    sha256:46ae…
  uv.lock            DIFFERS
    sha256:45cd… → sha256:2d84…
  parameters_hash    identical    sha256:275c…
  ```
  `pkg-a` appears **nowhere**, exit **0**. The filing is accurate and the owner is a surface (`reproduce`
  reads the environment back), not a schedule.
- **Every closed entry is struck, not deleted** — three `~~…~~` strikes, each with the date, the task,
  and what closed it; the `aggregate`-table row's attributes half is explicitly *not* re-struck. Verified
  against the branch diff: `spec-defects.md` is `296+/3-`, and the three deletions are the struck rows'
  own rewrites.
- **The consolidated RE-OWNED note** batch 5 flagged as "premature-by-one-merge" is **sound**: it dates
  itself to the merge and corrects five reasons *once*, in a new note, rather than editing five bodies —
  the same form the 2026-08-19 and 2026-08-21 re-ownings took, and the same convention every `CLAUDE.md`
  slice entry already uses. Its count of five is right (lines 1951, 8613, 8643, 8674, plus the
  spine-citing entry at 8572). Its stated **verification command** is not (Minor 2).

### § Executability: four rows, row 4 re-derived, nothing else moved

Extracted all six `| Figure | Count | Visible to `validate`? |` tables in the file programmatically and
compared them row by row: tables 2→3, 3→4 and **4→5 (H5b's)** are **identical on all six lines** —
header, separator and all four rows. The table stays **four rows**; **no fifth number is minted**; row 4
is `1` with a new derivation and its history stated as `1 → 0 → 1`; the earlier entry is appended to, not
edited (`92+/0-` on that file).

### The development record was not retro-edited

`git diff main...HEAD --numstat | awk '$2>0'` names only `CLAUDE.md`, `docs/reference.md`,
`spec-defects.md` (the live-list exception), the four `src/` and `tests/` files. `progress.md`
(234/0), the feasibility analysis (92/0) and the spine design (20/0) are **append-only**. The plan is
`175/0` — the sixteen ruling pointers were *inserted*, destroying nothing, which is the fix for batch 1's
structural Critical and is recorded as such.

### Both consistency passes over the four documents

**Mechanical**, written fresh for this pass: relative links and `#anchor` resolution across the four
documents, duplicate anchors, table row/header cell counts, empty rows, trailing whitespace, tabs and
invisible unicode — all with fenced blocks skipped. **Result: clean.** The three table hits it reported
are `\|` escaped inside cells (`reference.md:623`, `:1738`, `:3599`), false positives of the splitter,
each read by eye. **The sweep was proven able to fail**: appending a line with trailing whitespace and a
dead self-anchor to `reference.md` raised the count from 3 to 5, and the file was restored by copying a
pre-mutation copy back, not by `git checkout`. *The first run of this checker produced 21 false anchor
failures from a slugger that collapsed runs of whitespace to one dash* — GitHub emits `secrets--credentials`
for `Secrets & credentials` — which is the third time in two batches a throwaway checker had to be
debugged before it could be believed.

**Cross-document.** `cohort-pilot`'s intervals are **not narrowed**: every one of the 23 worked-example
literals (`0.581`/`0.488`/`0.661`, `0.607`/`0.517`/`0.683`, `0.412`/`0.347`/`0.477`, the deltas
`0.026`/`-0.007`/`0.059` and `-0.169`/`-0.213`/`-0.125`, `0.014`, the five hash prefixes, `228`, `240`)
has an **identical occurrence count** in `README.md`, `design-principles.md` and `reference.md` at `main`
and at `HEAD`. No config field is added, so § The one config file needs no change; no enum comment, no
version and no `Status` marker moves. The `reference.md` edits are five prose passages and two § Warnings
rows, each consistent with the others and with `CLAUDE.md`'s widened *Units are the inference base*
bullet.

### Readers of `aggregated`

`publishable report <run.yaml>` was run through the console script on a project carrying a **mixed** `by`
column. It renders the `by` metric row structurally (`value: 1.0`, `n: {…completed: 3…}`), which both
confirms `report.py`'s structural predicates work over the shape this slice newly produces **and** is the
measurement behind Major 3.

---

## Summary

| # | Grade | Finding | Route |
|---|---|---|---|
| 1 | **Major** | `W-STATS-CONTRAST-RESAMPLE-THIN` newly fires and is in none of the three "four things" enumerations | fix round: `CLAUDE.md` in place, feasibility **appended** |
| 2 | **Major** | `spec-defects.md:8694` states the all-or-nothing read rule *and* a reachable-`str` read case; the batch-1 fix round swept one of two files written by one commit | fix round: **delete** the false clause |
| 3 | **Major** | `report.py::_is_metric_entry`'s ground is false of a mixed `by` column, which keeps a full metric block | fix round: **delete** the parenthetical's second clause |
| 4 | Minor | arm G calls `1927` both "fourth" and "third" | fix now, gate named as editor |
| 5 | Minor | the RE-OWNED note's stated grep reaches 3 of the 5 entries it names (line-wrap) | fix in place |
| 6 | Minor | `W-STATS-COLUMN-THIN` prints once per column on a sub-floor roster | **file, do not fix** — owner unassigned with the reason |

**No Critical. Nothing in `src/` computes a wrong number, and the behaviour change is exactly the one the
slice enumerated — with one warning it did not.**
