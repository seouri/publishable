# H5 scoping — artifacts

**Measured on 2026-08-21 against commit `0bd29a3fde53137ee9bdd92dbf615271365050ee`** (`main` at HEAD,
clean tree). **Read-only**: nothing under `src/`, `tests/`, `docs/reference.md`, `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/feasibility-llm-growth-studies.md` or `docs/superpowers/spec-defects.md` was edited by this
pass. Every project, roster, config and run directory built for it lives under the session
scratchpad. This document is the whole deliverable.

The charter is one row in `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`
§ The hardening slices: **"`units.parquet` integrity: non-numeric recorded columns, cross-row type
unification, and the reserved-column namespace `finalize` merges into"**, marked *independent; may
land any time after the checkpoint*. It was written **2026-08-11** (the S5-checkpoint amendment to a
spine dated 2026-08-08) — before H3b, H3c, H3d, all of H4, all of H7 and all of H8 landed.

Follows `H8-SCOPING.md`'s shape, including its habit of saying how each claim was measured.

---

## 0. Executive summary

1. **Two of the charter's three items are already built, and the third is where a published number
   is silently wrong.** Cross-row type unification ships as `_check_column_types`; the
   reserved-column namespace ships **for recorded columns** (`unit` and `measurement` are both
   refused at `io.record` with `E-STEP-KEY-COLLISION`). What is open is *attributes* into that
   namespace, and **non-numeric recorded columns downstream of the write**.
2. **A non-numeric recorded column reaches `units.parquet` today and is invisible everywhere else.**
   Measured on two real end-to-end runs: `units.parquet` holds `valid: True` and `truth: 'pos'`;
   the table `aggregate` receives has **2 columns** (`score`, `site`); the record's `aggregated`
   block holds no trace of either.
3. **That produces a published metric with an interval that is wrong, at exit 0, with no
   diagnostic.** A template whose `aggregate` does `[r for r in units if r.get("valid")]` over a run
   where **all six units recorded `valid: True`** published
   `n_valid: {value: 0.0, ci95: [0.0, 0.0], method: percentile_over_units, resample_draws: 2000}`.
   Same shape as H4b-2's Critical, and reachable from a config that validates clean.
4. **Core has no reader of `units.parquet`, but the documents give it one in user code.** `report`,
   `study`, `diff`, `freeze` and `lineage` contain the string `parquet` zero times and `units_hash`
   covers the **roster**, not the table — so no shipped command can break. But `reference.md`:2430
   (§ Steps that need every condition) shows a worked `summary` step doing
   `io.read_condition(c, "step02_score", "units.parquet")`, and that call routes through
   `READERS[".parquet"]`. So the artifact has exactly one documented consumer, it is user code, and
   it is H5b's behaviour-change exposure — not H5a's.
5. **`E-STEP-RETURN-TYPE` has two emit sites and one § Errors row describing the other one.** The row
   names "a returned value core can't record" and a name collision; the code also fires from
   `_encode_parquet` for **any** `.parquet` a step writes whose columns disagree across rows. This
   repo's own "§ Errors carries one row per code, not per emit site" trap.
6. **Three new live defects, none filed.** `io.write` does not coerce its rows while `io.record`
   does, so `io.write("scores.parquet", [{"v": np.float64(1.0)}, {"v": 2.0}])` **raises
   `E-STEP-RETURN-TYPE` on two values that are both floats** — and the `np.bool_`-beside-`bool` form
   of that message names the same type twice ("recorded both a bool … and a bool"). An attribute
   named `by` writes a `by` column to `units.parquet` unrefused.
7. **The feasibility analysis' own claim that its `io.record` payload is "numeric throughout" is
   false against its own worked step.** That is the finding that decides the four-row table: see § 8.
8. **19 tasks, and it should split two ways on the write/downstream seam** — H5a write-side integrity
   and the reserved namespace (9), H5b non-numeric columns downstream to `aggregate` (10). See § 9.

---

## 1. Method

- **Ran, did not read, wherever a run could answer.** Four real end-to-end `publishable run`
  invocations against a scaffolded project (6-unit roster, `seed` × 2, `generic` and a
  project-local `probe_tpl` template discovered by path), each committed first so `run` accepted the
  tree. Run directories and `run.yaml` read key by key.
- **17 direct `_encode_parquet`/`_decode_parquet` cases** built and executed, not reasoned about
  (§ 3).
- **Four `StepIO.record` + `finalize` probes** for the reserved-column namespace, executed against
  real `Unit`/`UnitList` objects (§ 4).
- **Two feasibility configs re-measured through `validate_config`** with a can-fail control each,
  transplanted onto a scaffolded `generic` config over a 240-row synthetic roster carrying every
  attribute either config names (§ 8).
- Where a claim rests on **reading**, it says so.
- Gates at this commit: `uv run pytest` → **2835 passed, 1 skipped, 2 xfailed** (run directly).

---

## 2. What the specification requires — enumerated by reading, then confirmed by grep

Read first: `reference.md` § The per-unit tables, § The apparatus files, § Steps and artifacts
(including the writer/reader tables, the longest-suffix rule, the coercion paragraphs, *One rule, all
three surfaces*, and *One metric name is reserved: `by`*), § How artifacts are organized, § The unit
table is the inference base, § Statistical reporting, § Reporting strata, § Templates (the
`aggregate` contract and the `units.truth`/`units.pred` paragraph), § The importable surface,
§ Errors core raises, § Warnings core reports, § Validation, § Units: the thing being measured,
§ What isn't a repeat, § Steps that need every condition, § Package layout; `design-principles.md`
§ Ontology (the `units.parquet` row). Then grepped.

**`experimental-designs.md` yields nothing for H5, and that is a measured zero rather than an
unexamined one.** Its § Mistakes core prevents was read row by row (23 rows) and grepped for
`unit key`, `shadow`, `reserved` and `attribute`: every row about the unit table is about `n`,
attrition, pairing, clustering or correction — **no row claims anything about the column namespace or
the unit-key column**, so nothing there is falsified by § 4's finding and nothing there needs to
become "structurally impossible in the schema". The one consequence worth carrying: when H5a task 4
mints the reserved-attribute-name refusal, that section is a **candidate for a new row** (an
attribute silently replacing the unit key is exactly its subject matter) — a decision for the design,
not a gap in the document today.

| Specified | State at this commit | How measured |
|---|---|---|
| `units.parquet` holds one row per completed unit | **built** | real run: 6 rows, 6 completed units |
| Its columns are the unit key, then every declared attribute, then the union of every key any row recorded, a column absent from a row reading null | **built** | real run: `{unit, site, score, valid, truth}`; and `_encode_parquet([{v:1.0},{}])` → `[{v:1.0},{v:None}]` |
| `measurements.parquet` present **only** when a step passed `measurement=` | **built** | `finalize` guards on `self._measurement_rows`, and the docstring states the guard; real run with no measurement wrote no such file |
| `measurements.parquet`'s **column set** | **specified nowhere** | § The per-unit tables gives only "one row per (unit, measurement)". Code writes `{unit, measurement, **values}` — no declared attributes, unlike `units.parquet`. Read at `artifacts.py:665` |
| `ineligible.jsonl`, one line per skipped unit | **built** | `finalize`; not H5's surface |
| Cross-row type unification within a column | **built, undocumented** | 17-case probe (§ 3). `_check_column_types` promotes int/float, refuses everything else with `ContractError` · `E-STEP-RETURN-TYPE`. § The per-unit tables states **no rule at all** |
| `io.record`'s `values`, a step's return and `aggregate`'s return take the same scalars under the same coercion — "One rule, all three surfaces" | **built for those three** | `coercion.coerce_scalars`, one function, three call sites |
| `.csv`/`.parquet` via `io.write` take "a sequence of mappings, one per row, every value a scalar" | **built, and NOT coerced** | `StepIO.write` calls `WRITERS[suffix]` directly with no `coerce_scalars`; probe: `np.float64` beside `float` raises (§ 3). The document says nothing about coercion for a writer's rows |
| `E-STEP-RETURN-TYPE` has a § Errors row | **row exists, narrower than the code** | `reference.md`:1099 names "a returned value core can't record" and a name collision. Two emit sites: `coercion._refuse` and `artifacts._check_column_types`. Nothing in § Errors describes the second |
| One metric name is reserved: `by`; a template's `aggregate` returning it raises `E-STEP-KEY-COLLISION`, a step *recording* it keeps its value and draws `W-STATS-STRATUM-SHADOWED` | **built** | `cli.py`'s `if "by" in step_summary` warn arm; `_encode_parquet` writes a `by` column fine |
| "anything added to [the reserved set] is a breaking change to what a template's `aggregate` may return" | **the set is still one** | § Steps and artifacts, read. Load-bearing for § 9's task 4 |
| A recorded column may not shadow the unit key or the measurement column | **built** | probes A/B/C (§ 4): `E-STEP-KEY-COLLISION` on both, at `io.record` |
| A recorded column may not shadow a declared attribute | **built** | `artifacts.py:660`; and it is why E1–E6's recorded `truth` would be refused (§ 8) |
| An **attribute** may not take a reserved name | **`key`/`paths`/`attributes` only** | `units.RESERVED_FIELDS = ("key","paths","attributes")`, three call sites. `unit`, `measurement` and `by` are all accepted |
| The `aggregate` table's columns are "whatever the step recorded plus every declared unit attribute", so `units.truth` and `units.pred` "are the same shape whichever of the two supplied them" | **false of the code for a non-numeric recorded column** | § Templates:1680, read; then two real runs (§ 5) |
| A column name no row holds is `E-STEP-COLUMN-UNKNOWN` rather than an empty column | **built** | real run: `W-STATS-AGGREGATE-FAILED … E-STEP-COLUMN-UNKNOWN ContractError: 'truth' is not a column this table holds; it has score, site` |
| `collapse_repeats`/`summarize_step` drop rather than raise on a non-numeric column | **built and deliberate** | `stats.py:2472` docstring; `spec-defects.md` § ANSWERED in S2 |
| `units_hash` covers `units.parquet` | **not specified and not true** | `units_hash(roster)` over a `UnitList`; `provenance.units` is `{n, key}`. No hash covers the table. H6's boundary, § 7 |
| Any reader of `units.parquet` in **core** | **none** | a grep over `src/publishable/` for `units.parquet` and for `read_parquet` returns one write site in `artifacts.py` and one unrelated comment in `cli.py`; `grep -n parquet` over `report.py`, `study.py`, `diff.py`, `lineage.py`, `freeze.py` → **0 lines** |
| A reader of `units.parquet` in **user code** | **specified and built** | `reference.md`:2430's worked `summary` step calls `io.read_condition(c, "step02_score", "units.parquet")`. Dispatch read at `artifacts._read`: `_suffix_for` decides from `WRITERS`, the reader is `READERS[".parquet"]` = `_decode_parquet` — the same function whose output § 3 and § 4 measure |

---

## 3. Cross-row type unification, measured

17 cases through `_encode_parquet` → `_decode_parquet`. Built and run, not reasoned about.

| Case | Result |
|---|---|
| homogeneous `str` | **round-trips** |
| homogeneous `bool` | **round-trips** |
| `int` then `float` (and reversed) | **promotes to float**, both directions |
| `bool` then `int` | `ContractError` · `E-STEP-RETURN-TYPE` |
| `int` then `str` | `ContractError` · `E-STEP-RETURN-TYPE` |
| `str` then `bool` | `ContractError` · `E-STEP-RETURN-TYPE` |
| `None` then `int` | round-trips, `None` preserved |
| every value `None` | round-trips as `[{v: None}, {v: None}]` |
| empty row set | `[]`, no raise |
| a column named `by` | **round-trips** — as § Steps and artifacts requires |
| a column absent from one row | reads `None` in that row |
| `np.float64` then `float` | **`ContractError` · `E-STEP-RETURN-TYPE`** — "recorded both a float64 … and a float" |
| `np.int64` then `int` | **`ContractError`** — "an int64 … and an int" |
| `np.str_` then `str` | **`ContractError`** — "a str_ … and a str" |
| `np.bool_` then `bool` | **`ContractError`** — **"recorded both a bool … and a bool"** |
| homogeneous `np.float64` | round-trips as `float` |
| homogeneous `np.str_` | round-trips as `str` |

The bottom five are new. `_check_column_types` normalizes only the **exact** types `int` and `float`
to `float`; every other `type(value)` groups as itself, so a NumPy scalar and its Python counterpart
are two groups. Reachable only through `io.write`, because `io.record` runs `coerce_scalars` first —
and `io.write` does not (`StepIO.write` calls `WRITERS[suffix]` with the caller's object untouched).
`io.write("scores.parquet", result.rows)` is the shape § Steps and artifacts' own worked step uses,
and rows out of a model or a dataframe carry NumPy scalars. The `np.bool_` message is the sharpest:
it names one type twice and tells the author nothing.

---

## 4. The reserved-column namespace, measured

Four probes through real `StepIO.record` + `finalize`:

| Probe | Result |
|---|---|
| A: `io.record("U1", {"unit": "HIJACKED", …}, measurement="r1")` | `E-STEP-KEY-COLLISION` — "`unit` collides with the unit key column" |
| B: `io.record("U1", {"measurement": "HIJACK", …}, measurement="r1")` | `E-STEP-KEY-COLLISION` — "`measurement` collides with the measurement column" |
| C: `io.record("U1", {"unit": "HIJACK", …})`, no measurement | `E-STEP-KEY-COLLISION`, same message |
| D: a unit whose **attributes** hold `{"by": "lvl"}` | `units.parquet` = `[{unit: 'U1', by: 'lvl', v: 1.0}]` — **written, unrefused** |

So the namespace is **guarded from the recorded side and open from the attribute side**, and that
asymmetry is the whole of the charter's third item. `RESERVED_FIELDS` means *fields on `Unit`*; the
set an attribute may not take is a different set, and today it is smaller by three (`unit`,
`measurement`, `by`).

**The `unit` shadow reproduces end to end.** A config declaring `attributes: [site, unit]` over a
roster whose `key` is `unit_id` and which also carries a `unit` column **validates clean**
(`✓ config valid`) and its run publishes:

```
{'unit': 'alpha', 'site': 'north', 'score': 0.5, …}
{'unit': 'beta',  'site': 'south', 'score': 1.5, …}
```

`U01`–`U06`, the actual unit keys, appear **nowhere** in the artifact. The filing's severity bound
holds — the same run's `score` interval was computed over the correct six units, because
`collapse_repeats` reads `StepIO._rows` (which carries the real key) and never the parquet, and
`_attributed` restores `unit` from the roster. The corruption is confined to the published file.

---

## 5. Non-numeric recorded columns: the write is built and everything after it is not

Two real runs, one loud and one silent.

**Loud.** A project-local template whose `aggregate` reads `units.truth`, over a step recording
`{"score": float, "valid": True, "truth": "pos"|"neg"}`:

```
warning W-STATS-AGGREGATE-FAILED probe_tpl.aggregate
        condition 0 step 'step01_summarize_units': E-STEP-COLUMN-UNKNOWN ContractError:
        'truth' is not a column this table holds; it has score, site
```

Exit **0**. Every metric that `aggregate` computes is lost for the whole run, disclosed as one
warning. `units.parquet` holds `truth` for all six units.

**Silent, and this is the one that matters.** The same run with
`aggregate` = `{"n_valid": float(len([r for r in units if r.get("valid")])), "cols": float(len(units.columns))}`:

```yaml
n_valid: {value: 0.0, basis: units, n: {resolved: 6, completed: 6, …},
          ci95: [0.0, 0.0], method: percentile_over_units,
          correction: null, cohens_d: null, resample_draws: 2000}
cols:    {value: 2.0, …}
```

All six units recorded `valid: True`. The record says zero, with a resampled interval and 2000
draws behind it, at exit 0 with **no diagnostic of any kind** — because `.get` on a row returns
`None` rather than reaching `UnitTable.__getattr__`'s refusal. `cols: 2.0` is the direct
measurement: the table holds `score` and `site` and nothing else.

**Where the columns are lost.** `stats.collapse_repeats` skips a value that fails `_is_numeric`, and
`gathered.setdefault(key, …)` runs **only inside that loop** — so a unit whose every recorded column
is non-numeric is **absent from the collapsed table entirely**, not present with an empty row. A run
recording only a `str` column produced `aggregated: {step01_summarize_units: {}}` — an empty block,
no `by` block despite a declared `report_by: [site]`, and no warning.

**A declared attribute survives where a recorded column does not.** `site` is in the table because
`cli._attributed` merges the roster's attributes back *after* the collapse. So a template can read a
string attribute and cannot read a string it recorded — an asymmetry § Templates' own sentence
("whatever the step recorded plus every declared unit attribute") denies.

**The second empty-level gate, and a correction to its filing.** `cli.py`'s stratum loop has two
gates: `if not level_collapsed: continue`, then
`if set(level_summary) - set(level_derived or {})`. The second is unreachable today, as the filing
says — but the filing's *reason* ("the gate goes live exactly when non-numeric recorded columns
land, which is H5's work") is imprecise. Measured: non-numeric columns already land in
`units.parquet`. The gate goes live when **`collapse_repeats` admits a unit that recorded no numeric
column**, which is a `stats.py` change the charter names nowhere. It is H5b's (§ 9, task 15) —
correctly routed, wrongly explained.

---

## 6. The three filings that name H5, re-checked against HEAD

### 6a. "`units.parquet` type unification across rows within a column is unspecified" (line 745)

| Claim | Verdict at HEAD |
|---|---|
| "`_encode_parquet` hands the column to `pyarrow.table`, which unifies types per column" | **stale.** `_encode_parquet` calls `_check_column_types` *before* `pa.table`; pyarrow never sees a clashing column |
| int/float promote to float, deliberately | **true**, both directions, measured |
| "bool/int and str/int clashes **raise `pyarrow.lib.ArrowInvalid` / `ArrowTypeError`**" | **stale in its mechanism.** Both raise `publishable.errors.ContractError` · `E-STEP-RETURN-TYPE`, naming the column, both types and a unit for each |
| The three named pin tests | **all three exist** in `tests/test_artifacts.py`, and two of them already assert `ContractError` and the code — so the **pins were updated when the check landed and the filing was not**, which is what the entry's staleness is |
| The 2026-08-11 amendment: "OPEN as a documentation debt … § The per-unit tables states no rule for cross-row type unification at all" | **live and correct.** § The per-unit tables says only "the union, with a column absent from a row reading as null" |

**Verdict: mechanism claim dead, documentation claim live.** Two verdicts, not one. The entry also
predicts "whoever writes the slice that adds `aggregate` … should inherit this reasoning" —
`aggregate` shipped long ago and the reasoning was not inherited: `collapse_repeats` floats
everything and drops the rest, which is a *third* boundary the entry does not describe.

### 6b. "`np.str_` / `np.bytes_` refused by `coerce_scalars`'s `__len__` guard" (line 1923)

**LIVE, and the mechanism is exactly as filed.** Measured:

```
np.str_('a')    → ContractError E-STEP-RETURN-TYPE  "gave 'v' a str_"
np.bytes_(b'a') → ContractError E-STEP-RETURN-TYPE  "gave 'v' a bytes_"
np.float64(1.0) → 1.0        np.bool_(True) → True        np.int64(3) → 3
```

`_coerce_one` tests `type(value) in _SCALARS` (exact type, deliberately — `numpy.float64` is a real
`float` subclass), so `np.str_` misses it and hits the `__len__` refusal on the next line. The one
refinement worth carrying: `np.bytes_` would be refused **either way**, since plain `bytes` is not
in `_SCALARS` at all (measured: `b'a'` raises the same code) — so a fix that admits `np.str_` must
not be argued as also settling `np.bytes_`.

### 6c. "`finalize` lets a declared attribute named `unit` shadow the unit key" (line 3278)

**LIVE, reproduced end to end** (§ 4). Every claim checked:

| Claim | Verdict |
|---|---|
| `RESERVED_FIELDS` is `("key","paths","attributes")` and excludes `"unit"` | **true** |
| `attributes: [unit]` passes validation | **true** — measured, `✓ config valid` |
| every row's unit-key column is replaced | **true** — measured on a real run |
| "`columns` also carries `"unit"` twice" | **true of the list, and harmless in the artifact.** `recorded` excludes `"unit"`, but `attribute_names` can hold it, so `columns = ["unit", "unit", …]`; the row is then built as a `dict` comprehension over `columns`, which collapses the duplicate. Worth fixing as the list it is, not as a corruption |
| "the table a template's `aggregate` receives is unaffected — `cli.py` restores the key from the roster" | **true.** `_attributed` restores `unit` after the merge, and `collapse_repeats` never reads the parquet. Confirmed by a real run whose `score` interval was correct over six units |
| the fix "mints a new `E-` identifier" | **true, and now wider than filed**: `measurement` and `by` are the same class (§ 4), so the identifier covers three names, and § Steps and artifacts calls adding to the reserved set "a breaking change to what a template's `aggregate` may return" |
| `RESERVED_FIELDS` must split into two sets | **true and load-bearing** — the recorded side is already guarded by three separate messages in `artifacts.py`, so the split is between *fields on `Unit`* and *names an attribute may not take* |

### 6d. The two residue-table rows (lines 1921, 2572)

Both **live**, both re-explained above: the `aggregate`-table half in § 5, and the unpinned second
stratum gate in § 5's last paragraph, whose stated cause is imprecise.

### 6e. Entries H5 plausibly owns that name a different owner or none

Checked every `## ` heading in `spec-defects.md` mentioning a column, a coercion, an artifact or the
unit table, and every `H5` mention.

- **Nothing new routes to H5.** The `repeat_spread`, `resample_draws` and `report_by`-emptiness
  entries name H4 or *unassigned* and their surface is `stats.py`'s constructions, not the artifact.
- **Three defects found by this pass are filed nowhere**, and all three are H5's: `io.write`'s
  uncoerced rows raising on two floats; that message naming one type twice; and an attribute named
  `by` writing a `by` column. § 9 gives each a task.
- **One documentation gap is filed nowhere**: `measurements.parquet` has no documented column set,
  and unlike `units.parquet` it carries no declared attributes. Also H5's.
- **One § Errors row is narrower than its code** (`E-STEP-RETURN-TYPE`, § 2). H5's, because the
  second emit site is `artifacts.py`'s.

---

## 7. Where H5 ends and H6, H9 and H3c-3 begin

| Neighbour | The boundary, measured |
|---|---|
| **H6 hashes and provenance** | `units_hash(units: UnitList)` hashes the **roster in resolved order**, and `provenance.units` is `{n, key}` — measured on a real run. **No hash covers `units.parquet`.** So H5 owns the file's contents and H6 owns the roster's identity, and they do not touch: changing what the table's columns hold moves no hash. If H5 wanted the table hashed, that would be a new `provenance` key and an argument against § Three hashes — **out of scope, and named here so it is not folded in** |
| **H8 (shipped)** | `report`, `study`, `diff`, `freeze` and `lineage` contain the string `parquet` **zero times**; `report` renders from `run.yaml` alone (measured: `publishable report run.yaml` on the probe run printed `score` and nothing about `label`/`flag`). H8 shipped no reader of this artifact, so H5 breaks none of its commands |
| **H9** | `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`. `dry-run` prints unit-executions, not columns. No overlap |
| **H3c-3** | folds inside cells — `fold_basis` and the holdout, `units.py`'s partitioning. `collapse_repeats`' `fold_members` argument is the only contact point, and H5b changes what that function *returns*, not how it intersects. Name the collision in H5b's design and pin the fold path |
| **H4 (complete)** | the `report_by`-under-`resample` gap, `repeat_spread`'s `std: 0.0`, and a degenerate stratum's missing console warning are H4's or unassigned and stay so. H5b touches `stats.py`, which is where those live — **do not fold them in**, and say so in writing, on H4b-2's precedent |

---

## 8. What H5 moves in the four-row table

The table, quoted from the last two entries of
[the feasibility analysis](../feasibility-llm-growth-studies.md) § Executability on this build rather
than paraphrased:

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step` |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**Row 1 holds at HEAD, re-measured.** E1's and C1's `data.units` and `statistics` blocks were
transplanted verbatim onto a scaffolded `generic` config over a 240-row synthetic roster carrying
every attribute either names, and run through `validate_config`:

```
E1 data/statistics: 0 errors, 1 warnings   (W-DATA-CLUSTER-UNDECLARED on age_band)
C1 data/statistics: 0 errors, 1 warnings   (same)
E1 CAN-FAIL control (holdout.frac=0):  1 error  E-DATA-HOLDOUT-FRAC
C1 CAN-FAIL control (resample.n=3):    1 error  E-STATS-RESAMPLE-N
```

The warning is the same fixture artefact the 2026-08-16 entry already sets aside — a property of the
synthetic table's three-band `age_band`, not of these designs. Both controls fired, so neither clean
result is a fixture that cannot fail.

**H5 changes nothing `validate` sees, so row 1 stays 8 of 8** — with one thing checked rather than
assumed: § 9's task 4 mints a refusal for an attribute named `unit`, `measurement` or `by`, and
**none of the nine declares any of the three**. E1's attributes are
`truth, sex, age_band, visit_density, span_days, dx_family, record_source`; C1's are
`consensus_label, sex, age_band, count_stratum, span_days, dx_family, record_source,
sampling_weight, split`. Rows 2 and 3 are `io.reuse_from`'s and H4's and H5 touches neither.

**Row 4 is where H5 lands, and the analysis' own claim about it does not survive.** § Executability's
2026-08-20 correction states:

> All nine configs record through **one** request step whose `io.record` payload is numeric
> throughout, which is why it reaches so many.

**That is false against the analysis' own worked request step**, four sections earlier:

```python
io.record(unit.key, {
    "pred": r.pred, "prob": r.prob, "truth": unit.consensus_label,
    "valid": r.valid, "invalid_reason": r.invalid_reason,
    "prompt_tokens": …, "completion_tokens": …, "reasoning_tokens": …,
    "latency_ms": …, "attempts": …, "finish_reason": r.finish_reason,
})
```

`valid` is a bool; `invalid_reason` and `finish_reason` are strings; `truth` is a roster label, which
arrives through `csv.DictReader` as a string. **Four non-numeric columns in the one payload all nine
configs share** — including E5, which runs `01 → 03 → 05` and so runs the same request step.

And the analysis' own `aggregate` reads two of them: `rows = [r for r in units if r.get("valid")]`,
`pos = [r for r in rows if r["truth"]]`, `sum(1 for r in pos if r["pred"])`, and
`roc_auc(units.prob, units.truth)`. Against this build that is **exactly the silent failure measured
in § 5** — `sensitivity` computed over an empty `rows` — for C1–C3, whose attribute is
`consensus_label` and whose `truth` is therefore a recorded column; and for E1–E6 the recorded
`truth` collides with the *declared* attribute `truth` and is refused outright at `io.record` with
`E-STEP-KEY-COLLISION` (measured: that refusal exists, `artifacts.py:660`), which is a second,
different defect in the analysis and not H5's.

**E5 is one of E1–E6 and shares that collision, and it still does not change the count.** The
collision is a defect in the analysis' own step code — a step recording a column it also declared as
an attribute — so it is not a *core-side* dependency and does not enter row 4's predicate, which
counts exactly those. H5's column drop is core-side and does. Stated because the two claims sit one
paragraph apart and read as a contradiction otherwise.

**So the honest statement about row 4, derived from the row's own words rather than restated:**
"free of every core-side dependency this analysis can name" now has one more nameable dependency,
it is H5's, and it meets **all nine** — so **naming it moves row 4 from 1 to 0 today, and H5 landing
moves it back to 1**. That is a re-derivation of an existing row, not a fifth number, and this
document mints none. Whoever writes H5's design should append that entry to § Executability with its
own date and commit, and should quote the request step rather than the "numeric throughout" sentence.

**The general shape, again.** "Numeric throughout" was a claim carried into a correction that was
itself about carried claims — the correction re-measured *which configs* met the `report_by` gap and
took the payload's type on trust while doing it.

---

## 9. The task count, decomposed

**19 tasks. It should split two ways.** The seam is **write-side artifact integrity** against
**non-numeric columns flowing downstream** — different files, no shared state, and only the second
changes what an existing run's `run.yaml` reports.

### H5a — write-side integrity and the reserved-column namespace (9)

| # | Task | Surface |
|---|---|---|
| 1 | § The per-unit tables states the cross-row unification rule: int/float promote, everything else refuses, with the code | `reference.md` |
| 2 | § The per-unit tables states `measurements.parquet`'s column set (`unit`, `measurement`, then recorded keys) and that it carries **no** declared attributes, unlike its sibling | `reference.md` |
| 3 | § Errors core raises: `E-STEP-RETURN-TYPE`'s row widened to cover its **second emit site** — a written `.parquet` whose rows disagree on a column's type. One row per code, every site | `reference.md` § Errors |
| 4 | Mint the reserved-attribute-name identifier in § Errors and § Validation **before any code**, and re-argue § Steps and artifacts' "the set is one today; anything added is a breaking change" against a set of three | `reference.md` (three sections) |
| 5 | Split `RESERVED_FIELDS` into *fields on `Unit`* and *names an attribute may not take* (`+ unit, measurement, by`), refuse at `validate` and at roster resolution, all three existing call sites re-pointed | `units.py`, `validate.py` |
| 6 | `finalize`'s `columns` list no longer carries `unit` twice; dedupe by name, not by relying on the dict comprehension downstream | `artifacts.py` |
| 7 | Decide and implement whether `io.write`'s `.csv`/`.parquet` rows go through `coerce_scalars` — the "one rule, all three surfaces" invariant against a fourth surface — and fix `_check_column_types`' exact-type normalization so a NumPy scalar and its Python counterpart are one group | `artifacts.py`, `coercion.py`, `reference.md` § Steps and artifacts |
| 8 | `np.str_` coerces; `np.bytes_` stays refused **on the `_SCALARS` ground, not the `__len__` one**, and the docstring says which | `coercion.py` |
| 9 | Pins for 5–8, each with its mutation: a decoy attribute on **each side** of the reserved set; a message asserting two *different* type names (the `np.bool_` case is the fixture that catches the current one); the empty row set and the all-`None` column; and strike/amend filings 6a–6c and the two residue rows | `tests/`, `spec-defects.md` |

### H5b — non-numeric columns downstream to `aggregate` (10)

| # | Task | Surface |
|---|---|---|
| 10 | Decide, in the documents first, what the `aggregate` table carries: § Templates' "whatever the step recorded plus every declared unit attribute" is a commitment, and narrowing it needs an argument against `design-principles.md` | `reference.md` § Templates, § The unit table is the inference base |
| 11 | `collapse_repeats` admits a unit that recorded **no** numeric column, and carries non-numeric columns through — return type widens from `dict[str, dict[str, float]]` | `stats.py` |
| 12 | The collapse rule **across repeats** for a non-numeric column. Note the sibling that already got it right: `units.rule_for`/`coerce_for_rule`/`apply_rule` handle exactly this for `measurements` (`first`, `mode`, and a constant-column shortcut). **Do not invent a second one** | `stats.py`, reusing `units.py` |
| 13 | `summarize_step` keeps a non-numeric column **out of `aggregated`** while the table carries it — the column must not become a published metric with a `ci95` and a seat in the correction family. This is the whole cost argument | `stats.py` |
| 14 | The namespace where a carried non-numeric column meets `_attributed`'s attribute merge and `E-STEP-KEY-COLLISION`'s existing arbitration | `cli.py`, `artifacts.py` |
| 15 | Pin the second empty-level gate in `cli.py`'s stratum loop — reachable for the first time once task 11 lands, and **not** for the reason its filing gives | `cli.py`, `tests/` |
| 16 | The silent case from § 5 gets a discriminating test: a run where `aggregate` reads a recorded bool must not publish a number contradicting the column. **A fixture whose numbers agree with the bug is the trap here** — `n_valid: 0.0` over six `True` rows is a plausible-looking value | `tests/` |
| 17 | The loud case: `E-STEP-COLUMN-UNKNOWN` under `W-STATS-AGGREGATE-FAILED` must stop firing for a column the table now holds, and must still fire for one it does not | `tests/` |
| 18 | Behaviour-change disclosure: `aggregated` gains nothing and loses nothing for a numeric-only run — pinned against a captured `run.yaml` — and the case that *does* move is named in § What `status` means' neighbourhood if it moves at all | `tests/`, `reference.md` |
| 19 | Append the § Executability entry from § 8, dated and pinned, quoting the request step; and re-own or strike every filing this slice closes | `docs/feasibility-llm-growth-studies.md`, `spec-defects.md` |

### Should it split, and which first

**Yes, and on that seam.** Three grounds, none of them the count alone:

1. **Different files with no shared state.** H5a is `artifacts.py`, `units.py`, `coercion.py`,
   `validate.py`. H5b is `stats.py` and `cli.py`. The one contact point is task 14.
2. **Only H5b is a behaviour change to `run`.** This project has ruled twice that additive is fine
   and changing what an existing key reports is not (H7d Part B, H8b Decision 7). H5a adds refusals
   for configs that are corrupt today; H5b changes what `aggregated` may contain, which is why it
   carries task 18 and H5a carries no equivalent.
3. **H5b's first task is a document decision** with an argument against `design-principles.md` in
   it, and shipping it behind H5a's smaller, already-argued document work is the cheaper order.

**The split has a document consequence, and it is not optional.** The spine's § The hardening slices
says the set is closed and that "a residual that fits none of these is an argument for amending this
table" — so splitting H5 means **amending that table to define H5a and H5b**, and updating
`CLAUDE.md`'s order line, which today reads "H5 Artifacts, H6 Hashes and provenance, H9, then
H3c-3's remaining 14". That sentence has already gone stale twice on this project (H5 and H6 were
omitted from it for several slices). H8's three-way split is the precedent for both edits.

**H5a first**, because task 4's reserved-set decision is the one that touches the four documents'
enumerated `E-` registry and because it closes a live corruption of a shipped artifact in six tasks.
**Stated so the controller can invert it:** the *worse* defect is H5b's — a published metric with a
resampled interval that contradicts its own column, at exit 0, with no diagnostic, reachable from a
config that validates clean, versus a corruption needing `attributes: [unit]`. If severity decides
the order rather than size, H5b goes first and nothing in H5a blocks it.

---

## 10. Cost, risk, and testability

- **No core reader breaks.** `units.parquet` has no reader in `src/` and no hash over it (§ 2, § 7),
  so H5a cannot break a shipped command. That is unusually cheap for a slice touching a published
  artifact, and it is measured rather than hoped.
- **The same fact raises the stakes.** A corruption in `units.parquet` is invisible to every test
  that goes through `run.yaml` — which is every test in `tests/test_cli.py` that checks a metric.
  **A parquet assertion has to read the file.** And the one documented consumer is a `summary` step
  calling `read_condition(..., "units.parquet")`, so the `unit` shadow of § 4 corrupts more than the
  published file: it corrupts what that step reads. The filing's severity bound covers only the
  `aggregate` table and is therefore **narrower than the exposure**, which is a refinement to
  add when the filing is amended.
- **H5b is a behaviour change to `run` and must be additive.** For a numeric-only run — every test
  fixture in the suite, and every one of the nine feasibility configs' numeric columns — `aggregated`
  must be byte-identical. Pin that against a captured `run.yaml` **before** task 11 moves anything,
  on H8a's precedent for a pin captured in advance with its editor named.
- **Only a real `run` reaches the defect in § 5.** Both my direct-call probes of `_encode_parquet`
  round-tripped the string column happily; the silent wrong number appeared only when a template's
  `aggregate` ran against a collapsed table built by `cli.py`. This is H4b-2's lesson verbatim —
  every direct-call probe hand-builds the maps and never reaches it — so **H5b's reviews need
  end-to-end runs, not helper calls.**
- **Two mutations that would be blind, named in advance.** Emptying `_check_column_types`' body
  leaves the suite green in the `np.*` cases, because no fixture mixes a NumPy scalar with its
  Python counterpart — that is task 9's fixture, not evidence the check is unreachable. And
  replacing `collapse_repeats`' `_is_numeric` guard with `True` will *not* be caught by any
  assertion counting units, because the existing fixtures record numeric columns only.

---

## 11. Claims that did not survive

Stated plainly, most valuable first.

1. **The charter's three items are not three open items.** "Cross-row type unification" is **built**
   (`_check_column_types`, measured 17 ways) and only undocumented. "The reserved-column namespace
   `finalize` merges into" is **built for recorded columns** (`unit` and `measurement` both refused
   at `io.record`) and open only for **attributes**. What the charter does not say, and what the
   slice actually is, is *non-numeric columns downstream of a write that already works.*
2. **The feasibility analysis' "one request step whose `io.record` payload is numeric throughout" is
   false against its own worked step** — `valid` is a bool, `invalid_reason` and `finish_reason` are
   strings, `truth` is a roster label. This is the claim that decides the four-row table, and it was
   written inside a correction about carried claims.
3. **Filing 6a's mechanism is dead.** A bool/int clash does not raise `pyarrow.lib.ArrowInvalid`; it
   raises `ContractError` · `E-STEP-RETURN-TYPE` from core's own check, before pyarrow sees the
   column. **The filing's own pin tests already assert the new behaviour** — updated when the check
   landed while the filing was not.
4. **Filing 6a's forward-looking sentence was not honoured.** "Whoever writes the slice that adds
   `aggregate` … should inherit this reasoning" — `aggregate` shipped, and `collapse_repeats`
   invented a **third** boundary (drop silently) that the entry describes nowhere.
5. **The unpinned-stratum-gate filing routes correctly and explains itself wrongly.** The gate does
   not go live "when non-numeric recorded columns land" — they already land in `units.parquet`. It
   goes live when `collapse_repeats` admits a unit with no numeric column.
6. **`RESERVED_FIELDS` is not the only thing missing a name.** The filing names `unit`; measurement
   is guarded, but **`by` is not** — an attribute named `by` writes a `by` column to `units.parquet`
   unrefused, which is the same class in the artifact that § Steps and artifacts reserves the name
   for in the record.
7. **"`columns` carries `unit` twice" is true of the list and harmless in the file.** The dict
   comprehension that builds each row collapses the duplicate. Worth fixing as a list bug; not part
   of the corruption.
8. **The brief's premise that H8's shipped commands read `units.parquet` is false.** `report`,
   `study`, `diff`, `freeze` and `lineage` contain the string `parquet` zero times, and no hash
   covers the table. This inverts the risk framing the brief supplies.

## 12. What I could not measure

- **Whether the feasibility plugin's `r.pred` is a bool, a string or a number.** The analysis shows
  the payload and not the request object, so `pred` is *plausibly* non-numeric and I have not
  established it. Nothing in § 8 rests on it: `valid`, `invalid_reason` and `finish_reason` settle
  the question on their own.
- **The real plugin's behaviour.** Neither `growth_screen` nor `publishable-llm` exists to install,
  so § 8's mechanism is measured on a probe template that reproduces the analysis' `aggregate`
  shape, not on the analysis' own code. The two runs in § 5 are the evidence; the transfer to the
  nine configs is an argument from the payload they share.
- **Whether `E-STEP-KEY-COLLISION` on E1–E6's recorded `truth` fires before or after anything else
  they would hit at run time.** It is a run-time raise inside `io.record`, so it needs an executing
  config, and none of the nine executes. Filed here as a defect in the analysis, unmeasured in
  context.
- **A `measurements.parquet` written by a real run.** Its shape is read from `artifacts.py:665` and
  probed through direct `StepIO` calls (§ 4), not observed in a run directory — no scratchpad config
  declared `data.units.measurements`.
