# Task 1 report: The documents first

**Status:** complete. Two commits on `h3b-clustered-units-and-partitions`, atop `fc98a09`:

- `2c80d49` — the three edits the brief names.
- `6a3c3a9` — the reconciliation the cross-document pass then required, plus one clause the brief
  omitted and `H3b-SCOPING.md` § task 1 owes.

`docs/reference.md` only, no code touched.

## What landed

### Step 1 — the *Cluster attribute exists* row

§ Validation, inserted immediately before *Clustering looks undeclared*, which is where the weight
group puts the same row relative to *Weighting looks undeclared*:

> | Cluster attribute exists | `data.units.cluster_by` names `site`, which is not a unit attribute |

Phrased from the weight sibling verbatim in shape — `data.units.<field>` names `<thing>`, **which is
not a unit attribute**. That is the *declared attribute* framing (`weight_by`'s), not the *source
column* framing (`measurements.by`'s), which is what § Where units come from and § Clustered units'
own YAML say `cluster_by` is: line 1102 lists `cluster_by` beside `stratify_by`, `assign.from` and
`null_test.shuffle` as things that "all name attributes".

`site` is the example even though the next row treats `site` as present. The weight group does the
same — its *exists* row says `sampling_weight` is not an attribute and its two neighbours treat it as
one. Each row is an independent example.

### Step 2 — `W-DATA-CLUSTER-UNDECLARED`

Added to § Warnings core reports in the table's alphabetical position (before `W-DATA-INELIGIBLE`).
Absence verified tree-wide first: `grep -rn "W-DATA-CLUSTER\|Cluster attribute exists\|CLUSTER-UNDECLARED" .`
outside `.git` returned nothing.

**No name test**, per the brief and per § Weighted samples' "not by the same means". The trigger is
four predicates:

1. every unit carries a value for it;
2. its values are not all numeric — `units.is_measurement_numeric` reads at least one as neither a
   number nor a string that parses as one;
3. more than two distinct values;
4. at least one value held by more than one unit.

Plus an exclusion: an attribute a `sweep.groups` axis names or an `assign.from` reads, any
`stratify_by`, or `null_test.shuffle`.

Each clause was chosen against a false positive I could name, and the row says which:

| Clause | What it excludes | Why it is not arbitrary |
|---|---|---|
| not all numeric | `age`, `dose`, `latency` — 240 units, ~50 values, several units each | a numeric column with repeated values is a measurement far more often than an identifier |
| > 2 distinct | `label`, `sex` — cohort-pilot's own attributes | two values is a level set, and a cluster-robust *t* is CR1 with df = clusters − 1, so two clusters is no inference base at all |
| a value held by > 1 unit | a second key column | "many units each" is half of what the section already promises |
| `groups` / `assign.from` | every `between` design's arm | it would fire on all of them |
| `stratify_by` | `animal_strain` | § Clustered units requires it constant *within* a cluster, so it is coarser than one |
| `null_test.shuffle` | cohort-pilot's `label` | a cluster is what shuffling respects, not what it names |

`report_by` is deliberately **not** excluded: the config schema's own example is
`report_by: [sex, site]`, and a run that reports by `site` while `site` really is a cluster is a run
that wants both declarations, not a false positive.

**Checked against the two rosters the docs contain.** cohort-pilot (`[label, age, sex]`, 240 units):
silent on all three — the exact defect § Weighted samples warns about ("a warning that fires on
nearly every numeric attribute is one a reader learns to skip"). § Validation's own example
(`site`, 6 distinct across 240): fires, so that row stays true.

**No number in the trigger, and that was forced.** CLAUDE.md's "every threshold in that table lives
in `limits`" governs the check, not the markdown table its prose sits in, and *Clustering looks
undeclared* is a § Validation row. A ratio like "a tenth of the units" would be an unanchored
tunable. Anchoring it would mean a new `limits` key — which is `materialize.py` and `envelope.py`,
i.e. code, and putting the key in § The one config file without them is exactly the inverse defect
this slice exists to avoid. So the trigger is predicate-only, matching `W-DATA-WEIGHT-UNDECLARED`,
whose four clauses are also all predicates. `> 2 distinct values` is a kind test with a stated
reason (df = clusters − 1), not a tunable.

Written in present tense, like the neighbouring `cluster_by` rows 280–284 that also describe unbuilt
behavior; `NOT BUILT` at line 84 carries the interim.

### Step 3 — the `× measurements` rule

§ Clustered units, after the two consequences bullets and before the `assign.stratify_by` paragraph —
adjacent to the leak argument it invokes. Mirrors § Weighted samples' closing sentence in shape
(bold rule → mechanism → consequence → "a fact about the unit, not about the measurement") and
sharpens one thing: a top-level `collapse: mean` over a string column is *rejected*
(§ Validation, *Collapse rule fits the column*), so the collapse that actually happens is `first` or
`mode`, the only rules a string column admits.

States the reproduced fact as fact: `p1`'s replicate rows declaring `S1` and `S2` collapse to `S1`
under the `first` fallback. And states the consequence the brief asked for — a mis-collapsed weight
mis-sizes what one unit stands for; a mis-collapsed cluster decides which side of a train/test split
a unit lands on, so its real site is on both sides.

Prose only, no new § Validation row and no `E-` code — the weight sibling states its rule the same
way. See the concern below.

### The reconciliation the first commit owed (`6a3c3a9`)

Two sentences already characterized this warning's trigger, and minting the row made both stale —
the *schema fields in prose* class, invisible to any mechanical check:

- **§ Clustered units** (the section edited): "`validate` warns when an attribute looks like a
  cluster identifier **(few distinct values, many units each)**".
- **§ Weighted samples**: "a cluster is *structurally* distinctive, **a column with few distinct
  values and many units each**".

Applied literally, both parentheticals fire on `sex` — 2 distinct values, 120 units each, which is
exactly "few distinct values, many units each". A reader following the summary and a reader following
the row got different answers on cohort-pilot's own roster. **The row is the specification and the
summaries were the stale copies**, so both were widened to name the type and floor clauses and to
point at `W-DATA-CLUSTER-UNDECLARED` as the one place the trigger is stated. The row was not weakened
— its predicates are the part that has to be implementable.

§ Weighted samples' "not by the same means" argument survives untouched and is in fact sharper: a
*type* test is not a *name* test, and the sentence's next line ("`age`, `dose` and `latency` are
positive, numeric and varying exactly as a sampling weight is, so the name is the only discriminator
left") is now the precise complement of the row's type clause.

### One edit beyond the brief

`docs/superpowers/H3b-SCOPING.md` § Task order line 1 assigns task 1 **five** document changes; the
brief named three. Of the two omitted:

- **"add the cluster clause to *Leave-one-out is affordable*"** — genuinely missing and added.
  § Validation row 247 costed `k: all` over 240 *units* with no cluster clause, while § Repeat kinds
  already reads `k: all` as leave-one-*cluster*-out under `cluster_by`. That is the number task 4
  threads into `_fold_k`, so leaving it would make task 4 edit a document alongside its code — which
  the plan's own ordering rationale ("no document edit trails the code it governs") forbids. One
  clause, phrased like the identical one already in *Folds fit inside the cells*.
- **"add the *Clustered deltas aren't computed* row and its § Errors entry"** — **not** added, and
  this is a contradiction inside the scoping document rather than a gap. Its task 1 line assigns the
  row to task 1; its task 12 line assigns `E-DATA-CLUSTER-CONTRAST` to task 12. The brief resolved it
  toward task 12, which also matches the H3a precedent: *Weighted deltas aren't computed* and
  `E-DATA-WEIGHT-CONTRAST` landed together, in the task that built the refusal. Flagged rather than
  acted on — see concern 6.

## Verification

**Mechanical pass.** `python3 scratchpad/mech.py docs/reference.md docs/design-principles.md
docs/experimental-designs.md docs/feasibility-llm-growth-studies.md README.md CLAUDE.md` → `CLEAN`.
Checks: relative-file links, `#anchor` resolution (same-file and cross-file, GitHub slugger rules),
duplicate anchors, table row width vs. header, empty table rows, trailing whitespace, tabs,
invisible unicode, en dash in headings. Fenced blocks skipped for everything but whitespace.

**Every check proven able to fail**, by copying `docs/` to the scratchpad and injecting one fault per
check into a copy of the edited file:

| Injected fault | Reported |
|---|---|
| `](#what-isnt-a-repeatX)` in the new § Clustered units sentence | `1266: unresolved anchor #what-isnt-a-repeatX` |
| `### Clustered units` → `### Weighted samples` | `1249: duplicate anchor #weighted-samples (also line 1218)` |
| pipe removed from the new § Validation row | `280: table row has 1 cells, header has 2` |
| new row → `\|  \|  \|` | `280: empty table row` |
| trailing spaces on the new row | `280: trailing whitespace` |
| tab in the new row | `280: tab` |
| U+200B in the new row | `280: invisible unicode U+200B` |
| `### Clustered–units` | `1249: en dash in heading` |
| `experimental-designz.md#matched-case-control` | `1270: missing file experimental-designz.md` |
| **control:** all of the above inside a ```` ```yaml ```` fence | `CLEAN` — fences are skipped |

The anchors the new text introduces — `#clustered-units`, `#what-isnt-a-repeat`,
`#weighted-samples`, `#validation`, `#expansion-modes` — all resolve.

**Cross-document pass.**

- **Enum comments** — no enum gained a value. `collapse is mean | median | sum | first | mode` is
  quoted, not extended.
- **Schema fields in prose** — every field named (`data.units.cluster_by`, `stratify_by`,
  `assign.from`, `sweep.groups`, `statistics.null_test.shuffle`, `measurements`) exists in § The one
  config file. No field added, so **config completeness** is untouched, and no new `limits` key.
- **Declared vs. derived** — `cluster_by` stays a declaration everywhere; nothing newly shown as
  derived or as settable.
- **Worked example** — no value, interval, hash prefix or count changed. The new warning is silent on
  cohort-pilot's roster, so nothing owes it a mention.
- **Versions / NOT BUILT** — unchanged: 11 `NOT BUILT` occurrences, 3 `UNSUPPORTED` mentions, no
  `-UNSUPPORTED` code retired. The declarations described are still refused.
- **experimental-designs.md § Clustered and hierarchical data** — describes cluster-robust intervals,
  whole-animal folds, `k` bounded by animal count. Nothing about measurement rows or the warning's
  trigger. No conflict, no edit.
- **experimental-designs.md § Mistakes core prevents** — *Ignored clustering* says `validate` "flags
  an attribute that looks like an undeclared cluster", which is trigger-agnostic and agrees with what
  landed; *A cluster split across train and test* is about the partition and stays true. Neither
  needed an edit. See the concern below on the second.

**Tests.** `uv run pytest` → **1226 passed, 2 xfailed** — unchanged. `git diff --stat` for the commit
is `docs/reference.md | 4 ++++`, so no code path could have moved.

## Concerns

1. **The `× measurements` rule is advice, not prevention** — no check, no `E-` code, exactly like its
   weight sibling. But experimental-designs.md § Mistakes core prevents carries *A cluster split
   across train and test*, and CLAUDE.md's *Prevented mistakes* class requires that to be
   structurally impossible. It is impossible through the partition core computes; it is **not**
   impossible through the input file, which is the hole this sentence describes and does not close.
   Recorded in `docs/superpowers/spec-defects.md` with a proposed resolution (a § Validation row plus
   an `E-` code, shaped like *Holdout strata survive clustering*), to land with whichever slice reads
   the cluster column at collapse time. Not added here — Task 1 was scoped to state the rule.
2. **Two clustering-adjacent warnings in § Validation still carry no `W-` code**: *Clusters enough to
   resample* (`limits.min_clusters`) and both `limits.min_units_per_cell` rows. Pre-existing, and
   both belong to still-unbuilt slices, so they follow the same pattern this task just broke for
   *Clustering looks undeclared*. Worth a row in a later H3b task if `resample` lands in it.
3. **The trigger is a design decision this task had to make, not one the brief specified.** The brief
   said "state the structural trigger, and make it specific enough that a reader could act on it";
   the four predicates and the exclusion list above are my construction, defended against the two
   rosters the docs contain. Tasks 2–11 implement them, so if an implementer finds a clause
   unimplementable or a false positive I missed, the row is the thing to change — not the code.
4. **`docs/superpowers/` is gitignored**, so the spec-defect entry in concern 1 is not in the commit.
   That is the repo's existing arrangement, noted so nobody looks for it in the diff.
5. **No task in the plan owes the warning's emit site.** `W-DATA-CLUSTER-UNDECLARED` is now the first
   row in § Warnings core reports describing behavior that does not exist — § Validation rows 280–284
   already had that property, § Warnings did not, and documents-lead-code sanctions it. But reading
   `H3b-SCOPING.md`'s task table 2–12: task 2 is "cluster resolution, one authority … plus the
   **attribute-existence** check and the glob cross-check" — that discharges the *Cluster attribute
   exists* row, not the warning. Tasks 3–12 are partitioning, `_fold_k`, stratification, `n.clusters`,
   the constructions, wiring and the retirement. **None names the undeclared-cluster emit site**, even
   though the document's § Checks that could not fail already specifies its test ("assert it does not
   fire on a high-cardinality column, and that it does on the low-cardinality one, in the same
   config") and § Defects lists it as defect 8. Either task 2 should absorb it — it is a `validate`
   pass over the resolved roster, which is what task 2 builds — or a task owes it explicitly.
   Otherwise this row is the inverse defect with the sign flipped, and task 12 is where it surfaces.
6. **`H3b-SCOPING.md` contradicts itself on *Clustered deltas aren't computed***, assigning it to
   task 1 and its `E-` code to task 12. Recorded above; the caller may want the scoping line fixed so
   task 12's brief is not written against a row it assumes exists.
7. The brief's three claims of absence all checked out: no *Cluster attribute exists* row, no
   `W-DATA-CLUSTER-UNDECLARED` anywhere in the tree, and no measurement sentence in § Clustered
   units. Nothing in the brief was wrong.
