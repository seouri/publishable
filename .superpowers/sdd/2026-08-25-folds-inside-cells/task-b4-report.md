# Batch D, tasks 14–17 — report

**Status: all four complete.** Gates clean at every commit: `ruff check`, `ruff format --check`,
`mypy` (56 source files), and the **full, unfiltered** `uv run pytest` read from the run itself.

| Task | Commit | Full suite at that commit |
|---|---|---|
| 14 — `validate` sees the cells, both ends | `57cfc55` | 3401 passed, 1 skipped, 2 xfailed |
| 15 — the arm-narrowed train side (Ruling II) | `e01f240` | 3402 passed, 1 skipped, 2 xfailed |
| 16 — `E-DATA-HOLDOUT-CELLS` retired | `d22268d` | 3399 passed, 1 skipped, 2 xfailed |
| 17 — the resume re-derives the folds (Ruling KK) | `dde4789` | 3401 passed, 1 skipped, 2 xfailed |

Baseline was 3398/1/2. The arithmetic: +3 (task 14) → +2 (task 15: F4 and its `run`-scope control,
minus the deleted assert test) → −4 +1 (task 16) → +2 (task 17).

---

## Ruling II — the invariant, demonstrated rather than asserted

**The assert dies in `e01f240` and `holdout_train` comes from the arm in that same commit, with F4.**
Measured over **every commit on the branch**, whitespace-insensitively (a line-based `grep` reads
zero at every commit, because `ruff format` splits the assert across lines — the sweep was proved
able to fail before it was believed):

```
assert=1 narrowed=0   bc1aea4 … 57cfc55   (23 commits, task 1 through task 14)
assert=0 narrowed=1   e01f240  task 15
assert=0 narrowed=1   d22268d  task 16
assert=0 narrowed=1   dde4789  task 17
```

**No commit exists with `assert=0 narrowed=0`.** `e01f240` carries, in one commit: the deletion of
`assert holdout_train is None or arm_members is None`; the per-arm narrowing; and F4
(`test_h3c3_a_condition_scoped_holdout_trains_only_on_its_own_arm`), which is a **direct
`execute_plan` call** and so could exist at no earlier commit — that call trips the very assert being
deleted. Task 16 retires `E-DATA-HOLDOUT-CELLS` strictly after, in `d22268d`.

### The load-bearing disagreement with the brief — the brief's own snippet ships an empty train side

The brief (and the plan's task 15 section) prescribes:

```python
train_units = UnitList([u for u in holdout_train if u.key in arm_keys])
```

`arm_keys` is the local the **test-side** narrowing built, and `cli` passes `units=eval_roster` —
`_evaluation_roster(roster, holdout_plan)`, the **test** partition. So `arm_keys` is `arm ∩ test`,
and `holdout_train` is `roster ∩ train`, which is **disjoint from test by construction**. The
prescribed expression yields the **empty set for every arm**: shipped as written it would have
replaced a cross-arm leak with a step that fits on nothing. What surfaced it is the brief's own
demand that F4 assert the train side non-empty as well as contained — a subset assertion alone
passes on `[]`.

What shipped instead recomputes `_arm_keys` over the **train side's own keys**:

```python
train_arm = _arm_keys(execution.condition_index, {u.key for u in holdout_train}, arm_members)
train_units = UnitList([u for u in holdout_train if u.key in train_arm])
```

`_arm_keys` rather than a hand-written membership test, so the "the plan and the resolved arms
disagree" raise is not a second answer to which units are in this arm; and sited inside the existing
`condition_index is not None` guard, so a `run`- or `summary`-scoped execution keeps the whole
training roster — copying **where** the fold branch's narrowing sits, not only what it calls.

### F4 and its mutations

Eight units, two arms of four, **asymmetric** train sides (`{u0,u1,u2}` against `{u4,u5,u6}`), with
condition **1** asserted as well as condition 0.

- **MU-8** (narrow to `arm_members[0]` rather than the execution's own arm): **1 failed, 3401 passed**
  at `e01f240`+mutation — and the one failure is F4. *Checked against the fixture body in advance*:
  MU-8 is a **no-op at condition 0**, so a fixture exercising only the first condition would have been
  blind. That is why F4 asserts condition 1.
- **MU-8b, added because MU-8 alone does not demonstrate the leak is closed.** The pre-slice
  composition restored (`train_units = holdout_train`, unnarrowed) with the assert already gone — the
  exact state Ruling II forbids. **1 failed, 3401 passed**, F4 alone.
- Reverted by editing back, `diff` against a pre-mutation copy reporting **IDENTICAL**, and verified
  by **re-running the full suite**: 3402 passed.

`test_a_holdout_beside_cells_is_a_core_defect_not_a_silent_choice` is **deleted** — it pinned the
assert. Its fold sibling's docstring claimed `E-DATA-HOLDOUT-CELLS` "closes the arm interaction";
that clause is deleted rather than rewritten.

### Second disagreement — the "three docstring sites"

The brief: *"Update `cli._resolved_holdout`'s and `execute_plan`'s docstrings where they cite
`E-DATA-HOLDOUT-CELLS` as the reason a branch is unreachable — three sites."* Grepped
newline-insensitively over `src/`, **every hit attributed**:

| File | Hits | Attribution |
|---|---|---|
| `cli.py` | **0** | Task 13 (`40cd858`) had already rewritten that paragraph. The brief is stale. |
| `runner.py` | 2 | The assert and its comment — task 15's, both handled. |
| `units.py` | 4 | A **different** claim: that a holdout's `stratify_by` cannot name a group axis *because* the pair is refused. Task 16's, since that is when the ground goes false. |
| `validate.py` | 1 | The emit site itself — task 16's. |

The whitespace-normalized counts equal the line counts at every file, so no spelling straddles a
break.

---

## Task 14 — `E-DATA-HOLDOUT-EMPTY`, and the two rows

**(a)** `_holdout_test_roster` now calls `units.holdout_within_cells` with `_resolved_cells`' answer,
threaded from `validate_config`'s single local. **The helper already existed** — task 13 built it —
which is what the brief's *"grep for a helper that already exists before writing one"* is about;
nothing new was written. `holdout_for` leaves `validate.py`'s import list.

Two **forward claims task 13 shipped were false at `40cd858` and are true at `57cfc55`**, checked by
grep rather than assumed: `cli._resolved_holdout`'s *"the same single producer
`validate._holdout_test_roster` calls"*, and `units.cell_label`'s *"`holdout_within_cells` and
`validate._check_holdout` now name one too"*.

**(b)** The `E-DATA-HOLDOUT-EMPTY` bound is the thinnest **populated** cell when cells resolve. The
predicate is `units.populated_cells`' — the same projection the draw loops over — rather than a
second spelling, and it **replaces** rather than joins the roster-wide bound, because `holdout_sizes`
is largest-remainder and so non-decreasing in `n`: a thinnest cell that clears leaves nothing for a
roster-wide test to catch.

**Every `E-DATA-HOLDOUT-EMPTY` site, grepped newline-insensitively over `git ls-files` and attributed:**

| Where | Hits | What each is |
|---|---|---|
| `src/publishable/validate.py` | 5 | The docstring enumeration entry (updated), the `cells`-reader sentence (added), the `frac`-interval paragraph's cross-reference, **the emit site**, and `validate_config`'s note on why the code has rows in both tables. |
| `src/publishable/units.py` | 4 | `holdout_for`'s worked `n=2, frac=0.1` example, its "both sides are refused empty" rule, **its raise**, and `holdout_within_cells`' re-raise paragraph. |
| `docs/reference.md` | 2 | **The two rows**, both moved. |
| `tests/test_validate.py` | 15 | This task's three new tests plus the shipped `_check_holdout` fixtures. |
| `tests/test_units.py` | 4 | `holdout_for`'s own raises, at the source. |
| `tests/test_cli.py` | 2 | Task 13's C9/C22 pin, both sides. |
| `docs/superpowers/**`, `.superpowers/sdd/**` | — | The development record; exempt, and retro-editing it destroys the evidence it holds. |

**Which table's scope sentence put each row where.** § Errors `validate` reports says *"What decides a
row's table is whether a command **reports** it or core **raises** it"* — `_check_holdout` collects
through a `Collector`, so the declared-`frac` bound is that row, and it gained the cell denominator.
§ Errors core raises is the raising surface — `units.holdout_for` raises against a **realized** split
— so that row gained `holdout_within_cells`' re-raise naming the cell. Both are the **same code**: the
remedy is unchanged (widen `frac`, or resolve more units) and a second code would give one remedy two
names. The **train** side was deliberately not widened into the `validate` row: § Errors core raises
already owns it (*"the train side of any draw, since `validate` tests the test side alone"*), and
widening would give one fault two surfaces with two messages.

The ten-finding docstring enumeration is **updated**, not left stale.

### The empty-cell train-side raise, made to happen

C9's shape was made to happen and is pinned, at both ends:

- **At the source** (task 13's `test_h3c3_a_thin_cells_holdout_raises_naming_the_cell_on_both_sides`,
  re-read and re-run here): `holdout_for(UnitList([]), block, seed=7)` raises `E-DATA-HOLDOUT-EMPTY`
  reading *"over 0 resolved units leaves the **train** side empty"* — the train side, because
  `holdout_sizes(0, 0.2) == (0, 0)` and train is checked first. A per-cell message hard-coding "test"
  is wrong for that shape.
- **At `validate`, which is this task's end and was unpinned**: an empty cell must **not** become the
  bound. `holdout_sizes(0, 0.2) == (0, 0)`, so a bound taken over `min(cells.items(), key=len)` would
  refuse a design whose every drawn cell splits perfectly, and would name a cell no unit is in.
  `test_the_thinnest_cell_bound_skips_an_EMPTY_cell_rather_than_bounding_on_zero` calls `_check_holdout`
  directly with a hand-built empty cell (unreachable from a clean config — `units.arms_of` raises
  `E-DATA-ASSIGN-LEVELS` for a declared level no unit's value names, and `_resolved_cells`' `try`
  turns that into `None`) and pairs the absence with a **populated** thin cell that must report.

### Fixtures and mutation

- **F7**: 20 units split **18/2** at `frac: 0.2`. `holdout_sizes(20, 0.2) == (16, 4)` clears the
  roster; `holdout_sizes(2, 0.2) == (2, 0)` does not. Message asserted, not only the code.
- **Can-fail control**, paired in the same test: the same 20 units split **10/10**,
  `holdout_sizes(10, 0.2) == (8, 2)`, nothing reported.
- A no-cell message pinned **by equality**, so a widening that silently renamed the roster branch is
  visible. *Its first draft asserted `holdout_sizes(4, 0.2) == (4, 0)` and was wrong* — the measured
  value is `(3, 1)` — caught by computing rather than by reading; the fixture is two units.
- **MU-13** (bound left at `len(roster)`): **2 failed, 3399 passed** — F7 and the empty-cell test,
  and nothing else. Reverted by editing back, `diff` **IDENTICAL**, re-run: 3401 passed.

**Also deleted, unprompted:** a comment at the `_check_holdout` call site reading *"at this commit
`_check_holdout` reads neither"* of `roster`/`cluster_by`, which its own docstring contradicts
(*"Three of the ten read `roster`"*). Deleted rather than rewritten.

---

## Task 16 — the retirement, and MU-15's real catcher

`_check_evaluation_split_cells` is **deleted** with its call site; the fold arm went with task 10 and
the holdout arm was all that remained.

**`allocation.json`'s `holdout` gains `within: [<axis names>]`**, derived by
`build_allocation_document` from its own `group_axes` argument. `HoldoutPlan` gains no field and the
function still takes no roster. `train`/`test` stay flat. **C15 verified rather than carried**:
`read_allocation` has exactly two call sites (`lineage.py`'s definition, `cli.py`'s one call), and
`report.py`/`study.py`/`diff.py` contain the string `allocation` **zero** times — the sweep's can-fail
control (`grep -c "def "` over the same three files: 37/23/11) confirms the file list is real.

`reference.md` § `allocation.json` — who went where prints the key. Its document already declares an
`arm` axis beside a holdout, so it **is** the cell-drawn shape; the JSON block was re-parsed after the
edit and the anchors and column counts re-checked. Task 21 owns every other document site.

### MU-15 — the brief's predicted catcher is blind, and it was named in advance

The brief: *"MU-15: write `within` unconditionally — a no-axis `allocation.json` assertion **and
guard-pin arm C** both fail."* **Arm C does not fail**, and this was derived from its body before the
run: arm C's project is `_h9b_drawn_project`, which declares drawn arms and **no holdout**, so there
is no `holdout` block for a `within` to appear in.

Measured — **4 failed, 3395 passed**, arm C among the passes:

- `test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block`
- `test_a_read_holdout_records_neither_seed_nor_strata`
- `test_a_drawn_unstratified_holdout_records_its_seed_and_no_strata`
- this task's `test_a_holdout_drawn_within_cells_discloses_the_axes_it_was_drawn_inside` (its can-fail
  half: `'within': []` appearing on a no-axis document)

The three shipped ones catch it because they compare the holdout block by **equality**. Reverted by
editing back, `diff` **IDENTICAL**, re-run: 3399 passed.

### Tests deleted beyond the one the brief names

C18 names `test_a_group_axis_alone_triggers_the_refusal_without_between`. **Three more pin the same
deleted check** and would have failed:

- `test_allocation_between_alone_triggers_the_refusal_without_a_group_axis` — pins the `where` ternary
  that no longer exists. Deleted.
- `test_an_empty_group_axis_alone_does_not_trigger_the_refusal` and
  `test_an_evaluation_split_without_a_cell_structure_is_not_refused` — absence-only controls whose
  own docstrings name the trigger tests as their evidence. With the trigger gone they assert the
  absence of a code nothing emits. Deleted.

`test_a_holdout_beside_a_cell_structure_is_refused` is **rewritten to what is now true**, task 10's
precedent at the same fixture: 15 units, 12/3, `frac: 0.2` validates clean, because
`holdout_sizes(3, 0.2) == (2, 1)` — measured — and the retired code is asserted **absent** from the
same finding set so a clean verdict cannot be arriving from where the refusal used to.

*A near-miss worth recording:* the first deletion pass took each `def` up to the next `def` and so
swallowed the module-level `_FIFTY_CLUSTERS` constant that sat between two of them. Caught by running
the two affected files, not by reading; restored.

### Four code sites grounded on the retired refusal

Named by neither task 15's nor task 16's brief. `units.py` justified *four* times — including inside a
**raised message** — that a holdout's `stratify_by` cannot name a group axis *"since
`E-DATA-HOLDOUT-CELLS` refuses a holdout beside one"*. The **behaviour** is unchanged and comes from
§ Validation's *Stratification attribute exists* (`E-DATA-HOLDOUT-STRATIFY-UNKNOWN`); only the grounds
go false. **The false grounds are deleted, not rewritten.** `holdout_within_cells`' historical
sentence keeps the code name and now says when it was retired.

---

## Task 17 — Ruling KK

### Step 1: the safety argument was made to fail, and here is the output

F5 was written and run against the **unmodified** `_resumed_allocation`, before any replacement text
existed. It failed exactly at the claim:

```
    expected = partition_within_cells(overridden.roster, len(prepared.partitions),
                                      overridden.digest, cells_of(overridden.group_axes))
>   assert [[u.key for u in part] for part in overridden.partitions] == [...]
E   AssertionError: assert [['p04', 'p10...'p09', 'p03']] == [['p04', 'p10...'p09', 'p03']]
E     At index 1 diff: ['p05', 'p00', 'p08', 'p01'] != ['p05', 'p00', 'p08', 'p02']
```

**Same roster, same design digest, one unit swapped between the two arms in the recorded
`allocation.json`** — and the fold partition moves by exactly that unit. *"`partition_units` is a pure
function of the roster and the design digest"* is false under cells, measured, not argued.

**And the guards cannot see it**, which is why it needed a fixture: `_resumed_allocation` compares
the axis SET, each axis's level SET, and each axis's recorded key set against the roster's, in both
directions, and **nothing about membership within a level or about roster order**.

*On C11's literals:* the roster shape they were computed against is not recoverable from the
correction (six units, an axis with a level `c`), and no roster this task could construct reproduced
`sha256:f3ba4914…` / `2988051695` / `[u01, u04, u05]`. **The property those literals exist to
establish was measured directly instead**, on `u01`..`u06` at digest `"d"` with
`{"method": "random"}`: forward `units_hash` `sha256:81acbe3f…` against reversed `sha256:004c16ed…`;
`assign_seed_for` **1032553618** against **593484377**; the realized `c` arm `[u02, u01, u06]` against
`[u03, u01, u02]` — a different **set**, same size, from the same six keys. Roster order moves the
draw, and the set-equality guards pass regardless. F5 instantiates the same blindness through a
swapped membership, which needs no roster rewrite between attempts.

### Step 2 and 3

The re-derivation calls **`units.partition_within_cells`** — the same single producer `_prepare_run`
calls — on the **overridden** axes, and `replication.fold_members_for` follows. Nothing is re-derived
by hand. The `stratify_by` map both producers need is now **one helper**, `cli._fold_strata`, rather
than the same dict comprehension written twice. The docstring paragraph headed *"Fold partitions are
deliberately not touched here"* is **deleted** and replaced by a statement of what is now true.

**A disagreement with Decision 5's wording, and it is required rather than optional.** The design says
re-derive *"unconditionally, with no `if group_axes` gate"*. A **`prepared.partitions is None` guard
is necessary**: that is a design with **no `fold` level**, so there is no `k` to draw and nothing to
replace — and guard-pin arm C's own project is exactly that shape (`repeats: [{kind: seed, n: 2}]`).
The forbidden gate is on `group_axes`, and it stays forbidden. Both are stated in the replacement
docstring so the distinction is not left to be re-derived.

### Guard-pin arm C — measured, and it does NOT move

**Not edited.** Post-edit state matches the one specified in advance: *unchanged*. Two independent
reasons, both measured: `within` is rebuilt by `build_allocation_document` from `group_axes`, which
this function overrides consistently, and arm C's design declares no `fold`, so the re-derivation does
not run for it at all. Arm C passes at `d22268d` and at `dde4789` without an editor. **No other pin
arm was opened.**

### Fixture F5, and every moved-or-added assertion's own mutation

F5 is **`groups × fold`, never `groups × holdout`** (C27), with a **`random`** axis — under
`by_attribute` the recorded membership and a fresh re-read coincide, which is the
correct-and-buggy-readings-coincide trap pointed the other way. Its assertions are on **membership**:
both decompositions give 6/6 arms and three folds of four, so a size assertion passes under either
reading. It asserts equality against the producer's own answer on the overridden axes, **inequality**
against `prepared`'s pre-override partitions (without which the equality is satisfied by a
re-derivation that changed nothing), that the sizes are unchanged (so the difference is membership),
and that the union is still the whole roster.

- **MU-9** (the pre-slice code — no re-derivation): **2 failed, 3399 passed**. F5 and the MU-10
  replacement, and nothing else.
- **MU-10** (add a `group_axes` gate): **named blind in advance, and the replacement is owed and
  paid.** A gate is invisible to any byte-identical-partition assertion — the no-axis arm **is** the
  identical partition, which is the proof it is a no-op — and to guard-pin arm D, which wraps
  `_prepare_run` and never enters this function. The replacement,
  `test_h3c3_a_no_axis_resume_still_calls_the_producer_and_gets_the_same_folds`, asserts the producer
  is **called**, with arm D's own counting technique on **both** `cli`'s imported binding and `units`'
  own, summed. **Measured: MU-10 fails that pin alone — 1 failed, 3400 passed** — so every other
  shipped assertion, arm D included, was blind to it exactly as predicted.
- Both reverted by editing back, `diff` **IDENTICAL** each time, each verified by **re-running the
  full suite**: 3401 passed.

That replacement is a **direct** call, and the reason is worth carrying: a no-axis, no-holdout design
writes **no `allocation.json` at all** (`build_allocation_document` returns `None` when neither
partition is declared) and `command_resume` calls `_resumed_allocation` only when `read_allocation`
returned one — so the no-axis arm is unreachable through a real resume. That is an argument for a
direct call, not for leaving the arm unpinned.

---

## Concerns, for the reviewer

1. **`Prepared.cells` is not replaced by `_resumed_allocation`.** Decision 5 and the brief name
   `partitions` and `fold_members` only, and C20 fences `Prepared`'s other fields, so this was
   followed rather than widened. The residual was measured rather than assumed: `cells`' one reader
   below the override is `sweep.yaml`'s `partitions_within`, which projects **axis names** out of the
   first populated cell, and the guards force both sides' axis and level sets to agree — so a stale
   object and a re-derived one give that projection the same answer. **If a reviewer wants it
   replaced, it is one more field in the existing `dataclasses.replace` and the local is already
   computed.**
2. **`spec-defects.md`'s OPEN entry *"an evaluation split cannot be drawn within a cell"* is now fully
   closed by the code** — task 10 retired `E-REPL-FOLD-CELLS`, task 16 retired
   `E-DATA-HOLDOUT-CELLS`, and both splits draw within cells. It is **not** struck here: filings are
   batch E's, and `docs/superpowers/**` is fenced off this batch. It names H3c-3 as the owner of the
   retirement, so whoever takes it should strike it rather than re-own it.
3. **`reference.md` § A fixed holdout split still says the combination "is not built"**, and
   § Clustered units and `experimental-designs.md` § Between-subjects factorial with it. Those are
   **task 21's** by name, and task 21 has not run yet — the branch's `8862957` is a plan amendment,
   not the document sweep. Until it does, three normative sentences are false against the code.
4. **Task 22's end-to-end `groups × holdout` run is now constructible** and was not attempted here.
   Nothing in this batch exercises a *real* `run` that draws a holdout inside cells and hands a step
   its own arm's train side — F4 is a direct `execute_plan` call, by Ruling II's own design. That
   confirmation is still owed.
5. **`_h9b_holdout_project`'s docstring reason has moved.** It said the two halves of
   `allocation.json` "cannot be exercised by one config on this build"; that is false as of
   `d22268d`. Updated in place to say what the fixture now exists to pin (the holdout-only document,
   the shape with no `within`) rather than deleted, because the fixture is still wanted.
