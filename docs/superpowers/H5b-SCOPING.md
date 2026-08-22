# H5b scoping — non-numeric columns downstream to `aggregate`

**Measured on 2026-08-22 against commit `5ee3a0c`** (`main` at HEAD, clean tree). **Read-only**:
nothing under `src/`, `tests/`, `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md` or
`docs/superpowers/spec-defects.md` was edited by this pass. One `src/` file was mutated and restored
by content copy (§ 1); every project, roster, config, run directory and probe built for this pass
lives under the session scratchpad. This document is the whole deliverable.

The charter under test is [`H5-SCOPING.md`](H5-SCOPING.md) § 9's H5b table — **ten tasks, 10 through
19** — written 2026-08-21 against commit `0bd29a3`, **before H5a shipped**. Follows
[`H8-SCOPING.md`](H8-SCOPING.md)'s shape, including its habit of saying how each claim was measured.

---

## 0. Executive summary

1. **The central question — is H5b additive? — is answered NO, by measurement.** Holding one config
   and one step fixed and swapping in the H5b shape (§ 6), a derived metric's published `value` moved
   `4.0 → 6.0`, its `n.completed` moved `4 → 6`, its `ci95` widened, `vs_baseline`'s `n_paired` moved
   `4 → 6` — **and the Holm rank flipped, so a purely numeric recorded column's `ci95_corrected`
   moved too.** H5-SCOPING task 13's rule ("keep the column out of `aggregated`") does **not** make
   the slice additive; the numbers move because admitting a unit changes the inference base.
2. **The silent drop reproduces end to end, and it is reachable from the untouched scaffold.**
   `publishable init`'s own generated step records `{"present": True}` — one bool and nothing else —
   so a freshly scaffolded project's very first `run` publishes `aggregated: {step: {}}` at exit 0
   with no diagnostic (§ 3). `collapse_repeats` returns `{}`: not six units with a column dropped,
   **zero units**.
3. **A derived key colliding with a non-numeric recorded column is NOT refused — and two shipped
   claims say it is.** A real run published `valid: 1.0` in `run.yaml` while `units.parquet` held
   `valid: True` for all six units, no diagnostic (§ 4). `summarize_step`'s docstring ("even one
   dropped above for being non-numeric") and `reference.md` § Errors core raises both promise the
   refusal. **A green test in `tests/test_stats.py` names the exact hazard in its own docstring and
   does not prevent it**, because it hand-builds a `collapsed` no production caller can produce.
4. **The naive shape of the fix destroys a run record.** Letting a non-numeric column into
   `step_summary` reaches an unguarded subtraction at `cli.py`'s paired-contrast arm: measured, a
   `TypeError` outside every `try`, **run directory complete, every execution paid for, no
   `run.yaml`** (§ 5). That guard needs a task of its own, not an implied consequence of task 13.
5. **The blast radius on the suite is two tests, not the 12 the grep suggests** — measured by running
   the whole suite against the H5b shape, not by counting assertions (§ 7). Both are direct-call pins
   in `tests/test_stats.py`; one of them is item 3's.
6. **H5a moved four of H5b's ten tasks, not one.** The scoping named task 14 as the single contact
   point. Measured against the merged code: task 12's input space narrowed, task 14 narrowed on one
   side and **widened** on another, task 10 gained a question `reference.md` now routes to H5b by
   name, and `cli.py` carries a justification H5a falsified (§ 8).
7. **Two claims written after H5a merged are false, and one obligation was not discharged** (§ 9):
   the spine's own 2026-08-22 amendment says the behaviour-change exposure is "H5b's alone"; H5a's
   design says "Filed, not built, owner H5b" for a question `spec-defects.md` has no entry for; and
   H5a's Decision 11 required a row-4 re-derivation that its § Executability entry did not make.
8. **15 tasks, and it should not split.** See § 11.

---

## 1. Method

- **Ran, did not read, wherever a run could answer.** Eight real end-to-end `publishable run`
  invocations against two scaffolded experiments in one committed project — a 6-unit roster with a
  `site` attribute, `seed × 2`, one against `generic` and one against a project-local `probe_tpl`
  discovered by path. Every `run.yaml` and `units.parquet` read key by key.
- **The H5b shape was built as a monkeypatch and run through the real console entry point**, so the
  behaviour-change question is measured against `cli.command_run`'s own wiring rather than against a
  hand-built map. Its source is in the scratchpad; its rule is stated in § 6.
- **The suite was run three times**: baseline, under one `cli.py` mutation, and under the H5b shape
  installed as a pytest plugin. Baseline at this commit: **2891 passed, 1 skipped, 2 xfailed**
  (`uv run pytest -q`, 174s, run directly in the foreground).
- **The one `src/` mutation** (§ 7) was taken by copying `src/publishable/cli.py` to the scratchpad
  first and restored by copying back — never `git checkout`. Restoration verified by content
  (`grep -c 'MUTATION'` → 0, the original line present at its line) **and** by `git status --short`
  printing nothing.
- **Every sweep filters the FILE LIST, never the output**, and each is shown with a control that can
  fail. Where a claim rests on reading, it says so.

---

## 2. What the specification requires — enumerated by reading, then confirmed by grep

Read first: `reference.md` § The unit table is the inference base, § Templates (the four-operation
table, the `aggregate` contract, the `units.truth`/`units.pred` paragraph, *One metric name is
reserved: `by`*), § The per-unit tables (including the cross-row unification rule H5a task 1 added),
§ Statistical reporting, § Reporting strata, § Errors core raises, § Warnings core reports,
§ Validation, § Steps and artifacts, § What isn't a repeat; `design-principles.md` § Ontology.
Then grepped.

| Specified | State at this commit | How measured |
|---|---|---|
| The `aggregate` table's four operations — row iteration, `units.<name>`, `len`, `columns` | **built** | real run: `AGG columns= ['score', 'site'] len= 6`, and a row is a mapping |
| "Columns are whatever the step recorded plus every declared unit attribute" (§ Templates) | **false of the code for a non-numeric recorded column** | real run recording `{score, valid, truth}`: the table holds `score` and `site` only (§ 3) |
| "A column has one entry per row, in row order, reading `None` where that unit recorded nothing" | **built** | `UnitTable({'u1':{'a':1.0},'u2':{'b':2.0}})` → `t.a == [1.0, None]`, `t.b == [None, 2.0]` |
| "A name no row holds is `E-STEP-COLUMN-UNKNOWN` rather than an empty column" | **built**, one raise site (`stats.py`), one § Errors row | `t.c` → `ContractError` · `E-STEP-COLUMN-UNKNOWN`; `grep -rn 'E-STEP-COLUMN-UNKNOWN' src/` → 1 line |
| § Errors: "any name collision the record can't hold … **a derived key against a recorded column**" | **broader than the code** | a derived `valid` beside a recorded non-numeric `valid` publishes both, no diagnostic (§ 4) |
| § Steps and artifacts: a step recording a column called `by` "is reported as `W-STATS-STRATUM-SHADOWED`" | **true only when the column is numeric** | measured both ways with a can-fail control (§ 4) |
| `collapse_repeats`/`summarize_step` drop rather than raise on a non-numeric column | **built** — and **`collapse_repeats` drops the whole UNIT** when every recorded value is non-numeric | direct call: `collapse_repeats` → `{}` for six units each recording `{"present": True}` |
| The document states, anywhere in the four documents, that a non-numeric recorded column is dropped downstream | **it does not** | `grep -rn 'non-numeric\|not a number\|never a quantity' docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md` → 6 hits, every one about weights, clusters, hypothesis thresholds or `Estimate`; **none about the collapse.** The rule lives only in `spec-defects.md` § ANSWERED in S2 and in two docstrings |
| The mixed `str`-and-`float` column question is routed to H5b | **routed in `reference.md` and in H5a's design; filed nowhere** | § 9 |
| Any hash covers `aggregated` | **none** | the three hashes are `code_hash`, `parameters_hash`, `input_manifest_hash`; H6's boundary, § 10 |

**`experimental-designs.md` yields nothing for H5b, and that is a measured zero.** Its § Mistakes core
prevents was grepped for `column`, `numeric`, `aggregate` and `bool`: no row claims anything about
what the collapsed table carries, so nothing there is falsified by § 3 and nothing there has to
become structurally impossible.

---

## 3. The silent drop, exactly — every site, measured

**Two drop sites, and only the first fires in production.**

| Site | What it drops | Reachable from a real run? |
|---|---|---|
| `stats.collapse_repeats` — `if column == "unit" or not _is_numeric(value): continue`, with `gathered.setdefault(...)` inside that same loop | the **value** from a mixed unit's row; the **whole unit** when every recorded value is non-numeric | **yes**, on every run |
| `stats.summarize_step` — `if not raw or not all(_is_numeric(v) for v in raw): continue` | a whole column | **no.** All three production call sites (`cli.py`, two condition-level and one stratum-level) pass a table derived from `collapse_repeats`, which never emits one. Pinned only by direct-call tests |

Direct call, both cases:

```
only-bool  collapse -> {}
only-bool  summarize -> {}
mixed      collapse -> {'u0': {'score': 0.0}, … 'u5': {'score': 5.0}}
mixed      summarize -> ['score']
```

**End to end, on the untouched scaffold.** `publishable init`'s generated
`step01_summarize_units.py` records `io.record(unit.key, {"present": True})` and nothing else
(`src/publishable/generators/experiment.py`, `STARTER_STEP`). A committed project, a 6-unit roster, a
clean `validate`, and:

```yaml
aggregated:
  step01_summarize_units: {}
```

`units.parquet` for the same run holds `{'unit': 'U01', 'site': 'north', 'present': True}` for all
six. Exit 0, no diagnostic. **The defect's most reachable trigger is the first run a new user makes.**

**The loud case and the silent case, both reproduced.** With a step recording
`{"score": float, "valid": True, "truth": "pos"|"neg"}`:

- a template `aggregate` reading `units.truth` earns
  `W-STATS-AGGREGATE-FAILED … E-STEP-COLUMN-UNKNOWN ContractError: 'truth' is not a column this table
  holds; it has score, site` — the whole `derived` mapping lost, exit 0;
- a template `aggregate` doing `len([r for r in units if r.get("valid")])` over the same six units,
  **all of which recorded `valid: True`**, published
  `n_valid: {value: 0.0, ci95: [0.0, 0.0], method: percentile_over_units, resample_draws: 2000}` —
  **exit 0, no diagnostic of any kind**, because `.get` on a row returns `None` rather than reaching
  `UnitTable.__getattr__`'s refusal. `cols: 2.0` beside it is the direct measurement of the table's
  width.

**What `aggregate` receives, measured rather than read.** `units.columns` is `['score', 'site']`; a
row is `{'unit': 'U05', 'score': 4.5, 'site': 'north'}`; `units.valid` and `units.truth` each raise
`ContractError` · `E-STEP-COLUMN-UNKNOWN`. **A declared attribute survives where a recorded column
does not**, because `cli._attributed` merges the roster back *after* the collapse — so a template can
read a string it never recorded and cannot read a string it did.

---

## 4. Every consumer of a collapsed value — enumerated by reading, then confirmed

Read `cli.command_run`'s aggregation phase and `stats.summarize_step` first, then grepped. **The
protective seam is `summarize_step`'s output key set, not `collapsed`**: every consumer below except
`aggregate` itself is keyed off `step_summary`.

| Consumer | Where | What it does if a non-numeric value arrives |
|---|---|---|
| the interval constructions | `summarize_step`'s column loop | never reached today — the `_is_numeric` gate precedes them |
| `repeat_spread` | `cli.py`'s loop over `recorded_columns`, gated on `column in step_summary` | `_repeat_spread_entries` re-filters `_is_numeric` over the **raw** rows, so `member_means` is empty and no key is written. **Two independent gates, and the second is the one that holds** |
| `cohens_d` | the contrast arms | derived from the per-unit differences; unreachable unless the column is in `step_summary` |
| **`vs_baseline` and declared contrasts** | `cli._comparison_step_blocks`, paired arm and unpaired arm | **raw subtraction on `of_collapsed[k][metric_key]`. Measured: `TypeError`, uncontained — see § 5** |
| the correction family | `correction.py`, over `Member`s built from the contrast blocks | inherits whatever the contrast arms produced |
| `report_by` strata | `cli.py`'s stratum loop → `summarize_step` again | tolerates it: measured under the probe shape, a level block published `truth: {value: neg, ci95: null, method: null}` — a first-row value dressed as a metric |
| hypothesis verdicts | `hypotheses.py`, reading the record | inherits the record |
| `null_test` | `permutation_over_units` and friends | float arithmetic; unreachable behind the same gate |
| **`report`** | `report.py` walks `condition["aggregated"]` | **renders it.** Measured: `publishable report run.yaml` printed a condition-table row reading `truth` under `metric` and `neg` under `value`, with `ci95` and `method` both `null`, exit 0 |
| **`study`** | `study.py`'s `_floor_metric_entries` | walks every entry carrying `basis`, **structurally** — so a non-numeric metric block would enter the thin-metric floor check |

**The `by` asymmetry, measured with a can-fail control.** A step recording a **non-numeric** column
named `by` writes `by: 'lvl0'` into `units.parquet`, is dropped by the collapse, and therefore
**never reaches `if "by" in step_summary`** — so `W-STATS-STRATUM-SHADOWED` does not fire and
`aggregated[step]["by"]` is the strata block, with no diagnostic anywhere. The control: the identical
step recording `"by": float(i % 2)` fires `warning W-STATS-STRATUM-SHADOWED generic.aggregate`.
`reference.md` § Steps and artifacts states the warning without that qualification.

**The collision that is claimed and does not happen.** A `probe_tpl.aggregate` returning
`{"valid": 1.0}` beside a step recording `{"score": …, "valid": True}` published:

```
run.yaml       aggregated.step01_summarize_units.valid = {value: 1.0, ci95: [1.0, 1.0], …}
units.parquet  valid = True, for every one of the six units
```

No refusal, no warning, exit 0. `summarize_step` computes `collision = set(derived) & set(columns)`
where `columns` is built from `collapsed` — **from which the column has already been removed** — so
the check cannot see it. Two shipped claims say otherwise: `summarize_step`'s own docstring ("A
derived key colliding with a recorded column — **even one dropped above for being non-numeric** — is
refused") and `reference.md` § Errors core raises' `E-STEP-KEY-COLLISION` row. And
`tests/test_stats.py::test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused` is
green while its own docstring names the hazard verbatim: *"otherwise a bool column named `r` plus a
derived `r` would silently coexist as two different meanings under one key."* Its fixture is
`{f"u{i}": {"r": True} for i in range(5)}` — a `collapsed` `collapse_repeats` cannot produce, since
that input returns `{}`. **A seam named in a docstring and instantiated by no reachable fixture**,
the shape this repo has recorded twice before.

---

## 5. The naive fix loses a run record — measured

`cli.py`'s paired-contrast arm differences two collapsed values directly:

```python
of_collapsed[k][metric_key] - against_collapsed[k][metric_key]
```

and the unpaired arm builds `of_values`/`against_values` the same way. `_compute_vs_baseline` and
`_compute_declared_contrasts` are called from `command_run` **inside no `try`** — verified by scanning
every `try:`/`except` between the aggregation phase and the call site, and then by running it. With a
probe that lets a `str` column into `step_summary`, a real `publishable run` gave:

```
File ".../cli.py", line 1167, in _comparison_step_blocks
    of_collapsed[k][metric_key] - against_collapsed[k][metric_key]
TypeError: unsupported operand type(s) for -: 'str' and 'str'
```

and the run directory afterwards held `conditions/`, `config.yaml`, `environment/`,
`executions.jsonl`, `manifest/`, `sweep.yaml` — **and no `run.yaml`.** Every execution paid for, the
record lost: this project's named habit, reached through the exact route task 13 is supposed to
prevent. **A rule enforced only by convention at one function's output is not a guard**, and the
guard belongs at the subtraction as well.

---

## 6. Is H5b additive? — the central question, answered by measurement

**The rule measured.** A monkeypatch installing the H5b shape: `collapse_repeats` admits every unit
it was handed (including one whose every recorded value is non-numeric) and carries the non-numeric
values; `summarize_step` projects them away before summarizing, which is H5-SCOPING task 13's rule
exactly. Nothing else changed — same config, same step, same roster, same seeds, run through the real
`cli.main`.

**The fixture.** Six units; units 0–3 record `{"score": float(i) + threshold, "valid": True}`, units
4–5 record `{"valid": True}` only. `sweep.baseline: {probe_tpl.threshold: 0.5}` with
`grid: {probe_tpl.threshold: [0.4]}`, `statistics.correction: holm`, and a template `aggregate`
returning `n_rows` (the row count) and `mean_score`.

| Key | Today | Under the H5b shape |
|---|---|---|
| `aggregated…score.n.completed` | 4 | 4 — **unmoved**, correctly: a ragged column's own `n` |
| `aggregated…score.value` / `.ci95` | 2.0 / `[-0.0543, 4.0543]` | **unmoved** |
| `aggregated…n_rows.value` | **4.0** | **6.0** |
| `aggregated…n_rows.n.completed` | 4 | **6** |
| `aggregated…mean_score.n.completed` | 4 | **6** |
| `aggregated…mean_score.ci95` | `[1.0, 3.0]` | **`[0.8333, 3.1667]`** |
| `vs_baseline…mean_score.n_paired` | 4 | **6** |
| `vs_baseline…mean_score.correction_level` | 0.025 | **0.05** |
| `vs_baseline…score.correction_level` | 0.05 | **0.025** |
| `vs_baseline…score.ci95_corrected` | `[-0.10000000000000014, -0.09999999999999998]` | **`[-0.10000000000000017, -0.09999999999999995]`** |

**Three conclusions, and the third is the one nobody has stated.**

1. **H5b is a behaviour change to what an existing key reports, and task 13's rule does not avoid
   it.** Keeping the column out of `aggregated` keeps the *key set* stable and moves the *values*,
   because admitting a unit widens the inference base every derived metric and every derived contrast
   rests on. The argument that survives is H5a's own — these numbers move **because they were
   wrong**; the filing already says `n` is wrong and the interval is wrong — but it has to be made in
   the open, enumerated key by key, not inherited from the scoping's split ground.
2. **The `paired_keys` question is a record-visible ruling, not an implementation detail.**
   `base_keys = paired_keys(of_collapsed, against_collapsed, allowed)` is `set(of) & set(against)`
   over the collapsed tables, so admitting a unit that contributed no number to either side puts it
   in `n_paired`. Whether a unit with no numeric column belongs in the pairing intersection and in
   the resample pool is a decision H5b must make explicitly.
3. **"Byte-identical for a numeric-only run" is the wrong pin.** `score` carries no non-numeric value
   anywhere and **its corrected interval moved**, because Holm ranks on the point estimate over half
   the raw `ci95` width and the *other* metric's width changed. Identity holds only for a run with no
   non-numeric column **anywhere in the same correction family** — a materially narrower claim than
   H5-SCOPING task 18 states, and the scaffold's own step falsifies the loose version.

**One design hazard the probe exposed for free.** Projecting the non-numeric columns away at the
`summarize_step` boundary means the tables the 2000 resample draws are built from have **different
columns** than the single unresampled table `aggregate` was called on — measured: `AGG cols=
['score','site','valid']` once, then `['score','site']` on every draw. A derived metric that reads
the carried column computes its `value` from it and then every draw from nothing, arriving at a real
point estimate with an interval around a different quantity. Where the projection happens is
therefore part of task 13's decision, not a detail of it.

---

## 7. Blast radius — measured by running the suite, not by counting assertions

**The greps, each with a control that can fail** (the file list is filtered, never the output):

| Command | Count |
|---|---|
| `grep -rn 'aggregated' tests/*.py \| wc -l` | 239 |
| `grep -rn 'set(aggregated' tests/*.py \| wc -l` | 12 |
| `grep -rn 'collapse_repeats(' tests/*.py \| wc -l` | 25 |
| `grep -rn '\["summary"\]\|results.summary' tests/*.py \| wc -l` | 31 |
| `grep -rn 'zzz_no_such_string_zzz' tests/*.py \| wc -l` (control) | 0 |
| `grep -rn 'dict\[str, dict\[str, float\]\]' src/publishable/*.py \| wc -l` | 20 (16 `stats.py`, 4 `cli.py`) |

**A count is not the answer to "which would have to move."** So the H5b shape of § 6 was installed as
a pytest plugin and the whole suite run against it:

```
PYTHONPATH=<scratch> uv run pytest -q -p h5b_probe
4 failed, 2887 passed, 1 skipped, 2 xfailed
```

**Two of the four are the plugin's own artefact**, established by a control that installs only the
plugin's `sys.path` insert and patches nothing: `tests/test_templates.py::
test_two_repos_in_one_process_do_not_cross_contaminate` and `…::
test_a_repos_own_templates_are_reachable_from_a_second_call` fail identically under the no-op plugin.
**The real blast radius is two tests, both in `tests/test_stats.py`, both direct-call:**

| Test | Verdict |
|---|---|
| `test_collapse_drops_a_bool_column_rather_than_averaging_it` | **a correct move.** It pins the behaviour that is the defect. Its replacement is the new rule, not a weakening |
| `test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused` | **neither, and this is the finding.** It is a pin of a guarantee production cannot reach (§ 4). It must be *made real*, not moved: the same assertion driven from a real run |

**Not one of the 12 `set(aggregated) ==` assertions moves**, because no shipped fixture has a unit
whose every recorded value is non-numeric — the scaffold's `{"present": True}` step is uniform, so
under the H5b shape all its units are admitted with an empty numeric row and `aggregated` stays `{}`.
**That is the measurement that makes item 3 of § 6 load-bearing:** the suite is silent on exactly the
case where the numbers move, so a green suite after task 11 is no evidence at all.

**Three shipped test docstrings state the current behaviour and two of them state it wrongly.**
`tests/test_cli.py`'s `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts` says
*"`stats.summarize_step` drops a bool column outright"* and pins `aggregated ==
{"step01_summarize_units": {}}` in prose — but `summarize_step` never sees the column; it receives
`{}` (§ 3). `test_a_baseline_sweep_reports_a_delta` says *"records only a bool … filtered by
`_is_numeric`"*, which names the right predicate in the wrong function.
`test_an_unclustered_resampled_contrast_draws_what_it_always_drew` says the default step *"grows no
`basis: units` column"*, which is true. All three are claims about the code that H5b must re-derive.

---

## 8. H5a's contact points — the scoping said one, and it is four

H5-SCOPING § 9 says *"The one contact point is task 14."* Measured against the merged code:

| Contact | What H5a did | Effect on H5b |
|---|---|---|
| **Task 14**, the attribute side | `units.RESERVED_COLUMNS = ("unit","measurement","by")` refuses a declared attribute of those names at `validate` and at roster resolution; `io.record`'s plain branch now refuses a `measurement` column | **narrowed.** The attribute-versus-column arbitration is settled for every config |
| **Task 14**, the `by` side | `by` became a refused *attribute* name while a recorded `by` column stayed legal by explicit ruling | **widened.** § 4's silent non-numeric `by` is the residue, filed nowhere, and it is the one case where "the refusal removes a producer, not the possibility" bites |
| **Task 12**, the collapse rule | Decision 6 coerces roster attribute values at `resolve_units` | **narrowed.** Every attribute reaching `_attributed` is now one of the four scalars, so the collapse rule H5b writes faces a smaller input space than the scoping assumed |
| **Task 10**, the documents | § The per-unit tables now states the cross-row rule **and routes its open half to H5b by name**: *"whether the table `aggregate` receives carries such a column at all is **H5b's Decision 10**"* | **widened**, and the routed question is unfiled (§ 9) |
| **`cli._attributed`**, not a task at all | H5a made its stated justification false | new: the docstring argues `unit` is restored after the merge "because nothing refuses an attribute *named* `unit`". `RESERVED_COLUMNS` now does, for every config. The restore is still needed — a directly built `Unit` bypasses it, per the open filing — but the reason has to be rewritten to the reason that is true |

H5a **closed** none of H5b's ten tasks and **retired** none of its filings.

---

## 9. The filings H5b owns — each re-checked, plus three that do not exist

`grep -n 'H5b' docs/superpowers/spec-defects.md` returns nine lines. Three are owning entries; one is
a pointer; five are `unassigned`-with-a-reason notes that name H5b only to exclude it.

### 9a. "A unit whose only recorded column is non-numeric is silently dropped" — Owner: H5b

**REPRODUCES, every claim.** `collapse_repeats` over six units each recording `valid: True` → `{}`
(direct call). The published `n_valid: {value: 0.0, ci95: [0.0, 0.0], resample_draws: 2000}` over six
`True` rows at exit 0 with no diagnostic → reproduced on a real run at this commit (§ 3). Its stated
check for the closer — carry with the column, carry without it, or refuse loudly, and the silent drop
must stop — stands, and § 6 adds the fourth question it does not name: **does such a unit enter
`paired_keys` and the resample pool?**

### 9b. "The `aggregate` table omits declared unit attributes and non-numeric columns" — RE-OWNED to H5b

**REPRODUCES.** The attributes half is closed (`site` is in the table). The non-numeric half is live:
`units.columns` is `['score','site']` for a step that recorded `valid` and `truth` (§ 3).

### 9c. "The second empty-level gate in `cli`'s stratum loop is unpinned" — RE-OWNED to H5b

**REPRODUCES, and the mutation still survives the whole suite.** `src/publishable/cli.py`'s
`if set(level_summary) - set(level_derived or {}):` replaced with `if True:` → **2891 passed, 1
skipped, 2 xfailed**, unchanged from baseline. Restored by content copy and verified two ways (§ 1).
The gate is unreachable today for the reason H5-SCOPING gave rather than the reason the filing gives:
it goes live when `collapse_repeats` admits a unit with no numeric column, which is task 11.

### 9d. The pointer at the bool/int-clash entry

*"That is a different question … and it is **H5b's**, not H5a's"* — correct, and it points at 9b.

### 9e. Three things routed to H5b or created by H5a that are filed NOWHERE

**Sweep:** `grep -n '<claim>' docs/superpowers/spec-defects.md` for each, file list filtered to that
one file; control `grep -c 'E-STEP-RETURN-TYPE' docs/superpowers/spec-defects.md` → 4, so the sweep
can hit.

1. **The mixed `str`-and-`float` column question.** H5a's design Decision 1 says of it: *"Filed, not
   built, owner **H5b**."* Grepping that one file for `more forgiving` and for `mixed column`
   returns **0 lines**. `reference.md` § The per-unit tables carries the question in prose and names
   no owner. **A design line saying "Filed" is not a filing** — the same failure H5a's own batch-9
   review caught once, in the same slice, for the `.csv` null question. Second instance, missed.
2. **A derived key colliding with a non-numeric recorded column is not refused** (§ 4), while two
   shipped claims and one green test say it is. Unfiled.
3. **A non-numeric recorded column named `by` draws no `W-STATS-STRATUM-SHADOWED`** (§ 4). Unfiled.

### 9f. Two claims written after H5a merged that are false, and one obligation undischarged

1. **The spine's own 2026-08-22 amendment**, in the spine design's § The hardening slices, says
   *"the behaviour-change exposure is **H5b's alone**, and H5a went first"* and sizes H5a at **9**
   tasks. H5a's design says loudly that it **is** a behaviour
   change — four stoppages and one retirement — the controller **approved on that distinction**
   (*"H5a refuses corrupting input; H5b changes what an existing key may contain"*), and H5a shipped
   **13 plan tasks in nine batches**. The amendment was written after all of that. **Append a
   correction; do not edit it** — a spec records what was decided when it was written.
2. **H5a's Decision 11 ruling was not discharged.** It said row 4's `1 → 0` re-derivation *"must be
   appended regardless of which slice does it"* if H5b did not land in cycle, *"because row 4 reads
   `1` today and the honest figure is `0`."* The § Executability entry dated 2026-08-22 against
   `71f3c6e` leaves **row 4 at 1** and substitutes a prose paragraph. H5b inherits the settlement.
3. **`cli._attributed`'s justification**, § 8's last row.

---

## 10. Where H5b ends — the neighbours, in writing, on H4b-2's precedent

| Neighbour | The boundary, measured, and it is not folded in |
|---|---|
| **H4 (complete)** | The `report_by`-under-`resample` gap was **converted 2026-08-18 to a documented permanent limitation** — the code is unchanged and the entry says so; `repeat_spread`'s `std: 0.0` was **RE-OWNED 2026-08-21 to unassigned**, H4 being complete; a degenerate stratum's missing console warning still reads **"H4 Statistics"**, which no longer exists as an owner and is itself stale. H5b touches `stats.py`, which is where all three live. **They stay where they are, and the third's ownership should be corrected by whoever next sweeps this file — not by H5b, and not silently by H5b's design** |
| **H3c-3** | Folds inside cells. `collapse_repeats(results, step, cond, fold_members=…)` is the contact, and it is real: H5b changes what that function **returns**, not how it intersects. But **H5b widens the return type at 20 annotation sites**, so H3c-3 is cheaper after H5b than before it. Name the collision in H5b's design and pin the fold path |
| **H6** | No hash covers `aggregated` or `units.parquet`. Changing what the collapsed table holds moves no hash. A hash over the table is a new `provenance` key and an argument against § Three hashes — **out of scope, named so it is not folded in** |
| **H8 (shipped)** | H5-SCOPING framed this boundary around `units.parquet` and got the right answer to the wrong question. `report`, `study`, `diff`, `freeze` and `lineage` read no parquet — **but `report.py` and `study.py` both read `aggregated`**, which is the key H5b changes (§ 4). `report` renders a non-numeric `value` without complaint; `study`'s thin-metric floor walks any entry carrying `basis`, structurally. Neither moves under task 13's rule, and **that must be pinned rather than assumed**, because it is precisely the additive-only claim the ruling requires |
| **H9** | `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`. No overlap |
| **The generator** | `STARTER_STEP` is `src/publishable/generators/experiment.py`, not `stats.py` or `cli.py`, so it is outside the charter's stated surface — and it is the defect's most reachable trigger (§ 3). Whether to change it is a decision, and § 11 gives it a task rather than letting it be assumed either way |

---

## 11. Decomposition — 15 tasks, and it should NOT split

The charter is ten. Measured at **15**. Six of the charter's ten survive intact, four grow, and five
are new — three of them forced by measurements the charter's author could not have made, since H5a
had not shipped.

| # | Task | Surface | Charter |
|---|---|---|---|
| 1 | **The guard pin, captured BEFORE anything moves, with its editor named in advance.** Not "`aggregated` is byte-identical for a numeric-only run" — § 6 falsifies that. The pin is: a run with **no non-numeric column anywhere in the correction family** is byte-identical, and the run that *does* move has every moving key enumerated in the pin's own docstring | `tests/` | 18, rewritten |
| 2 | § Templates: what the `aggregate` table carries. "Whatever the step recorded plus every declared unit attribute" is a commitment; narrowing it needs an argument against `design-principles.md` | `reference.md` | 10 |
| 3 | § The per-unit tables' routed mixed-type question **decided** (H5a Decision 1 routes it here by name); § Statistical reporting states what `aggregated` may not hold; any new `W-` minted before the code | `reference.md`, § Errors, § Warnings | new |
| 4 | `collapse_repeats` admits a unit that recorded no numeric column and carries non-numeric values; return type widened, **20 annotation sites** swept | `stats.py`, `cli.py` | 11 |
| 5 | The across-repeats collapse rule for a non-numeric column. **The sibling that already got it right is `units.rule_for`/`coerce_for_rule`/`apply_rule`**, which solves exactly this for `measurements`. Do not invent a second one | `stats.py`, reusing `units.py` | 12 |
| 6 | `summarize_step` keeps a non-numeric column out of `aggregated` — **and the projection's placement is part of the decision**, because projecting at this boundary gives the 2000 resample draws a narrower table than the unresampled call (§ 6) | `stats.py` | 13 |
| 7 | **The contrast guard.** A non-numeric value can never reach `cli.py`'s paired subtraction or its unpaired vectors; the measured `TypeError`-with-no-`run.yaml` (§ 5) is the mutation that proves it | `cli.py`, `tests/` | new |
| 8 | **The `paired_keys` ruling.** Does a unit with no numeric column enter the pairing intersection, `n_paired`, and the resample pool? Record-visible, so it is a decision with grounds, not a consequence of task 4 | `stats.py`, `cli.py`, `reference.md` | new |
| 9 | The `by` arbitration: `W-STATS-STRATUM-SHADOWED` for a non-numeric `by` column, with the numeric control as its can-fail arm; `_attributed`'s falsified justification rewritten (**prefer deleting the claim to rewriting it**) | `cli.py` | 14, widened |
| 10 | Make the derived-key collision real for a non-numeric recorded column, or delete both claims that promise it. `test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused` becomes reachable from a real run | `stats.py`, `reference.md` § Errors, `tests/` | new |
| 11 | The second empty-level gate pinned, with the end-to-end route that first makes it reachable | `cli.py`, `tests/` | 15 |
| 12 | `E-STEP-COLUMN-UNKNOWN` stops firing for a column the table now holds and still fires for one it does not | `tests/` | 17 |
| 13 | The silent case's discriminating test. **A fixture whose numbers agree with the bug is the trap**: `n_valid: 0.0` over six `True` rows is a plausible value, and so is `n_rows: 4.0` over six units | `tests/` | 16 |
| 14 | `report` and `study` pinned as readers of `aggregated` — unmoved, or moved deliberately (§ 10). Plus the three shipped test docstrings that state the drop and two of which state it wrongly (§ 7) | `tests/` | new |
| 15 | The records: strike 9a/9b/9c, **file** 9e's three, append the § Executability entry with its own date and commit and settle 9f's row-4 obligation, and append a correction to the spine amendment (9f.1) | `spec-defects.md`, feasibility analysis, spine | 19, widened |

**Should it split? No.** Fifteen sits inside this project's range (H8a 10, H8c 12, H3c-3 17, H4's
sub-slices 14–17), and the three grounds that justified splitting H5 do not recur inside H5b: it is
two files with one shared phase, and the behaviour-change argument (§ 6) has to be made **once**,
over the whole set of moving keys, or it is not an argument. Splitting would put tasks 4 and 6 in
different slices with a half-changed `collapsed` between them.

**If the controller wants a split anyway, the seam is not the file boundary.** It is **stop the silent
drop** (1, 2, 4, 5, 6, 7, 8, 12, 13) against **the namespace, the readers and the records** (3, 9, 10,
11, 14, 15), and the first goes first — it holds the Critical.

**Order against the remaining slices: H5b next, before H6, H9 and H3c-3's remaining 14.** Two grounds
that are measurements rather than preferences. It is the only remaining slice holding a **silently
wrong published number reachable from the untouched scaffold** — every other open Critical-shaped
entry needs a hand-built `Unit` or an unusual template. And it is **cheaper before H3c-3 than after**:
H3c-3's folds-in-cells work reads `collapse_repeats`, whose return type H5b widens at 20 annotation
sites, so doing it first avoids a retrofit. Nothing in H6 or H9 blocks or is blocked by it.

---

## 12. Claims that did not survive

Most valuable first.

1. **"Only H5b's task 13 keeps it out of `aggregated`, so the key set is stable and the change is
   contained."** The key set is stable and **six values move**, including a corrected interval on a
   column with no non-numeric value in it (§ 6). The scoping's own split ground — *"H5b changes what
   an existing key may **contain**"* — understates it: H5b changes what existing keys **report**.
2. **"The one contact point is task 14."** Four (§ 8), and one of them is a justification in `cli.py`
   that H5a falsified.
3. **`summarize_step`'s docstring and `reference.md` § Errors both promise a collision refusal that
   cannot happen** (§ 4) — and a green test names the hazard in its own docstring while its fixture
   builds a state no production caller can reach.
4. **`W-STATS-STRATUM-SHADOWED` is not the guarantee § Steps and artifacts states** — it fires for a
   numeric `by` column and not for a non-numeric one, measured both ways.
5. **The spine's own amendment, one day old, is false about H5a** (§ 9f.1), and H5a's Decision 11
   obligation on row 4 was not discharged (§ 9f.2).
6. **H5-SCOPING's H8 boundary answered the wrong question.** "No shipped command reads
   `units.parquet`" is true and does not cover `report` and `study`, which read `aggregated` — the
   key H5b changes.
7. **The 12 `set(aggregated) ==` assertions are not the blast radius.** Two tests move, measured by
   running the suite against the H5b shape; the suite is **silent on the case where the numbers move**
   (§ 7), so passing it after task 4 is no evidence.
8. **"`collapse_repeats` drops the column"** is the wrong description of the worst case. It drops the
   **unit** — and the H5a ledger, this file's own predecessor filings, and one shipped test docstring
   all describe the milder version.

---

## 13. What I could not measure

- **Whether the feasibility analysis' row 4 should read `0` or `1` today.** E5's step records `truth`
  while E1–E6 also *declare* `truth` as an attribute, so E5's `io.record` would raise
  `E-STEP-KEY-COLLISION` before core's drop ever bites. Whether an analysis-side defect that
  pre-empts a core-side one removes the core-side dependency from row 4's predicate is a judgement
  H5b's design must make; I established the payload (`valid` a bool, `invalid_reason` and
  `finish_reason` strings, `truth` a roster label) and the `aggregate` that reads them, both quoted
  from the analysis itself, and nothing more.
- **The real plugin.** Neither `growth_screen` nor `publishable-llm` exists to install, so § 6's
  transfer to the nine configs is an argument from the payload they share, not an observation.
- **Whether `r.pred` is a bool.** The analysis shows the payload and not the request object. Nothing
  above rests on it.
- **A `measurements.parquet` written by a real run**, and therefore what the collapse rule of task 5
  does across a declared `data.units.measurements` in practice. No scratchpad config declared one.
- **Whether the two `tests/test_templates.py` failures under the plugin have any second cause.** They
  reproduce under a no-op plugin that only inserts a `sys.path` entry, which is sufficient to rule
  them out of the blast radius, and I did not look further.
