# H5b batch 3 review — tasks 7, 8, 9, 10, 11

Branch `h5b-non-numeric-downstream`. Commits reviewed: `848835e` (task 7), `1e8cb51` (task 8),
`b276704` (task 9), `e613c11` (task 10), `1268c96` (task 11), `09954ea` (report), `3be2808` (in-batch
fix round).

**Verdicts.** Task 7 **FAIL** · task 8 **PASS** · task 9 **FAIL** · task 10 **PASS** · task 11 **PASS**.
Three Majors, three Minors, **no Critical**. Every Major is a **claim** defect — a comment, a normative
row, or a report grep — and **no shipped code is wrong**. The behaviour this batch built was verified
correct at every point I could reach it by running.

**Suite, run in the foreground after every mutation was reverted: 2926 passed, 1 skipped, 2 xfailed**
(190s). `uv run ruff check .` → all checks passed; `uv run ruff format --check .` → 93 files already
formatted; `uv run mypy` → no issues in 52 source files. `git status --short` empty.

**Delta reconciliation, independently re-derived.** Baseline 2920 passed / 3 xfailed. Task 7: the
converted xfail moves into `passed` (+1, xfailed 3 → 2) plus Fixture G's three arms (+3) = 2924. Task 9:
Fixture F's two tests (+2) = 2926. Task 10 renames one test and replaces its fixture, no net add. Tasks
8 and 11 are documents and records. **2926 / 2 xfailed reconciles exactly.**

---

## What I verified by BEHAVIOUR versus by READING

**By behaviour (ran it):** task 7's guard end to end in both states; task 7 mutations (i), (ii), (iii);
task 9 mutations (i) — in **both** assertion orders — and (ii); task 10's real-path collision, its
prescribed mutation's blindness, and its replacement mutation; the numeric, non-numeric **and mixed**
`by` column's full published block through a real `run`; `W-STATS-COLUMN-THIN`'s absence at a low floor;
the full suite five times.

**By reading (greps, indentation, call sites):** the `recorded_columns` scope walk; the
`by`-in-`step_summary`-implies-`by`-in-`recorded_columns` widening argument; all eight
`E-STEP-KEY-COLLISION` raise sites against the § Errors row; the `_attributed` docstring deletions; the
xfail conversion's byte-identity.

**My own mechanical consistency pass** over the four documents (links, `#anchor`s, duplicate anchors,
table column counts, trailing whitespace, tabs, invisible unicode, fenced blocks skipped) returned 21
hits, **all 21 my own slugger's `&` handling** (three hyphens where GitHub emits two). Real issues:
**zero** — zero dead file links, zero table-column mismatches, zero trailing whitespace, zero tabs, zero
invisible unicode. This is my measurement, not the report's claim repeated.

---

## Task 7's conversion of the strict xfail: NOTHING WAS WEAKENED

Every clause of the report's account checks out, and the pin is **strictly stronger**.

Mechanically, `git show "df37f2e:tests/test_cli.py"` against `HEAD`:

| Claim | Verified |
|---|---|
| `@pytest.mark.xfail(reason=…, strict=True)` removed | Yes |
| `reason=` prose rewritten into the docstring | Yes |
| Test body byte-identical | Yes — the `run_a_project(...)` call is unchanged context in the diff |
| **Both** original assertions byte-identical | Yes — `assert doc["run_dir"] is not None` and `assert (doc["run_dir"] / "run.yaml").exists()`, unmoved |
| Exactly **one** assertion added | Yes — three lines: the `yaml.safe_load`, the `entry` lookup, `assert entry["n_paired"] == 3` |
| Renamed `…_crashes` → `…_no_longer_crashes` | Yes |

**And the underlying fix proven by behaviour, which is what settles it.** Deleting both `_is_numeric`
clauses from the paired `col_keys`:

```
E  TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'   src/publishable/cli.py:1203
```

and inspecting the run directory that crash left behind:

```
results/run_2026-08-22T17-53-04Z_399bddc/
  conditions  config.yaml  environment  executions.jsonl  manifest  sweep.yaml
executions.jsonl: 10 lines          run.yaml: ABSENT
```

*Every execution paid for, the record lost*, observed as a fact about the filesystem. Guard restored:
`run.yaml` written, `vs_baseline…score.n_paired == 3`. The pin went from *did the run keep its record* to
*did the run keep its record **and** is the narrowing right*, and it fails on the first of those under
mutation. **No weakening, verified by behaviour rather than by reading the report's description of
itself.**

---

## Findings

### Major 1 (task 9) — two normative passages reworded in this batch are non-total over the three reachable mixtures Controller ruling 1's own amendment enumerates

The § Warnings row task 9 rewrote frames itself as **exhaustive**:

> Fired for a `by` column **whatever it holds**: one whose every value is a number keeps its own metric
> block beside the warning, and one no unit recorded a number for keeps none

and § Steps and artifacts' reserved-`by` paragraph now reads *"and its own metric block too **where every
unit recorded a number for it**."*

**The reachable middle case is in neither.** Measured end to end through a real `run`, a step recording
`by` as a number for 20 of 40 units and `None` for the rest (`{"pred": float(i), "by": (float(i) if i % 2
== 0 else None)}`, `report_by: [cohort]`):

```
MIXED KEYS: ['by', 'pred']
MIXED BY: {"value": 19.0, "basis": "units", "n": {"resolved": 40, "completed": 20, "ineligible": 0,
           "failed": 0}, "ci95": [13.462378863959492, 24.537621136040507], "method": "t_over_units",
           "correction": null, "repeat_spread": {"std": 0.0, "n": 5, "kind": "seed"}}
MIXED WARN: True
```

A full metric block, a real interval, and the warning. Neither passage describes it, and a reader taking
the row's own "whatever it holds" enumeration at face value concludes such a column keeps no block.

**Why this is a Major and not a wording nit.** Controller ruling 1's **amendment, in this slice's own
plan**, exists solely to enumerate these three mixtures, and says of batch 1: *"Batch 1 shipped an
all-or-nothing read sentence that this ruling rejects."* Its table names the middle row explicitly — *"A
number for some units, `None` for others → A block computed over the units that carried a number."* Task
9 shipped an all-or-nothing **write** sentence and an all-or-nothing normative row, in the same slice,
after the ruling that was written to stop it. The row is the stronger half; the § Steps sentence survives
a sufficient-condition reading and the row does not.

**The § Errors/§ Warnings rule this breaches** is not "one row per emit site" — the row correctly covers
the one emit site — but that a row's stated enumeration must be total over the states the code reaches.

*No code is wrong.* The behaviour above is exactly what Ruling 1 requires.

### Major 2 (task 7, fix round) — the guard comment's *corrected* ground is itself half false: `W-STATS-COLUMN-THIN` is conditional, and it is asserted as a standing disclosure

`3be2808` rewrote the guard's comment to replace a ground the report itself declared wrong. The
replacement ends:

> **No new code is minted**, and not on the ground that this path is unreachable — the live case above is
> reachable. The disclosure is the narrowed `n_paired` itself, beside the condition-side
> `W-STATS-COLUMN-THIN` **that the same column already earns.**

**Made to happen.** `W-STATS-COLUMN-THIN` fires only when a column's contributing count is below
`limits.min_reported_n` (`cli.py`'s `if contributing < column_floor`, guarded by
`isinstance(column_floor, (int, float))` — so an absent limit fires nothing at all). Driving the ragged-
`None` contrast fixture with `limits.min_reported_n: 1`:

```
LIMITS {'min_reported_n': 1, 'max_executions': 100} | n_paired 3 | COLUMN-THIN: False
```

Three of six units silently dropped from the contrast, and **no `W-STATS-COLUMN-THIN` anywhere**. The
"already earns" half of the ground does not hold.

**This is written down in the plan already.** Controller ruling 5's own cost-if-wrong: *"a project
declaring a floor of 1 gets no warning for a column one unit carries."* The comment asserts as a standing
disclosure the exact thing the ruling names as the case where it is absent.

**The conclusion survives; the ground does not.** *No new code should be minted* still holds on the
`n_paired` half alone, which is unconditional and always in the record. So this is a **comment** defect —
this repo's most-recorded habit — landed in the round whose stated purpose was correcting a wrong ground.
*If a comment says this is the disclosure, check the disclosure fires.*

### Major 3 (task 7, report) — the `blast_radius` grep claim is false at its own commit, and it is stated with maximum emphasis

Report: *"`grep -rn "blast_radius" --include="*.py" --include="*.md" .` returns **exactly one line** — the
renamed definition — so nothing else referenced the old name. **Grep reported, not a count asserted from
memory.**"*

Measured at `848835e`, the task 7 commit:

```
$ git grep -n "blast_radius" 848835e -- '*.py' '*.md'
task-b2-report.md:73   …test_ruling_1s_blast_radius_…_crashes…      ← OLD NAME
task-b2-report.md:227  …_crashes                                    ← OLD NAME
task-b2-review.md:67   …_crashes                                    ← OLD NAME
tests/test_cli.py:17816  (the renamed definition)
tests/test_cli.py:18045  (Fixture G's docstring, citing the renamed test)
```

**Five lines, three files** — and **two inside `tests/test_cli.py` alone**, so even the narrowest reading
of "exactly one line" is false in the one file the task edited. Three hits carry the **old** name.

**No action is owed on the state.** Those are development record, deliberately not retro-edited — which
is precisely the treatment **task 10 gave the identical situation in this same batch**, where it
enumerated the old collision-test-name hits and explained that a scoping and a spec are not retro-edited.
The batch knew how to answer this question correctly and answered it correctly once. **The claim is the
defect, not the state**, and it is the shape check 12 exists to catch: it hid in a claim about *other
files*, stated as measured.

### Minor 4 (task 9, report) — the "85 insertions, 0 deletions" figure, framed as mechanical, is wrong

Report: *"`git diff -- tests/test_cli.py` for `b276704` is **85 insertions, 0 deletions**, so the count is
mechanical rather than eyeballed."* Measured:

```
$ git show b276704 --numstat -- tests/test_cli.py
93      0       tests/test_cli.py
```

**The conclusion is correct** and I verified it independently rather than from the count: extracting both
arm C bodies at `df37f2e` and at `HEAD` and diffing them, the 58 lines are **byte-identical** (the only
differing line is the section-header comment I used as the awk boundary, which is Fixture F's new
header). Arm C untouched. Only the figure offered as proof is wrong.

### Minor 5 (task 10, report) — the old-collision-test-name enumeration miscounts and omits a file

Report: *"four development-record files — `H5b-SCOPING.md` **twice**, this slice's plan twice, and its
design once."* Measured at `df37f2e`, the state task 10 step 1's "grep the suite for the old name first"
would have seen:

```
task-4-brief.md:1   H5b-SCOPING.md:3   plan:2   design:1   tests/test_stats.py:1
```

`H5b-SCOPING.md` has **three** hits, not two, and **`task-4-brief.md` is a fifth file** the enumeration
omits. Substance unaffected — all are development record and correctly left alone. Task 10's *reasoning*
about this class is the best in the batch; only its arithmetic slipped.

### Minor 6 (task 9) — the `W-STATS-STRATUM-SHADOWED` grep could not have established the site list it is cited as establishing

Report and § Corrections 15 both say `grep -rn 'W-STATS-STRATUM-SHADOWED' src/publishable/*.py` returns
**two** lines: `cli.py`'s emit site and one `report.py` docstring. But at `df37f2e` the code was
**line-wrapped** inside `_is_strata_block`'s docstring —

```
    all when a recorded column of that name exists (`W-STATS-STRATUM-
    SHADOWED`: "no strata are reported for this step"), so the two shapes
```

— so that full-string grep **never matched that site**. § Corrections 15 found it by reading. Task 9's own
reflow puts the code on one line, so the grep now returns **three**:

```
cli.py:3596  report.py:91 (_is_metric_entry)  report.py:112 (_is_strata_block)
```

**No site was missed** — step 3b corrected both `report.py` docstrings, which is the substance and it is
right. But the enumeration rests on reading, not on the grep it cites, and the report presents the grep
as the establishing measurement. This is the repo's own *"a grep for one spelling"* trap in miniature:
enumerate by reading, then confirm with greps, and say which did the work.

---

## Note, not a finding — task 8's construction name

Task 8's second paragraph says *"`paired_percentile_over_units` draws over the intersection and recomputes
the derived metric on each draw"*, where the brief specified `paired_percentile_of_derived` ("draws over
`base_keys`"). I looked hard at this and it does **not** survive as a finding: the trailing clause
*"recomputes the derived metric on each draw"* scopes the sentence to the derived case, where it is true,
and the paragraph **immediately above** already tells the reader the recorded column *"narrows again — to
the units carrying a real number for that column."* No reader reaches a wrong conclusion about the
recorded-column pool. `reference.md` documents constructions by **method string** and
`paired_percentile_over_units` has its own construction-table row, so naming it is idiomatic and changes
no claim. Recorded only so the substitution is visible: `cli.py:1277-1280` calls
`paired_percentile_of_derived` with **`col_keys`** for the recorded-column arm while reporting
`method: paired_percentile_over_units`, so the method string does span both halves — the sentence's
scoping clause is what keeps it correct.

---

## Every mutation re-run

Counts are **read from the summary line**. The report's mutation counts are **point-in-time** — task 7's
against the 2924-passed state at `848835e`, tasks 9 and 10's against 2926 — and **every one reconciles
against the state at its own commit.** Given four prior miscounts in this slice family, stating this
explicitly: **no miscount in the mutation table.** My re-runs are at `HEAD` (2926), so my totals sit two
higher than task 7's rows by construction.

| Mutation | Report | My re-run at HEAD | Verdict |
|---|---|---|---|
| **T7 (i)** delete both `_is_numeric` clauses from paired `col_keys` | 2 failed / 2922 | **2 failed / 2924** — the converted xfail **and** Fixture G's paired arm. Raw `TypeError` on `NoneType` and on `str`, and the crashed run directory has `executions.jsonl` 10 lines and **no `run.yaml`** | **Confirmed**, and the strongest mutation in the batch |
| **T7 (ii)** delete them from unpaired `of_col`/`against_col` | 1 failed / 2923 | **1 failed** (targeted) — unpaired arm only, `TypeError: unsupported operand type(s) for +: 'float' and 'str'` at `stats.py:481`, paired arm green | **Confirmed**; the two-ended fixture is justified |
| **T7 (iii)** move the narrowing into `of_values`/`against_values` (§ Corrections 2) | 1 failed / 2923 | **1 failed** — `assert 5 == 3` at `n_of`, **while the interval still computes** | **Confirmed.** § Corrections 2 is genuinely pinned, not prose |
| **T9 (i)** point the gate back at `step_summary` | 1 failed / 2925 | **1 failed / 2925**. Structural assertion fails, and the failure output shows `step_block['by']` holding the **`cohort` strata**. I then **swapped the assertion order** and the stdout assertion fails too — `'W-STATS-STRATUM-SHADOWED' in '  warning W-ENV-UNLOCKED …'`. **Both halves fail independently**, as the report claims | **Confirmed by running both orders** |
| **T9 (ii)** widen the gate to drop a numeric `by` from `aggregated` | 3 failed / 2923 | **3 failed / 2923** — arm C's two tests **plus** `test_report.py::test_a_recorded_column_named_by_renders_as_a_real_metric_row`, the undisclosed third | **Confirmed**, including the third |
| **T10 prescribed** `_across_repeats` omits a disagreeing column's key | 6 failed / 2920, renamed test **passes** | **6 failed / 2920**, and the renamed test is **absent from the failure list**. Mechanism confirmed directly: `_repeats_disagree([True])` → `False`, so a disagreement mutation cannot reach a fixture whose single repeat agrees | **Blind, as predicted.** Six named failures all match |
| **T10 replacement** revert the empty-record admission (admit only units with ≥1 numeric value) | 11 failed / 2915, renamed test **fails** | **11 failed / 2915**, and `test_a_derived_key_colliding_with_a_non_numeric_recorded_column_is_refused` **FAILS**. All nine other named pins present | **Confirmed. The replacement genuinely discriminates** where the prescribed one could not |

Every mutation was reverted **by editing the file back** (or restoring a pre-mutation copy), verified by
`diff` against that copy **and by re-running**, with `__pycache__` cleared each time. `git status --short`
is empty and the full suite is back at 2926 / 1 / 2.

**Two claims I found unpinned and did not raise as findings.** The reworded warning **message text** is
asserted by nothing (only the code is), which matches the repo's convention and the old text was equally
unasserted — the report grepped this and reported 0. And the unpaired guard's **cluster-list** consumer
(`[of_clusters[k] for k in of_col]`) is separated from the `of_values` placement only by `n_of` in the
shipped fixture; Fixture G declares no cluster **deliberately**, and its docstring says why (a length
mismatch would fail the mutant for the wrong reason). `n_of` separates the two placements, which is what
§ Corrections 2 needed. Correct call.

---

## Check-by-check

**§ Errors, `E-STEP-KEY-COLLISION` — re-derived by grep, row ASSERTED correctly.**
`grep -rn 'code="E-STEP-KEY-COLLISION"' src/publishable/*.py` → **8** raise sites, read in full:
`stats.py:3262` (a derived key taking the reserved metric name `by`), `stats.py:3270` (a derived key
against a recorded column), and `artifacts.py` × 6 — a recorded column named `unit`, one named
`measurement`, and one shadowing a declared attribute, **each twice**, once in `io.record`'s
`measurement=` branch and once in its unmeasured branch. The § Errors row's five collision phrases map
one-to-one onto all eight, and the row's *"a derived key against a recorded column"* is unqualified so
the widened input needs no edit. The row also already carries the *re-reported as
`W-STATS-AGGREGATE-FAILED` rather than raised* clause. **The row is not narrower than its code; asserting
rather than editing was right.**

**§ Warnings, `W-STATS-STRATUM-SHADOWED` — one emit site (`cli.py:3596`), row covers it; but see Major 1
for the enumeration and Minor 6 for the grep.**

**Task 9's arbitration answers from the recorded-column SET, structurally — not from the name.** Verified
three ways. (a) The gate is `if "by" in recorded_columns`, and `recorded_columns = {col for cols in
collapsed.values() for col in cols}` sits **unconditionally at the same 20-space indent** in the same
`for step_name in sorted(recording_steps):` body (line 2919 is the only enclosing statement at shallower
indent between 2900 and 3600) — in scope, not stale, no reassignment between. (b) The widening argument
holds by reading: a **derived** `by` raises at `stats.py:3256` (`RESERVED_METRIC_NAMES`), and the
containment retry at `cli.py:3164` passes **no `derived=` argument at all**, so the only route into
`step_summary` is the column loop over the same `collapsed`. (c) **A recorded column legitimately named
`by` keeps everything**, measured through a real `run` with three seed repeats:

```
NUMERIC BY: {"value": 39.0, "basis": "units", "n": {…"completed": 40…},
             "ci95": [31.522424170049817, 46.47757582995018], "method": "t_over_units",
             "correction": null, "repeat_spread": {"std": 0.0, "n": 3, "kind": "seed"}}
```

**Value, interval, method and `repeat_spread` all survive**, `cohort` is not a key inside it, and the
warning fires. Non-numeric: no `by` key in the step block at all, warning fires. And a real `report_by`
stratum is still published under `by` and still excluded from the metric reading — pinned structurally by
`report.py`'s `_is_metric_entry`/`_is_strata_block` and by
`test_h8c_arm_a_the_records_field_level_shape`'s `aggregated_step["by"]["cohort"]` walk, green throughout.
**This is the structural answer, not the string.**

**Task 9 step 3b.** Both `report.py` docstring claims checked, and the `_is_strata_block` one is
**verified false pre-task-9 by behaviour**: under mutation T9 (i) the failure output showed a non-numeric
`by` column's run publishing the `cohort` **strata** under `by` while `units.parquet` carried the measured
column. So *"`cli.py` does not write this block at all when a recorded column of that name exists"* was
false and is now true, and *"numeric or not"* is the correct narrowing. `_is_metric_entry`'s narrowing is
correct too. **No code in `report.py` changed** — confirmed in the diff.

**Task 9 step 4.** Both `_attributed` grounds **deleted verbatim, not rewritten**, checked in
`git show b276704`. The true reasons (the unit key surviving a bootstrap draw; an attribute merging into
**rows** and never into `collapsed`) are untouched and nothing was invented in their place. Independently
confirmed that the deleted ground was false: `units.py:33` is `RESERVED_COLUMNS = ("unit",
"measurement", "by")`, read at **three** sites (246, 279, 465).

**Task 10 "fires for free" — verified on the REAL path, not a hand-built mapping.**

```
collapse_repeats([_result("", [{"unit": f"u{i}", "r": True} for i in range(5)])], "analyze", 0)
  → {'u0': {'r': True}, 'u1': {'r': True}, 'u2': {'r': True}, 'u3': {'r': True}, 'u4': {'r': True}}
summarize_step(that, {"completed": 5}, derived={"r": 1.0}, seed=7)
  → ContractError E-STEP-KEY-COLLISION: 'r' collides with a recorded column of the same name
summarize_step(that, {"completed": 5}, seed=7)                → {}      (the control)
```

The collapse produces exactly the mapping the old test hand-built, the refusal fires, **no new code**.
The renamed test's assertion is unchanged, its fixture is a real `collapse_repeats` output, and it is
distinct from Fixture E (which carries a numeric column beside the colliding one). Live overruling 1
respected — no task 4 pin re-added.

**Task 11.** § Reporting strata genuinely carried no such sentence before the edit (checked). The struck
entry quotes its own live text before striking. Its blind mutation's cited replacement is real: task
4's mutation (iii) result is at `task-b2-report.md:84` (*"Replace `cli.py`'s second empty-level gate with
`if True:` → Fixture H's absent-level assertion FAILS (`b` reappears in `by`)"*) and
`test_fixture_h_the_all_non_numeric_level_is_absent_the_numeric_one_present` exists at
`tests/test_cli.py:17708`. **Not re-running a recorded mutation was the right call.** The correction to
the S4d filing's own reasoning is sound: both the old and new accounts are true statements, but the
operative mechanism is the collapse, and saying so is the useful correction.

**Guard pins.** No arm was edited. `git show <c> --unified=0 -- tests/` per commit shows task 7 touching
only the converted xfail and its own new section, task 9 appending after arm C's second test, task 10
touching only the renamed test. Arm C's two bodies are **byte-identical** across `df37f2e..HEAD` (Minor 4
records that the report's supporting figure is wrong while the conclusion is right). Arms with no
authorized editor (A, C, D) passed on every one of my five full-suite runs. **Arm F** — flagged in the
report's fix round as omitted from an earlier draft — is real and its prediction is now genuinely run
rather than reasoned: task 7's narrowing lands in `of_col`/`against_col`, which is what
`permutation_over_contrast`'s `[of_clusters[k] for k in of_col]` reads, and arm F's literals did not move.
**No arm moved without an authorized editor.**

**Undisclosed drops: none found.** Each brief's steps were walked against the diff. Task 7 step 4's *"a
comment at the guard and nowhere else"* is honoured — the unpaired arm carries no restatement. Task 7
step 1's `_is_numeric` sorts first among the lowercase names in the import block, which is what ruff
enforces and it passes. The one substantive deviation from a brief — task 7 step 5's *"publishes no
entry"* — is disclosed, correct, and now split into two tests. The second deviation (task 8's
construction name) is recorded above as a note.

---

## Adjudication of the report's own four concerns

1. **Two tests where Fixture F names one — ACCEPTED as disclosed, no finding.**
   `test_a_non_numeric_by_column_still_reaches_the_unit_table` is a genuine second claim: the CLI-layer
   fact that suppression is not a **drop** is not what `test_artifacts.py`'s must-stay-green control
   proves (that one never reaches `collapse_repeats`). A widening, disclosed loudly rather than folded
   in, which is the right handling.
2. **The warning-message text change — ACCEPTED, no finding.** Required by Ruling 7 (*delete the false
   premise, do not rewrite it*), and the clause **was** deleted rather than conditioned. Nothing asserted
   the old text and I confirmed the only remaining hits repo-wide are the report quoting itself. The
   scope widening is real and correctly disclosed. Note that the row it forced is Major 1.
3. **Fixture G's `str` end-to-end arm is a production control — ACCEPTED, no finding, and the honesty
   matters.** It passes before the guard as well as after and says so in its own docstring. Crucially the
   controller's actual requirement — a `run.yaml`-exists assertion on the **file** — is met by the
   converted xfail, which I confirmed **does** fail with no `run.yaml` when the guard is removed. The
   labelling prevents the weaker arm being mistaken for the proof.
4. **Decision 7's ground wrong for the reachable ragged-`None` case — the diagnosis is RIGHT and the new
   ground is HALF WRONG.** The report is correct that *unreachable from a validated config* is true of the
   `str` case and false of the ragged-`None` case, and correct that a note would not have been enough — a
   new ground was owed and was written. But the new ground's second clause is Major 2. **The conclusion
   (mint no code) stands on the `n_paired` clause alone**, which is unconditional; the residual the report
   routes to the whole-branch reviewer — whether the contrast side wants a disclosure of its own — is a
   fair `statistics`-surface question and correctly not task 7's.

## Adjudication of the three disagreements the report claims

All three are real. (1) **Task 7 step 5's "publishes no entry" is false of the code** — Fixture G's paired
arm asserts and passes `n_paired: 0`, `ci95: None`, `delta: None`, `method: None`, which is Decision 7's
own stated shape, so the brief is the outlier and asserting the measured shape rather than minting an
unchartered skip branch was right. (2) **Task 10's prescribed mutation is blind** — confirmed by running
and by the mechanism (`_repeats_disagree([True])` is `False`). (3) **The S4d filing names the wrong
operative mechanism** — sustained.

---

## What tasks 8, 10 and 11 got right, since a PASS should say why

Task 8's claim was checked against `paired_keys` and the paired `col_keys` **before** the sentence was
written, and the sentence describes the code (including task 7's sharpening — a recorded column's count
is now the units carrying a **real number**, not merely the key). Task 10's fixture-made-real is the model
form of this repo's *make the seam reachable rather than re-describe it*, its § Errors row assertion is
correct against all eight sites, its struck entry names the worst of the three false claims correctly, and
it **predicted its own mutation's blindness in advance and named a replacement that works**. Task 11
checked the section for the sentence before adding one, quoted the entry before striking it, corrected the
entry's own reasoning, and declined to re-run a recorded mutation for the stated reason.

## Required before merge

Majors 1 and 2 are both **claim** repairs with no code change: make the § Warnings row's enumeration total
over Ruling 1's three mixtures (and repair § Steps and artifacts' *"where every unit recorded a number"*
alongside it), and correct the guard comment's `W-STATS-COLUMN-THIN` clause to say the disclosure is
conditional on `limits.min_reported_n`. Major 3 and the three Minors are report corrections. **Nothing in
`src/` needs to move.**
