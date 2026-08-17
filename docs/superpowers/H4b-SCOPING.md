# H4b scoping — weights and clusters through contrasts, and retiring `E-DATA-WEIGHT-CONTRAST`

Read-only measurement against `main` at `b65ab91`, on 2026-08-17. This re-measures the H4b row of
`docs/superpowers/H4-SCOPING.md` § 6, taken at `cb96c7d`, and the H4b claims of
`docs/superpowers/H4a-SCOPING.md`, taken at `eaf3605`. **Both predate H3d, H7c, H7b Part A and H7b
Part B.** Every identifier below was grepped, read or probed at `b65ab91`; nothing is carried.
Where this document contradicts either predecessor it says so and shows the command; where it
confirms one, it says that too.

**Verdict: 22 tasks**, against the charter's **14**. Recommendation: **split it two ways on the
payoff seam** — weights (3 of 9 configs) and clusters (0 of 9) — which is what H4-SCOPING itself
proposed as its fallback and which this measurement upgrades to the primary recommendation.

**Baseline at `b65ab91`:** `uv run pytest -q` → **2118 passed, 1 skipped, 2 xfailed**, 123 s.

**The headline, measured rather than asserted:** H4b retires **one refusal that 3 of 9 configs
hit**, and **six of nine have no remaining core-side blocker** — E1, E2, E5 unchanged from H7b
Part B, and C1, C2, C3 newly, measured as `E-DATA-WEIGHT-CONTRAST` being the *sole* error on their
shapes (§ 6.1). **The executable count stays at three**, because C1–C3's `io.reuse_from` dependency
is unsettled and no config can settle it. The two figures are the same distinction H7b Part B's own
§ 8 drew between its cell wording and its prose, and they must not be collapsed in either direction.

---

## 0. Executive summary — the seven things that change what H4b is

1. **The three functions the refusal message names are not on the payoff path.** The published
   message and the `reference.md` row both say the refusal lifts "once the paired estimators take
   weights", naming `paired_t_over_units`, `paired_delta_of_derived` and
   `paired_percentile_of_derived`. **C1, C2 and C3 all declare `statistics.resample`**, so
   `resample_columns` is `True`, so a column contrast is routed through
   `paired_percentile_of_derived` with a `_column_mean` closure and its `Member` carries `pool`
   rather than `diffs` (`cli.py`: `corrected_from_pool = is_derived or resample_columns`).
   **`paired_t_over_units` is therefore never called on C1–C3, raw or corrected**, and the derived
   half is settled one level down (§ 2.1). The weighted work that makes the measured payoff run is
   a **closure change plus a record change**, not an estimator change. A spec written from the
   charter or from the refusal message gets this backwards. § 2.
2. **A weighted contrast has no `method` string anywhere in the four documents.** Swept by
   spelling over the four documents by name:
   `grep -ohE '\bweighted_[a-z_]+|[a-z_]*paired_[a-z_]+|percentile_[a-z_]+|welch_[a-z_]+|t_over_[a-z_]+' README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md | sort | uniq -c`
   → sixteen distinct spellings, **no `weighted_paired_*` among them**. § Statistical reporting
   names the weighted per-condition forms explicitly (`weighted_t_over_units`,
   `weighted_t_over_units_clustered`) and gives the clustered contrast forms a **suffix rule**; it
   gives weights on a contrast neither. H4b must mint the naming before it emits one. § 3.
3. **The contrast record has nowhere to put `effective` or `clusters`.** § Weighted samples says
   Kish's size "joins the three-part `n` as `effective`" and § Clustered units says the same of
   `clusters`; a contrast entry carries a **scalar** `n_paired` and no `n` mapping at all
   (`reference.md` § Contrasts' own fenced example, and `_comparison_step_blocks`' literal
   `{delta, basis, paired, method, n_paired, ci95, cohens_d, correction}`). H4-SCOPING's task item
   *"`effective`/`clusters` beside `n_paired`"* is an **undocumented invention** — no sentence in
   the four documents licenses it. § 3.
4. **`correction._corrected_bounds` re-runs an unweighted construction on weighted evidence, and
   nothing would fail.** It calls `paired_t_over_units(member.diffs, confidence=1.0 - level)`
   directly, and `Member` has no weights field. A weighted column contrast on the **non-`resample`**
   path would publish a weighted raw `ci95` beside an unweighted `ci95_corrected` — precisely the
   failure `Member.__post_init__`'s own docstring names for the pool/diffs mix, one level over. § 4.
5. **`resample.stratify_by` is honoured for every per-condition metric and silently dropped for
   every contrast — and it is unfiled.** `paired_percentile_of_derived` is the **only** percentile
   construction in `stats.py` with no `strata` parameter (`grep -n 'strata' src/publishable/stats.py`
   → four `strata:` parameters, at `:493`, `:682`, `:919`, `:1510`; `:1136`'s signature has none),
   and no contrast call site passes one. **All three payoff configs declare
   `stratify_by: [consensus_label, count_stratum]`.** `grep -n 'stratify_by' docs/superpowers/spec-defects.md`
   ∩ *contrast* → **zero hits**, against a control of **35** `stratify_by` mentions in that file.
   This is the `hash_index`-shaped pair for this slice. § 7.
6. **`E-DATA-CLUSTER-CONTRAST`'s row cannot be made true by H4b.** It says "**none of those five
   constructions exists in this build**". Two of the five are unpaired forms — `welch_*_clustered`,
   `unpaired_percentile_*_clustered` — which `E-DATA-ALLOCATION-CONTRAST` refuses independently and
   which **H4c** owns. So the count cannot be walked down to zero; the row must be rewritten to
   **enumerate** which forms exist. That converts a self-maintaining claim into a maintenance
   obligation, which `CLAUDE.md` § Habits warns against, and it is unavoidable here for the reason
   stated. § 5.
7. **The brief's own count is the spelling-count substitution.** It says *"I count 5 in
   `validate.py` and 3 rows in `reference.md`."* Measured: `grep -rn 'E-DATA-WEIGHT-CONTRAST'
   src/publishable/*.py` → **five hits, one of which emits** (`validate.py:5016`); the other four
   are a docstring and three comment lines. `grep -n 'E-DATA-WEIGHT-CONTRAST' docs/reference.md`
   → **three hits, one of which is the code's own row** (`:524`); the other two are
   `E-DATA-ALLOCATION-CONTRAST`'s and `E-DATA-CLUSTER-CONTRAST`'s rows *citing* it. There is also
   **one § Validation row** the brief does not count (*Weighted deltas aren't computed*). So the
   real shape is **1 emit + 1 § Errors row + 1 § Validation row + 2 sibling rows to re-word**. § 1.

---

## 1. Every site of `E-DATA-WEIGHT-CONTRAST`, enumerated by reading then confirmed by grep

Read `validate._check_sweep` in full, then confirmed. `§ Errors carries one row per code, not per
emit site` — so the unit of work is every site that raises *or* reports it.

| Site | Kind |
|---|---|
| `validate.py:5016`, in `_check_sweep` | **The one emit.** Guard: `comparisons > 0 and isinstance(weight_by, str) and weight_by` |
| `validate.py:5059`, `:5098` | Comments in the two sibling guards, both citing it as the precedent |
| `validate.py:3470` | `_check_unimplemented`'s docstring, naming it in the combination-refusal family |
| `validate.py:4002` | A comment citing it as the placement precedent |
| `reference.md:524` | **Its § Errors row** — the one line whose final cell is the code itself, which is what tells a row from a citation. Located by anchoring a grep on that cell at end-of-line; it returns this line alone |
| `reference.md:329` | **Its § Validation row**, *Weighted deltas aren't computed*. Located by reading the table, not by grepping the code — the row names no identifier |
| `reference.md:484`, `:514` | `E-DATA-ALLOCATION-CONTRAST`'s and `E-DATA-CLUSTER-CONTRAST`'s rows, each contrasting its own read-per-comparison or read-per-family behaviour against this one. **Both must be re-worded, neither deleted** |
| `tests/test_validate.py:7316–7390`, `:7537`, `:7870` | Five tests plus two comment blocks |

Can-fail control on the same file list: `grep -rnc 'E-DATA-CLUSTER-CONTRAST' src/publishable/validate.py`
→ **4**, a different number from the same shape of sweep.

**The guard reads the resolved family, not the declaration — re-verified by probe, not carried.**
§ 6's probe run includes the two edges the guard's own comment argues for: a bare `sweep.baseline`
with no axis beside it stays legal under a weight, and a declared contrast over a sweep with no
baseline is caught. Both hold at `b65ab91`.

### The complete set of things that must exist for it to retire

Re-derived at `b65ab91`, not carried from H4-SCOPING's one-line answer:

1. A decision on the **derived** half — weighted estimator, or record-only (§ 2.1). **Settled by
   the code, needs filing.**
2. A `method` string vocabulary for a weighted contrast — **absent from all four documents** (§ 3).
3. A record shape: `weighted_by` on a contrast entry, and somewhere for `effective` — **absent**
   (§ 3).
4. The weighted **closure** on the `resample`-declared column path — **the payoff path** (§ 2.2).
5. A weighted `paired_t_over_units` for the non-`resample` column path — **absent**.
6. `weights` reaching `_compute_vs_baseline` / `_compute_declared_contrasts` /
   `_comparison_step_blocks` — **none of the three takes it today**.
7. A weighted corrected bound: `Member` weights, or a forced pool (§ 4) — **absent**.
8. A weighted `cohens_dz` — **documented, absent** (§ 7).
9. Kish over the **paired intersection**, not over the condition (§ 8's trap).
10. The two sibling rows re-worded and the § Validation row struck (§ 1).
11. The feasibility analysis's § Executability **re-dated**, not edited (§ 6).

**Two of eleven are decisions, six are absent code, three are documents.** None was done by H3d,
H7c or H7b.

---

## 2. What a weighted contrast actually needs — and the payoff path the charter misses

### 2.1 The derived half is settled one level down. **H4-SCOPING § 4.3 is CONFIRMED at `b65ab91`.**

`stats.summarize_step`'s docstring, read in full rather than grepped:

> A DERIVED metric is not weighted here, and that is the same document's other half: core "computes
> weighted means for `basis: units` column metrics, hands the column to `aggregate` like any other
> attribute so a derived metric can weight itself". There is no per-unit vector to weight … so the
> weight column reaches `aggregate` as a unit attribute and the template decides; `cli.py`'s
> `_attributed` is what puts it there. **`weighted_by` and `effective` still travel beside a derived
> metric** — the declaration is true of the run either way.

That argument transposes onto the paired derived forms unchanged: their draws are uniform over the
paired intersection and the weighting lives inside `aggregate`. And the mechanism is already wired
on the contrast path — `cli.py:2057` builds each resample callable as
`tmpl.aggregate(_attributed(units, attrs), cfg)`, so a **derived** contrast's `compute_of` /
`compute_against` already see the weight column as an attribute.

**So `paired_delta_of_derived` and `paired_percentile_of_derived` need no `weights` parameter**, and
two of the three functions the refusal message names are not touched at all. H4-SCOPING called this
"H4b's first task, not an observation" and asked that it be *settled and filed*. It is settled by
the code; the filing is still owed, and it narrows a **published refusal message** and a normative
§ Errors row, so it is a document task and not a note.

### 2.2 The payoff path is a closure, and the closure can reach the weights

All three C configs declare `resample`, so `resample_columns=True`, so a **column** contrast never
reaches `paired_t_over_units`:

```
cli.py:936    if resample_columns and n_paired >= 2:
cli.py:952        resampled = paired_percentile_of_derived(of_collapsed, against_collapsed,
                      col_keys, _column_mean, _column_mean, seed, draws=draws)
cli.py:1014   corrected_from_pool = is_derived or resample_columns
```

`_column_mean` computes `sum(column) / len(column)` over the plain collapsed table. **Verified: the
construction preserves the unit key inside every draw** — `stats.py:1177–1178` builds each drawn row
as `{"unit": k, **of[k]}`. So a weighted `_column_mean` can look each weight up by `unit` and the
payoff path is **one closure change plus threading the mapping into
`_comparison_step_blocks`** — not a new parameter on the construction, and not a new construction.

**`_comparison_step_blocks` never calls `_attributed`**, so the collapsed table it hands the closure
holds recorded columns only; the weight has no route today by either spelling. The threading is the
task, and it is small.

### 2.3 What the invariant requires, item by item, against what exists

`CLAUDE.md`'s invariant, checked clause by clause:

| Clause | State at `b65ab91` |
|---|---|
| a contrast is over the **intersection of both sides' completed units** | **Built.** `stats.paired_keys`, narrowed by `units_matching(roster, comp.within)` |
| recorded as `n_paired` | **Built.** Scalar, in every entry |
| its interval is **its own construction**, never a difference of the two sides' | **Built and argued** in `paired_t_over_units`' docstring |
| `paired_percentile_over_units` **drawing once for both sides** | **Built** (H4a), and `paired_percentile_of_derived`'s docstring argues both failure modes |
| the `welch_`/`unpaired_` counterparts | **Absent.** An alternation grep for both stems over `src/publishable/` → three hits, **all prose**, two of them inside `E-DATA-ALLOCATION-CONTRAST`'s own message. **H4c's** |
| `weight_by` **weights an enriched sample's estimates** | **Built per condition only.** `weighted_t_over_units`, `weighted_t_over_units_clustered`, and `percentile_over_units{,_clustered}`'s `weights=` parameter |
| and **records `weighted_by`** | **Per condition only.** `cli.py:1421–1422` sets it on `weighted_beside` and `beside_n`; a contrast entry has no such key and `_comparison_step_blocks` takes no `beside_n` |

**H4a-SCOPING § 1.2's correction is re-confirmed and still matters:** the weighted *percentile*
forms are **not** missing — `percentile_over_units` (`:487`) and `percentile_over_units_clustered`
(`:674`) both take `weights: Sequence[Any] | None` and recompute the weighted mean per draw. Only
the **paired** side has no weighted form, and per § 2.2 the paired side's payoff case wants a
weighted closure rather than a weighted signature.

---

## 3. The naming and the record shape — both absent, both normative

**No `weighted_paired_*` spelling exists in the four documents.** § Statistical reporting handles
the three axes three different ways:

| Axis | How the document handles it |
|---|---|
| clustering, per condition | **Explicit rows**: `t_over_units_clustered`, `percentile_over_units_clustered` |
| weighting, per condition | **Explicit rows**: `weighted_t_over_units`, `weighted_t_over_units_clustered` |
| clustering, on a contrast | **A suffix rule**: "each takes a `_clustered` suffix and reads the cluster as the draw" |
| weighting, on a contrast | **Nothing.** No row, no suffix rule, no sentence |

The precedent is already in the record: `spec-defects.md`'s two **RESOLVED (H3b task 13)** entries
are *"The method table has no row for a clustered percentile"* and *"… no row for a weighted
clustered interval either"*. The same gap, on the contrast side, has never been filed. H4b mints the
vocabulary first and emits second, or it publishes a `method` string no document defines.

**And the record has nowhere for the sizes to go.** § Contrasts' fenced example is
`{delta, basis, paired, method, n_paired, ci95, ci95_corrected, correction, correction_level, family_size, family}`
— `n_paired` is a scalar, and the section argues *why* it is not the condition's `n`
("the condition-level `n` can't carry this, because it belongs to one condition and the contrast
spans two"). § Weighted samples' `effective` and § Clustered units' `clusters` both "join the
three-part `n`", which a contrast does not have. **So H4-SCOPING's *"`effective`/`clusters` beside
`n_paired`"* is a shape H4b must design and document, not one it can implement from a row. The
cross-document pass bites: § Contrasts' fenced example, § Statistical reporting's construction
tables, and § The two files' `run.yaml` example all move together.

---

## 4. The corrected bound — a weighted raw interval with an unweighted counterpart, and a green suite

`correction.py` imports `paired_t_over_units` at module scope and `_corrected_bounds` calls it:

```python
if member.diffs is not None:
    got = paired_t_over_units(member.diffs, confidence=1.0 - level)
    return None if got is None else (got.low, got.high)
if member.pool is not None:
    return interval_at(member.pool, 1.0 - level)
```

`Member`'s fields are `where, step, metric, delta, ci95, pool, diffs, declaration_index` — **no
weights**. `__post_init__` enforces exactly one of `pool`/`diffs`, and its docstring gives the
reason in exactly the terms that apply here: both set "would let `_corrected_bounds` silently take
the `diffs` branch and build a *t* interval as the corrected counterpart of a *percentile* raw one —
narrower or wider than the truth by construction, not by evidence".

**A weighted column contrast with no `resample` declared reproduces that fault one axis over**: a
weighted raw `ci95` and an unweighted `ci95_corrected` on the same row. Two remedies, and the
decision is H4b's:

- add a `weights` field to `Member` and thread it into `_corrected_bounds` — which reopens the
  exactly-one-of invariant's argument for a third field, or
- require a weighted column contrast to carry `pool` (i.e. force the percentile path under a
  weight), which makes weighting imply resampling and needs its own justification.

**Neither is visible to any existing test.** `Member`s are constructed at exactly one site
(`grep -rn 'Member(' src/publishable/*.py` → `cli.py:1016`, plus three `RepeatMember`/`RepeatLevel`
hits in `replication.py` as the control), and no test compares a raw to a corrected construction
under a weight, because the combination is refused today.

---

## 5. Clusters through contrasts — two constructions, not five, and why the row can't be counted down

`grep -rn 'paired_t_over_units_clustered\|paired_percentile_over_units_clustered' src/ docs/reference.md`
→ **exit 1**. Neither name exists anywhere, in code or in the documents: they are **derived from the
suffix rule**, not written down. H4-SCOPING listed them as though they were named surfaces; they are
not.

What a clustered contrast needs that an unclustered one does not, read off the suffix rule:

| Construction | Needs | Exists |
|---|---|---|
| `paired_t_over_units_clustered` | CR1 over the **differenced** values, df = clusters − 1, and a membership mapping | **No.** `paired_t_over_units(diffs, confidence)` takes a list and nothing else |
| `paired_percentile_over_units_clustered` | whole clusters drawn **jointly across both sides**, one draw for each | **No.** `paired_percentile_of_derived` takes no membership parameter — the same absence as its missing `strata` (§ 7) |
| `welch_t_over_units_clustered` | the arm-level values, cluster-robust | **No — and unreachable.** `E-DATA-ALLOCATION-CONTRAST` refuses every unpaired comparison. **H4c's** |
| `unpaired_percentile_over_units_clustered` | each side's own clusters | **No — same.** H4c's |
| a clustered draw for a **derived** metric | membership on `percentile_of_derived` | **No.** This is `E-DATA-CLUSTER-DERIVED`, raised at `stats.py:1900`, **run time and per condition** — not "clusters through contrasts" at all |

**So retiring `E-DATA-CLUSTER-CONTRAST` needs the two paired forms, and only because
`E-DATA-ALLOCATION-CONTRAST` stands.** A sequencing constraint the charter does not own: the charter
orders H4b before H4c, and nothing enforces it. **If H4c lands first or concurrently, the unpaired
clustered forms become reachable with nothing built.** State it in the design.

And the row's own sentence — "**none of those five constructions exists in this build**" — cannot be
made true by H4b, since two of the five stay absent. It must be rewritten to **enumerate** which
exist. `CLAUDE.md` § Habits is explicit that a self-maintaining claim is worth more than an
enumeration ("Rewriting a sentence when a table row was the thing that was wrong"), so this trade
has to be argued in the commit rather than made silently.

**`E-DATA-CLUSTER-DERIVED` must be assigned to a side by name.** It is run-time, per-condition, and
not a contrast at all. H4-SCOPING put it in H4b's cell without noticing; a two-way split has to say
which half owns it. Recommendation: the cluster half, because the construction it needs is the same
membership-aware derived draw.

---

## 6. `report_by`, the correction family, and the nine — measured by running `validate`

### 6.1 The probe

Run at `b65ab91` through `tests/test_validate.py`'s own `write_config` fixture over a 20-row
weighted, two-stratum table, with `statistics.resample: {method: bootstrap, n: 2000, stratify_by:
[consensus_label, count_stratum]}` — the C-configs' own block — and `correction: holm`. Probe file
created, run, and deleted; no tracked file was touched.

```
C1 weight+baseline+resample                -> ['E-DATA-WEIGHT-CONTRAST']
control: same, no weight_by                -> ['W-DATA-WEIGHT-UNDECLARED']
C2 weight+2 declared contrasts             -> ['E-DATA-WEIGHT-CONTRAST']
weight + within contrast                   -> ['E-DATA-WEIGHT-CONTRAST']
weight + report_by, no comparison          -> []
cluster + baseline                         -> ['E-DATA-CLUSTER-CONTRAST', 'W-DATA-WEIGHT-UNDECLARED']
weight + cluster + baseline                -> ['E-DATA-CLUSTER-CONTRAST', 'E-DATA-WEIGHT-CONTRAST']
```

**`E-DATA-WEIGHT-CONTRAST` is the sole error on a C1- and a C2-shaped config.** The control fires a
different code on the same fixture, so the singleton is the weight's shape and not a fixture that
reports one thing. The last row confirms `validate` **collects**: both refusals report together,
neither gating the other.

### 6.2 `report_by` versus a `within` contrast — the invariant, verified both ways

| Claim | Verified |
|---|---|
| a `within` contrast **joins** the correction family | **Yes.** A declared contrast resolves to a `Comparison`, reaches `_comparison_step_blocks`, and mints a `Member` per metric. The probe's `weight + within contrast` row is refused, which is the refusal reading the resolved family |
| `report_by` **does not** join it | **Yes, structurally.** `Member`s are built at one site, in a loop over `sorted((set(of_summary) & set(against_summary)) - {"by"})` — `by` is where the whole `report_by` block lives, excluded with a comment saying why. The `report_by` code path never constructs a `Member` at all |
| a weighted `report_by` with no comparison is legal | **Yes**, probed: zero findings |

H4a-SCOPING § 7 reached the same conclusion from the same call site; **re-verified rather than
carried**, and it now needs a *pin* rather than a build, exactly as H4a task 18 recorded.

### 6.3 The nine

**Two figures, and they are not the same figure.** *No remaining core-side blocker* is H7b Part B's
own cell standard — "this config's `data`/`statistics` blocks validate with zero errors and every
field they declare is honoured". *Executes* is the stricter claim that section exists to keep apart.
**Six of nine meet the first after H4b; three meet the second, unchanged.**

| Config | State once H4b lands |
|---|---|
| **E1**, **E2**, **E5** | Unchanged. `weight_by: null`, so H4b touches none of them |
| **E3**, **E4**, **E6** | Blocked on `io.reuse_from` — `grep -rn 'reuse_from' src/` → exit 1; control `grep -rln 'read_upstream' src/` → two files. Unbuilt, **unowned** |
| **C1**, **C2**, **C3** | **No remaining core-side blocker** — `E-DATA-WEIGHT-CONTRAST` is probed above as their *sole* error, so retiring it takes them to zero. Whether they *execute* turns on `io.reuse_from`, which the analysis declines to settle and which **no config and no grep can answer**, since it is a step-level call and `growth-shortcut`'s steps do not exist. **The cell's second clause — "every field they declare is honoured" — is false for these three either way**, on two counts that bite exactly them: § 7's silently-dropped `resample.stratify_by`, and the `report_by` level's unresampled column interval. All three declare `resample: {stratify_by: [...]}` *and* `report_by` |

**The honest form, in the shape the analysis's own § Executability uses:**

> H4b retires **one refusal that 3 of 9 configs hit** (`E-DATA-WEIGHT-CONTRAST`) — the last
> core-side refusal C1, C2 and C3 carry — and takes the *no-remaining-core-side-blocker* count from
> **three to six**: E1, E2, E5 unchanged, C1, C2, C3 newly. **The executable count stays at three.**
> C1–C3's `io.reuse_from` dependency is unsettled, the analysis says so in its own words, and this
> measurement does not settle it either; and two declarations all three carry — `resample.stratify_by`
> on a contrast, and a `report_by` level's column interval — are still not honoured after this slice.

**Do not write "unblocks 3 of the nine", and do not write "six of nine execute."** The first is the
refusal-gated count the charter states and reads as the executable count a month later; the second
promotes a blocker count to an execution count across an unsettled dependency. Both are the
conflation `CLAUDE.md`'s feasibility procedure step 10 exists to prevent, and every slice since H4a
has had to correct one of them.

---

## 7. Documented with no code, and code with no row — in this area

| Item | State |
|---|---|
| **`resample.stratify_by` on a contrast** | **Honoured per condition, silently dropped on every contrast, and unfiled.** `paired_percentile_of_derived` is the only percentile construction with no `strata` parameter; no contrast call site passes one. § Weighted samples states the rule generally ("resampling within each stratum so a bootstrap can't return a replicate whose stratum composition the design ruled out") and § Statistical reporting's `paired_percentile_over_units` row is silent. **All three payoff configs declare one.** `grep -n 'stratify_by' docs/superpowers/spec-defects.md` ∩ *contrast* → zero, control 35. **This is the `hash_index` shape: file it, and H4b cannot honour a weighted contrast draw without deciding it** |
| **A weighted `cohens_dz`** | **Documented, absent.** § Statistical reporting: "A weighted condition standardizes by the weighted standard deviation, on the same weights the mean used." `cohens_dz(diffs)` takes a list; `cli.py` computes it from the local `diffs`. It will stay unweighted unless a task names it |
| **"a contrast between two weighted conditions uses the same weights on both sides"** | § Weighted samples' **only** sentence about a weighted contrast, and it names no construction, no `method` string, and no check. It adds "worth checking when it isn't" under `allocation: between` — no code checks it |
| **`weight_by` × `cluster_by` on a contrast** | **Still underspecified**, as H3b-SCOPING filed. § Weighted samples says only "`cluster_by` still decides the draw when both are declared", which settles the per-condition form (`weighted_t_over_units_clustered`) and nothing about a contrast. Probed: both refusals co-report, so the combination is **currently unreachable and becomes reachable the moment H4b retires either one** |
| **`E-DATA-CLUSTER-CONTRAST`'s "five constructions"** | **Arithmetic that cannot be walked to zero** by the slice that owns the row (§ 5) |
| `E-DATA-WEIGHT-CONTRAST` | **Row and code and § Validation row, all three present.** Recorded so it is not re-scoped as owed |
| § *How a metric becomes a number* | **A section cited by eighteen files that does not exist.** Filed, **owner unassigned**, with the note "H4b is next to touch that material". H4b should claim or explicitly decline it; silence is how it goes stale |

### Already filed and owned — verified at `b65ab91`

`grep -c 'H4b' docs/superpowers/spec-defects.md` → **5**, and reading each hit places it in **four**
entries. Two more name **H4 Statistics** in terms that resolve to this slice:

| Entry | Owner as filed | What it costs H4b |
|---|---|---|
| **"The contrast path discloses nothing about its resample, and `paired_percentile_of_derived` never got the zero-width sweep"** (`:5544`) | "all deferred with a named owner — **H4b**" | **Three findings**: a contrast-scope thin finding needing a `where` and a registry row; the zero-width sweep's fourth construction; and **a contrast entry carrying no resolved-`resample` echo** while every `aggregated` block beside it does. Task 20 |
| **"A column resample is only ever defined given finite inputs"** (`:5287`) | "**Owner re-assigned to H4b**" | Two `*_is_a_known_unfixed_gap` tests that must move **with** the entry, not silently. Task 22 |
| **"A column metric's `resample_draws` records the requested `n`"** (`:5204`) | routes the finiteness residue to "its own **H4b** owner below" | Bookkeeping only — the pointer must not outlive the entry it points at |
| **"§ *How a metric becomes a number* is cited across the repo and does not exist"** (`:5627`) | **unassigned**; "**H4b** is next to touch that material" | Claim it or decline it in writing. Task 22 |
| **"`percentile_of_derived` reported a zero-width interval … and a `report_by` asymmetry deferred beside it"** (`:5467`) | "whichever slice hardens `report_by` (**H4 Statistics**)" | **Live on C1–C3**: a level's recorded-column interval stays `t_over_units` under a declared `resample` while its derived metrics get a *stratified* percentile. Task 21 |
| **`paired_percentile_of_derived`'s sorted-pool precondition unasserted** (`:2365`) | "**H4 Statistics** — the slice that adds new percentile constructions" | That is this slice, twice over (tasks 15, 7). Task 22 |

**If H4b ships without discharging or re-owning each, the filing count goes up rather than down**
— a closed slice that did not close its own entry re-owners to nobody.

---

## 8. Traps specific to this slice

**`effective` computed over the wrong denominator, with no payoff fixture that can see it.**
`weights` is built at `cli.py:1413` from `roster` — **the whole roster** — while `eval_roster` is
not computed until `:1584`. A weighted contrast's `effective` must be Kish over the **paired
intersection's** weights, and the natural implementation reaches for the mapping and sums it.
**C1–C3 all declare `holdout: null`, so no payoff config separates the two readings.** The
discriminating fixture is a weighted contrast under a declared `holdout`. This is
`summarize_step`'s own "a vector filtered differently weights the wrong unit" discipline one level
over, and the reason it holds per condition today is that `summarize_step` looks the weight up by
**the column's own keys**.

**The roster argument is inert unless a comparison declares `within` — and H3d's finding holds with
a condition.** `_comparison_step_blocks` uses `roster` for exactly one thing,
`units_matching(roster, comp.within)`, and `units_matching` returns `None` when `within is None`.
So H3d task 15's "structurally inert to their roster argument" is **confirmed, for the unqualified
case only**. A `within` contrast — the subgroup that joins the correction family — is the one shape
where H3d's test-partition narrowing is load-bearing, and it is exactly where a weighted
intersection lands. A mutation on the roster argument with no `within` in the fixture cannot fail.

**A mutation on the three named functions cannot reach the payoff.** Emptying, breaking or
reversing `paired_t_over_units` proves nothing about C1–C3, because their column contrasts never
call it (§ 2.2). **A mutation is a claim too**: check the two branches can differ before trusting
"this would prove the weighting works". The discriminating mutation is on the `_column_mean`
closure.

**A weighted-contrast test whose fixture's weights cannot change the answer.** A weight vector that
is constant — or one where the weighted and unweighted means coincide by symmetry — makes every
assertion pass under an unweighted implementation. This is the shape that produced sixteen
uncatchable checks across two H3c slices: *a fixture whose numbers agree with the bug*. Compute the
unweighted and weighted answers by hand first, confirm they differ, then assert.

**A test asserting only that `weighted_by` is present.** The key being a string in the record is not
the arithmetic having happened — the per-condition case makes exactly this three-way argument
(`value`, interval, `n.effective` "move together" because "a weighted interval beside an unweighted
point estimate would be a declaration accepted whose effect is half delivered"). A contrast has the
same three-way obligation and one fewer place to put the third part (§ 3).

**Retiring the refusal before the record shape exists.** The refusal is what keeps a weighted
contrast from publishing a number nobody can interpret. Delete the emit last, after every construction,
record key and disclosure lands — the discipline H7b Part A's decision 7 bought and H7b Part B kept.

**A grep for one spelling.** `E-DATA-WEIGHT-CONTRAST` appears at five sites in `validate.py` and
**one emits**; at three sites in `reference.md` and **one is its row**. The brief itself made this
substitution. Every count in this document was reached by reading the function or the table and then
confirming by grep, in that order.

**A carried line number.** `H4-SCOPING.md` cited `validate.py:4138` for this emit and `H4a-SCOPING.md`
cited `:4966`; it is at **`:5016`** today, and `stats.py:1441`'s `E-DATA-CLUSTER-DERIVED` is at
**`:1900`**. H7b-PartB-SCOPING's `validate.py:4966` was correct at `53090e9` and is stale at
`b65ab91` — **+50 lines in one slice**. Cite by name.

---

## 9. § CLI reference's `Status` column — nothing moves, and one thing to leave alone

`tests/test_cli.py` asserts set equality between the document's `NOT BUILT` command rows and
`cli.NOT_BUILT_COMMANDS`, so a row that moves must move in both places in one commit.
`NOT_BUILT_COMMANDS` at `b65ab91` holds `demo, diff, docs, draft, dry-run, freeze, list-templates,
report, reproduce, resume, study add, study new`. **`plugin new` is gone** — H7b Part B built it,
which is a change since both predecessor scopings.

**H4b moves no row in any of the three `Status`-carrying tables.** It adds no command, and
`weight_by` / `cluster_by` / `resample` are declarations rather than commands. § The one config file
now reads *"**One** declaration above is not yet built"* — `statistics.null_test`, H4d's, at `:156`,
the only `NOT BUILT` declaration marker left after H4a, H3d and H7b Part B each removed one.
**H4b must not touch that count**: retiring a combination refusal is not retiring a declaration, and
`_check_sweep`'s own comment makes exactly that placement argument for both of H4b's codes.

**Nothing in this area overclaims today.** Checked by reading each `Status` cell in § Operation
commands and § Creation commands rather than by grepping for the marker.

---

## 10. Decomposition — 22 tasks, against the charter's 14

Grain matches `H7b-PartB-SCOPING.md`, `H7c-SCOPING.md` and `H3d-SCOPING-2.md`: each new construction,
each new record key, and each document-table edit is its own task. **Ordered by payoff, which is
the non-obvious part** — the closure, record and derived-decision tasks are what make C1–C3 run;
the weighted `paired_t_over_units` and the `Member` decision make the *general* case honest and are
not on the payoff path.

**Three ordering constraints, none of which the charter states.** **Task 5 before task 7** — a
stratified draw would live *inside* the weighted closure, so building the closure before deciding
whether a contrast's draw stratifies bakes the answer in by omission, which is how
`resample.stratify_by` got dropped on this path in the first place (§ 7). **Tasks 2 and 3 before
tasks 7–10** — an emitted `method` string and a record key must exist in a document before code
writes them. **Task 13 last among the weight tasks and task 18 last among the cluster ones**: a
refusal is deleted only after everything it was standing in for exists.

**Weights — decisions and documents (5)**

| # | Task | Against the charter |
|---|---|---|
| 1 | **Settle and file the derived/column split** (§ 2.1). The paired derived estimators take no weights; the record does. Narrows a published refusal message and a normative § Errors row, so it is a filing, not a note | **NEW as a task.** H4-SCOPING named it; the code has since settled it and the filing is still owed |
| 2 | **Mint the weighted-contrast `method` vocabulary** in § Statistical reporting — rows or a stated rule, on the H3b-task-13 precedent (§ 3) | **NEW.** Neither predecessor noticed the absence |
| 3 | **Design and document the contrast record shape** under a weight: `weighted_by` on the entry, and where Kish's size goes given a scalar `n_paired`. § Contrasts' fenced example, § Statistical reporting, and § The two files' `run.yaml` move together | **NEW.** H4-SCOPING assumed a shape no document licenses |
| 4 | **Decide the corrected bound** (§ 4): `Member` weights, or force the pool. Argue it against `__post_init__`'s exactly-one invariant | **NEW.** H4-SCOPING's "`Member` evidence over the right pool" did not reach the unweighted-counterpart fault |
| 5 | **Decide `resample.stratify_by` on a contrast** and file it (§ 7). A weighted contrast draw cannot be built without an answer | **NEW.** Unfiled by anyone |

**Weights — the payoff path (5)**

| # | Task |
|---|---|
| 6 | **Thread `weights` into `_compute_vs_baseline`, `_compute_declared_contrasts` and `_comparison_step_blocks`** — none takes it today |
| 7 | **The weighted `_column_mean` closure** on the `resample`-declared column path, looking each weight up by the `unit` key the construction already preserves (§ 2.2). **This is the task C1–C3 actually need** |
| 8 | **`weighted_by` on every affected contrast entry**, with the three-way obligation of § 8 pinned: value, interval and size move together |
| 9 | **Kish over the paired intersection**, not over the condition or the mapping (§ 8's first trap), with the `holdout` fixture that separates the readings |
| 10 | **A weighted `cohens_dz`** — the documented rule with no code (§ 7) |

**Weights — the general case (3)**

| # | Task |
|---|---|
| 11 | **A weighted `paired_t_over_units`** — weighted mean of differences, weighted variance, df from Kish. The non-`resample` column path. *Off the payoff path* |
| 12 | **Implement task 4's corrected-bound decision** |
| 13 | **Retire `E-DATA-WEIGHT-CONTRAST`** — the emit, its 40-line comment block, its § Errors row, its § Validation row, the two sibling rows re-worded, and five tests. **Last among the weight tasks** |

**Clusters (5)**

| # | Task |
|---|---|
| 14 | **`paired_t_over_units_clustered`** — CR1 over the differenced values, df = clusters − 1 |
| 15 | **`paired_percentile_over_units_clustered`** — whole clusters, one joint draw for both sides |
| 16 | **`clusters` beside `n_paired`**, in the shape task 3 designs |
| 17 | **The clustered derived draw**, retiring **`E-DATA-CLUSTER-DERIVED`** — run-time, per condition, and assigned to this half by name (§ 5) |
| 18 | **Retire `E-DATA-CLUSTER-CONTRAST`**, rewriting the "five constructions" sentence as an enumeration and arguing the trade (§ 5) |

**Regression and residue (4)**

| # | Task |
|---|---|
| 19 | **The regression pin.** An unweighted, unclustered config must produce byte-identical output: `t_over_units` / `paired_t_over_units` / `percentile_over_units` / `paired_percentile_over_units`, `resample_draws: 2000`, `cohens_d: null` for a derived metric, and the worked example's intervals — which `CLAUDE.md` § The worked example says were checked numerically and **must not be narrowed back** |
| 20 | **The three filed contrast-path disclosure gaps** (§ 7, entry 1): a contrast-scope thin finding with a `where` and a registry row, the zero-width sweep's fourth construction, and the resolved-`resample` echo |
| 21 | **`report_by` under a weight and a cluster** — pin that a level mints no `Member` (§ 6.2), and discharge or re-own the level's `resample_columns` asymmetry, **live on all three payoff configs** |
| 22 | **The remaining filings**: the finiteness entry re-owned to H4b, the sorted-pool precondition, and the § *How a metric becomes a number* phantom section claimed or explicitly declined. Plus the feasibility analysis's § Executability **re-dated** with § 6.3's wording |

### The seam, and it is the recommendation rather than the fallback

**Split on payoff: weights (tasks 1–13, 19–22 in part) versus clusters (14–18).**

| Half | Retires | Payoff | Tasks |
|---|---|---|---|
| **H4b-1 — weights through contrasts** | `E-DATA-WEIGHT-CONTRAST` | **3 of 9** configs lose their last core-side refusal | **≈ 15** |
| **H4b-2 — clusters through contrasts** | `E-DATA-CLUSTER-CONTRAST`, `E-DATA-CLUSTER-DERIVED` | **0 of 9** — no feasibility config declares `cluster_by` | **≈ 7** |

22 is above this repo's band (H3c-1 20, H7b Part A 20, H3d 19, H7c 14, H7b Part B 13), and the two
halves are independent: nothing in the weighted work needs a membership mapping and nothing in the
clustered work needs a weight — **except the combination of § 7's fourth row, `weight_by` ×
`cluster_by` on a contrast, which is unreachable today only because both refusals stand and becomes
reachable the moment either retires.** That is the one thing the split does not cleanly cut, and the
cheap answer is the precedent this repo already has: keep refusing the *combination* under a
narrower code while honouring both declarations, exactly as H3a did minting
`E-DATA-WEIGHT-CONTRAST` and H3b `E-DATA-CLUSTER-DERIVED`.

**Assign it to H4b-1, the weights half, by name — not to "whichever ships first."** That phrasing is
how a deferral ends up owned by nobody, which is the failure this section's opening paragraph
describes. H4b-1 is the right owner on two grounds: it ships first under the recommended order, and
it is the half whose retirement makes the combination reachable for the three configs that exist.
H4b-2 then *retires* the new code as part of task 18.

H4-SCOPING offered this seam as a fallback ("if 14 is too large"). At 22 it is not a fallback, and
its second suggestion — that the cluster half "can ride with H4c, which is the same construction
work one level over" — is **stronger** than it knew: § 5 shows two of the five clustered contrast
forms are H4c's already, so H4c would be building three of five rather than two.

---

## 11. What the charter does not own but this slice will inevitably touch

- **`correction.py`.** No task in the charter names it; § 4 shows the corrected bound is a decision
  with two defensible answers and no test that can see either.
- **`cli.py`'s weight-construction site at `:1413`, and its distance from `eval_roster` at `:1584`**
  (§ 8). H3d moved six denominators to the test partition and this mapping was not among them.
- **`_comparison_step_blocks`' signature.** It takes no `beside_n` and no `weights`; three of the
  filed findings and four of the tasks above all need something threaded into it.
- **`report_by`'s level path** (§ 7, entry 3), live on exactly the three payoff configs.
- **The `E-DATA-ALLOCATION-CONTRAST` ordering dependency** (§ 5), which no charter row states.
- **`tests/test_validate.py`'s five `E-DATA-WEIGHT-CONTRAST` tests and two comment blocks**, plus
  every test asserting a finding *set* that contains the refusal — those are deletions from a list,
  not rewrites, because `validate` collects.
- **`experimental-designs.md` § Mistakes core prevents and § What core will not do for you**, which
  the cross-document pass covers and which no task above would otherwise open.

---

## 12. What is NOT in H4b

| Out | Owner |
|---|---|
| `welch_t_over_units`, `unpaired_percentile_over_units` and both clustered counterparts; `paired` becoming derived in `_comparison_step_blocks`; the `cohens_d` *d*s branch; `E-DATA-ALLOCATION-CONTRAST` | **H4c.** Its refusal is also what makes H4b's two-construction cluster half sufficient (§ 5) |
| `statistics.null_test`, `p_value`, `p_value_corrected`, `fdr_bh` made real | **H4d.** `grep -rn p_value src/` → still zero matches |
| `io.reuse_from` and `lineage.py` | **Unowned**, filed. Blocks E3/E4/E6 and unsettles C1–C3 (§ 6.3) |
| `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap | **H4c**, where H4a-SCOPING § 7 declined it with a measured 3–5 task cost. H4b must not fold it in |
| Folds and holdouts within cells; `E-REPL-FOLD-CELLS` / `E-DATA-HOLDOUT-CELLS` | **H3c-3** |
| The apparatus probe, `apparatus_facts`, the change gate, `cli.py`'s hardcoded `"apparatus": None` | **H7d** |
| `study` / `report` / `diff` / `freeze` | **H8** |
| An `Estimate` returned by a `summary` step | **Never recomputed.** It is `reported: true`, outside the correction family, and it is the documented route both of H4b's refusals offer. A weighted or clustered pass that walks every metric block **must skip it** — a test H4b owes, not a boundary it merely respects |
| Interactions, dose-response orderings, differences-in-differences | **Refused.** Contrasts do not nest, and C3's own primary gate is one — an `Estimate`, which the analysis already routes |
