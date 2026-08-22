# H5b batch 3 — tasks 7, 8, 9, 10, 11

Branch `h5b-non-numeric-downstream`. Baseline read before anything moved: **2920 passed, 1 skipped,
3 xfailed**. Final: **2926 passed, 1 skipped, 2 xfailed**.

| Task | Commit | What it is |
|---|---|---|
| 7 | `848835e` | The contrast guard at the subtraction, and the strict xfail converted |
| 8 | `1e8cb51` | § Statistical reporting states which units enter the pairing intersection |
| 9 | `b276704` | The `by` arbitration answers from the recorded columns; `_attributed` loses two false grounds |
| 10 | `e613c11` | The derived-key collision driven from the collapse's own output |
| 11 | `1268c96` | The empty-level gate's rule stated, its filing struck |

**Delta arithmetic, stated because a dropped xfail reads as a miscount.** 2920 + 4 (task 7: the
converted xfail moves from `xfailed` into `passed`, plus Fixture G's three arms) = 2924, and the
xfail count goes 3 → 2. + 2 (task 9: Fixture F's two arms) = 2926. Task 8 and task 11 are documents
and records only, no test delta. Task 10 renames one test and replaces its fixture: no net add.
2926 passed, 2 xfailed reconciles exactly.

---

## Task 7 — the guard, and what happened to the strict xfail

**The xfail was converted, not deleted and not weakened.** What changed:

- the `@pytest.mark.xfail(reason=…, strict=True)` decorator was **removed**;
- the `reason=` prose was **rewritten into the docstring** — what it disclosed, that task 7 closed
  it, and what the assertions now pin;
- the test body and **both** of its original assertions (`doc["run_dir"] is not None`,
  `(run_dir / "run.yaml").exists()`) are **byte-identical**;
- **one assertion was ADDED**: `vs_baseline…score.n_paired == 3`, the narrowed count over the three
  units that carried a number;
- it was **renamed** `…_crashes` → `…_no_longer_crashes`, because the old name describes behaviour
  that no longer exists. `grep -rn "blast_radius" --include="*.py" --include="*.md" .` returns
  exactly one line — the renamed definition — so nothing else referenced the old name. Grep reported,
  not a count asserted from memory.

**Why that is not a weakened pin.** A weakened pin asserts less. This one asserts strictly more: it
went from *did the run keep its record* to *did the run keep its record AND is the narrowing right*.
The device worked as designed — the moment the guard landed the strict xfail became a strict XPASS
and the suite went red, which is exactly the signal it was built to produce.

### The end-to-end evidence: the `TypeError` is gone and a `run.yaml` is written

Through the **installed console script** (`uv run --project <repo> publishable run`) on a project
scaffolded by `publishable new` + `generate experiment`, outside this repo, committed clean, six
units, `score` numeric for three and `None` for three, two conditions:

| State | Exit | Run directory | `run.yaml` | `vs_baseline…score` |
|---|---|---|---|---|
| guard removed (pre-task-7) | `1`, raw traceback `TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'` at `cli.py`'s subtraction | complete, `executions.jsonl` **10 lines** | **absent** | — |
| guard in place | `0` | complete | **written** | `n_paired: 3`, `delta: 0.0`, `method: paired_t_over_units` |

That is *every execution paid for, the record lost* observed as a fact about the file, then closed.
The guard was also proven by direct call: `_comparison_step_blocks` over a `str` column raised the
measured `TypeError` before, and returns after.

### A disagreement between the brief and the code — step 5's "publishes no entry"

Task 7 step 5 says the direct call must publish **no entry** for the non-numeric key. **Measured, it
publishes an entry** with `n_paired: 0`, `ci95: null`, `delta: null`, `method: null` —
`metric_block[metric_key] = {...}` in the paired recorded-column branch is unconditional, and an
empty `col_keys` gives `mean_of([])` and `paired_t_over_units([])`. That is Decision 7's **own**
stated shape (*"an all-dropped metric publishes `n_paired: 0` and `ci95: null`, which is the shape a
reader can already read"*), so the code and the design agree and the brief's sentence is the outlier.
Asserted as measured rather than made true by an unchartered skip branch. **"No entry" is true of
the end-to-end arm** — a wholly non-numeric column never enters `aggregated`, so it never becomes a
`metric_key` — and the two claims are now two separate tests.

Also verified while there: the `Member` built on that path takes empty `diffs` without raising, so
the fix does not trade a `TypeError` for a `ValueError` outside every `try`.

### § Corrections 2 verified against the code before building on it

`n_of` is `len(of_col)`, `n_against` is `len(against_col)`, `of_clusters`/`against_clusters` are
built by keying off `of_col`/`against_col`, and `permutation_over_contrast` reads
`[of_clusters[k] for k in of_col]`. Read at `_comparison_step_blocks`, all four confirmed. The
filter went into `of_col`/`against_col`.

### Fixture G's unpaired arm is RAGGED, and that is deliberate

With every cell a `str` the narrowed vectors would be empty, no interval would compute, and
mutation (iii) would have nothing observable to catch — it is specified as *`n_of` fails while the
interval still computes*. Three numeric and two `str` cells per side give `n_of`/`n_against` of `3`
against a wide `5`. No cluster is declared, so the mutant cannot fail on a length mismatch in
`[of_clusters[k] for k in of_col]` instead.

### Mutations — full unfiltered suite, counts READ from the summary line

| Mutation | Read | Which tests, and the property-preserving arm |
|---|---|---|
| (i) delete both `_is_numeric` clauses from the paired `col_keys` | **2 failed**, 2922 passed, 2 xfailed | Fixture G's paired direct-call arm (measured `TypeError`) **and** the converted xfail (the ragged real run). Property-preserving arm below leaves both green |
| (ii) delete them from the unpaired `of_col`/`against_col` | **1 failed**, 2923 passed | Fixture G's unpaired arm only — `TypeError: unsupported operand type(s) for +: 'float' and 'str'` in `mean_of`. The paired arm is untouched, which is why this fixture has both ends |
| (iii) move the unpaired narrowing into `of_values`/`against_values` (§ Corrections 2) | **1 failed**, 2923 passed | Fixture G's unpaired arm, failing on **`assert 5 == 3`** at `n_of` while the interval still computes — the count and the vector disagreeing, which is the whole correction |
| property-PRESERVING, two arms in one run: swap the order of the two paired `_is_numeric` clauses, **and** add the filter *redundantly* to `of_values`/`against_values` while keeping it in `of_col` | **0 failed**, 2924 passed | Confirms the fixture pins the behaviour rather than the code's shape, and specifically that (iii) failed because of the **removal from `of_col`**, not the addition to `of_values` |

Every mutation reverted by **editing the file back**, `__pycache__` cleared, and each revert verified
by `diff` against a pre-mutation copy **and** by re-running. One revert needed a second `ruff format`
pass — removing the guard let the formatter collapse two membership lines, and re-adding it did not
re-split them; caught by the `diff`, not by `git status`.

**No § Errors or § Warnings row for task 7.** Decision 7: no code is minted, the path is unreachable
from a validated config, and a row that can never fire misleads. Nothing was added.

---

## Task 8 — `n_paired` and the pairing intersection

**Step 2 first, as instructed.** `paired_keys` read: `keys = set(of) & set(against)`, narrowed by
`allowed` (the `within` stratum), sorted. **No column awareness at all.** The paired recorded-column
arm's `col_keys` narrows by column membership — and, **after task 7, also by numeric-ness**. So the
asymmetry the sentence describes is real: a derived metric's `n_paired` is `len(base_keys)`, a
recorded column's is `len(col_keys)`. The code and the sentence agree; **no disagreement to report
here**, and the claim was checked by reading both, not by trusting the brief.

Task 7 sharpens the sentence beyond what the brief anticipated: a recorded column's count is now the
units carrying a **real number** for it, not merely those carrying the key. The paragraph says
"carrying a real number for *that* column" for that reason.

§ Statistical reporting gained two paragraphs beside the existing **`n_paired` is the intersection**
one: the consequence (derived can exceed, recorded cannot, and both are right), and why it is honest
(`paired_percentile_over_units` draws over the intersection and recomputes, so narrowing the count
without narrowing the pool would put a count beside an interval computed over a different set).

**Consistency passes.** Mechanical, written fresh as a script: every relative link and `#anchor` in
the four documents resolves, no duplicate anchors, no trailing whitespace, no tab, no invisible
unicode, every table row matches its header's column count. Fenced blocks skipped. Three
"table column" hits on the first run were my slugger and counter being wrong, not the documents:
`&` in a heading gives GitHub a **double** hyphen (`secrets--credentials`) and the three flagged
rows carry escaped `\|` inside inline code. Both were fixed in the checker and the pass then returns
**0 issues** — proved able to fail by the first run's own hits.

**Cross-document, declared vs. derived.** `n_paired` is derived, so grepped for it as a settable
input: it appears in `docs/reference.md` only, in `run.yaml` output examples and prose about the
record (`n_paired: 412`, `330` twice, and one prose `n_paired: 0`), plus § Warnings and the
construction table. **It appears in no config example and in none of the other three documents.** No
worked-example value, enum comment, version or prevented-mistake is touched — the edit adds no field.

**Mutation: named blind, a document has no behaviour.** Replacement, as the brief specifies: task 1's
arm E, which pins the moved derived `n_paired` and the unmoved recorded-column one in the same
assertion block.

---

## Task 9 — the `by` arbitration

### The three required greps, reported rather than repeated

1. `grep -rn 'W-STATS-STRATUM-SHADOWED' src/publishable/*.py` → **two lines**: `cli.py`'s `warn`
   call (the one emit site) and a **docstring** in `report.py` (`_is_metric_entry`). § Corrections 15
   confirmed exactly.
2. `grep -rn '"by": ' tests/*.py` → the design's claim *"no test in the suite records a non-numeric
   `by`"* is **false**, as § Corrections 1 says. `tests/test_artifacts.py` records
   `{"by": "north", "score": 10}` twice (r1/r2) in
   `test_a_measured_by_column_survives_the_collapse_into_units_parquet`, and `{"by": 2.0, …}` in its
   numeric sibling. Everything in `tests/test_cli.py` is a `sweep.groups` entry or a
   `measurements` declaration **except** `_RECORDS_A_BY_COLUMN_STEP`'s `{"pred": float(i), "by":
   float(i) * 2.0}` — the numeric arm. `tests/test_report.py` records the same numeric shape. **The
   narrowed claim is true: no test in `tests/test_cli.py` records a non-numeric `by` column**, so
   Fixture F's end-to-end arm existed nowhere. The artifacts test never reaches `collapse_repeats`
   and stayed green throughout (full suite, every run).
3. `grep -n RESERVED_COLUMNS src/publishable/units.py` → `RESERVED_COLUMNS = ("unit",
   "measurement", "by")`, read at three call sites (two in the declaration checks, one at roster
   resolution). **So `_attributed`'s ground *"nothing refuses an attribute named `unit`"* is false**,
   quoted before being called false.

### Step 1: the gate, and reading both branches rather than asserting the widening

`recorded_columns = {col for cols in collapsed.values() for col in cols}` is assigned
**unconditionally at the loop-body level** of `for step_name in sorted(recording_steps):`, at the
same indent as the gate and above it, and is already read twice in that body. Verified by indentation
and by walking every enclosing compound statement — it is in scope.

**The widening is only a widening, read rather than asserted:** `by` in `step_summary` implies `by`
in `recorded_columns`, because (a) a **derived** `by` is refused inside `summarize_step` by
`RESERVED_METRIC_NAMES = frozenset({"by"})`, and (b) the `except ContractError` containment retry
calls `summarize_step` with **no `derived=` argument at all** — read at the retry's call site. So the
only route into `step_summary` is the column loop over the same `collapsed` that `recorded_columns`
is built from.

This is **not** the reserved-NAME-for-a-structural-fact fault. There the question was *is this entry
a stratum?* and a name was given as the answer. Here the question **is** whether a column of that
name was recorded, so the recorded-column set is that question's own answer; `step_summary` was the
proxy, and Fixture F is what the proxy could not see.

### The message and the two § Warnings/§ Steps passages — every emit site checked

The gate move is one expression. Two claims had to move with it, both of which were **false of a
non-numeric `by` column**:

- **The warning's own message** said the column *"keeps its value but gets no contrast delta"*. A
  non-numeric column keeps no metric block, so that clause is the Ruling 7 shape. The clause was
  **deleted**, not rewritten around a condition, and replaced by the two consequences that hold in
  both cases: *"gets no contrast delta and no seat in the correction family, and no strata are
  reported for this step"* — wording lifted from `reference.md` § Steps and artifacts, which already
  said exactly that.
- **§ Warnings core reports' `W-STATS-STRATUM-SHADOWED` row**, located **by its code**, not by
  position. **ONE row, ONE emit site, two conditions**, and the row now says so: it fires for a `by`
  column whatever it holds, one whose every value is a number keeping its own metric block beside
  the warning and one no unit recorded a number for keeping none. `grep -rn` for the code returns two
  lines and the second is `report.py`'s docstring — not an emit site, but a claim this slice moves,
  handled in step 3b. No other row moved.
- **§ Steps and artifacts' reserved-`by` paragraph** claimed *"the column keeps its recorded
  value"*, unqualified. **Three readings reported:** the row (now covers both), the paragraph (was
  true of the numeric case only), the code (numeric keeps a block, non-numeric does not). The
  paragraph now says the column keeps its recorded value **in `units.parquet`**, and its own metric
  block too **where every unit recorded a number for it**.

`grep -rn "keeps its value but gets no contrast delta" .` → **zero** hits after the edit; the sweep
covered `src/`, `tests/`, `docs/` and this file's siblings, filtering the **file list** and never the
output.

### Step 3b — `report.py`, narrowed, no code changed

`_is_strata_block`'s *"`cli.py` does not write this block at all when a recorded column of that name
exists"* was **false today for a non-numeric `by`** and **true after step 1**; it now says *"numeric
or not"*. `_is_metric_entry`'s *"keeps its value … as a real metric entry"* was true of the numeric
case only; it now names that case and adds that a non-numeric one keeps no metric block, which is
why a structural test reads both shapes. **No code in `report.py` changed** — both predicates are
the sibling that already got this right.

### Step 4 — the two grounds DELETED, not rewritten

`_attributed`'s docstring lost, verbatim: *"— not reachable while every roster attribute arrives from
`csv.DictReader` as a string, and the reason not to depend on that staying true"* and *"because
nothing refuses an attribute *named* `unit` (`units.py` reserves `key`, `paths` and `attributes`, the
fields of `Unit` itself), and"*. The true reasons stay untouched: the unit key column must survive a
bootstrap draw that duplicates units, and an attribute is merged into **rows** and never into
`collapsed`. Nothing was invented in their place. Checkable in `git diff` for `b276704`.

### Mutations — full unfiltered suite, counts READ

| Mutation | Read | Which tests |
|---|---|---|
| (i) point the gate back at `step_summary` | **1 failed**, 2925 passed | `test_a_non_numeric_recorded_by_column_warns_and_suppresses_the_strata`. **Both its assertions were measured to fail, separately**: pytest short-circuits, so the test was run once in each assertion order. With the stdout assertion first it fails on the missing warning; with the structural one first it fails on `assert 'by' not in step_block` — and the failure output shows `step_block['by']` holding the **`cohort` strata** while `units.parquet` holds a measured `by` column, which is the defect itself. The assertion order was then left structural-first, and the docstring records why |
| (ii) widen the gate to also drop `by` from `step_summary` (numeric case) | **3 failed**, 2923 passed | Pin arm C's **both** tests (`…keeps_its_metric_and_warns`, `…warns_even_with_no_report_by_declared`), plus an **undisclosed third**: `tests/test_report.py::test_a_recorded_column_named_by_renders_as_a_real_metric_row`, arm C's report-side sibling, which the brief did not name. Reported as a side effect, not a weakness |
| Named **blind in advance**: the `_attributed` deletion and the two `report.py` narrowings | — | A docstring has no behaviour. Replacement as the brief states: the B3 review's *were the grounds deleted rather than rewritten?* check against `git diff`. **Pin arm C's two bodies have zero lines changed** — `git diff -- tests/test_cli.py` for `b276704` is **85 insertions, 0 deletions**, so the count is mechanical rather than eyeballed |

**End to end through the console script**, same outside-the-repo project, step recording
`{"pred": float(i), "by": "lvl%d" % (i % 2)}` with `attributes: [cohort]` and `report_by: [cohort]`:
`W-STATS-STRATUM-SHADOWED` fires once per condition (two conditions, two warnings), `run.yaml`
carries **no** `by:` key anywhere under `aggregated` (grep count `0`), `pred` publishes normally,
exit `0`.

---

## Task 10 — the derived-key collision

### Does the refusal really fire for free? Verified by RUNNING, not by reading

```
collapse_repeats([_result("", [{"unit": f"u{i}", "r": True} for i in range(5)])], "analyze", 0)
  → {'u0': {'r': True}, …, 'u4': {'r': True}}        # exactly the fixture the test hand-built
summarize_step(that, {"completed": 5}, derived={"r": 1.0}, seed=7)
  → ContractError E-STEP-KEY-COLLISION: 'r' collides with a recorded column of the same name
summarize_step(that, {"completed": 5}, seed=7)       # the control
  → {}                                              # the column earns no block, as ruled
```

**Yes — no new code.** The check is `set(derived) & set(columns)` with `columns` built from
`collapsed`; task 4's admission of the record is the whole fix.

### Step 1 — the test made real, renamed, and NOT a duplicate

`test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused` →
`test_a_derived_key_colliding_with_a_non_numeric_recorded_column_is_refused`. Its fixture is now the
output of a real `collapse_repeats` call; its assertion is unchanged; the word *dropped* is gone from
the name and from the docstring (nothing is dropped after task 4).

**Old-name grep, reported:** `grep -rn` for the old name returns `tests/test_stats.py` (the
definition, now renamed) plus **four development-record files** — `H5b-SCOPING.md` twice, this
slice's plan twice, and its design once. Those keep the old name **deliberately**: a scoping records
what was measured on its date and a spec what was decided when written, and neither is retro-edited.

**It is distinct from task 4's Fixture E, not a duplicate of it.** Fixture E's first arm carries a
numeric `score` **beside** `r`. This fixture carries **no numeric column at all** — the shape the
collapse used to drop wholesale (`{}`), which is precisely why this test was unreachable in the first
place, and which is also Ruling 8's empty-record admission. Live overruling 1 says tasks 10 and 11
must not re-add task 4's pins, and this does not.

### Step 2 — the § Errors row ASSERTED, and every emit site checked

`grep -rn 'E-STEP-KEY-COLLISION' src/publishable/*.py` → **eight raise sites** plus three prose
mentions. Read: `stats.py` twice — the reserved metric name `by`, and the derived-vs-recorded-column
collision; `artifacts.py` six times — a recorded column named `unit`, one named `measurement`, and
one shadowing a declared attribute, **each appearing twice**, once in `io.record`'s `measurement=`
branch and once in its unmeasured branch. The § Errors row's five collision phrases (*a derived key
against a recorded column, a derived key taking the reserved metric name `by`, a recorded column
against a unit attribute, a recorded column named `unit`, or one named `measurement`*) cover all
eight. The row's *"a derived key against a recorded column"* is unqualified, so the widened input
needs no row change, and the row already carries the *re-reported as `W-STATS-AGGREGATE-FAILED`
rather than raised* clause. **The row is not narrower than its code. Nothing was edited.**

### Step 3 — recorded as found-and-closed, in the struck form

A new struck section at the end of `spec-defects.md`, naming the three shipped claims that promised
the refusal (`summarize_step`'s docstring qualifier, the § Errors row, and the green test's own
docstring), and saying that the **green test naming the hazard verbatim is the worst of the three**,
because it is the one a reader greps for and stops looking. It names what it closes upstream — one
corner of the H4b-2 Critical, where a derived key colliding with a recorded column's name published
an *unclustered* contrast interval because the refusal could not see the column — and claims no more:
the numeric case was already refused and is pin arm D(ii).

### Mutations — and the prescribed one is BLIND for this test, named in advance

| Mutation | Read | Which tests |
|---|---|---|
| Prescribed: `_across_repeats` omits a disagreeing column's key | **6 failed**, 2920 passed | `test_fixture_e_a_disagreeing_collided_column_still_refuses` (task 4's arm — the one the brief means by *"the renamed test's second arm"*, which after live overruling 1 lives in Fixture E, not in the renamed test), plus Fixture D arm 2, Fixture L, the bool-vs-float both-orders pin, the collapses-to-`None` pin, and one `test_cli.py` end-to-end. **The renamed test PASSED** — its fixture's `r` **agrees** across repeats, so a disagreement mutation cannot reach it. Predicted before running and confirmed by running |
| **Replacement, owed and named in advance:** revert the empty-record admission — admit only units with at least one numeric value | **11 failed**, 2915 passed | **The renamed test FAILS**, which is the discriminating pin the prescribed mutation could not supply. Also arm E, arm G, Fixture B, Fixtures D arm 1 and arm 2, the seven-moving-keys pin, the no-column-at-all admission, the fold pin, and the empty-record `n_rows` pin — Ruling 8's own unpinned behaviour, now demonstrably pinned |
| Property-PRESERVING: build the fixture from a **different repeat label** (`_result("seedX", …)`) | **0 failed** on the targeted test | The collapse output is identical, so the test pins the collapse's output rather than the label it came from |

Both reverted by editing back, verified by `diff` **and** by re-running.

---

## Task 11 — the empty-level gate's document and record halves

**Step 1, checked before adding.** § Reporting strata carries **no** sentence stating this rule: it
has the `t_over_units`-under-`resample` limitation, the no-`p_value`-for-a-level rule, and the
two-marginal-splits rule, and nothing about an empty level's absence. (`test_a_level_that_completed_
nothing_gets_no_block` pins the **first** gate and cites *"the same absent-not-empty rule the `by`
block itself follows"* — a test docstring, not the document.) One paragraph added, stating that a
level block must carry at least one entry from the level's own table, that a block of nothing but
derived metrics over a table with no numeric column is the empty case wearing a value, and that
absent-not-empty is the rule `vs_baseline` and `contrasts` already follow — a `by: {}` claiming a
stratification was performed and found nothing.

**Step 2, the entry quoted before striking.** Its live text was:

> The second empty-level gate in `cli`'s stratum loop is unpinned | **RE-OWNED 2026-08-22 to H5
> Artifacts, sub-slice H5b, by name.** H5a's own plan (…) routes "the second empty-level gate in
> `cli.py`'s stratum loop" to H5b task 15 by that description; the gate goes live exactly when
> non-numeric recorded columns land, which H5a does not build, and the gate is not deleted in the
> meantime

and the **original** S4d row it descends from read:

> It is currently **unreachable**, because the first gate (`if not level_collapsed: continue`)
> already catches every empty level a numeric-only table can produce.

Both struck, with the correction spelled out: **that reason names the wrong mechanism.** The measured
reason is about the **collapse** — before task 4, `collapse_repeats` did not admit a unit whose every
recorded value was non-numeric, so no level could hold rows that produced no metric entry. The first
gate would still fire for a level with **no rows**; it was never why a level *with* rows and no
numeric column was unreachable, because that state did not exist.

**Step 4 — named blind, with its replacement stated as a fact.** Task 4's mutation (iii), `if True:`
in place of the gate, **already ran against the full suite and already failed Fixture H**; recorded
in `task-b2-report.md`'s mutation table as *"Replace `cli.py`'s second empty-level gate with `if
True:` → Fixture H's absent-level assertion FAILS (`b` reappears in `by`)."* Read there before being
cited. **Not re-run here** — re-running a mutation whose result is recorded is not evidence, and
running it against a stale checkout is worse.

Both consistency passes re-run over the four documents after this edit: **0 issues**.

---

## Claims about other tests, rows or code — what was grepped

Every claim below was greped rather than carried, per *before writing "no existing test asserts X",
grep for it*:

- `blast_radius` across `*.py`/`*.md` → 1 hit, the renamed definition. No stale reference.
- `"by": ` across `tests/*.py` → the full hit list is in task 9 above; the design's suite-wide claim
  is false and the `test_cli.py`-only claim is true.
- `RESERVED_COLUMNS` in `units.py` → the constant quoted, three readers.
- `W-STATS-STRATUM-SHADOWED` in `src/publishable/*.py` → 2 lines, one emit site + one docstring.
- `E-STEP-KEY-COLLISION` in `src/publishable/*.py` → 8 raise sites + 3 prose, all read.
- `keeps its value but gets no contrast delta` repo-wide → 0 after the edit.
- `no strata are reported` across the four documents, `src/` and `tests/` → 4 hits, each checked
  against the reworded row.
- the old collision test name → 1 test definition + 4 development-record files, which keep it.
- `n_paired:` across the four documents → 4 hits, all `run.yaml` output or prose, none settable.
- `Fixture H` / `if True:` in `task-b2-report.md` → the recorded mutation result, read before cited.

**No claim of "zero disagreements".** Three were found: task 7 step 5's *publishes no entry* (the
code publishes an entry with `n_paired: 0` — the design agrees with the code); task 10's prescribed
mutation being blind for the test it names, because that arm lives in Fixture E after live overruling
1; and the S4d filing's stated reason for the gate's unreachability being the wrong mechanism.

## Guard pins

No pin arm was edited. Arms A–E and arm G were untouched; arms with no authorized editor (A, C, D)
all passed on every full-suite run, and arm C's two bodies have **zero** lines changed, shown
mechanically by the 85-insertions-0-deletions diff. No arm with no authorized editor fired.

## Gates

`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` (52 source files) clean before
every commit. `.superpowers/sdd/.gitignore` was found clobbered to a bare `*` at the start of this
batch and restored from `HEAD` before the first commit; verified intact before each subsequent one.

## Concerns

1. **Task 7's warning-message edit in task 9 is a behaviour change to a shipped diagnostic's text**,
   beyond what task 9's brief asked for. It was necessary — the deleted clause was false of the case
   task 9 makes reachable, which is Ruling 7's shape — but it is a widening of scope and is disclosed
   as one rather than folded in silently. Nothing asserted the old text (grepped: 0 hits).
2. **Fixture G's `str`-column end-to-end arm passes before the guard as well as after**, and is
   labelled in its own docstring as a production control rather than a discriminating test. The arm
   that actually crashed at HEAD is the converted xfail. Presented that way so the `str` arm is not
   mistaken for the end-to-end proof.
3. **Task 7's guard now also narrows the ragged-`None` case**, which is reachable from a validated
   config — `_is_numeric(None)` is `False`. Decision 7 argues the guard's path is *unreachable from a
   validated config* and declines a diagnostic on that ground; that argument is true of the `str`
   case and **not** of the ragged-`None` case, where the guard silently drops the `None` units from
   the contrast. It is not silent in the record — `n_paired` reports the narrowed count, and
   `W-STATS-COLUMN-THIN` already fires on the condition side for such a column — but the *contrast*
   side has no disclosure of its own. Raised for the whole-branch reviewer rather than acted on:
   minting a contrast-side code is not task 7's, and Decision 7 explicitly rejects one.
