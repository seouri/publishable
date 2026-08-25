# Batches E and F — tasks 18 through 23, the last of H3c-3 and the last of the project

**Status: all six complete. ONE BLOCKING ITEM for the controller, at the top.** Written 2026-08-25.

| Task | Commit | What landed |
|---|---|---|
| 18 | `3c0e2f6` | `W-DATA-CELL-THIN` (Ruling JJ), gated on a cell structure |
| 19 | `810fbee` | The empty cell × the per-cell bound; the per-stratum bound is recorded, not added |
| 20 | `cb48191` | The struck filing, the governing re-ownering, the three new filings |
| 20 fu | `34fef75` | The governing block's counts stated against a moment |
| 21 | `be51e77` | The documents — and H9d guard-pin arm C is **RED** |
| 22 | `7ef6846` | Two real runs; the STEP reads `io.units.train` under a group axis |
| 23 | `dbe71c0` | Two real resumes; the roster-order lever measured blocked; § Executability |

Branch base: batch D's follow-up at `c44c34d`, whose full unfiltered suite I confirmed myself
before editing anything: **3402 passed, 1 skipped, 2 xfailed** — the figure the dispatch gave,
measured rather than carried. Final: **3416 passed, 1 FAILED, 1 skipped, 2 xfailed**
(3402 + 6 + 4 + 2 + 2). `ruff check`, `ruff format --check` and `mypy` (56 source files) clean at
every commit.

---

## 0. BLOCKING — H9d guard-pin arm C is red, was NOT refreshed, and the controller must ratify

`tests/test_cli.py::test_h9d_arm_c_two_of_the_four_documents_are_byte_identical_at_merge[docs/experimental-designs.md]`
**fails.** The arm declares **NO AUTHORIZED EDITOR**, and its own docstring says *"a red arm here is
a FINDING — a hash to investigate, never a hash to refresh."* **I did not touch it.**

- The **other** parametrization, `[docs/design-principles.md]`, **passes** — the blast radius is one
  file.
- The computed digest is `868a51dd8800062bc85a753c60524e15f48c040790aec0a3f836fdbadd4bf81d`, so
  ratification is one line in `_H9D_ARM_C_DIGESTS`.
- **The argument for ratifying rather than reverting.** Arm C is a **scope claim, not a correctness
  pin on behaviour**: its docstring excludes `README.md` and `reference.md` *because H9d's own tasks
  12 and 14 had to edit them*, so what the arm asserts is *H9d touched neither of these two*. H3c-3's
  charter overrides that for one of them. `experimental-designs.md` § Between-subjects factorial said
  *"A fold or a holdout drawn within each cell is not built"* — **false against the code**, found by
  batch D (its concern 3), named in task 21's brief table by the controller, and named again in the
  dispatch as mine. **No slice follows to correct it later.** The arm did not catch a defect; it
  caught a later slice being chartered to touch a file an earlier slice froze.
- Reverting the sentence instead would ship a knowingly-false normative sentence in a document that
  will never be edited again. That is the trade, stated so the controller decides it rather than me.

**No other pin arm was opened.** H3c-3's own arms A, B, C, D and E all pass; arm E is the one my task
18 code had to satisfy and MU-11 is caught there.

---

## 1. Task 18 — MU-11 built and run, and the gate proven not to fire on a generated project

`validate._check_cell_size` emits `W-DATA-CELL-THIN` from **one** site, once, for the thinnest
**populated** cell below `limits.min_units_per_cell`, over `_resolved_cells`' decomposition, gated on
`cells is not None`.

**MU-11 was owed by this task (batch A declared it in advance, in arm E's own docstring, because my
code did not exist yet) and it is paid.** Written as the naive ungated implementation C16 actually
warns about — a no-axis design read as one cell holding the whole roster — rather than as the removal
of the `return`, which would raise rather than warn and so would test nothing. **Measured against the
full unfiltered suite: 4 failed, 3404 passed.** The four:

| Failing test | What it proves |
|---|---|
| `test_h3c3_pin_arm_e_a_six_unit_no_axis_config_validates_with_no_findings_at_all` | The arm captured for MU-11 |
| `test_a_generated_local_config_validates_with_no_version_finding` | A **really generated** project warns |
| `test_no_enum_comment_names_a_value_validate_or_run_would_refuse` (`test_materialize.py`) | The scaffold's own config warns |
| `test_the_thin_cell_warning_is_gated_on_a_cell_structure_resolving` | This task's own config-level control |

**Three of the four run over projects `publishable init`/`new` produced**, which is the direct
evidence the launcher asked for: with the gate, they are silent; without it, they warn. `materialize`
writes `min_units_per_cell: 20` into every one of them.

**MU-12** (largest cell for smallest) fails the 7/5-at-floor-6 fixture **alone** — 1 failed, 3407
passed. F3's equal 6/6 arms are blind to it by construction, which is why both fixtures exist and why
F3's docstring says so.

Both mutations reverted by editing back and `diff`-ing **IDENTICAL** against a pre-mutation copy, each
verified by re-running the full suite.

### The disagreement that mattered: `units.thinnest_cell` is the WRONG helper here

Batch B's concern 2 predicted tasks 14 and 18 as `thinnest_cell`'s callers. **Task 18 is not one, and
the two answers genuinely differ.** `thinnest_cell` returns a **fold basis** — the cluster count under
a declared `data.units.cluster_by`, the unit count otherwise — because `replication._fold_k` bounds
`k` against indivisible things. `limits.min_units_per_cell` counts **units**, and says so in its name.
On a design whose thinnest cell holds 2 clusters of 5 units, at floor 6, this check must be silent and
`thinnest_cell` would have it report — naming a cluster count as though it were a unit count. **That
fixture ships**
(`test_the_thin_cell_floor_counts_UNITS_where_the_fold_bound_counts_clusters`), with a can-fail half
at floor 20 where the unit count really is thin. `units.populated_cells` is the shared piece and it
**is** shared, so the empty-cell rule has one spelling and not two.

### Documents

§ Warnings core reports gains **one** row, inserted in the table's alphabetical position (after
`W-APPARATUS-UNANSWERED`). § Validation's *Cells are populated* and *Allocation is coherent* both lose
*"specified, not built in this build"* and both name `W-DATA-CELL-THIN` — **two § Validation rows,
one code**. Per the design's own instruction: **no precedent was found for two § Validation rows
naming one code**, and I did not find one either; the nearest shapes are four rows over one derivation
with **four** codes, and one row pointing at another row. Stated rather than implied. § The one config
file's comment is rewritten to state the gate. § Weighted samples' *"and nothing warns"* paragraph is
**deleted**, being false after this commit; the one true clause in it (an arm no unit resolves to is
`E-DATA-ASSIGN-LEVELS`) survives inside the *Cells are populated* row, so a true claim was not deleted
along with the false ones.

`experimental-designs.md`'s *"`limits.min_units_per_cell` is checked per cell"* needed **no edit**:
it was false before this commit and is true after it. It sits on the same line as task 21's sentence,
which is why this is stated rather than left to look like an oversight.

---

## 2. Task 19 — the brief's second bullet is FALSE against the code

**The brief says:** *"A cell that is **empty** … makes the bound `0`, so any `k ≥ 1` is refused."*
**`units.thinnest_cell` skips cells holding no units**, so an empty cell bounds nothing. Measured on a
roster whose `sex=f × arm=treatment` intersection is empty — `cells_of` gives **3 / 3 / 4 / 0** — and
pinned at both ends:

- `k: 3` validates clean on the fold side; `k: 4` is refused naming `sex=m, arm=control`, with the
  **empty** cell asserted **absent** from the message. A bound naming it would send a reader to a
  combination nobody can enrol into.
- The same reading at the holdout end, a different code and a different loop:
  `holdout_sizes(3, 0.2) == (2, 1)` is clean, `frac: 0.1` bites and still names a populated cell.
- **Recorded where it cannot be refused:** an empty cell with no evaluation split earns **nothing at
  all** (asserted by equality), and with a floor declared earns **only task 18's warning** — which
  names the thinnest **populated** cell, not the empty one. That is measured, not the brief's
  phrasing: the two are different claims and the second is the true one.

An empty cell is instantiable from a clean config **only through an intersection** — a single axis's
unrealized level is `E-DATA-ASSIGN-LEVELS`, which `_resolved_cells`' `try` turns into `None`. That is
why the fixture crosses two axes.

**The `partition_units` docstring**, body untouched. `k` is checked against **one** basis rather than
*"the whole roster's"*, which cells made false; the independent partition lists are **cells ×
strata**. **I did not adopt the brief's phrase `cells × c × s`**: its `c` is undetermined against the
code — the independent lists are one per (populated cell, stratum), and `clusters` is not a multiplier
of them — so the docstring states the true multiplier rather than the brief's. The paragraph now says
in those words that H3c-3 **moved the basis and multiplied the lists and did not add the bound**, that
**no slice follows**, and that the filing states it as a fact.

---

## 3. Task 20 — every filing struck or left open with "no slice follows"

**(a) Struck.** `## OPEN — an evaluation split cannot be drawn within a cell` is **struck in place**,
never deleted, with the heading rewritten to
`## ~~an evaluation split cannot be drawn within a cell~~ — STRUCK 2026-08-25 (H3c-3): CLOSED, by the
slice this entry named as the owner of the retirement`. The struck note quotes the sentence the entry
turned on — *"**No build draws one**"* — as the thing that is now false, and records that the scope
did **not** change so no re-ownering was needed.

**(b) The governing re-ownering.** Measured at that commit, newline-insensitively over each `## `
section's own collapsed body (this file is hard-wrapped and `H3c-3's remaining 14` wraps mid-phrase in
at least one place, which the `RE-OWNED 2026-08-22` entry hit and recorded):

| Measured | Count |
|---|---|
| `## OPEN` headings | 56 |
| …naming `H3c-3` | 33 |
| …naming *whichever slice* | 10 (2 are the **rejection** of that form; 1 is `technical_n`, re-ownered in its own body) |
| union — what the entry governs | **38** |

The sweep is proved able to fail: the same walk over `Owner:` returns non-zero, over `H99z-4` returns
**0**.

**The correction is written ONCE**, as `## RE-OWNED 2026-08-25`, on this file's own established
precedent — `RE-OWNED 2026-08-19`, `-21` and `-22`, the last of which states the rule verbatim:
*"The correction, once, here rather than five times in five bodies … editing five bodies would destroy
what each recorded on its date."* **No entry changes owner.** Every one already read `unassigned`, and
every one now reads it for a **stronger** reason: *no remaining slice* becomes **no slice follows this
one**. The seven live *"whichever slice next touches X"* owner lines are named by their question, not
by position, and each is stated as shipping open.

`technical_n` is re-ownered **in its own body**, because its own owner line instructed it: *"or H3c-3
if it retrofits the holdout to cells first — re-owner this entry when that slice finishes."* H3c-3 did.
The gap is **wider by one axis**, not closed: `_cond_beside_n`'s third argument is `eval_roster`, which
under cells is the test partition **and** may then be arm-narrowed, so the identity check distinguishes
neither narrowing from the other.

**(c) The three new filings, each quoted by heading:**

1. `## OPEN — a cluster may span two cells, which breaks the between-sides independence H4c's
   clustered unpaired constructions assume — **Owner: unassigned, and no slice follows this one**`
   — with C1's own measured roster named as a fixture that already has one.
2. `## OPEN — limits.min_clusters counts clusters over the whole roster while a resample under a cell
   structure draws inside one — **Owner: unassigned, and no slice follows this one**` — Ruling LL's
   call stands; the precision gap does not, and H3c-3 neither moved it nor made it worse, which is
   recorded so silence is not read as inference.
3. `## OPEN — k is bounded by no per-STRATUM basis, so a stratified fold can still come out empty,
   and cells add a multiplier rather than a bound — **Owner: unassigned, and no slice follows this
   one**`.

**Two filings describing code this slice changed were re-read and RE-MEASURED**, per the rule that a
filing's claims go stale like any other comment: `units.stratum_names`' call-site count **8 → 9**
(`_check_holdout` gained the cell decomposition), and `command_run`'s reference count **195 → 202**,
`cli.py` **34 → 36**. **Neither number is corrected in place**, on those entries' own arguments — the
first says explicitly that chasing the count is the wrong fix — and both re-measurements are recorded
beside the claims they update.

**A self-inflicted fault, caught and fixed in `34fef75` rather than shipped.** The 56/38 figures were
measured **before** the three filings the same commit appends, each of which names H3c-3 in its own
provenance line — so a re-run at that commit returns **59 and 41**. That is a count carried forward
without re-deriving what it counted, sitting inside the entry whose whole subject is stale counts. Both
numbers, and which moment each belongs to, are now stated.

---

## 4. Task 21 — the six sites, and the two the controller keeps

Every site named by what it does, never by position. `reference.md`: *One split, not one cell each*
**removed**; *Folds fit inside the cells* **rewritten back** rather than deleted (it read *"Superseded
by One split, not one cell each"*, and deleting the pointed-at row while leaving the pointer is how a
table acquires a dangling reference); the `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS` rows
**removed from the § Errors registry**; § A fixed holdout split's *"refused, not drawn"* bullet
**replaced**; § Clustered units' paragraph to the **present tense**, keeping *"Partitions are computed
once per run, not once per condition"* and its reconciling paragraph untouched.
`experimental-designs.md` § Between-subjects factorial: *"is not built"* → what is built.

**C2 honoured**: none of these repaired a present-tense falsehood at the time it was written. They
repair a build state that moved.

### The six `E-REPL-FOLD-CELLS` sites, and M15's count is wrong in BOTH directions

M15 says `E-DATA-HOLDOUT-CELLS` → 3 and `E-REPL-FOLD-CELLS` → 4, *"both `reference.md`-only"*.
Measured newline-insensitively over a filtered file list with a can-fail control:

| Code | `reference.md` before | `reference.md` after | `CLAUDE.md` |
|---|---|---|---|
| `E-REPL-FOLD-CELLS` | 4 | **0** | **2 — the controller's** |
| `E-DATA-HOLDOUT-CELLS` | 3 | **0** | **2 — the controller's, and NOT predicted** |

**The controller's amendment named the `E-REPL-FOLD-CELLS` pair. There is a second pair.**
`E-DATA-HOLDOUT-CELLS` also survives at 2 `CLAUDE.md` sites, which M15's *"reference.md-only"* hides
for both codes equally. **Four `CLAUDE.md` sites, not two, and I took none of them.** They are in the
H3d and H4b-1 paragraphs of the repository-status section.

Other M15 checks, every hit attributed: `is not built` 3+1 → **0** (the third `reference.md` hit was
inside the *Folds fit inside the cells* row itself, which is why the count is not 2+1); *One split,
not one cell each* 2 → **0**; `within each cell` 2 → **3**, the growth being the two rewritten
paragraphs plus § A fixed holdout split's new bullet. *Cells are populated* 2 and *Allocation is
coherent* 1 are **task 18's** arithmetic — the deleted § Weighted samples paragraph named both, and
the new *Allocation is coherent* row cross-references *Cells are populated* by name.

### The three false normative sentences, corrected

All three are batch D's concern 3, and all three are in the table above: `reference.md` § A fixed
holdout split, `reference.md` § Clustered units, `experimental-designs.md` § Between-subjects
factorial. Each was **honestly marked** when written and became false when the code moved.

### Both consistency passes

**Mechanical**, over the four documents plus the feasibility analysis, skipping fenced blocks
throughout: relative links, `#anchor` resolution, duplicate anchors, table column counts, empty rows,
trailing whitespace, tabs, invisible unicode, `×`-not-`x`. **0 problems**, with a can-fail control.
**Two false-positive bugs in my own checker were found and fixed before I believed its output** — an
emphasis strip that ate `_` out of anchors (8 phantom bad anchors) and a cell splitter blind to `\|`
(3 phantom column mismatches). Reporting the checker's own defects because a checker that reports
noise is one a reader learns to skip.

**Cross-document**, over the four only. The **worked example** is untouched, verified mechanically:
`git diff` over the branch filtered for its own literals (`0.581`, `0.607`, `0.412`, `0.488`, `0.026`,
`8e21`, `1a2b`, `3d8a`, `6b1f`, `2f5c8d0`, `228`, `240`, `cohort-pilot`) returns **nothing** — the
intervals are not narrowed back. Config completeness: the only config-file change is a comment, and
`limits.min_units_per_cell` was already in § The one config file. Enum comments: none touched. Schema
fields in prose: none added or removed. Declared vs. derived: unchanged. Versions: unchanged. `Status`
column: no command moved. Prevented mistakes: `experimental-designs.md` § Mistakes core prevents makes
no claim about this combination, checked.

**A sweep the brief did not name and I ran anyway**: count phrases and positional row locators whose
referent is either shortened registry or the § Validation table — *"N rows"*, *"N codes"*, *"the two
rows above"*, *"further up"*, *"one row per"*. Every hit attributed; **none refers to a row this task
removed or moved.** The nearest, *Assignment names a method*'s *"the 'Allocation needs arms' and
'Every axis is assigned' rows above, between them"*, names its rows and they are still adjacent.

---

## 5. Task 22 — the real run whose STEP reads `io.units.train` under a group axis

**The debt batch D's concern 4 records is paid.** Task 15's F4 is a direct `execute_plan` call by
Ruling II's own design, so nothing until now had run the arm-narrowed training side through the
command. **Asserting `allocation.json`'s own `train` list would prove what core wrote, not what the
step saw** — which is the gap F4 already covers. So the evidence is produced from the object core
handed the step: `_H3C3_TRAIN_SEEING_STEP` writes `split.json` from `io.units`/`io.units.train`, and
records `n_train` per unit so the fact also survives in the **per-unit table**, in `run.yaml`.

- **`groups × fold`** — 12 units, arms of **9 and 3**, `{kind: fold, k: 3}`. `partitions_within ==
  ["arm"]`; every (arm, fold) pair holds that arm's own share (3 and 1), crossed from `partitions`
  against `allocation.json`'s `arms`; `train == arm − test` and **non-empty** for every
  condition-scoped execution; `n_train` is **6 for `control` and 2 for `treatment`**; the attrition
  identity `resolved == completed + ineligible + failed` holds over a **non-empty** set of blocks
  (returned as a list and asserted truthy, because an identity checked over zero blocks holds
  vacuously).
- **`groups × holdout`** — a separate fixture (C27), seed repeats, `frac: 0.5`. Each arm's test side
  is half of **that arm**; the step's train side equals `arm ∩ recorded train` and is asserted
  **strictly smaller** than the roster-wide train side, which is what makes the narrowing visible
  rather than merely consistent; `n_train` is 3 where a roster-wide side would be 6.

**MU-B caught my own first draft.** The fold fixture began with even 6/6 arms; MU-B (the per-cell loop
reduced to the whole-roster draw) **passed** against it — 12 units in 3 roster-wide folds of 4 happen
to give each arm 2 per fold, so the correct and buggy readings coincided. Found by running the
mutation, not by reading. The fixture is uneven for that reason and MU-B then fails it alone
(`assert 4 == 9 // 3`). **MU-A** (the arm narrowing of the holdout train side disabled) fails the
holdout fixture **and** task 15's F4, and leaves the fold fixture green — two separate branches, which
is why two mutations. Both reverted by editing back, `diff` **IDENTICAL**.

---

## 6. Task 23 — which lever worked, measured

**The roster-order lever is BLOCKED, and the measurement ships as a test.** `resume` compares
`manifest_hash(recorded)` against the tree's and refuses `E-RESUME-INPUT-MOVED`. **Blocked twice
over**, and the second reason was measured rather than predicted: `manifest` records `size` and
`mtime_ns` beside the content hash, so even a **byte-identical rewrite** is refused — the can-fail
half failed with the same code until it restored the recorded `mtime_ns` with `os.utime`, after which
the same resume returns `EXIT_OK`. The refusal is **correct**, and it is pinned so a later reader
finds a fact rather than a story.

**The lever that works is the crashed run's own `allocation.json`** — the artifact `resume` treats as
authoritative and which no hash on the resume path covers. It is the lever F5 already uses
(`_h9b_swapped`) and it instantiates the identical blindness through the command. **The plugin-resolver
fallback was not needed and was not built. The end-to-end arm was NOT declined.**

- **`groups × fold`, `method: random`** — the fixture § 6.2 of the re-scoping says H9b could not
  build. One unit swapped between arms in the record; every post-edit execution has `|test| == 2` and
  `train == arm − test`, which holds only if the folds were re-derived inside the **recorded**
  decomposition. **MU-9** fails it with `assert 3 == 2` — an uneven per-arm fold — alongside F5 and
  the MU-10 replacement.
- **`groups × holdout`** — a separate fixture (C27). One unit swapped **within** one arm's split, so
  no axis guard sees it and no size changes; asserted on the **step's** `split.json`, not on the file
  the test wrote, because `allocation.json` agreeing with itself is a tautology. **MU-H** (the
  recorded holdout ignored) fails it alone.

`_resumed_allocation` was **not touched** (task 17 owns it) and **guard-pin arm C was not touched**.

### § Executability on this build — re-derived, and it does not move

One entry appended; `docs/feasibility-llm-growth-studies.md` is the only file touched there and only
in that section. **All four rows derived per row, no fifth number minted:**

- **Row 1 — 8 of 8, unchanged.** Both retired codes needed a **cell structure**. `grep -n "groups:"`
  → two config hits, **both `groups: []`**; `grep -n "allocation:"` → two config hits, **both
  `within`**; `grep -n "kind: fold"` → **nothing**; the one `holdout:` block sits beside that same
  `allocation: within`. `E-REPL-FOLD-K-TOO-LARGE`'s and `E-DATA-HOLDOUT-EMPTY`'s widened bounds widen
  only when cells resolve, and none do. **The new warning cannot move this row in either direction**:
  the row counts **errors** and a warning never changes an exit code, and its gate excludes all nine.
  `min_units_per_cell: 20` appears in **three** of the config blocks — exactly the shape C16's gate
  exists for.
- **Row 2 — 0, untouched.** No upstream is read and no lineage walked.
- **Row 3 — 7, untouched and now PERMANENTLY unowned.** A construction inside `summarize_step`.
  Task 20's governing entry states its owner as `unassigned` with *no slice follows* as a fact.
- **Row 4 — 1, unchanged.** E5, with the plugin written and installed.

**The four-row table is reproduced byte-identically, H8a cells included**, extracted programmatically
by both methods the preceding entries describe (last `| Figure | Count | Visible to` header read
forward while lines start with `|`; and a fixed six-line slice from the same index) and verified equal
to the H9d entry's after the append. Updating the cells is how a repeated table stops being repeated.

---

## 7. Concerns for the controller

1. **Arm C, § 0.** The one blocking item. Digest supplied; ratification is one line.
2. **Four `CLAUDE.md` sites, not two.** `E-DATA-HOLDOUT-CELLS` has a `CLAUDE.md` pair the amendment
   did not predict, on top of `E-REPL-FOLD-CELLS`'. All four left for the controller.
3. **`CLAUDE.md`'s order line is stale and is not mine.** *"Order of the slices that remain: … H9,
   then H3c-3's remaining 14"* goes false the day this merges, as does *"H3c-3 17 against a charter
   saying 6"* reading as live work. Reported, not taken — same ruling and same reason as the four
   code sites.
4. **`limits.min_clusters`, `min_reported_n`, `max_ineligible_fraction` are untouched and still
   unread where they are unread.** Task 18's brief fences them, and **nothing follows this slice**, so
   they ship that way. `min_units_per_cell` was the only one Ruling JJ decided.
5. **Three things this slice declines ship declined**, filed under § 3(c) with *no slice follows*
   stated as a fact: the spanning cluster, `min_clusters`' denominator under cells, and the
   per-stratum fold bound. None is a deferral and none has an owner to name.
6. **The `_h3c3_split_files_by_condition` helper added in task 22 was edited in task 23**, once, to
   strip `sweep.condition_dir_name`'s `<nn>_` prefix — a drawn axis's condition directory carries the
   index prefix and a `by_attribute` one's did too, which task 22's assertions happened to be blind to
   because they read the label with `split("=")`. Not a pin, my own helper from the previous commit,
   and both tasks' tests pass under the normalized form. Recorded because editing a shipped test's
   helper in a later task is the shape this repo watches.
