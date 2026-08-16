# Task 11 review: construction 2 — whole clusters, `stratify_by`, and the relation between the two constructions

Reviewed: `51d887e..9d5e75c` (one commit). Files in scope: `src/publishable/units.py`,
`tests/test_units.py`.

## Verdicts

1. **Spec compliance: ❌** — every prescribed behaviour is built and behaves as the brief
   describes, but Step 3(a)'s deliverable (the new `data.units.holdout.stratify_by`
   declaration path) is pinned by **nothing** — corrupting it back to the exact bug the
   step exists to fix leaves the **full suite green** — and the merged
   `E-DATA-HOLDOUT-EMPTY` raise has three message branches of which two are unpinned.
   Neither of the two cases whose test this task deleted is covered by a replacement.
2. **Task quality: ❌** — `test_a_stratified_clustered_holdout_composes_both_rules`
   cannot fail when the composition it is named for is dropped entirely (full-suite-green
   mutation, Finding 2); a **bolded** docstring guarantee is false and is contradicted by
   another sentence in the same docstring and by the called function's own docstring
   (Finding 3).

**Attribution, so the ❌ is reviewable rather than punitive.** The implementer executed
the brief faithfully: all three of Step 5's mutations do discriminate, and I re-ran two of
them myself and reproduced the reported result exactly. The gap is that the brief's
mutation set never touched the composition or any message path, and the Global Constraint
(*every new error site pinned by its MESSAGE*) binds the task rather than the brief —
the posture task 10's review took on its own Finding 5.

---

## The two adjudications the parent asked for FIRST

### 1. The deleted test — deletion justified on substance, coverage **NOT** replaced (either case)

*Verified by running both former cases directly* (`uv run python`, a 10-unit
`_holdout_roster` equivalent):

| former case | outcome today |
|---|---|
| `stratify_by: ["x"]` | `NotImplementedError` — `` `data.units.holdout.stratify_by` names 'x', which no resolved unit carries … `` |
| `clusters={f"u{i}": "c0"}` (one cluster) | `ContractError` `E-DATA-HOLDOUT-EMPTY` — `` …leaves the test side empty over whole clusters. … `` |

So the deleted assertion (`"clustered or stratified" in str(exc.value)`, `NotImplementedError`)
genuinely contradicts this task's purpose — both cases now produce different, correct
outcomes, and one is no longer a `NotImplementedError` at all. **Deleting rather than
editing was the right call**; retaining it would be the "temporary refusal read as
permanent" trap.

**But neither case is pinned by any replacement test, and neither message is pinned at
all.** Verified two ways:

- `grep -rn "data.units.holdout.stratify_by\|over whole clusters\|stratum declaration" tests/`
  → **no hits**. No test anywhere references the holdout declaration path or the clustered
  message suffix.
- *Mutation, full suite.* I changed the holdout call site's argument from
  `"data.units.holdout.stratify_by"` to `"data.units.assign.holdout.stratify_by"` — **the
  precise bug Step 3(a) exists to fix, a path no config can hold** — and simultaneously
  changed `" over whole clusters"` to `" over whole potatoes"`. `uv run pytest` →
  **1917 passed, 2 xfailed**. Both reverted by editing the lines back; revert verified by
  `diff` against a pre-mutation copy (clean) and by re-running the suite.

The clustered-empty case is also the one task 10's reviewer explicitly handed forward
(*"the refusal has to be restated per branch … flagged here so it is not read as already
handled"*). It **was** restated correctly in the code (Finding 4 below, positive), and is
tested by nothing.

### 2. The rewritten message fragment — **clean, not vacuous**

`assert f"leaves the {empty_side} side empty" in str(exc.value)`.

*Verified by re-running task 10's own mutation.* I inverted the side-naming line to
`side = "test" if not train_keys else "train"`, deleted `__pycache__`, ran
`uv run pytest tests/test_units.py -k holdout` → **2 failed** (both parametrizations of
`test_a_holdout_that_leaves_a_side_empty_raises`), 34 passed. The reported failure text
confirms it discriminates on the named side, not on the invariant tail. Reverted by
editing the line back; verified by `diff` (clean) and by re-running (36 passed).

**No vacuous assertion was reintroduced.** The rewrite was also forced: `"apportions the
… side zero"` no longer exists anywhere, and the two phrasings are mutually exclusive
strings.

---

## Findings

### Critical

**None.** No input `validate` admits produces a wrong partition. Cluster integrity,
stratum balance, and the empty-side refusal are all correct on the paths I exercised.

### Important

**Finding 1 — Step 3(a)'s entire deliverable, and two of the merged raise's three message
branches, are pinned by nothing.** (Global Constraint.)

Three unpinned branches in the one raise plus one unpinned message site, reported as one
finding:

- the `_stratum_groups` holdout call site's `declaration` argument (proved green above);
- `", drawn within {len(strata)} stratum declaration(s)"` — no test contains the string;
  `test_a_stratified_holdout_that_leaves_a_side_empty_across_every_stratum_raises`
  asserts **only** `exc.value.code`;
- `" over whole clusters"` — proved green above, and no test reaches the clustered
  empty-side branch at all.

The brief itself instructed a grep for tests pinning the *old* `_stratum_groups` wording
("a test pinning the old wording must move with it"). I ran it
(`grep -rn "stratify_by\` names" src/ tests/`): there were none, and none were added —
so that message is now unpinned for **both** of its callers.

Smallest fixes: assert the full `str(exc.value)` fragment in the stratified-empty test;
add a clustered-empty test (one cluster over the whole roster, `frac: 0.2`) asserting
`" over whole clusters"`; add a test that a `stratify_by` naming no attribute raises with
`` `data.units.holdout.stratify_by` `` in the message — which also restores the first half
of the deleted test's coverage.

**Finding 2 — `test_a_stratified_clustered_holdout_composes_both_rules` cannot fail when
the composition is dropped.**

*Verified by mutation, full suite.* I changed the branch head `if strata:` to
`if strata and clusters is None:` — a stratified **clustered** draw then ignores the strata
entirely and deals clusters over the whole roster, which is the exact defect the test is
named for. `uv run pytest` → **1917 passed, 2 xfailed**. Reverted by editing back;
`diff`-verified clean; re-ran (202 passed in `tests/test_units.py`).

Why it is blind: at `frac: 0.5` over 8 clusters of 2 split 4/4 across two bands, an
unstratified clustered draw still lands units of both bands on both sides, so
`members & train and members & test` holds either way. The test also never asserts
`plan.strata`. This is the brief's own warned shape — a fixture whose numbers agree with
the bug — in the test written to rule it out.

Fix that would bite: pin the per-band test counts (a correct stratified draw at this
fixture forces 4 test units per band) **and** a membership literal, the way
`test_a_stratified_holdout_splits_within_each_stratum` does; plus
`assert plan.strata == ("band",)`.

**Finding 3 — a bolded docstring guarantee is false, and is contradicted by two other
docstrings.**

`holdout_for`'s new paragraph: *"With one cluster per unit the two agree on the **SIZES**
and differ on the **MEMBERSHIP**."*

*Verified by sweep.* For every `n` in 2..39 × 12 values of `frac`, I compared
`len(plan.test)` for the unclustered draw and the singleton-clustered draw at the same
seed: **90 disagreements**, in both directions and including outright disagreements about
whether the draw is legal at all —

| n | frac | unclustered | singleton-clustered |
|---|---|---|---|
| 2 | 0.1 | `E-DATA-HOLDOUT-EMPTY` | returns 1 train / 1 test |
| 5 | 0.3 | 1 test | 2 test |
| 6 | 0.6 | 4 test | 3 test |
| 8 | 0.3 | 2 test | 3 test |

The claim contradicts a sentence in the **same docstring** — *"including a clustered
draw's realized sizes, **which a declared `frac` alone cannot predict**"* — and the
called function's own docstring, which states *"Every realized size can differ from its
exact target share"* and *"**No bound on that deviation is promised**"*. The sweep says
which of the two is wrong.

The fixture blesses the coincidence: `test_the_clustered_and_unclustered_constructions_are_not_the_same_draw`
pins `len(plain.test) == len(clustered.test) == 4`, true at `n=10, frac=0.4` and not a
property. Fix: drop or qualify the size-equality sentence (keep the realized-sizes one),
and drop the size equality from that assertion. **Do not** add a general size-equality
property test — that would encode the false claim.

The rest of the same paragraph is accurate: I read `_assign_whole_clusters_by_ratio`'s
body (`src/publishable/units.py`, `members` → `rng.shuffle(order)` →
`order.sort(key=-len)` → `argmin counts[i]/weights[i]`) and "shuffles cluster names, sorts
largest-first, deals each cluster to the bucket furthest below its own target share" is
exactly what it does, as is the non-optional-`Mapping` argument for two paths.

**Finding 4 — the `_stratum_groups` message got the path fixed and the codes not, so it
now sends a holdout reader to two codes their declaration cannot produce.**

*Verified by reading the raised message back* (case A of the probe above). The tail still
reads: *"…and no already-drawn `sweep.groups` axis resolves … `validate` refuses it as
`E-DATA-ASSIGN-STRATIFY-FORWARD`; a stratum naming nothing at all is refused as
`E-DATA-ASSIGN-STRATIFY-UNKNOWN`"*. A holdout's `stratify_by` admits **only** a unit
attribute (the brief says so, and the call site passes no `resolved`), and `validate`
refuses the unknown name as **`E-DATA-HOLDOUT-STRATIFY-UNKNOWN`**
(`docs/reference.md` § Errors). So a holdout reader is told about a `sweep.groups` path
they cannot take and two codes they cannot hit.

This is not cosmetic given Step 3(a)'s own rationale, added verbatim to the docstring:
*"the message it raises names the config path a reader has to go and fix."* Half the
message was made caller-aware and half was left assign-specific, while the new docstring
paragraph asserts the parameter makes the message right for more than one caller. Fix:
either branch the tail on the declaration, or generalize it to name the fault rather than
the assign-side codes.

### Minor

**Finding 5 — the empty-check comment's "more easily" is false at singleton clusters.**
*"a cluster is the smallest thing that can move, so a clustered draw reaches an empty side
more easily rather than being exempt from the refusal."* The sweep above shows the
opposite at singleton clusters: `n=2, frac=0.1` raises unclustered and returns 1/1
clustered. The sentence's actual job — the refusal is **shared**, not skipped — is correct
and worth keeping; the "more easily" needs the qualifier "with clusters larger than one".

**Finding 6 — `test_a_thin_stratum_alone_does_not_raise`'s second assertion is arithmetic,
not a check.** `holdout_sizes(1, 0.2) == (1, 0)` forces `u9` onto the train side under any
correct per-stratum apportionment, so `tiny <= set(plan.train)` cannot distinguish
constructions. The test's real value is the *absence* of a raise (a per-stratum coverage
rule would raise here), which it does carry — so this is a note, not a defect.

---

## Positive verification

- **Parent (a), the two constructions are genuinely two — YES.** I re-ran the brief's
  mutation (a) myself: the unclustered `else:` rerouted through
  `_assign_whole_clusters_by_ratio(list(roster), weights, rng, {u.key: u.key …})` →
  `test_the_clustered_and_unclustered_constructions_are_not_the_same_draw` **FAILED** on
  `set(plain.test) != set(clustered.test)` ("Both sets are equal") and
  `test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes` **FAILED**
  on its literal. Reverted by editing back; `diff` clean; both re-pass.
- **A named mutation for `test_a_clustered_holdout_keeps_every_cluster_whole`** (the
  parent asked for one per added test, and the brief supplied none): rerouting the
  unstratified clustered branch to singleton clusters
  (`{u.key: u.key for u in roster}`) → that test **FAILED** alone (1 failed, 201 passed).
  Run by me; reverted and re-verified.
- **Parent (b), the per-stratum literal is load-bearing and stable — YES.** I re-ran
  Step 5(b) (`rng = random.Random(seed)` moved inside the stratum loop):
  `test_a_stratified_holdout_splits_within_each_stratum` **FAILED on the membership
  literal only** (`u9` vs `u8`), the count assertion passing — reproducing the report
  exactly. Independently of the literal: the stratum iteration order is
  `dict.setdefault` insertion order over units in **roster order**, read at
  `_stratum_groups`' body and documented in its docstring ("Insertion order is roster
  order … the order they come out in is part of what the seed determines"). Not set
  iteration, not sorted keys — so the literal is deterministic across runs and
  interpreters.
- **Parent (c), the refusal restated per branch — YES in the code.** The check is over the
  realized `train_keys`/`test_keys` after every branch, not over `holdout_sizes`' declared
  sizes; task 10's separate pre-check is gone, so one fault raises once. The clustered
  realized-empty case does refuse (probe case B). Only the **test** is missing
  (Finding 1).
- **Parent (f), the Python-version claim — CONFIRMED.** `pyproject.toml:5` is
  `requires-python = ">=3.11"`; nesting a same-quote f-string inside an f-string is a
  `SyntaxError` before PEP 701 (3.12), so the local `declaration` binding is required, not
  stylistic. The implicit-concatenation rewrite preserves the text: `f" within each of the
  " f"{…} " f"strata of …"` yields the identical `" within each of the 2 strata of sex"`,
  which `test_a_blocked_draw_on_an_axis_stratum_names_the_strata_when_an_arm_is_empty`
  pins and which passes.
- **Task 10's Finding 6 is closed.** `plan.strata` is now `strata` rather than a hard-coded
  `()`, and `assert plan.strata == ("band",)` is breakable.
- **No call-site enumeration was added.** The new `_stratum_groups` docstring paragraph
  says "more than one caller" rather than counting them — correct, given the two stale
  enumerations already in this file.
- **Gates, re-run by me after every revert:** `uv run pytest` → 1917 passed, 2 xfailed;
  `uv run ruff check .` → All checks passed; `uv run mypy` → Success, 42 files.

## Mutation hygiene

Six mutations, all to `src/publishable/units.py`. A copy was taken to the scratchpad
before the first. Every revert was done **by editing the file back** — never
`git checkout --` — and verified twice: by `diff` against the pre-mutation copy (exit 0)
and by re-running the affected tests. `__pycache__` was deleted before every run. The
final gate run was performed after all reverts.

Housekeeping: `.superpowers/sdd/.gitignore` was found clobbered to a bare `*` again during
this review and restored from `HEAD` (its own tracked content), per CLAUDE.md.
