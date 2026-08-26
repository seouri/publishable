# Batch B — tasks 4, 5, 6 and 7

**Status: all four complete, gates clean.** Written 2026-08-25.

| Task | Commit | What landed |
|---|---|---|
| 4 | `0a4cf1e` | The hoist inside `_prepare_run`; `Prepared.cells` |
| 5 | `742ad5a` | `validate._resolved_cells` |
| 6 | `6f3c1f8` | The cell-aware basis at the two callers that ask the fold's question |
| 7 | `962fc05` | `E-REPL-FOLD-K-TOO-LARGE` names the cell, at all three emit sites |

Branch base: batch A at `864f702`. Final suite: **3377 passed, 1 skipped, 2 xfailed**
(3355 pre-batch + 22 new). `ruff check`, `ruff format --check` and `mypy` clean at each commit.
The four task commits above closed at 3372; a **follow-up round** (§ 9) added five tests and closed a
self-contradiction in `Prepared`'s docstring.

---

## 1. Task 4 — the order, before and after

**Before** (`864f702`), by function name, inside `_prepare_run`:

`clusters_of` → `fold_basis` (inside the `resolve_repeats` call) → `resolve_repeats` →
`partition_units` → `fold_members_for` → `sweep_block` → `_resolved_group_axes` →
`_resolved_holdout` → `_evaluation_roster` → `arm_members`.

**After** (`0a4cf1e`):

`clusters_of` → `sweep_block` → `_resolved_group_axes` → `arm_members` → `cells_of` →
`fold_basis` → `resolve_repeats` → `partition_units` → `fold_members_for` → `_resolved_holdout` →
`_evaluation_roster`.

`_resolved_holdout` and `_evaluation_roster` did **not** move (C19), and `swept_paths` stayed beside
its own reader.

**Guard-pin arms A, B, D and E were re-run and are unchanged.** `pytest -k h3c3_pin_arm` is 5 passed
at `962fc05` (four arms in `test_cli.py`, arm A in `test_units.py`), and
`git diff bf68454..HEAD -- tests/test_units.py` has **no deleted lines at all**, which is the
mechanical form of "arm A's literals were not edited". Arm C was not touched: task 17 is its sole
authorized editor.

### Disagreement D1 — the hoist is THREE statements, not two, and Decision 12 says two

`_resolved_group_axes` reads `sweep_block`, which was defined **below** the fold region
(`sweep_block = doc.get("sweep") or {}`, immediately above `swept_paths`). It travels with the two
calls; `swept_paths = wide_swept_paths(sweep_block)` does not, and stayed. Measured by moving the two
and reading `ruff`'s `F821`.

### Disagreement D2 — C20's unpack line CANNOT land at task 4, and this is measured

C20 says *"adding `cells` is one field and one unpack line"*. `_execute_prepared` unpacks `Prepared`
into **locals**, and its own docstring says *"a local nothing reads is an `F841`"*. Nothing in phases
6–10 reads `cells` at this commit — its readers are `_resumed_allocation` (task 17) and whatever
writes `partitions_within` (task 11). Experiment: field + unpack line added,
`uv run ruff check .` → **1 error, `F841 Local variable cells is assigned to but never used`**, cited
by line. Edited back and **diffed byte-identical** against a pre-edit copy. **The field landed here;
the unpack line lands with its first reader**, exactly the shape batch A measured for C25 (F401+I001).
**C20 also binds task 17, so that obligation moved and the controller has to route it.**

**And the correction reached the sentence that contradicted it, in the follow-up round.**
`Prepared`'s docstring said `c` *"is therefore the **one** field `_execute_prepared` does not unpack
— so of the thirty-six, thirty-five are read in phases 6-10"*. Both halves went false the moment
`cells` landed, and the appended 37th-field paragraph twenty lines lower did not repair them: **a
sentence contradicting the argument that justifies the thing it describes.** The "one field" clause
now names `cells` beside `c`, and the opening count says *thirty-six when this docstring's
measurement was taken, thirty-SEVEN since task 4* — the `ast` walk's measurement is untouched.
Worth carrying: **appending a correction does not retire the sentences above it**, and the first
attempt at this edit put a line at column 0 inside the docstring, which made `ruff format`
**re-indent the entire docstring to eight spaces** — 50 insertions for a two-sentence change, caught
by reading `git diff --stat` rather than by any gate.

### The `== 36` assertion moved, and the mutation that fails it

`tests/test_cli.py::test_h9b_the_allocation_override_replaces_four_fields_and_round_trips_the_rest`
asserts `len(dataclasses.fields(Prepared))`, now **37**. It is not a guard-pin arm — batch A split arm
C off precisely so this test keeps its own editors — and the docstring says *36 when this test was
written, plus `cells`, added by H3c-3 task 4* rather than being rewritten to claim 37 was always the
number. `Prepared`'s own docstring **appends** the correction: the `ast` walk found 36 and that stays
true as history; `cells` is the thirty-seventh, added rather than found.

### Assert, not assume: realized once per run

`test_h3c3_the_hoisted_axes_and_reduction_are_each_realized_exactly_once` installs counting wrappers
at `cli._resolved_group_axes` and `cli.arm_members` and drives a **real `command_run`** (not a direct
`_prepare_run`), asserting `len == 1` for each. A count rather than a membership deliberately: two
draws of one `by_attribute` axis agree, so a membership assertion cannot see a second call. The test's
reporting half asserts the two condition labels, so it cannot pass by nothing having run.

**MU-16**, a second `arm_members(...)` left behind at the old position: **1 failed, 3356 passed** at
`0a4cf1e`'s tree — that test alone.

**`Prepared.cells`' own mutation**, `cells = cells_of(group_axes)` with the `if group_axes else None`
dropped: **1 failed, 3356 passed** — `test_h3c3_prepared_carries_the_cell_decomposition_and_none_without_an_axis`
alone, on its no-axis half. That is D1-from-batch-A's *"owed once at the caller"* discharged: the
rule is written **once** in `cells_of`' docstring and **once** at this caller, and the caller's
version is `None`.

---

## 2. Task 5 — `_resolved_cells`

Realizes each `sweep.groups` axis through `units.assignment_for` at the **real** `design_digest(doc)`,
in declaration order, threading `resolved=dict(axes)`, then calls `cells_of`. The docstring cites
`_holdout_test_roster` by name and repeats its ground. `_check_assign`'s placeholder digest is
deliberately not copied, with the reason stated where a reader meets it.

**Ten tests.** A `by_attribute` axis (exact memberships); a `random` axis compared against
`cli._prepare_run().cells` **for the same config** — two sources that must agree rather than each
agreeing with itself; `blocked` beside `cluster_by` → `None`, with the same doc/roster under
`method: random` resolving two real cells so the `None` is **attributed to the method**, and
`_error_codes` showing `validate` still reports `E-DATA-ASSIGN-BLOCKED-CLUSTER`; six malformed shapes
→ `None`, each paired in the same test with the resolvable control; no roster → `None`.

**The can-fail control held only after a fixture fix.** The random fixture's first form declared
`assign.arm.seed: 4242`, which makes the draw **digest-independent** — so the digest mutation
(`design_digest(doc)` → `"validate"`) left it green. Measured, not reasoned: the mutation ran, the
test passed, and the fixture was the fault. With the declared seed removed the mutation fails that
test alone: **1 failed, 3366 passed**.

**A second fault the same run exposed**, worth carrying: my `_arm_roster` helper **shadowed an
existing module-level `_arm_roster`** in `tests/test_validate.py`, and the four
`test_assign_levels_*` tests failed on a `TypeError` while `pytest -k resolved_cells` stayed green.
A `-k`-filtered run cannot see a name collision at module scope. Renamed `_h3c3_arm_roster`.

---

## 3. Task 6 — Ruling LL, and which question each of `fold_basis`' three call sites asks

Stated **in the code, at each site**, where a reader meets it, and each cites Decision 4's three-site
table rather than restating it:

| Call site | The question, as the code now says it | What it calls |
|---|---|---|
| `validate_config`'s `basis` → `_check_replication` | *the FOLD's basis* — how many indivisible things a fold can be drawn from, **in the cell that has fewest** | `thinnest_cell` when cells resolve, `fold_basis` otherwise |
| `validate_config`'s `basis` → `_check_sweep`'s `k: all` budget | the same question, **the same local** (C5) | the same one number |
| `_check_resample`'s `limits.min_clusters` | *how many independent draws does a percentile interval rest on* — over the per-unit table, which spans every cell | **`fold_basis`, unchanged** |
| `_prepare_run`'s | the run's own fold basis, same rule as `validate`'s | `thinnest_cell` when cells resolve, `fold_basis` otherwise |

The predicate is `cells is not None` at **both** fold sites and it is one comparison at each, because
`_resolved_cells` and `_prepare_run` both answer triviality as `None`. Two callers deciding
"is this decomposition trivial" for themselves is how `validate` bounds `k` against one number while
the run draws against another.

### C5's seam is now instantiated by a fixture, not only argued

*"It is one local and stays one local"* is the argument, not the check, and a seam named in a brief
and instantiated by no fixture is a shape this project has hit twice in one slice. `_check_sweep`'s
`k: all` budget produces one observable finding, `W-EXEC-BUDGET`
(`len(conditions) × repeat_total > limits.max_executions`), so the discriminating fixture is F2 with
`{kind: fold, k: all}`: 2 conditions, and `repeat_total` of **2** on the cell basis against **5** on
the roster's, giving products of 4 and 10 that a `max_executions: 5` separates. An equal-arm fixture
gives the same product either way and separates nothing.

`test_the_k_all_budget_is_sized_from_the_same_cell_basis_the_bound_uses` pins both directions —
silent at 5, warning at 3 naming *"2 conditions × 2 repeats = 4 executions exceeds 3"*.
**Mutation** (a second, roster-wide basis resolved for `_check_sweep` while `_check_replication`
keeps the cell one): **4 failed, 3373 passed** — that test plus
`test_a_cluster_by_under_a_glob_source_is_reported`,
`test_an_unreadable_cluster_leaves_k_all_unresolved_rather_than_raising` and one more, because the
second resolution sits **outside** the `try` and turns a collecting `validate` into a raising one.
That is the same second-`try` hazard the `min_clusters` comment names, arriving from the other side,
and it is why C5 is *one local* rather than two calls that agree.

**Deleted rather than rewritten**: *"Not threaded through `basis` in this slice; doing so is a cheap
follow-up, not a correctness gap today."* `grep -rn "cheap follow-up" src/ tests/ README.md
docs/design-principles.md docs/experimental-designs.md docs/reference.md` → **zero hits**. The
paragraph above it gained one clause naming cells as the third reason the two derivations are not the
same.

**The prescribed mutation, and the test written for it.**
`test_the_min_clusters_denominator_is_roster_wide_not_the_thinnest_cell`: 16 units in 8 clusters,
`control` holding 3 and `treatment` 5, so the roster-wide count (8) and the thinnest cell's (3) fall
on **opposite sides** of a floor of 4. Both directions in one test — `min_clusters: 4` silent,
`min_clusters: 20` warning and naming 8, not 3 and not 16. Mutation (that site's `fold_basis` →
`cell_fold_basis` over `_resolved_cells`' answer): **1 failed, 3367 passed** — that test alone.

### Disagreement D3 — Decision 8's swallow list is SIX, not five

Wiring `_resolved_cells` into `validate_config` made
`test_a_ratio_whose_values_are_not_usable_shares_is_refused[all-zero]` **crash**: an
`assign.<axis>.ratio` of all zeros reaches `units._apportion`'s `n * weight / total` with
`total == 0`, and `ZeroDivisionError` is an `ArithmeticError` that none of the design's five listed
types catches. Before this wiring nothing in `validate` drew that shape for real —
`_check_assign` refuses it from the declaration. Without the sixth entry a config `validate` is
supposed to **refuse** raises a traceback: the collecting-to-raising fault the whole `try` exists to
prevent, reached through a config the suite already had. `ZeroDivisionError` added, with the fixture
that found it named at the site; the list stays an **enumeration** rather than `except Exception`, for
`REPL_DECLARATION_CODES`' reason. **A correction is appended to the design** (§ *Correction to
Decision 8*) rather than retro-edited into Decision 8. The pin is that existing test, which fails
with the entry removed — measured, since that is how it was found.

---

## 4. Task 7 — three emit sites, and the grep that does not find them

**`grep -rn "E-REPL-FOLD-K-TOO-LARGE" src/` → 6 hits**, every one attributed:

| Hit | What it is |
|---|---|
| `validate.py:3749` | membership in `REPL_DECLARATION_CODES` — the set deciding the raise becomes a finding. **Not an emit site** |
| `validate.py:3877`, `validate.py:3881` | two lines of the comment task 7 added at the forwarding site |
| `replication.py:145` | a comment in `_fold_k` about `stratify_by`'s removal |
| `replication.py:184` | **emit site 2 of 3** — the clusters raise |
| `replication.py:190` | **emit site 3 of 3** — the units raise |

**Emit site 1 of 3 does not appear in that grep at all**: `validate.py`'s `c.error(exc.code, …)` emits
`exc.code`, so the literal is nowhere near it. Six hits, three emit sites, and neither number is the
other — which is exactly why C12 counts sites by reading. Reported as *what was grepped*, not as a
count.

**The clause, at each site.** `_fold_k` gained `cell=None` beside `cluster_by`; `resolve_repeats`
gained `fold_cell=None` to carry it; `_check_replication` gained `fold_cell` and forwards it. Every
existing caller is unchanged, and with `cell is None` both messages are **byte-identical** to today's
— asserted as an exact string, not as an absence. The docstring states that `None` means *no cells
resolved*, not *cells resolved and unnamed*.

**`units.thinnest_cell` was added** because the message must name the **argmin** cell and
`cell_fold_basis` returns an `int`. It is one walk returning `(basis, label)`, with `cell_fold_basis`
delegating to it, so the number and the label cannot disagree about which cell the bound bit on. A
caller re-deriving the label by looking for a cell whose basis equals the number would be a second
derivation of the thing `fold_basis`' single-derivation rule keeps single. Ties go to the first cell
in `cells_of` key order (strict `<`), stated in the docstring **and now in `reference.md`'s
normative row** — which is why the follow-up round gave it a fixture rather than leaving it
documented only: `test_a_tie_between_two_cells_goes_to_the_first_in_key_order`, two cells of two
clusters each so only the order can decide, run in both insertion orders with levels named `aaa` and
`zzz` so *last wins* and *alphabetically first wins* are both ruled out. F2's own cells are 2 and 3,
so it could not have tested this. `test_thinnest_cell_returns_the_cell_the_minimum_came_from` pins
the label following the **minimum** rather than the position, in both orders, and asserts
`cell_fold_basis`' number beside it so the two cannot drift.

**MU-3's refusal half, built and run.** `test_the_fold_bound_is_the_thinnest_cells_and_validate_names_that_cell`
uses F2 exactly: 16 units, `control` = `A`×5 + `B`×3, `treatment` = `C`×4 + `D`×3 + `E`×1, no spanning
cluster; cell cluster counts 2 and 3, roster 5. `{kind: fold, k: 3}` is the discriminator — 3 ≤ 5
clears the roster bound, 3 > 2 fails the cell bound. Under `max` for `min` the basis is 3, `k: 3`
clears, and `E-REPL-FOLD-K-TOO-LARGE` **disappears from the finding set**. Run: **7 failed, 3365
passed** — batch A's six direct arms plus this one, which is the arm batch A declared owed.
The honouring half is in the same test: `k: 2` on the same fixture is **not** refused.

**MU-7, one mutation per site, each against the full unfiltered suite** (baseline **3372 passed**):

| Mutation | Result | Which tests |
|---|---|---|
| `fold_cell=fold_cell` dropped at `validate`'s `resolve_repeats` call | 1 failed, 3371 passed | the `validate` test **alone** |
| `{in_cell}` dropped from the **clustered** message | 2 failed, 3370 passed | the `resolve_repeats` clustered test **and** the `validate` test |
| `{in_cell}` dropped from the **unclustered** message | 1 failed, 3371 passed | the direct `_fold_k` test **alone** |

**The middle row is reported as it measured, not as "alone".** The `validate` fixture declares
`cluster_by`, so its message *is* the clustered one — the two tests cannot be independent of that
string. What the three rows do establish is that **each site has a test that fails when only that
site is broken**, which is the property MU-7 exists for.

**The § Errors asymmetry is ANSWERED from the code rather than filed.** No row is owed in § Errors
core raises: `validate`'s cell draw and `_prepare_run`'s call `units.assignment_for` over the same
roster at the same `design_digest(doc)` through the **same skip rules** (copied verbatim, task 5), so
they resolve the same cells and take the same minimum — a `k` this check clears is a `k` `_fold_k`
clears at run. **The one input the two spell differently was checked rather than assumed**:
`validate_config` reads the declaration through `_units_declaration(...) or {}` and `_prepare_run`
through `(doc.get("data") or {}).get("units")`. Read at `_units_declaration`: it returns that same
object, or `None` — and `None` for a non-mapping only *after* reporting `E-CONFIG-SHAPE`, which is an
error. So for any config that validates clean the two accessors are the same mapping and neither can
see an `assign` block the other cannot. That clause is in the comment, because without it the answer
rests on an equality nobody verified. Where the draw faults, `_resolved_cells` returns `None` and the roster-wide basis is
used at both ends, since the fault is the same fault; the config then meets that fault under its own
code. `E-DATA-HOLDOUT-EMPTY` has rows in both tables because its two bounds are genuinely **two
computations** — `_check_holdout` against a declared `frac`, `holdout_for` against a realized split —
which is the asymmetry rather than an inconsistency. Written at the forwarding site, where the next
reader of that `c.error` will meet it.

**The § Errors row** was rewritten to cover all three sites and stays **one row**. Mechanical pass on
`docs/reference.md`: zero duplicate heading anchors, zero broken internal anchors, zero trailing-
whitespace or tab lines, and the edited row has the same column count as its neighbours (checked at
563–568). The row cites `#expansion-modes`, an anchor that exists — the first draft cited
`#group-axes-between-subjects-arms`, which does not, caught by the pass.

---

## 5. The bit-stability oracle — re-run, values unchanged

The oracle: **a design with no cells must draw the partition it drew at `3d72910`.** Arm A pins the
output of all three `partition_units` paths; arm D pins the call.

| Arm | Test | State |
|---|---|---|
| A | `test_h3c3_pin_arm_a_the_three_partition_draws_are_byte_identical` | **passing, literals unedited** |
| B | `test_h3c3_pin_arm_b_a_no_axis_sweep_document_carries_only_the_flat_partitions` | passing, unedited |
| D | `test_h3c3_pin_arm_d_a_no_axis_prepare_makes_exactly_one_bare_digest_partition_call` | passing, unedited |
| E | `test_h3c3_pin_arm_e_a_six_unit_no_axis_config_validates_with_no_findings_at_all` | passing, unedited |

`pytest -k h3c3_pin_arm` → **5 passed** at `962fc05`, and every one of the seven full-suite runs in
this batch included them. `git diff bf68454..HEAD -- tests/test_units.py` has **no deleted lines**,
so arm A's three captured draws — the 5 × 10 unclustered folds, the clustered
`[[S1_0…S1_6, S4_0], [S3_0…S5_0]]`, and the clustered-and-stratified triple — are the same bytes
batch A captured. **A no-cell design comes out bit-identical**, which is what the oracle asks: on
that path `cells` is `None`, `thinnest_cell` is never called, and `resolve_repeats` receives the
identical `fold_basis(roster, cluster_by)`.

---

## 6. Every added or moved assertion, with the mutation that fails it

| Assertion | The mutation |
|---|---|
| `_resolved_group_axes` and `arm_members` called exactly once each, through a real `command_run` | **MU-16**, a duplicate `arm_members` call: 1 failed, 3356 passed |
| `Prepared.cells` is the two arms' memberships / `None` with no axis | `cells_of(group_axes)` without the `else None`: 1 failed, 3356 passed |
| **moved** — `len(dataclasses.fields(Prepared)) == 37` | omitting the `cells` field: that assertion is the only one in the suite that reads the count (`grep -rn "dataclasses.fields(Prepared)" tests/` → one test), and `mypy` catches the constructor from the other end |
| `_resolved_cells`' random-axis memberships equal `_prepare_run`'s | digest → `"validate"`: 1 failed, 3366 passed, that test alone |
| the six malformed shapes are `None`, with a resolvable control | each parametrized case carries its own control **in the same test**, so a function returning `None` for everything fails the control half |
| `E-DATA-ASSIGN-BLOCKED-CLUSTER` still reported beside a `None` decomposition | the `method: random` companion in the same test attributes the `None` to the method |
| `W-STATS-RESAMPLE-CLUSTERS` silent at `min_clusters: 4`, firing at 20 | that site's `fold_basis` → `cell_fold_basis`: 1 failed, 3367 passed, that test alone |
| the all-zero-ratio config **reports rather than crashes** | removing `ZeroDivisionError` from `_resolved_cells`' `except`: that is how the fault was found — the existing test crashes |
| the clustered refusal names the cell and its cluster count | `{in_cell}` dropped from the clustered message: 2 failed, 3370 passed |
| the unclustered refusal names the cell, and `cell=None` gives the exact old string | `{in_cell}` dropped from the unclustered message: 1 failed, 3371 passed |
| `validate` forwards the label | `fold_cell=` dropped at its `resolve_repeats` call: 1 failed, 3371 passed |
| the cell bound refuses `k: 3` and accepts `k: 2` on F2 | **MU-3's refusal half**, `max` for `min`: 7 failed, 3365 passed |
| a `cell` label changes no bound (`_fold_k(…, 2, None, cell) == 2`) | narrowing the bound when `cell is not None` fails here and nowhere else |

Every revert was performed by **editing back**, diffed byte-identical against a pre-mutation copy,
and verified by **re-running the full suite**. No `git checkout -- <file>` was used.

---

## 7. Disagreements with the briefs, the plan and the design — every one, with what was grepped

**This is not a count of zero.** Six, plus the claims that held.

**D1 — the hoist is three statements** (§ 1). Measured by `ruff`'s `F821`.

**D2 — C20's unpack line cannot land at task 4** (§ 1). Measured by `ruff`'s `F841`, edited back and
diffed identical. **The obligation moved to whichever task first reads `cells` in phases 6–10.**

**D3 — Decision 8's swallow list is six, not five** (§ 3). Measured by an existing test crashing.

**D4 — a `k: all` can NEVER reach `E-REPL-FOLD-K-TOO-LARGE`, so task 7's brief's second test could
not be built as written.** The brief prescribes *"three tests, one per site (a fixed `k` through
`validate`, a `k: all` through `resolve_repeats`, a direct `_fold_k` call)"*. Read at
`replication._fold_k`: `k == "all"` **assigns `k = fold_basis`**, and the bound below is
`k > fold_basis`, which is then false by construction. There is no `k: all` config that reaches this
code at all. The replacement keeps three distinct sites by making them **three forwarding hops**
rather than three `k` shapes: `validate_config` → `_check_replication` → `resolve_repeats` (the
`validate` test), `resolve_repeats` → `_fold_k` with a fixed oversized `k` and a cluster declared (the
clustered raise), and `_fold_k` called directly with no cluster (the units raise). Both message
variants are covered; without the split one of the two raises would have shipped unpinned.

**D5 — `thinnest_cell` supersedes `cell_fold_basis` at both callers, so C25 is discharged for
`cells_of` only.** C25's `cell_fold_basis` import is gone again from `validate.py` and `cli.py`. C25 requires the name in both import lists;
task 6 put it there and task 7 replaced it with `thinnest_cell`, because both callers need the label
as well as the number and a second call would be a second walk. **`cell_fold_basis` therefore has
zero production callers at `962fc05`** — kept, not folded away, because the tasks that bound
`E-DATA-HOLDOUT-EMPTY` and `W-DATA-CELL-THIN` over the thinnest cell want the number and not the
label. Stated in its own docstring so a later task finds it by grep, and raised as a concern below.

**D6 — one existing test's stub signature had to move.**
`tests/test_validate.py::test_an_unresolved_repl_code_is_not_swallowed` monkeypatches
`resolve_repeats` with `def _boom(doc, digest, fold_basis=None)`, which raises `TypeError` once the
real call passes `fold_cell=`. Found by the full suite, not by reading; the stub gained
`fold_cell=None`. **A signature, not an assertion** — the test still pins the `else: raise` branch
exactly as before.

### Claims grepped, and which held

- *"`fold_basis` has three call sites and `_check_sweep` reads the same `basis` local"* (C4, C5) —
  `grep -n "fold_basis" src/publishable/validate.py`: one import, one `basis` local threaded to both
  `_check_replication` and `_check_sweep`, one `limits.min_clusters` call. **Held.**
- *"`Prepared` is thirty-six fields and `_execute_prepared` unpacks them one per line"* (C20) —
  counted in `cli.py` and asserted live by the h9b test. **Held**, and now 37.
- *"`_resolved_group_axes` already sits above `_resolved_holdout`"* (C19) — read at `864f702`.
  **Held**, which is why only the fold half needed the hoist.
- *"`expand(doc)` is above the whole region, in `_prepare_run`"* (C3) — read. **Held**; the hoist
  resolved nothing new.
- *"Ruling S's claim that the two calls stay where they are"* —
  `grep -rn "stay exactly where\|stays exactly where" src/ tests/` → **zero hits** after task 4;
  before it, two, in `_resumed_allocation`'s docstring and in the h9b test's. **Both deleted rather
  than rewritten.**
- *"the `min_clusters` sentence"* — `grep -rn "cheap follow-up"` over `src/`, `tests/` and the four
  documents → **zero hits**. **Deleted.**
- *"`_check_evaluation_split_cells` refuses a `fold` beside a cell structure, and `validate`
  collects"* — read at `validate.py` § the two-codes-one-site function. **Held, and load-bearing**:
  it is what makes MU-3's refusal half reachable through `validate` at all, since
  `E-REPL-FOLD-CELLS` is reported *beside* `E-REPL-FOLD-K-TOO-LARGE` rather than instead of it.
- *"`cells_of({})` returns one empty cell and the caller composes the whole roster"* (batch A's D1)
  — read `cells_of`' docstring. **Held**, and the caller's half is written once, at
  `_prepare_run`, as `None`.
- *"C17: gating on the resolved axes gates on both cell-structure shapes"* — not relied on here;
  `_resolved_cells` returns `None` on no resolved axis and nothing in this batch gates a warning.
- *Two comments naming `cell_fold_basis` where the code now calls `thinnest_cell`* —
  `grep -rn "cell_fold_basis" src/` after task 7 found them at `validate.py` and `cli.py`. **Both
  corrected**; a comment that names the wrong function is the same defect as one claiming a
  guarantee the code does not provide.

---

## 8. Concerns for the controller

1. **C20's unpack-line obligation moved out of task 4 and nothing carries it.** `Prepared.cells` is a
   field with no `_execute_prepared` unpack line, because an unread local is an `F841` (measured). The
   first task in phases 6–10 that reads `cells` — task 11 for `partitions_within`, or task 17 — must
   add that line. **No brief says so**, and C20 says the opposite. This is the shape of a finding
   falling out of the chain, so it is here as well as in the commit message.
2. **`cell_fold_basis` has zero production callers at `962fc05`** (D5). Tasks 14 and 18 are its
   expected callers — the `E-DATA-HOLDOUT-EMPTY` bound and `W-DATA-CELL-THIN`, both of which want the
   thinnest cell's count and not its label. **If neither uses it, the slice ships a tested function
   nothing calls**, and C25's import obligation is then discharged only for `cells_of`. The docstring
   names both expected callers so a grep finds it.
3. **Task 4 makes `Prepared.cells` derivable from `group_axes`, and `_resumed_allocation` overrides
   `group_axes` from the record without touching `cells`.** At this commit that is consistent — task
   17 owns Ruling KK and the re-derivation — but between `0a4cf1e` and task 17 a resumed run holds
   `cells` from the *fresh* draw beside `group_axes` from the *record*. Nothing reads `cells` in
   phases 6–10 yet, so nothing can observe it; it is stated because "nothing reads it yet" is exactly
   the argument that stops being true when task 11 lands.
4. **A `-k`-filtered pytest run cannot see a module-scope name collision** (§ 2). My first
   `_arm_roster` shadowed an existing helper of the same name in `test_validate.py`, and
   `pytest -k resolved_cells` stayed green while four unrelated tests broke. The general form:
   **a new module-level helper needs a grep of its own file for the name**, and a filtered run is not
   evidence about the suite.
5. **Decision 12's "exactly two calls" and Decision 8's five-item swallow list are both corrected by
   this batch**, the first in the report only (a plan/design phrasing) and the second by an appended
   correction in the design file. Neither design section was retro-edited.

---

## 9. The follow-up round

Four items, none of which any gate would have caught.

1. **`Prepared`'s docstring contradicted itself** (§ 1). Closed by naming `cells` in the "one field"
   clause and dating the count, not by rewriting the `ast` walk.
2. **C5's seam had code and no fixture** (§ 3). Closed with a fixture and its mutation:
   **4 failed, 3373 passed**.
3. **The tie-break was in a normative row with no fixture** (§ 4). Closed with two tests, four arms.
4. **The § Errors answer rested on an unverified input equality** (§ 4). Verified at
   `_units_declaration`, and the clause added to the comment.

Final suite after the round: **3377 passed, 1 skipped, 2 xfailed**.
`git diff 864f702..HEAD --stat` touches ten files and
**`docs/feasibility-llm-growth-studies.md` is not among them.**
