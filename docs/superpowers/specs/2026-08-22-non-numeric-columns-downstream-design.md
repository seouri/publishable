# H5b — non-numeric columns downstream to `aggregate`

**Written 2026-08-22 against `7dba9e8`** (`main` at HEAD, clean tree). Design only; nothing under
`src/` or `tests/` and none of the four documents was edited by this pass. Every probe built for it
lives in the session scratchpad.

Its input is [`H5b-SCOPING.md`](../H5b-SCOPING.md), measured 2026-08-22 against `5ee3a0c` — **15
tasks, do not split** — which re-measured [`H5-SCOPING.md`](../H5-SCOPING.md) § 9's ten-task charter
after H5a shipped. The scoping is the input, not the answer: every decision below names what was run
for it, and where the scoping ran something first it says whether this pass re-checked it.

---

## What this slice is, in one paragraph

A step records a column that is not a number — a bool, a label, a reason string. Today
`collapse_repeats` drops the value, and drops the whole **unit** when every value it recorded is
non-numeric, so the table a template's `aggregate` receives is narrower than the table
`units.parquet` holds and sometimes empty. H5b makes the collapse carry what the step recorded,
admits the unit, keeps the non-numeric column out of `aggregated` (it has no interval and no seat in
the correction family), closes the guard that a non-numeric value can never reach `cli.py`'s
contrast subtraction, and makes the derived-key collision the shipped docstring already promises
true. **It changes what existing keys in `run.yaml` report**, and the argument for that is made in
the open below rather than inherited from the split that created this slice.

---

## The measurement this rests on

Run for this design, by direct call against the installed package (`uv run python`, scratchpad
probes `p1`–`p6`):

| Measured | Result | Why it matters |
|---|---|---|
| `summarize_step` over a `collapsed` **already carrying** non-numeric values | publishes the numeric column and the derived metrics only, raises nothing | Decision 4: the projection is already at the output. `summarize_step` needs **no code change** |
| `summarize_step(collapsed_with_bool, derived={"valid": 1.0})` | **raises** `ContractError` · `E-STEP-KEY-COLLISION` | Decision 8: the collision becomes real for free, because `columns` is built from `collapsed` |
| `summarize_step`'s derived branch | `derived_n = {**counts, "completed": len(collapsed)}` | the key that moves, and why |
| `attrition` over the same executions | `{resolved: 6, completed: 6, ineligible: 0, failed: 0}` while the derived block published `completed: 4` | § The behaviour change's corroborating fact |
| `coerce_scalars({"valid": None, …})` | returns `None` unchanged — **`None` is a legal recorded value** | Decision 3: a `None` cell **cannot** be the disagreement signal |
| `io.record(key, {})` | writes `{"unit": key}` and adds the key to `recorded_keys` | Decision 1's edge case (an admitted unit with an empty row) is reachable |
| `percentile_of_derived` over the full table vs. one stripped of the bool column | `(6.0, 6.0)` vs. **`(0.0, 0.0)`** for a metric counting the bool | Decision 4's mutation: a point estimate outside its own interval |
| `provenance.environment.uv_lock_hash` (`cli.py`) and `diff`'s `uv.lock` row (`diff.py`) | both exist | § The behaviour change's cost, stated with its real mitigation and its real gap |

Re-checked from the scoping rather than taken on trust: `collapse_repeats` returns `{}` for six units
each recording only `valid: True` (§ 3 — reproduced by `p3`); the derived metric's `n.completed`
moves 4 → 6 (`p3`, `p4`); the paired-contrast arm differences `of_collapsed[k][metric_key]` with no
enclosing `try` (read at `cli.py`'s `_comparison_step_blocks`, and the metric-key source read at the
same function's `sorted((set(of_summary) & set(against_summary)) - {"by"})`).

**Not re-run:** the scoping's end-to-end run of the H5b shape through `cli.main` (§ 6's two-condition
Holm table) and its whole-suite run under that shape. Those are cited as its measurements, dated to
`5ee3a0c`, and the guard pin below requires the plan to **re-measure** the correction half rather
than copy the literals.

### What this pass found that the scoping did not

1. **`summarize_step` requires no change at all.** The scoping's task 13 ("`summarize_step` keeps a
   non-numeric column out of `aggregated`") is already true of the shipped code, and its own §6
   hazard — the 2000 draws seeing a narrower table than the unresampled call — exists **only** in the
   probe that implemented the projection at the wrong end. Decision 4.
2. **`None` is a legal recorded value**, so the obvious cheap disclosure channel for a disagreeing
   non-numeric column is unavailable. Decision 3.
3. **Today's derived metric block contradicts its own arithmetic** — `{resolved: 6, completed: 4,
   ineligible: 0, failed: 0}` in one mapping, while `attrition` over the same executions says
   `completed: 6`. That is a stronger ground for the behaviour change than "the numbers were wrong",
   and it is bounded: it does **not** hold for a ragged recorded column, where per-column
   `completed` below `resolved − ineligible − failed` is documented and correct.
4. **The scaffold's own symptom does not change.** `generic` inherits `BaseTemplate.aggregate`
   returning `{}`, so a project scaffolded by `publishable init` publishes `aggregated:
   {step01_summarize_units: {}}` **before and after this slice**. What changes is that a template
   reading `units.present` stops raising and `len(units)` stops being `0`. Decision 12.
5. **No test records a non-numeric `by` column.** `tests/test_cli.py`'s
   `_RECORDS_A_BY_COLUMN_STEP` records `{"pred": float(i), "by": float(i) * 2.0}` — the numeric arm —
   and the only other `"by":` hits in the suite are `sweep.groups` entries. Grepped, not assumed.

---

## Decisions

### 1. The collapse carries every recorded value and admits every unit it was handed

The filing (`spec-defects.md`, *a unit whose only recorded column is non-numeric is silently
dropped*) names four options: carry with the column, carry with the column omitted, refuse loudly,
or the silent drop. **Carry with the column.**

`collapse_repeats`' inner loop stops skipping a value for failing `_is_numeric`, and a unit that
passed the membership gate gets a row in the returned mapping even when that row is empty.

**Grounds.** § The unit table is the inference base makes the per-unit table the basis of every
interval and `n` a count of **units**; `attrition`, over the same executions, already counts such a
unit as `completed` (measured: `{completed: 6}` beside a derived block reading `completed: 4`), so
the collapse is the only place in the program that thinks it is not a unit. § Templates already
states the answer — *"Columns are whatever the step recorded plus every declared unit attribute"* —
so carrying is the reading the documents already commit to (Decision 10). The empty-row case is
reachable: `io.record(key, {})` settles the unit and records no column (measured).

**Rejected.** *Carry with the column omitted* leaves `units.parquet` and the `aggregate` table
disagreeing about what was measured, and leaves `E-STEP-COLUMN-UNKNOWN` firing for a column the run
demonstrably holds. *Refuse loudly* costs a completed run its record — this repo's named habit,
*every execution paid for, the record lost* — for a step that recorded a bool, which the scaffold's
own generated step does. *The silent drop* is the defect.

**Cost if wrong.** A template whose `aggregate` iterates rows and assumes every row carries its
numeric column now meets rows that do not, and raises — contained as
`W-STATS-AGGREGATE-FAILED`, costing that step's `derived` mapping. That failure is **loud and
attributed**, where today the same template silently computed over a subset. The exposure is real and
is the second half of § The behaviour change.

### 2. Across a unit's repeats, a non-numeric column collapses to its value when constant and to `None` when it disagrees

A numeric column averages. A non-numeric one has no average, and the config declares no rule for
repeats (`data.units.measurements.collapse` governs *measurements*, not repeats).

**Grounds, and the sibling.** `units.rule_for` / `coerce_for_rule` / `apply_rule` solve exactly this
for `measurements`, and `apply_rule`'s **constant-column shortcut** is the half that transfers:
*"Attributes constant within a key collapse to that value with no rule needed"* (§ What isn't a
repeat), quoted in `apply_rule`'s own comment. The half that does **not** transfer is the rule name:
`first` and `mode` are answers to a question the user declared for `measurements` and never declared
for repeats, and both are order-dependent here — `collapse_repeats` iterates `rows_by_label` in
execution order, which `order: randomized` shuffles, and the function's own `sorted(candidates)`
comment says sorting exists precisely so *"that order is a property of the roster instead of of the
shuffle."* Picking `first` would put the shuffle back into a published column.

**So: reuse `apply_rule` for the constant case and refuse to invent a rule for the other.** A
disagreeing column's cell is `None` — no value is honest, and the per-repeat `units.parquet` files
still hold every observation.

**Why `None` rather than omitting the key.** Omitting it would remove the column from
`summarize_step`'s `columns` list when every unit disagrees, and `columns` is what the derived-key
collision check reads (Decision 8) — so omission reopens the silent-coexistence defect through a
second door. `None` keeps the column visible and unpublishable (`_is_numeric(None)` is `False`).

**Cost if wrong.** A project whose steps legitimately record a per-repeat label (a `finish_reason`
that differs by design) reads `None` where it wanted the modal value. The route is
`data.units.measurements` with a declared `collapse`, which is the mechanism for a declared
within-unit collapse, and the disclosure is Decision 3's warning.

### 3. The disagreement is disclosed by a warning `cli.py` fires from a pure `stats.py` function — **not** by the `None` cell

**The obvious design is wrong and was measured wrong.** The first draft of this decision said *a
`None` value can only be produced by the disagreement rule, so `cli.py` can warn by scanning
`collapsed`.* Measured: `coerce_scalars({"valid": None})` returns `None` unchanged, and
§ The per-unit tables states that a recorded cell may hold `None` and that a column of all `None`
round-trips. **A recorded `None` and a collapsed disagreement would be the same cell**, so warning
from the cell answers the question with a proxy — the fault § Answering a question with a proxy
records six times.

**The answer:** a new pure function in `stats.py` beside `repeat_spread`, taking the same four
arguments the collapse takes plus the unit keys, returning the columns whose values disagreed per
unit; `cli.py` calls it in the aggregation phase and warns. **That is the sibling that already got it
right** — `repeat_spread` is a separate pure function over `results`, called from `cli.py` beside the
collapse, for a per-column across-repeat fact, with the warning living at the call site; `stats.py`
imports no findings channel and must not gain one. It asks the rows the direct question instead of
inferring from a collapsed value, which is why it survives `None` being legal.

**Mint `W-STATS-REPEATS-DISAGREE`** in `reference.md` § Warnings core reports **before the code**, one
row, and the row covers its single emit site. The stratum loop re-filters the same `collapsed` rather
than collapsing again, so there is no second site.

**Cost if wrong.** A run recording a legitimately per-repeat non-numeric column gets one warning per
step per condition. That is noise, not damage, and it is the direction *no diagnostic is the only one
of the options that cannot be right* points.

### 4. The projection stays at `summarize_step`'s **output**; nothing strips `collapsed`

Measured: `summarize_step` over a `collapsed` carrying `valid: True` and `truth: "pos"` publishes
`score` and the derived metrics and raises nothing — the column loop's existing `if not raw or not
all(_is_numeric(v) for v in raw): continue` **is** the projection. So this task ships no code in
`summarize_step`; it ships a docstring correction, a document sentence (Decision 11) and a pin.

**And the placement is a correctness rule, not a tidiness one.** `summarize_step` passes the
`collapsed` it received straight to `percentile_of_derived`, which rebuilds each draw's table from
whole rows. Stripping the column at the input would give the 2000 draws a narrower table than the
single unresampled `aggregate` call in `cli.py`. Measured on the same fixture: a metric counting the
bool column reports `value: 6.0` with `ci95: [6.0, 6.0]` against the full table and `ci95: [0.0,
0.0]` against the stripped one — **a point estimate outside its own interval.** That is Fixture I's
assertion and Mutation 4.

**One clause of `summarize_step`'s docstring stops being true and is deleted, not rewritten**: *"A
derived key colliding with a recorded column — **even one dropped above for being non-numeric** — is
refused."* After Decision 1 no column is dropped above, so the qualifier describes nothing; the
sentence without it is exactly true. *Prefer deleting a claim to rewriting it.*

**Cost if wrong.** None identified: the output-side projection is what ships today, and the input-side
one is the mutation this decision exists to forbid.

### 5. The widened return type is `dict[str, dict[str, Any]]`, swept at all 20 annotation sites

`grep -rn 'dict\[str, dict\[str, float\]\]' src/publishable/*.py | wc -l` → **20** (16 `stats.py`, 4
`cli.py`), re-run at `7dba9e8`.

**Rejected: a `Scalar = bool | int | float | str | None` union.** Every arithmetic consumer
(`t_over_units`, `mean_of`, the contrast arms) re-narrows at runtime through `_is_numeric`, which
mypy cannot see, so a union forces a `cast` at each of them — twenty annotations traded for a dozen
casts that assert the same runtime fact twice. `Any` states the honest thing: the table holds what
the step recorded, and the narrowing is a runtime check with its own pin (Decision 7).

**Verified by `uv run mypy`, not by a mutation** — an annotation change has no observable behaviour,
so naming a mutation for it would be naming one whose branches cannot differ.

**Cost if wrong.** A future arithmetic consumer added without a runtime narrowing gets no static
error. Decision 7's guard and its mutation are what stand in for the type.

### 6. A unit with no numeric column **does** enter `paired_keys`, `n_paired` and the resample pool

`base_keys = paired_keys(of_collapsed, against_collapsed, allowed)` is `set(of) & set(against)`, so
Decision 1 puts such a unit in the intersection. Ruled deliberately rather than inherited, because it
is record-visible: the scoping measured `vs_baseline…mean_score.n_paired` moving 4 → 6.

**Grounds.** It is a unit that completed in both conditions; a derived metric is computed over the
whole table, so the unit's row is part of what the metric was computed from whether or not it carries
that metric's column. The per-column arms need no change and get none: the paired arm already narrows
to `col_keys = [k for k in base_keys if metric_key in of_collapsed[k] and …]`, which is why the
scoping measured the recorded column `score`'s own `n` **unmoved** at 4 while the derived metric's
moved.

**Rejected: narrowing `paired_keys` to units carrying at least one numeric column.** That would make
`n_paired` disagree with the pool `paired_percentile_of_derived` actually draws from — the
construction draws over `base_keys` and recomputes — so the published count would describe a
different set than the interval beside it. This project has one recurring version of that fault
(*a vector filtered or ordered differently*), and it is the one thing this decision must not do.

**Cost if wrong.** A derived contrast's `n_paired` can exceed the number of units that influenced the
difference. It is still the honest figure, because it is exactly the pool the interval rests on, and
§ Statistical reporting's `n_paired` is documented as the paired intersection rather than as a count
of contributing values.

### 7. The contrast guard is an `_is_numeric` filter in the comprehension that already filters by membership — it **skips**, it never raises

Measured route: a non-numeric column cannot become a `metric_key` today, because
`_comparison_step_blocks` iterates `set(of_summary) & set(against_summary)` and `of_summary` is
`aggregated`'s step block. So after Decision 4 the subtraction is unreachable **by convention at
another function's output**, and the scoping measured what happens when that convention breaks: a
`TypeError` at `of_collapsed[k][metric_key] - against_collapsed[k][metric_key]`, outside every `try`,
run directory complete, **no `run.yaml`.**

**A rule enforced only by another function's output is not a guard**, so the filter goes at the
subtraction: `col_keys` gains `and _is_numeric(of_collapsed[k][metric_key]) and
_is_numeric(against_collapsed[k][metric_key])`, and the unpaired arm's `of_values`/`against_values`
gain the same narrowing in the same comprehension that builds them.

**Rejected: raising.** The two existing core-bookkeeping guards in that function raise `ValueError`,
and both sit in code reached before any interval is built; a raise **here** loses the `run.yaml` this
guard exists to protect. **Rejected: a new warning code.** The path is unreachable from a validated
config, and a code whose § Errors row could never fire is a row that misleads.

**Skipping is not silence.** A unit dropped this way is dropped exactly as a unit missing the column
is dropped today, and `n_paired` reports what remains — `0` already means *pairing failed*
(`CLAUDE.md` § Invariants), so an all-dropped metric publishes `n_paired: 0` and `ci95: null`, which
is the shape a reader can already read.

**Cost if wrong.** If a future change routes a non-numeric column into `aggregated` deliberately,
this filter silently empties its contrast instead of refusing it. The filter's own mutation and the
end-to-end control (Fixture G) are what make the choice visible.

### 8. The derived-key collision becomes real with **no new code**, and the green unreachable test is re-driven from the collapse's own output

Measured: `summarize_step({u: {"score": …, "valid": True}}, …, derived={"valid": 1.0})` **raises**
`E-STEP-KEY-COLLISION` today. The check is `collision = set(derived) & set(columns)` with `columns`
built from `collapsed`, so Decision 1 is the whole fix: the column is in `collapsed`, so it is in
`columns`, so the collision fires.

Three shipped things claim this refusal and one green test names the hazard while proving nothing:
`tests/test_stats.py::test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused`
builds `{f"u{i}": {"r": True} for i in range(5)}` — a `collapsed` no production caller can produce.
**It is not deleted and not moved: it is made real.** Its fixture becomes the output of a real
`collapse_repeats` call over `ExecutionResult`s recording a bool, and its assertion is unchanged.

The containment is already right and is not touched: `cli.py` catches the `ContractError` as
`W-STATS-AGGREGATE-FAILED` and retries with no `derived`, so the run keeps its record and loses the
`derived` mapping.

**And this closes one corner of the H4b-2 Critical for the non-numeric case** — a derived key
colliding with a recorded column's name published an *unclustered* contrast interval because the
refusal could not see the column. For a non-numeric column it now can.

**Cost if wrong.** A template that today publishes a derived `valid` beside a recorded bool `valid`
loses its whole `derived` mapping and gets a warning. That is a run that publishes two different
meanings under one key today, at exit 0 — see § The behaviour change, stoppage 1.

### 9. A recorded column named `by` is answered from the recorded-column set, and **both** arms warn and suppress the strata

Today `cli.py` tests `if "by" in step_summary`, so a **non-numeric** `by` column draws no
`W-STATS-STRATUM-SHADOWED` and the strata are published under the same name the column holds in
`units.parquet` — measured by the scoping both ways, with the numeric case as its can-fail control.
After Decision 4 the non-numeric column still never reaches `step_summary`, so the gate must move.

**It moves to the recorded-column set** — the same `{col for cols in collapsed.values() for col in
cols}` the `repeat_spread` loop already computes — which is the direct question (*did any unit record
a column called `by`?*) rather than a proxy for it. This is not the *reserved name standing in for a
structural fact* fault: there the question was *is this entry a stratum?* and the answer was a name;
here the question **is** whether a name was recorded.

**Both arms warn, and both suppress the strata**, because `reference.md` § Steps and artifacts
already states it without qualification — *"no strata are reported for the step at all"* — and
because a run whose `units.parquet` holds a `by` column and whose `run.yaml` holds a `by` strata block
is the two-meanings-under-one-name case the reserved name exists to prevent. The § Warnings row is
reworded to cover a column that keeps no `aggregated` entry (a non-numeric one has none to keep);
**one row, one emit site, both conditions.**

**`_attributed`'s two falsified grounds are deleted rather than rewritten.** Its docstring argues
`unit` is restored *"because nothing refuses an attribute named `unit`"* — H5a's `RESERVED_COLUMNS`
now does, at `validate` and at roster resolution — and argues a numeric attribute's publication is
*"not reachable while every roster attribute arrives from `csv.DictReader` as a string"*, which H5a's
`coerce_scalars` at `resolve_units` (`units.py`) makes weaker than it reads: a resolver may yield a
float and it stays a float. Both grounds go; the true reasons stay — the unit key column must survive
a bootstrap draw that duplicates units, and an attribute is merged into **rows** and never into
`collapsed`, which is why it can never be published as a metric.

**Cost if wrong.** A project recording a non-numeric `by` column loses its `report_by` strata where
today it keeps them silently. It gains the warning that says so.

### 10. § Templates' sentence becomes **true**; no narrowing argument is owed, and the charter's premise for its task 10 was wrong

`H5-SCOPING` task 10 says § Templates' *"whatever the step recorded plus every declared unit
attribute"* is a commitment and *"narrowing it needs an argument against `design-principles.md`."*
Measured against the code and against Decision 1: the slice does not narrow it — it makes it true for
the first time. So the document work is a **confirmation plus two additions**, not a narrowing:

- § Templates states the collapse rule for a non-numeric column (Decision 2) and that such a column
  is a column and never a metric — the same shape the paragraph already uses for a declared
  attribute (*"It is a column here and nothing else — never a metric"*).
- § Statistical reporting states what `aggregated` may not hold: a metric block's `value` is a
  number, so a recorded column is published only when every value carried for it is a real number.

**Cost if wrong.** If a later slice wants a non-numeric metric, it inherits a sentence to argue
against. That is the correct cost of stating a rule.

### 11. The routed mixed-`str`-and-`float` question is decided: the **read** publishes a column only if every carried value is a real number, and the **write** is not loosened

§ The per-unit tables leaves it live — *"The more forgiving reading … is a live question for how the
table `aggregate` receives should treat such a column, and is not decided here"* — and H5a's
Decision 1 says of it *"Filed, not built, owner H5b."* **There is no such filing**
(`grep -n 'more forgiving\|mixed column' docs/superpowers/spec-defects.md` → 0 lines, re-run at
`7dba9e8`; control `grep -c 'E-STEP-RETURN-TYPE'` → 4). *A design line saying "Filed" is not a
filing* — and the discharge here is a **decision**, not a late filing.

**The read's rule is total over however a mixed column arises**, which is what makes it a decision
rather than a reachability claim: `summarize_step`'s column loop requires *all* carried values
numeric, so one string in a column of floats costs that column its metric block and nothing else.
The column still reaches `aggregate`, where a template that knows what the mixture means can use it.

**The write stays strict.** `E-STEP-RETURN-TYPE` on a genuinely mixed `.parquet` column is not
loosened here: loosening it would make a column's published-or-not status depend on the data rather
than on the config, so one run of a config would publish a metric and the next would not, with no
diagnostic distinguishing them. The read's tolerance decides the write's strictness only in the
direction H5a's own refusal table names — and it decides it *no*.

**Cost if wrong.** A project whose column is legitimately `str`-for-some-units still loses the whole
execution's record at `finalize`, which is H5a's boundary and is unchanged. If that turns out to be
the wrong trade, the reopening is a write-side change with no remaining slice owning it, and
Decision 14's records task files it as such.

### 12. `STARTER_STEP` is not changed

`publishable init`'s generated step records `{"present": True}` and nothing else, which the scoping
calls the defect's most reachable trigger. Measured consequence of Decision 1: **the symptom does not
move.** `generic` inherits `BaseTemplate.aggregate` returning `{}`, so the scaffold's first run
publishes `aggregated: {step01_summarize_units: {}}` before and after — the difference is that the
six units are now in the table, `len(io.units)`-shaped metrics are right, and a template reading
`units.present` stops earning `E-STEP-COLUMN-UNKNOWN`.

**Grounds for leaving it.** After this slice an empty `aggregated` over a bool-only step is the
**honest** answer: nothing numeric was measured. Recording a fabricated numeric column so the
scaffold's first run shows a metric would put a number nobody measured into every new project, and
the line is a `# TODO: replace with your analysis` placeholder by design.

**Cost if wrong.** A new user's first run still shows an empty `aggregated` and has to read the
document to learn why. The § Templates sentence Decision 10 adds is where they read it.

### 13. The slice is **not additive**, and it ships — the argument in the open

Held in § The behaviour change below, said loudly and in a section of its own, on H5a's and H8b
Decision 7's precedent.

### 14. Row 4 of the § Executability table goes `1 → 0 → 1`, and E5's analysis-side defect does **not** pre-empt the core-side dependency

H5a's Decision 11 ruled that H5b appends this entry and that the re-derivation *"must be appended
regardless of which slice does it"* — and the entry dated 2026-08-22 against `71f3c6e` left row 4 at
`1` and substituted a paragraph. H5b discharges it.

**The predicate is *"free of every core-side dependency this analysis can name."*** The
non-numeric-column drop is core-side and it meets E5: the analysis' one shared request step records
`valid` (a bool), `invalid_reason` and `finish_reason` (strings) beside its numeric columns, so E5's
own units enter the collapse with those values dropped. So row 4 reads **0** today and **1** once
this slice lands.

**The pre-emption question, decided.** The scoping could not settle whether E5's analysis-side
`E-STEP-KEY-COLLISION` removes the core-side dependency from the predicate. **It does not.** The
E-family declares `attributes: [truth, sex, age_band, …]` while the shared step records `"truth":
unit.consensus_label` — a recorded column shadowing a declared attribute, which `io.record` refuses
with `E-STEP-KEY-COLLISION`. That is a defect in the **analysis' own shown plugin code**, fixable by
renaming one key with no change to core, and the row's predicate names core-side dependencies only.
Letting it pre-empt would answer a different question — *would this config as literally written
run?* — under a heading that asks about core, and would pin row 4 at `0` until the analysis is
edited, which is exactly the *carried phrase answering no consistent question* failure the two
corrections in that section were written about.

**So the entry names both, separately**: row 4 moves `0 → 1` on the core-side dependency, and the
`truth` collision is named as an analysis-side obligation that changes no core-side count — the same
treatment the H8a entry gave E3's `summary`-step obligation. What this pass established is the
payload and the attribute list, both quoted from the analysis; **it did not run the plugin, which
does not exist.**

**Cost if wrong.** If a reviewer holds that an analysis-side blocker belongs in the predicate, row 4
reads `0` both before and after this slice and the entry's own paragraph still says which dependency
moved — the table stays quotable either way, which is the property the corrections asked for.

---

## The behaviour change, said loudly

**H5b is not additive.** This project has ruled twice — H7d Part B, H8b Decision 7 — that an additive
change to a shipped surface is fine and that changing what an existing key reports needs the argument
made in the open. Here is the argument, and the scoping's own measurement is what forces it into the
open: keeping the column out of `aggregated` keeps the **key set** stable and **moves the values**,
because admitting a unit widens the inference base every derived metric and every derived contrast
rests on.

**What is being corrected, in one line.** A run whose six units all recorded `valid: True` publishes

```yaml
n_valid: {value: 0.0, ci95: [0.0, 0.0], method: percentile_over_units, resample_draws: 2000}
```

at exit 0 with no diagnostic — a false number wearing an interval that asserts certainty about it and
a draw count asserting work done over an empty table.

**The corroborating fact, measured.** Today's derived metric block reads `{resolved: 6, completed: 4,
ineligible: 0, failed: 0}` in one mapping, while `attrition` over the same executions returns
`completed: 6`. A derived metric's `completed` is `len(collapsed)` — the table's own row count — so
that block contradicts its own accounting. **The identity does not bind a ragged recorded column**,
where a per-column `completed` below `resolved − ineligible − failed` is documented and correct
(`summarize_step`'s docstring says so); the claim is about the derived block only, and overclaiming it
would be the kind of proxy this design is trying to avoid.

**Every key that moves, enumerated.** Computed here, `seed=7`, `draws=2000`, six units of which four
recorded `{score: float(i), valid: True}` and two recorded `{valid: True}`, `counts = {resolved: 6,
completed: 6, ineligible: 0, failed: 0}`, template `aggregate` returning `n_rows` (row count),
`n_valid` (rows whose `valid` is `True`) and `mean_score` (mean of the scores present):

| Key | Today | After |
|---|---|---|
| `n_valid.value` / `.ci95` | `0.0` / `[0.0, 0.0]` | **`6.0` / `[6.0, 6.0]`** |
| `n_rows.value` / `.ci95` | `4.0` / `[4.0, 4.0]` | **`6.0` / `[6.0, 6.0]`** |
| `mean_score.value` | `1.5` | `1.5` — **unmoved** |
| `mean_score.n.completed` | `4` | **`6`** |
| `mean_score.ci95` | `[0.5, 2.5]` | **`[0.3333333333333333, 2.5]`** |
| `mean_score.resample_draws` | `2000` | **`1998`** — two draws held no scored unit and are dropped as degenerate |
| `score` (the recorded column) | `1.5`, `n.completed 4`, `ci95 [-0.5542602567605206, 3.5542602567605206]` | **every key unmoved** |

And from the scoping's two-condition Holm fixture, dated `5ee3a0c` and **to be re-measured by the
plan rather than copied**: `vs_baseline…n_paired` 4 → 6, the two metrics' `correction_level` swapping
`0.025`/`0.05`, and a purely numeric column's `ci95_corrected` moving in its last digits because Holm
ranks on the point estimate over half the raw `ci95` width and the *other* metric's width changed.

**Three things newly stop running.**

1. A template's `aggregate` returning a key that collides with a **non-numeric** recorded column
   loses its whole `derived` mapping and earns `W-STATS-AGGREGATE-FAILED` · `E-STEP-KEY-COLLISION`,
   where today both are published under one name (Decision 8).
2. A step recording a non-numeric column named `by` loses that step's `report_by` strata and earns
   `W-STATS-STRATUM-SHADOWED`, where today the strata are published silently (Decision 9).
3. A template's `aggregate` that assumes every row carries its numeric column now meets rows that do
   not and may raise — contained, costing that step's `derived` mapping (Decision 1's cost).

**Nothing is retired**, and one new warning is minted (`W-STATS-REPEATS-DISAGREE`, Decision 3).

**Cost if the ruling is wrong.** Two runs of the same config, over the same data, with the same seed,
on either side of this slice publish different numbers in `aggregated`. `code_hash`,
`parameters_hash` and `input_manifest_hash` are all `identical` between them, so **`diff` reports no
row that points at the change.** The one row that does move is `uv.lock` — verified: `cli.py` writes
`provenance.environment.uv_lock_hash` and `diff.py`'s `ROW_LABELS` holds a `uv.lock` row reading
exactly that key — and it moves only because upgrading `publishable` is what delivered the new
behaviour. So the honest statement is: **the change is visible as a dependency change and is not
visible as a statistics change**, and a reader comparing two runs across the upgrade must read the
`uv.lock` row as covering it.

**Why ship it anyway.** The alternative is a published metric that contradicts its own column at
exit 0 with no diagnostic, reachable from a config that validates clean and from the step
`publishable init` generates. *No diagnostic is the only one of the options that cannot be right.*
The distinction the controller adopted on H5a — *H5a refuses corrupting input; H5b changes what an
existing key may contain* — is the one this slice sits on, and the scoping measured that it changes
what existing keys **report**, not merely what they may contain. That is the sentence a reviewer
should hold this design to.

---

## What this slice refuses to build, each with its route and owner

| Refused | Route and owner |
|---|---|
| A non-numeric **metric** in `aggregated` (a modal label with a `basis` and a `ci95: null`) | **Refused by design, here.** § Statistical reporting defines a metric block around a number and an interval; `report` renders any entry structurally and `study`'s thin-metric floor walks anything carrying `basis` (both measured by the scoping), so a string wearing that shape would be rendered and floor-checked as a metric. A domain that wants one returns an `Estimate` from a `summary` step |
| Loosening `E-STEP-RETURN-TYPE` for a genuinely mixed `.parquet` column | **Decision 11 decides it: no.** The residual — whether the write should ever be forgiving — is **unassigned with a reason**: no remaining slice (H6, H9, H3c-3's remaining 14) has the write side as its surface, and H5a is merged. Filed by task 15 |
| A rule for a *disagreeing* non-numeric column other than `None` (`first`, `mode`) | **Refused, Decision 2.** The declared route is `data.units.measurements` with a `collapse` rule |
| Changing `STARTER_STEP` | **Refused, Decision 12** |
| A hash over `aggregated` or over `units.parquet` | **Out of scope, named so it is not folded in.** A new `provenance` key and an argument against § Three hashes — **H6's** boundary if anyone wants it. Nothing in this slice moves any hash |
| Folds inside cells | **H3c-3.** Its contact is `collapse_repeats(…, fold_members=…)`, and this slice changes what that function **returns**, not how it intersects. H3c-3 is cheaper after H5b than before it (the 20 annotation sites are swept here), and the fold path is **pinned** by this slice rather than assumed — Fixture K |
| A warning for a unit admitted with an entirely non-numeric row | **Refused, with the reason.** After Decision 1 nothing is lost: the unit is in the table, in `n.completed`, and in `units.parquet`. A warning for the ordinary case would fire on every run of the scaffold |
| A new error or warning code for the contrast guard | **Refused, Decision 7.** Unreachable from a validated config; a § Errors row that can never fire misleads |
| `BaseTemplate.field_convention`, declarable on a shipped class and read by nothing | **Not H5b's.** Named because § Misreadings calls it the sole remaining example of an unbuilt reader of a shipped surface, and an implementer reading `units.py` will meet it |
| `.csv`'s null encoding (H5a's appended correction) | **Unassigned, already filed.** Not this slice's surface |

### The collisions that stay exactly where they are

On H4b-2's precedent, in writing, so no reviewer has to wonder whether they were folded in:

- **The `report_by`-under-`resample` gap** — converted 2026-08-18 to a documented permanent
  limitation, live on **seven** of the analysis' nine configs. `stats.py` is this slice's surface and
  the gap lives there; **it is not folded in**, and the § Executability entry repeats the row
  unchanged.
- **`repeat_spread`'s `std: 0.0`** — RE-OWNED 2026-08-21 to unassigned. Untouched. This slice adds a
  function *beside* `repeat_spread` (Decision 3) and changes nothing inside it.
- **A degenerate stratum's missing console warning** — its filing still reads "H4 Statistics", an
  owner that no longer exists. **This slice does not correct that ownership and does not silently
  inherit it**; the scoping's ruling stands: it is for whoever next sweeps that file.
- **H3c-3's `fold_members`** — named above, pinned, not folded in.

---

## What each change makes reachable, and which batch pins it

Two shipped behaviours go live at task 4 and their pins would otherwise sit two batches later, where
the collapse batch's green suite would be no evidence about either. This is the
interaction-between-batches failure H7d Part B recorded twice, and it is why this table is in the
design rather than left to the plan.

| Change | What it makes reachable, with no further code | Pinned in |
|---|---|---|
| Task 4 (carriage + admission) | `E-STEP-KEY-COLLISION` for a derived key against a non-numeric recorded column — **measured: raises today given the wider `collapsed`** | **the same batch** (Fixture E) |
| Task 4 | `cli.py`'s second empty-level gate, whose `if True:` mutation survives the whole suite today | **the same batch** (Fixture H) |
| Task 4 | `E-STEP-COLUMN-UNKNOWN` stops firing for a carried column | the same batch (Fixture B), pinned both directions in the pins batch |
| Task 4 | draws that hold no unit carrying a metric's column become degenerate (`resample_draws` 2000 → 1998) | the same batch (Fixture A) |
| Task 5 (the collapse rule) | a `None` cell in `collapsed`, and Decision 3's warning | the same batch (Fixtures C, D) |
| Task 7 (the contrast filter) | nothing new — it guards an unreachable route | its own batch, direct-call plus an end-to-end control (Fixture G) |

**Consequence for the plan: tasks 10 and 11 of the scoping's list keep their document and record
halves in a later batch, and their *pins* move into the collapse batch.** The design says so here so
the dispatch cannot drop it — *a ruling that overrules a brief has to reach the brief.*

---

## The discriminating fixtures

**A fixture is a claim too.** Every literal below was computed by running something, and the
computation is named. Six fixtures in one earlier slice failed their own constraints, every one caught
by computing rather than by reading.

### Fixture A — the moving run, key by key

Six units, `seed × 2`; units 0–3 record `{"score": float(i), "valid": True}`, units 4–5 record
`{"valid": True}`. Template `aggregate` returns `n_rows` (row count), `n_valid` (rows whose `valid` is
`True`) and `mean_score` (mean of the scores present, `None` when none are). `counts` from
`attrition`: `{resolved: 6, completed: 6, ineligible: 0, failed: 0}` — **computed, not written**
(probe `p3`). Every literal in § The behaviour change's table comes from `summarize_step` run over
both the today-shaped and the after-shaped `collapsed` at `seed=7, draws=2000` (probe `p4`), and the
test asserts them **against `summarize_step`'s own output**, not against a transcription.

Its load-bearing assertion is the one nobody would think to write: `mean_score.value` is `1.5` in
**both** states. A fixture in which every number moves cannot tell "the table widened" from "the
metric changed".

### Fixture B — the scaffold's own run, end to end

`publishable init`'s `STARTER_STEP` unmodified, six units. Asserts `aggregated.step01_summarize_units
== {}` (unchanged before and after — Decision 12), and, with a project-local template whose
`aggregate` returns `{"n_present": float(len([r for r in units if r.get("present")]))}`, that the
value is **6.0** and that no `W-STATS-AGGREGATE-FAILED` appears. Today the same project publishes
`0.0` at exit 0. The control that can fail: a template reading `units.absent_column` still earns
`E-STEP-COLUMN-UNKNOWN` under `W-STATS-AGGREGATE-FAILED`.

### Fixture C — repeats that disagree on a non-numeric column

One unit, two repeats, recording `{"flag": True}` and `{"flag": False}`. Asserts
`collapsed["p0"]["flag"] is None` — the key **present**, the value `None` — and that
`W-STATS-REPEATS-DISAGREE` names `flag`. `values[0]` is `True`, so a mutant carrying the first value
gives `True`, which the assertion separates from `None`.

This is the replacement for `test_collapse_drops_a_bool_column_rather_than_averaging_it`, whose
assertion (`"flag" not in collapsed["p0"]`) pins the behaviour that is the defect. It is a **correct
move**, not a weakening, and it is named as one in the pin (arm B).

### Fixture D — repeats that agree on a recorded `None` (the control Decision 3 rests on)

Two repeats both recording `{"valid": None}`. Asserts the cell is `None` **and that
`W-STATS-REPEATS-DISAGREE` does not fire** — asserted on `capsys`' stderr stream, not on an exit
code, because *when you assert an absence, assert it on the stream the thing writes to*. This is the
fixture that makes the difference between Decision 3 and the version this design rejected: under the
rejected `None`-as-signal rule it fails.

### Fixture E — the collision, driven from the collapse's own output

`collapse_repeats` over `ExecutionResult`s recording `{"score": float(i), "r": True}`, its return fed
to `summarize_step(…, derived={"r": 1.0})`. Asserts `E-STEP-KEY-COLLISION`. The existing test's
fixture is replaced by this one and its assertion is unchanged — **the seam becomes reachable rather
than being re-described.** Plus the end-to-end arm: a real run whose template returns a colliding key
publishes no `r` metric, warns, and **writes its `run.yaml`**.

### Fixture F — a non-numeric `by` column, with the numeric arm as its can-fail control

A step recording `{"pred": float(i), "by": f"lvl{i % 2}"}` with `report_by` declared. Asserts
`W-STATS-STRATUM-SHADOWED` fires, `"by" not in aggregated[step]` (a non-numeric column has no metric
block to keep) and no strata block. The control is the two **existing** tests over
`_RECORDS_A_BY_COLUMN_STEP`, which records `float(i) * 2.0`: they must stay green, asserting
`aggregated[step]["by"]["value"] == 39.0`. **Grepped: no test in the suite records a non-numeric
`by`**, so this arm exists nowhere today.

### Fixture G — the contrast guard, both ends

*Direct call:* `_comparison_step_blocks` driven with an `aggregated` carrying a `str`-valued metric
key and a `collapsed` carrying `str` values for it. Asserts it returns without raising and publishes
no entry for that key. Today that call is the measured `TypeError`.
*End to end (the honest half):* a real run recording a non-numeric column asserts `run.yaml` exists,
`vs_baseline` holds no entry for the column, and exit is `0` — which is the claim about production,
stated separately from the direct-call claim about the guard. The direct-call arm's docstring says in
so many words that it drives a state production cannot reach and why the guard exists anyway.

### Fixture H — the stratum's empty level

A run with `report_by` on an attribute one of whose levels contains **only** units whose every
recorded value is non-numeric, and a template returning one derived metric. Asserts that level is
**absent** from the `by` block while the other level is present. Under `if True:` the empty level
appears carrying nothing but a derived value over a table with no numeric column — the case the gate's
own comment describes and that nothing could reach before task 4.

### Fixture I — where the projection sits

`summarize_step` over the Fixture A table with a derived metric that reads the bool column. Asserts
`ci95[0] <= value <= ci95[1]` and, concretely, `value == 6.0` with `ci95 == [6.0, 6.0]` and
`resample_draws == 2000`. Computed both ways (probe `p5`): the full table gives `(6.0, 6.0)`, a table
stripped of the bool column gives `(0.0, 0.0)` — a point estimate outside its own interval.

### Fixture J — `report` and `study` as readers of `aggregated`

The Fixture A run's `run.yaml` rendered through `report`, and a two-member bundle through `report
study.yaml`. Asserts the condition table holds `n_valid`, `n_rows`, `mean_score` and `score` and **no
row for `valid`**, and that `study`'s thin-metric floor sees the same four entries. This is the
additive-only half of the ruling for the shipped commands, and the scoping's own instruction was that
it *must be pinned rather than assumed*.

### Fixture K — the fold path

The existing `fold_members` collapse fixture re-asserted over a roster where one fold's units record
only a bool: each unit is admitted **within its own fold** and `handed_to`'s intersection is
unchanged. The claim is that Decision 1 changed what the function returns and nothing about how it
intersects — H3c-3's contact point, pinned rather than named.

---

## The mutations, each with the assertion that catches it and two branches that can differ

**Checked in advance: for each, the mutated and unmutated code produce different observable results.**
This repo has shipped mutations that were what the code already did, and mutations whose two branches
could not differ.

| Mutation | Caught by | The two branches differ because |
|---|---|---|
| 1. Restore `or not _is_numeric(value)` in `collapse_repeats`' inner loop | Fixture A's `n_valid.value` (`6.0` vs `0.0`) and Fixture B's `n_present` | measured today: that exact input yields `{}` for a bool-only roster and drops two units in Fixture A's |
| 2. Admit only units with at least one **numeric** value (keep the carriage, drop the admission) | Fixture A's `n_rows.value` (`6.0` vs `4.0`) and `mean_score.n.completed` | the two rules differ exactly on units 4–5, which carry a value and no number — the case a single-arm fixture would miss |
| 3. Carry `values[0]` instead of `None` for a disagreeing column | Fixture C's `is None` | `values[0]` is `True` there, by construction |
| 4. Omit the key entirely for a disagreeing column | Fixture C's key-presence assertion **and** a second arm of Fixture E whose colliding column disagrees across repeats | omission removes the column from `summarize_step`'s `columns`, so the collision stops firing — two assertions because the cell-level one alone leaves the collision consequence unpinned |
| 5. Project non-numeric columns out of `collapsed` at `summarize_step`'s **input** | Fixture I's `value` -inside- `ci95` assertion | measured: `[6.0, 6.0]` against the full table, `[0.0, 0.0]` against the stripped one |
| 6. Delete `_is_numeric` from the paired arm's `col_keys` comprehension | Fixture G's direct-call arm | measured: the unguarded subtraction raises `TypeError` on `str` operands |
| 7. Delete it from the unpaired arm's `of_values`/`against_values` | Fixture G's unpaired arm (a `sweep.groups` axis) | the two arms are separate comprehensions, so a mutation in one must be caught by an assertion on that one — this is why the fixture has both |
| 8. Point Decision 9's `by` test back at `step_summary` | Fixture F's warning assertion and its no-strata assertion | measured by the scoping both ways: the non-numeric column never reaches `step_summary`, so the mutant is silent |
| 9. Widen Decision 9 to suppress a **numeric** `by` column's metric block | pin arm C — the two existing tests asserting `aggregated[step]["by"]["value"] == 39.0` | the numeric arm keeps its metric block; a widened guard removes it |
| 10. Replace `cli.py`'s second empty-level gate with `if True:` | Fixture H's absent-level assertion | measured at `5ee3a0c`: this mutation leaves the **whole suite** green today. It stops being blind at task 4, which is the point of the reachability table |
| 11. Delete the `W-STATS-REPEATS-DISAGREE` call site | Fixture C's warning assertion, asserted on stderr with the column name in it | the message names `flag`; nothing else in that run's output does — checked against the run's other diagnostics rather than assumed |
| 12. Make Decision 3's new function answer from the collapsed cell rather than from the rows | Fixture D | a recorded `None` is indistinguishable from a disagreement at the cell, which is the whole ground for Decision 3 |
| 13. Restore `summarize_step`'s deleted docstring clause | nothing — **named blind in advance** | a docstring has no behaviour. Its replacement is mutation 4's second arm, which pins the property the clause was describing, and the batch review reads the sentence against the code |

**Two more named blind in advance, each with its replacement.**

- **The annotation sweep (Decision 5)** has no observable behaviour; `uv run mypy` is its check, and a
  union-versus-`Any` mutation could not produce a different runtime result. Replacement: mutation 6,
  which pins the runtime narrowing the annotation stopped expressing.
- **Emptying the `_is_numeric` gate in `summarize_step`'s column loop** is *not* blind and is worth
  naming so nobody assumes it is: it publishes the non-numeric column as a metric, caught by Fixture
  A's key-set assertion and by Fixture J's `report` row assertion.

---

## The guard pin, captured before anything moves

Four arms, captured in the **first** batch, before any code task runs. **Two arms have no authorized
editor, so a passing arm is itself the proof.** This device is the answer to five slices weakening a
pin quietly, and to the two that pinned one list twice and edited both.

| Arm | The claim | Sole authorized editor | State specified in advance |
|---|---|---|---|
| **A** | A run with **no non-numeric recorded column anywhere in it** publishes a byte-identical `results` block: captured as a literal snapshot of `run.yaml`'s `results` mapping for a two-condition, two-seed, Holm-corrected run over 40 units with one numeric column and one derived metric | **NONE** | unchanged. A passing arm after every task is the proof that the numeric-only path did not move |
| **B** | The run that **does** move: Fixture A's, with every moving key and both its values in the docstring | **task 4 only** | the "After" column of § The behaviour change's table, literal for literal. Task 4 flips the four literals named there and nothing else; any other edit to this arm is a finding |
| **C** | The **numeric** `by` column keeps its metric block and its warning: `tests/test_cli.py::test_a_recorded_column_named_by_keeps_its_metric_and_warns` and `::test_a_recorded_by_column_warns_even_with_no_report_by_declared`, asserting `value == 39.0` | **NONE** | zero lines changed. The batch review that lands Decision 9 checks `git diff` over both test bodies and reports the line count |
| **D** | `E-STEP-COLUMN-UNKNOWN` still raises for a name **no** row holds, and the derived-key collision still raises for a **numeric** recorded column | **NONE** | unchanged. These are the two behaviours the slice narrows *around* and must not narrow *away* |

**Arm A's claim is stated twice on purpose, because the loose version is what the scoping falsified.**
The rule is: identity holds when no non-numeric column exists **anywhere in the same correction
family**, because Holm ranks across the family and one metric's width moves another's corrected
interval. The **fixture** takes the safe framing — none anywhere in the run — so that a later fixture
edit cannot quietly turn the rule into the false loose one. Both sentences are in the docstring,
labelled *the rule* and *what this fixture pins*.

---

## The § Errors and § Warnings work

**One row per code, covering every emit site.** That shape was the whole-branch Major on two of H8's
sub-slices and shipped twice inside a third.

| Code | Work | Sites |
|---|---|---|
| `W-STATS-REPEATS-DISAGREE` | **minted in § Warnings core reports before any code** (Decision 3), naming the step, the condition, the column and the unit count | one — `cli.py`'s aggregation phase. The stratum loop re-filters the same `collapsed` and does not collapse again, so there is no second site; this was established by reading the loop, then confirmed by `grep -n 'collapse_repeats(' src/publishable/*.py` → **one** production call site |
| `W-STATS-STRATUM-SHADOWED` | its § Warnings row reworded to cover a column that has **no** `aggregated` entry to keep, and § Steps and artifacts' reserved-`by` paragraph checked against it | one site, two conditions (Decision 9) |
| `E-STEP-KEY-COLLISION` | **no row change.** § Errors already names *"a derived key against a recorded column"* and already says this site is re-reported as `W-STATS-AGGREGATE-FAILED` rather than raised. No emit site is added — the same site sees a wider input | unchanged; task 10 asserts the row against the code rather than editing it |
| `E-STEP-COLUMN-UNKNOWN` | **no row change.** The row describes *"a column no row of the unit table holds"*, which stays exactly true as the set of held columns widens | unchanged; pinned both directions |
| `E-STEP-RETURN-TYPE` | **no row change** (Decision 11 does not loosen the write) | unchanged |

---

## The § Executability entry this slice owes

Appended to [the feasibility analysis](../../feasibility-llm-growth-studies.md) § Executability on
this build, dated to H5b's own merge and pinned to its commit, and it **repeats the four-row table
with row 4 re-derived and the other three character for character**:

- **Row 4 goes `1 → 0 → 1`**, with the re-derivation in the entry's own prose (Decision 14): the
  named core-side dependency is a non-numeric recorded column vanishing between the write and
  `aggregate`; it meets **all nine** configs, since all nine record through one request step whose
  payload carries `valid`, `invalid_reason` and `finish_reason`; and this slice closes it.
- **Rows 1, 2 and 3 are repeated unchanged** — 8 of 8 validating clean, 0 blocked on `io.reuse_from`,
  **7** meeting the `report_by`-under-`resample` gap. Row 3 is not this slice's and is not folded in.
- **The analysis-side `truth` collision is named as an analysis-side obligation** that changes no
  core-side count, the treatment the H8a entry gave E3's `summary`-step obligation.
- **No fifth number is minted**, and the entry says the two things the corrections require: do not
  quote a single figure for this analysis' executability, and name the dependency.

---

## The records this slice owes

`spec-defects.md` is a live list, so a closed gap is struck rather than left to mislead; every other
tracked record is appended to, never retro-edited.

| Record | Work |
|---|---|
| *a unit whose only recorded column is non-numeric is silently dropped* (Owner H5b) | **struck**, with which of its four options was taken and why, and with the fourth question it did not name — `paired_keys` — answered (Decision 6) |
| *the `aggregate` table omits declared unit attributes and non-numeric columns* (RE-OWNED to H5b) | its non-numeric half **struck**; the attributes half was already closed |
| *the second empty-level gate in `cli`'s stratum loop is unpinned* (RE-OWNED to H5b) | **struck**, naming Fixture H, and correcting the entry's own account of *why* it was unreachable |
| **Unfiled item 1** — the mixed `str`/`float` column question H5a's design says is *"Filed, owner H5b"* with no entry | **discharged by Decision 11 in `reference.md`**, and the residual write-side half filed **unassigned with a reason**. The design says plainly that H5a's line pointed at nothing: *a design line saying "Filed" is not a filing*, second instance in one slice pair |
| **Unfiled item 2** — a derived key colliding with a non-numeric recorded column is not refused | **closed by Decision 8**, so it is recorded as *found and closed in the same slice* rather than filed live |
| **Unfiled item 3** — a non-numeric recorded `by` column draws no `W-STATS-STRATUM-SHADOWED` | **closed by Decision 9**, recorded the same way |
| The spine's 2026-08-22 amendment (§ The hardening slices) | **append a correction, do not edit**: its H5b row says "(10)" and this slice is **15**, and its behaviour-change sentence has already been corrected once the same day. The append records the count and that the exposure is what § The behaviour change here enumerates |
| `CLAUDE.md`'s order line | H5b removed from *remaining*; H6, H9 and H3c-3's remaining 14 stated as what is left |
| `cli._attributed`'s docstring | two falsified grounds **deleted** (Decision 9) |
| The three shipped test docstrings the scoping measured | re-derived: `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts` says `summarize_step` drops the bool column — it never sees it; `test_a_baseline_sweep_reports_a_delta` names `_is_numeric` in the wrong function; `test_an_unclustered_resampled_contrast_draws_what_it_always_drew`'s claim is true and stays. **Grepped, all three exist at the names the scoping gave** (`tests/test_cli.py`) |

---

## Task decomposition — 15, and the batches

The scoping's 15 stand; what moves is where two of them are **pinned** (§ What each change makes
reachable). Order within a batch is the order listed.

| Batch | Tasks | Contents | What its review must look for |
|---|---|---|---|
| **1 — the documents, the mint, and the pin** | 1, 2, 3 | The guard pin's four arms captured **before anything moves**; § Templates and § Statistical reporting (Decision 10); § The per-unit tables' routed question decided (Decision 11); `W-STATS-REPEATS-DISAGREE` minted (Decision 3) | Does any new sentence claim a behaviour the code will not have after batch 2? Does the pin have a named sole editor per arm, **two arms with none**, and arm A's rule and fixture framing stated as two things? Is the mint's row true of the site batch 2 will add? Mechanical pass on every `reference.md` edit |
| **2 — the collapse. THE BEHAVIOUR CHANGE** | 4, 5, 6, and the pins for 10 and 11 | Carriage and admission with the 20 annotation sites (Decisions 1, 5); the across-repeats rule reusing `apply_rule`'s constant shortcut (Decision 2); the disagreement function and its warning (Decision 3); `summarize_step`'s deleted clause (Decision 4); Fixtures A, B, C, D, E, H, I, K; mutations 1–5, 10–12 | **A real-command review**: run the console script end to end on Fixture A's and Fixture B's projects and read `run.yaml` key by key against § The behaviour change's table — not `validate`, not a direct call. Then: is arm B's edit exactly the four literals specified in advance? Is arm A still passing untouched? Are the collision and the empty-level gate pinned **here** rather than promised to batch 3? Does the ruling's enumeration match what the run actually printed? |
| **3 — the guards and the namespace** | 7, 8, 9, 10, 11 | The contrast filter (Decision 7); the `paired_keys` ruling documented (Decision 6); the `by` arbitration and `_attributed`'s deleted grounds (Decision 9); the collision test made real (Decision 8); the empty-level gate's document and record halves | Arm C's `git diff` line count over the two existing `by` tests — **report the number**. Does the direct-call arm of Fixture G say in its own docstring that it drives an unreachable state, and does the end-to-end arm carry the production claim? Were the two `_attributed` grounds **deleted** rather than rewritten? |
| **4 — the pins and the readers** | 12, 13, 14 | `E-STEP-COLUMN-UNKNOWN` both directions; the silent case's discriminating test; `report` and `study` pinned (Fixture J); the three shipped docstrings re-derived | Does any assertion here pass if the behaviour is neutered? Grep every claim the briefs make about other tests before repeating it, and **report what was grepped** |
| **5 — the records** | 15 | Strikes, filings, the § Executability entry, the spine correction, `CLAUDE.md`'s order line | **This batch gets a full review, not a skim.** Twice a controller ran a final batch straight into the whole-branch gate, and the second time three of four Majors lived in it. Check every struck entry against the code, every "filed" against the file, and the § Executability table's three unchanged rows character for character |

**Every batch gets a review.** Batch 2 is the behaviour change and gets the real-command review.

**Should it split? No**, and the scoping's grounds hold after this design: tasks 4 and 6 would land in
different slices with a half-changed `collapsed` between them, and § The behaviour change's argument
has to be made **once**, over the whole set of moving keys, or it is not an argument.

---

## What could not be measured, and what this design assumed

- **The two-condition Holm half of § The behaviour change** is the scoping's measurement at `5ee3a0c`,
  not this pass's. The plan **re-measures** it for pin arm B rather than copying the literals; if the
  correction-level swap does not reproduce, arm B's docstring is what has to change, and the
  discrepancy is a finding rather than a fixture repair.
- **The nine configs' real behaviour**, because neither `growth_screen` nor `publishable-llm` exists
  to install. Decision 14 rests on the payload and the attribute list quoted from the analysis, and
  says so.
- **A `measurements.parquet` written by a real run**, so the interaction between Decision 2's
  repeat-level rule and a declared `data.units.measurements` collapse is reasoned from
  `collapse_measurements`' code and not observed. The two operate at different levels — measurements
  collapse inside a unit's execution, repeats collapse across executions — and Fixture K's fold arm is
  the nearest thing this design pins. **The plan should build one.**
- **Whether any project in the wild reads `aggregated` for a column this slice newly admits**, which
  is unknowable and is why § The behaviour change states the `diff` gap rather than claiming a
  mitigation.
