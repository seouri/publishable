## Task 2: The documents — three under-specifications, thirteen codes, two rows, and the inference-base ruling

**Files:** Modify `docs/reference.md`, `docs/superpowers/spec-defects.md`. No code, no test file.

**Interfaces:**
- Consumes: nothing.
- Produces: the normative statements every later task enforces — the `train`/`test` literals (tasks 7, 10), the `allocation.json` home for a holdout's `seed`/`strata` (task 17), the `holdout.seed` row in § What `auto` derives from with `E-DATA-HOLDOUT-SEED` (task 5), all twelve § Errors rows (tasks 5–8), the two new § Validation rows (tasks 7, 8), the `resample` × `holdout` sentence (task 16), and decision 5's inference-base ruling (tasks 15, 17).

**Why the documents are first.** `CLAUDE.md`: the four documents are normative and they lead; where the code cannot follow them the document changes first. Five of the things below are things no document currently says, so a later task would otherwise be inventing a rule and implementing it in the same commit.

**Decision 5, settled here so no later task re-derives it.** `CLAUDE.md`'s invariant is that **units are the inference base and `n` counts units**. Under a holdout, the units that produce a result are the **test** partition, so:

- `n.resolved`/`n.completed`/`n.ineligible`/`n.failed` count **test** units. A 20 % holdout over 240 reports `resolved: 48`, which § A fixed holdout split already says.
- Every interval is over that same table, so nothing about the correction family changes: a holdout narrows the denominator and adds no member.
- `provenance.units.n` and `provenance.units_hash` stay **whole-roster**. They are the roster's *identity*, not a metric's denominator — that is what makes `240` there and `48` in a metric's `n` two true numbers rather than a contradiction.
- The training units are **not** `ineligible` and **not** `failed`. They were never handed out, so they appear in no count at all.

- [ ] **Step 1: Write the failing test** — the test here is a set of throwaway greps, run in Step 2 and not kept. Filter the **file list**, never the output:

```bash
cd /Users/joon/src/tries/publishable
# Every code this slice mints must exist in reference.md § Errors after Step 3.
for code in E-DATA-HOLDOUT-METHOD E-DATA-HOLDOUT-FRAC E-DATA-HOLDOUT-FROM \
            E-DATA-HOLDOUT-NO-DRAW E-DATA-HOLDOUT-SEED \
            E-DATA-HOLDOUT-STRATIFY-UNKNOWN E-DATA-HOLDOUT-FOLD \
            E-DATA-HOLDOUT-VALUES E-DATA-HOLDOUT-STRATIFY-VARIES \
            E-DATA-HOLDOUT-EMPTY E-DATA-HOLDOUT-CELLS E-REPL-FOLD-CELLS \
            E-DATA-HOLDOUT-VARIES; do
  printf '%s %s\n' "$code" "$(grep -c -- "$code" docs/reference.md)"
done
# The three under-specifications.
grep -n 'holdout.*train.*test' docs/reference.md | head
grep -n '"holdout":' docs/reference.md
grep -n "holdout.seed" docs/reference.md
```

- [ ] **Step 2: Run it, confirm it fails** — every code prints `0`; `grep -n '"holdout":'` returns only the one `allocation.json` example line with no `seed` in it; `holdout.seed` appears only in § What `auto` derives from's *prose*, with no row in the table beneath it and no refusal code. That is the confirmation.

- [ ] **Step 3: Implement** — six edits to `docs/reference.md` and one to `docs/superpowers/spec-defects.md`.

  **(a) § A fixed holdout split — settle the `by_attribute` literals, and mark the cells prose honestly.** Replace the sentence beginning "`by_attribute` covers a split that already exists" with:

```markdown
`by_attribute` covers a split that already exists, which benchmark datasets usually ship: name the column (`from: split`) and core partitions rather than draws. **The column's values must be exactly `train` and `test`** — two fixed literals, not "whichever two values are there". A holdout declares no `levels` for core to read an order out of, and inferring one from the data would make which side is evaluated depend on a lexical accident of the input; a column holding `{A, B}`, or `{train, test, dev}`, is refused as `E-DATA-HOLDOUT-VALUES`. Rename the column's values, or map them in the step that produces the roster.
```

  Then replace the **fourth** interaction bullet (the one beginning "**Under `allocation: between`, the split happens within each cell**") with:

```markdown
- **A roster-wide split beside a cell structure is refused, not drawn.** Under `allocation: between`, or under a non-empty `sweep.groups`, a single split of the whole roster would leave cells with unequal test sizes and, at worst, a cell with no test units at all — so core refuses the combination outright (`E-DATA-HOLDOUT-CELLS`), rather than recording a partition whose imbalance a reader would have to cross against the arms list by hand to see. A `fold` repeat beside the same cell structure is refused for the identical reason and under its own code, `E-REPL-FOLD-CELLS`. Drawing *within* each cell is the design that lifts both refusals, and it is not built.
```

  Then append one paragraph to that section, immediately before "The realized membership is written to `allocation.json`":

```markdown
**A holdout narrows a denominator and adds nothing to the correction family.** `statistics.resample` draws over the per-unit table, which under a holdout holds only the units that recorded — the test partition — so a percentile interval rests on that many units, and on that many [clusters](#clustered-units) when `cluster_by` is declared. `limits.min_clusters` is checked against the **test** partition's cluster count for that reason: a roster of 50 clusters under a `frac: 0.2` holdout resamples roughly 10, and warning against the wider number would be warning against a denominator no interval used. The units held back for training produced no result, so they are counted nowhere: not `completed`, not `ineligible`, not `failed`. `provenance.units.n` and `units_hash` stay whole-roster regardless — they are the roster's identity, not a metric's denominator, which is why `240` there and `48` in a metric's `n` are two true numbers rather than a contradiction.
```

  **(b) § Validation — two new rows.** Insert them immediately after the existing *Holdout strata survive clustering* row:

```markdown
| One split, not one cell each | `data.units.holdout` or a `{kind: fold}` level is declared beside `allocation: between` or a non-empty `sweep.groups` — one roster-wide evaluation split would give the cells unequal test sizes, and a cell none at all once the split is fine enough |
| Holdout leaves a test partition | `holdout.method: random` with `frac: 0.01` over 40 units apportions the test side zero units, so every metric would be over nothing |
```

  **(c) § Errors `validate` reports — thirteen rows.** Add them in the `data.units` block, after the existing `E-DATA-ASSIGN-*` rows, each with the code in the right-hand column, in the order the Global Constraints table lists them. Write each row's left-hand cell as the fault, with the sentence of reasoning the surrounding rows carry — the thirteenth (`E-DATA-HOLDOUT-VARIES`) belongs beside its `E-DATA-CLUSTER-VARIES` / `E-DATA-WEIGHT-VARIES` / `E-DATA-ASSIGN-VARIES` siblings rather than with the rest, since it is raised by `resolve_units` at run time and not by `validate` — check which table those three live in and put it there. For example:

```markdown
| `data.units.holdout.method` is absent, is not a string, or is not one of `random`, `by_attribute`. An allowlist, not a denylist: a method named here and realized nowhere would validate clean and then partition on something core never drew | `E-DATA-HOLDOUT-METHOD` |
| Under `method: random`, `data.units.holdout.frac` is absent, is not a real number, or is outside the open interval (0, 1). Both endpoints are excluded: `0` holds nothing out and `1` holds everything out, and each leaves one side of the split empty | `E-DATA-HOLDOUT-FRAC` |
| Under `method: by_attribute`, `data.units.holdout.from` is absent, is not a string, or is empty — there is no column to read the partition out of, and unlike [`assign.<axis>.from`](#allocation-within-subjects-or-between-subjects) a holdout has no axis name to default to | `E-DATA-HOLDOUT-FROM` |
| A `data.units.holdout` field that means nothing under the declared method: `frac` under `by_attribute`, which reads a partition rather than drawing one, or `from` under `random`, which draws one rather than reading one. The same fault [`E-DATA-ASSIGN-NO-DRAW`](#errors-validate-reports) names one declaration over | `E-DATA-HOLDOUT-NO-DRAW` |
| `data.units.holdout.seed` is present and is neither `auto` nor a plain integer — a quoted `"1234"`, a `1.5`, or a `true` is a pin nothing can honour, and honouring it as far as the derivation would record a derived seed under a key the config wrote deliberately | `E-DATA-HOLDOUT-SEED` |
| `data.units.holdout.stratify_by` names a value `data.units.attributes` does not declare, names the column `data.units.measurements.by` names — consumed when a unit's rows collapse, so no resolved unit carries it — or is not the name of an attribute at all: a non-string, an empty string, or an empty list. Checked from the declaration alone, so it reports whether or not a roster resolved | `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` |
| `data.units.holdout` and a `{kind: fold}` repeat level are both declared. Two answers to one question — how the data is divided for evaluation — leaving "which units is this metric over?" with none | `E-DATA-HOLDOUT-FOLD` |
| Under `method: by_attribute`, the column `data.units.holdout.from` names does not resolve to exactly `train` and `test`: a unit carries some other value, carries none, or one of the two literals names no unit at all. Read through `units.arms_of`, the single authority for a column-read partition, so the same set equality an arm assignment requires is the one a holdout requires | `E-DATA-HOLDOUT-VALUES` |
| `data.units.holdout.stratify_by` names an attribute that varies within a `data.units.cluster_by` cluster, checked through `units.stratum_varies_within_cluster` — the single authority *Fold strata survive clustering* and *Resample strata survive clustering* also read. Whole clusters go to one side of a holdout, so a cluster carrying two stratum values can be dealt to neither | `E-DATA-HOLDOUT-STRATIFY-VARIES` |
| Under `method: random`, unstratified and unclustered, `frac` apportions the test side zero units over the resolved roster — every metric would be over nothing. Reported for the unstratified, unclustered draw only, mirroring *Every arm draws units*: a stratified or clustered split is checked where the run performs it, because a cluster is the smallest thing that can move and only the draw knows what it moved | `E-DATA-HOLDOUT-EMPTY` |
| `data.units.holdout` is declared beside `data.units.allocation: between` or a non-empty `sweep.groups`. One roster-wide split across a cell structure gives the cells unequal test sizes and, at worst, a cell with no test units — refused rather than recorded, because the imbalance is only visible to a reader who crosses `allocation.json`'s membership against the arms list by hand | `E-DATA-HOLDOUT-CELLS` |
| A `{kind: fold}` repeat level is declared beside `data.units.allocation: between` or a non-empty `sweep.groups`, refused for the identical reason and at the identical check site as `E-DATA-HOLDOUT-CELLS`. `k` is bounded by the whole roster's [fold basis](#validation), so a roster-wide partition can leave a small arm with folds holding none of its units | `E-REPL-FOLD-CELLS` |
| Under [`data.units.measurements`](#what-isnt-a-repeat), the column `data.units.holdout.from` names is not constant across the rows collapsing into one unit — the unit would be filed on whichever side the row the collapse happened to keep says, making a train/test membership an accident of row order. The fourth member of the family `E-DATA-CLUSTER-VARIES`, `E-DATA-WEIGHT-VARIES` and `E-DATA-ASSIGN-VARIES` already form, and raised where they are raised: at run time, by `resolve_units`, which is the one place holding the pre-collapse rows that prove it | `E-DATA-HOLDOUT-VARIES` |
```

  **(d) § `allocation.json` — the holdout's `seed` and `strata` home.** Replace the JSON example's `"holdout"` line with:

```json
  "holdout": {"train": ["P0002", "P0007"], "test": ["P0011", "P0019"],
              "seed": 3310985422, "strata": ["label"]},
```

  and add this paragraph immediately after the existing "**`seed` and `strata` are keyed by axis…**" paragraph:

```markdown
**A holdout carries its own `seed` and `strata`, inside its own block.** The top-level `seed` and `strata` are keyed by *axis name*, and a holdout is not an axis — hanging it off a fabricated key would invite a reader to index it as one. So the `holdout` block is self-contained: `train` and `test` always, `seed` only when the split was **drawn** (`method: random`), and `strata` only when it declared a non-empty `stratify_by`. A `by_attribute` holdout carries neither, for the reason a `by_attribute` axis is left out of both above: it reads a partition the data already holds, so a seed would record a draw that never happened and a `stratify_by` would describe how a draw was balanced when none was. There is no `holdout_hash`; `provenance.allocation_hash` covers this file whole, both partitions being of one roster drawn once.
```

  **(e) § What `auto` derives from — the missing row and the missing refusal.** Add to the four-row table:

```markdown
| `data.units.holdout.seed` | digest + the resolved roster | the roster changes, or the unit declaration does — see below |
```

  and extend the "**A seed that is *present* must be one or the other**" paragraph's last sentence to read:

```markdown
`sweep.sample.seed` is refused as `E-SWEEP-SAMPLE-INVALID`, `assign.<axis>.seed` as `E-DATA-ASSIGN-SEED`, and `holdout.seed` as `E-DATA-HOLDOUT-SEED`. A pinned `holdout.seed` is excluded from the design digest the same way a pinned `assign.<axis>.seed` is, and for the same reason: a seed that is itself inside the digest it is mixed with would make the derivation self-referential, and would move every *other* derived draw in the run.
```

  **(f) § Weighted samples — the `resample` × `holdout` sentence.** Extend the sentence beginning "`fold`, `holdout`, and `assign` all take a `stratify_by` already" with:

```markdown
A `holdout` also decides what a draw is *over*: `resample` draws from the per-unit table, which under a holdout holds the test partition alone — see [A fixed holdout split](#a-fixed-holdout-split).
```

  **(g) `docs/superpowers/spec-defects.md` — file the `technical_n` gap.** Append a new entry at the end of the open section:

```markdown
## OPEN — `technical_n` is a whole-roster figure beside a test-partition `n`

`cli._cond_beside_n` withholds `technical_n` from a condition whose roster was narrowed to
an arm, on the stated grounds that "copying a whole-roster figure onto a subset states a
spread nobody computed over that subset". A `data.units.holdout` narrows the same way and
the same withholding is not applied: `technical_n` is `{min, max, median}` over the whole
roster's measurement counts, and under a holdout it would sit beside an `n` counting the
test partition alone.

**Deliberately not closed by H3d.** It needs `data.units.measurements` *and*
`data.units.holdout` declared together, which no config in
`docs/feasibility-llm-growth-studies.md` does, and closing it inside H3d's task 15 would
add an unbudgeted behaviour change to the task the scoping already names as the one most
likely to ship wrong. The mechanism is cheap when it is wanted: `_cond_beside_n` already
takes the un-narrowed roster as its third argument and decides by identity.

**Found by:** H3d, Task 2 (documents-only). **Owner:** whichever slice next changes
`_cond_beside_n`, or H3c-3 if it retrofits the holdout to cells first — re-owner this entry
when that slice finishes rather than leaving it pointing at a closed one.
**Severity:** Minor. Both numbers are individually true and separately labelled; the fault
is that a reader must know which roster each was computed over.
```

- [ ] **Step 4: Run, confirm it passes** — re-run every grep from Step 1: each code now prints a non-zero count, the `allocation.json` example carries `seed` and `strata` inside its `holdout` block, and `holdout.seed` appears in the `auto` table. Then the **mechanical pass** over `docs/reference.md` and `docs/superpowers/spec-defects.md`: `grep -n ' $' docs/reference.md docs/superpowers/spec-defects.md` returns nothing; `grep -nP '\t' docs/reference.md` returns nothing; every new table row has the same column count as its header (`E-` rows are 2 columns, § Validation rows are 2, the `auto` table is 3); every `#anchor` added above resolves against a heading that exists (`grep -n '^#' docs/reference.md`); no heading was added, so no anchor can collide; `×` was not needed and no `x` was used for multiplication. Then the **cross-document pass**: `grep -rn "holdout" docs/design-principles.md README.md` — confirm nothing there states a rule these edits contradict, and in particular that no passage shows `holdout` as producing a derived value these edits now declare settable, or the reverse. Then `uv run pytest` — `tests/test_materialize.py` pins the generated config's comment text; these edits touch no `materialize.py` line, so it must still pass untouched.

- [ ] **Step 5: Mutate** — a documents-only task has no code mutation, so mutate the **sweep** instead, which is the thing that can silently be wrong here. Temporarily change one occurrence of `E-DATA-HOLDOUT-VALUES` in `docs/reference.md` to `E-DATA-HOLDOUT-VALUE` and re-run the Step 1 loop: it must print `E-DATA-HOLDOUT-VALUES 0`. That proves the loop can fail. Edit it back in place and re-run; it prints a non-zero count.

- [ ] **Step 6: Commit** — `docs: settle the holdout's three under-specifications, its thirteen codes, and the inference base`. Use `git add -f docs/superpowers/spec-defects.md` if `scripts/sdd-workspace` has clobbered `.superpowers/sdd/.gitignore` in the meantime.

---

