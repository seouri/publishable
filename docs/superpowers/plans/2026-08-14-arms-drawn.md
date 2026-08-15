# H3c-2 Arms Drawn Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `assign.method: random` and `assign.method: blocked` draw the arm assignment — honouring `ratio`, `block_size` and `stratify_by`, keeping whole clusters on one side, seeded from `assign.seed` — recorded in `allocation.json` under `provenance.allocation_hash`, retiring `E-DATA-ASSIGN-DRAWN`.

**Architecture:** The draw joins `units.arms_of` under **one authority**: a pure function of `(roster, axis block, digest)` returning a per-axis membership plan, callable from `validate` and from `cli.command_run` alike. `arm_members`' `axes` parameter changes from `(column, levels)` — a shape that cannot express a drawn axis — to that plan type. Nothing computes membership twice.

**Tech Stack:** Python 3.12+, `uv`, pytest, ruff, mypy. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-08-14-arms-drawn-design.md`
**Measurement:** `docs/superpowers/H3c-2-SCOPING.md`

## Global Constraints

Every task's requirements implicitly include this section.

- **The documents lead the code.** Where code cannot follow, **the document changes first**; where the code is wrong, record the gap rather than editing a document to describe code that does not exist.
- **`validate` collects findings and never raises.** `units`/`artifacts` raise `ContractError`; `validate` catches.
- **Assert exact numbers and strings, not directions**, and **every probe needs a control that must report.** Six checks in H3c-1 turned out unable to fail, every one caught by a mutation and none by reading. **Run the mutation before believing the test, and run it where the behaviour lives** — not where the test happens to look.
- **Vary what the config is *about*, not only how it is spelled.** H3c-1's adversary suite ran nineteen shapes against one roster, so every refusal in it was roster-incidental rather than structural. A refusal that happens to fire must be **attributed** before it is counted.
- **The drawing fixture trap, named:** `ratio {control: 1, treatment: 1}` with `block_size: auto` over a roster whose length is a multiple of the block gives `random` and `blocked` **the same arm sizes**. Use a roster length that is *not* a multiple, pin the seed, and assert the within-block property. A fixture whose cluster boundaries coincide with block boundaries hides task 11 entirely.
- **One roster per run.** An arm is a subset view. `units_hash` and every provenance claim rest on it.
- **Mutation testing is never reasoned about.** Apply, run the named test, confirm FAIL, revert, confirm PASS. **Delete `__pycache__` between mutation and revert**; **verify reverts by behaviour, never `git status`**.
- **Never write a phrase locating a table row by position** ("the two rows above", "further up"). H3c-1 wrote five and was wrong twice — once in a row no diff touched, falsified by an insertion that moved it. Name what a sibling row *does*. When you insert or remove a row, check every row it **moved**, and every count phrase near it.
- **Never filter the output of a sweep whose job is to find a string** — filter the file list instead. A reviewer checking exactly this rule lost a true hit to `grep -v superpowers`, because the matching line contained that path.
- `uv run pytest`, `uv run ruff check .`, `uv run mypy` green. **Do not run `ruff format .`** — repo-wide, pre-existing, out of scope.
- Cite by section, never line number; `×` not `x`; **hyphen never an en dash** in anything becoming a filename or anchor.
- **The worked example declares no `groups`, `allocation` or `assign`.** Nothing about `cohort-pilot` may move: 240/228/12; r = 0.581 / 0.607 / 0.412; delta 0.026, ci95 [−0.007, 0.059]; kendall −0.169, [−0.213, −0.125]; `repeat_spread` std 0.014; hashes `8e21`/`1a2b`/`3d8a`/`6b1f`; README's demo `2f5c8d0`.

---

## Verified interfaces — read from the code before any task was written

| Site | Signature / fact |
|---|---|
| `units.arms_of` | `(roster: UnitList, column: str, levels: Sequence[str]) -> dict[str, list[Unit]]`. Docstring: *"**The single authority** for arm membership"*. Raises `ContractError` on a partition violation |
| `units.arm_members` | `(roster: UnitList, axes: Mapping[str, tuple[str, Sequence[str]]], conditions: Sequence[Any]) -> dict[int, frozenset[str]]`. **The `axes` type is what task 7 changes** |
| `units._assign_whole_clusters` | `(units: list[Unit], k: int, rng: random.Random, clusters: dict[str, str] \| None) -> list[list[Unit]]` — `k` **equal** buckets, least-loaded-first. Pinned by a fold bit-stability oracle |
| `units.stratum_varies_within_cluster` | `(roster: UnitList, cluster_by: str, stratify_by: str) -> tuple[str, list[str]] \| None` |
| `units.units_hash` | `(units: UnitList) -> str`, over the list in resolved order |
| `sweep.sample_seed_for` | `(config: dict[str, Any]) -> int \| None`. **The precedent for task 6**: a pinned integer is returned literally and the digest is not computed at all |
| `cli._resolved_group_axes` | `(units_decl, sweep_block) -> dict[str, tuple[str, list[str]]]`, gated on `by_attribute`. **Cannot express a drawn axis** |
| `artifacts.build_allocation_document` | `(roster: UnitList, group_axes: Mapping[str, tuple[str, Sequence[str]]]) -> dict[str, Any] \| None`, returning `seed: {}` / `strata: {}` as literals |
| `validate.DRAWN_ASSIGN_METHODS` | `("random", "blocked")`, read from one `elif` in `_check_assign` — the single retirement site |
| `hashes.design_digest` | Strips `assign.<axis>.seed` per axis; **new sibling keys are digested**, which is what § What `auto` derives from requires |

**No fixture named in this plan exists yet.** `tests/test_validate.py` has `write_config`, `codes`/`_error_codes` and `_between`; `tests/test_runner.py` has `_arm_roster12` (7/5) and a 5-unit/3-cluster harness; `tests/test_cli.py` has `run_a_project` and an end-to-end group-axis test.

---

## Task 1: Documents, part A — the ten refusal surfaces

**Files:** Modify `docs/reference.md`, `docs/experimental-designs.md`

Nothing below may land a check describing a rule no document states, and **the retirement in task 14 removes a code named at ten independent prose sites**. Find them now, while they are still true, so task 14 is a deletion rather than an archaeology exercise.

- [ ] **Step 1: Enumerate, then verify the enumeration can fail.** `grep -n 'E-DATA-ASSIGN-DRAWN' docs/*.md` — the scoping measured 9 in `reference.md` and 1 in `experimental-designs.md`. Run the same grep against a code you know is present and absent (`E-DATA-ASSIGN-LEVELS`, `E-DATA-NOTHING`) and show both outputs. Record the site list in your report; task 14 works from it.
- [ ] **Step 2: § Validation's *Assignment method isn't drawn* row.** It says `random`/`blocked` are "specified, not built in this build; only `by_attribute` executes". Leave it — task 14 removes it — but check its wording still matches `DRAWN_ASSIGN_METHODS` exactly.
- [ ] **Step 3: The four rows this slice implements.** *Ratio names levels*, *Block size fills the arms*, *Stratification is forward-only*, *Allocation strata exist*. Read each and write down, in your report, the exact fault each describes. Tasks 5, 10, 12 and 13 implement them and must not drift from these words.
- [ ] **Step 4: Commit.**

```bash
git commit -am "docs: name the drawing surfaces the code is about to implement"
```

---

## Task 2: Documents, part B — the two rulings

**Files:** Modify `docs/reference.md`

Both are settled. Write them down **before any code**, because tasks 10 and 11 implement them.

- [ ] **Step 1: `blocked` beside a declared `cluster_by` is refused.** *Settled by the user.* § Where units come from makes `blocked` the one declaration reading roster order as data; § Clustered units says a cluster is drawn whole under `blocked`. **Block size counts units and a cluster is indivisible, so no block size honours both.** Amend § Clustered units' sentence — which currently says "With `method: random` or `blocked` a cluster is drawn as a whole" — so it claims only what will be true: `random` draws whole clusters, and `blocked` beside `cluster_by` is refused. Amend § Allocation's `blocked` paragraph the same way. Name the code task 11 mints.
- [ ] **Step 2: `block_size: auto` when `ratio: {}`.** *Settled by the controller.* `auto` is "twice the sum of `ratio`", and `{}` **is** equal allocation, so the implied ratio is 1 per level and its sum is the level count: `auto` is **twice the level count**. Say it in § Allocation rather than leaving it inferable — it is the value `init` writes and the one most designs carry.
- [ ] **Step 3: Mechanical pass over the edited passages, then commit.**

```bash
git commit -am "docs: settle blocked-beside-clusters and auto block size over an empty ratio"
```

---

## Task 3: Documents, part C — which row owns the stratum fault

**Files:** Modify `docs/reference.md`

**Two § Validation rows overlap on `assign.stratify_by`** and the overlap is a real ambiguity, not a wording nit. *Stratification attribute exists* contemplates only a unit attribute. *Allocation strata exist* admits a name that is "neither a unit attribute **nor a group axis**" — and **an axis name is exactly what forward-only stratification requires**.

- [ ] **Step 1: Write the ruling into the rows.** *Allocation strata exist* owns `assign.<axis>.stratify_by`, including the axis-name case; *Stratification attribute exists* keeps `fold` and `holdout`. Say so in both rows, naming what the other one covers rather than where it sits.
- [ ] **Step 2: Register the new code.** `E-REPL-FOLD-STRATIFY-UNKNOWN`'s registry row already promises the shared row covers `holdout.stratify_by` and `assign.<axis>.stratify_by`, "each reported by its own code once its block is built". Mint `E-DATA-ASSIGN-STRATIFY-UNKNOWN` and give it a registry row in sort order. **Check every row your insertion moves.**
- [ ] **Step 3: Commit.**

```bash
git commit -am "docs: allocation strata exist owns the assign stratum, and its code is registered"
```

---

## Task 4: The `assign` per-axis whole-leaf closure

**Files:** Modify `src/publishable/envelope.py`, `docs/reference.md`; Test `tests/test_validate.py`

**H3c-1 was assigned this and did not ship it**, and § The one config file records the gap in so many words: *"`envelope.py` still types the block a bare `dict` with no per-axis-key closure, so a misspelled field inside an axis block (`stratifyy_by` for `stratify_by`) is silently ignored"*. **This lands ahead of tasks 5–13, which add four new keys inside those blocks** — every one of them silently ignorable until this is closed.

- [ ] **Step 1: Write the failing test**

```python
def test_a_misspelled_key_inside_an_assign_block_is_reported(write_config):
    """`stratifyy_by` is silently ignored today: `envelope.py` types
    `data.units.assign` a bare `dict` and none of its children, so nothing
    closes an axis block. The control is the correctly spelled key, which must
    NOT be reported — an allowlist that rejects everything passes the first
    assertion and fails the design."""
    units = {
        "allocation": "between",
        "assign": {"arm": {"method": "by_attribute", "stratifyy_by": ["site"]}},
    }
    assert "E-CONFIG-KEY-UNKNOWN" in codes(write_config({"data.units": units}))
    ok = {
        "allocation": "between",
        "assign": {"arm": {"method": "by_attribute", "from": "arm"}},
    }
    assert "E-CONFIG-KEY-UNKNOWN" not in codes(write_config({"data.units": ok}))
```

- [ ] **Step 2: Run it and confirm it fails** on the first assertion, not the second.
- [ ] **Step 3: Implement.** The axis *keys* are user-chosen names no fixed dotted path can name — that is why the block was left open. Close it one level down: every axis block's **own** keys are the closed set `{method, from, ratio, block_size, stratify_by, seed}`. Read how `check_envelope` reports an unknown key elsewhere and use the same code.
- [ ] **Step 4: Mutate** — remove one name from the closed set and confirm a test names it. **Then check the reverse**: a config using every one of the six must report nothing.
- [ ] **Step 5: Amend § The one config file's gap sentence** — it currently records this as unclosed. The document changes with the code.
- [ ] **Step 6: Commit.**

---

## Task 5: `ratio` validation, and the live gap under `by_attribute`

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_validate.py`

**Ships before drawing exists and closes a gap that is live today.** § Allocation says *"Under `method: by_attribute` a `ratio` describes a draw that didn't happen, so `validate` rejects a non-empty one"* — and **nothing reads `ratio` anywhere in `src/`.**

- [ ] **Step 1: Write the failing tests.** Three faults and two controls:

```python
def test_a_partial_ratio_is_refused(write_config):
    """§ Allocation: 'a partial mapping is rejected rather than defaulted, since
    "one entry per level" is checkable and "the levels I left out get the
    average" is a rule nobody should have to infer.' Two levels, one entry."""
    ...  # assert the exact finding set

def test_a_ratio_naming_an_undeclared_level_is_refused(write_config):
    """`ratio: {control: 1, f: 2}` against levels [control, treatment]."""

def test_a_non_empty_ratio_under_by_attribute_is_refused(write_config):
    """The draw didn't happen, so the proportion describes nothing."""

def test_an_empty_ratio_is_equal_allocation_and_is_accepted(write_config):
    """The control, and it must report: `{}` is what `init` writes and what most
    designs carry, so a check that refused it would fire on the common case.
    Assert the exact finding set, not an absence."""

def test_a_full_ratio_under_a_drawn_method_is_accepted(write_config):
    """The second control. Under this build the config still reports
    E-DATA-ASSIGN-DRAWN — assert that exact set, so the test keeps its teeth
    when task 14 retires that code and the set becomes empty."""
```

- [ ] **Step 2: Run them and confirm each fails for its own reason.**
- [ ] **Step 3: Implement** in `_check_assign`, beside the existing method checks. *Ratio names levels* is the row.
- [ ] **Step 4: Mutate each branch separately** — each test must die to its own branch and no other.
- [ ] **Step 5: Commit.**

---

## Task 6: The `assign.seed` derivation

**Files:** Modify `src/publishable/units.py` (or a new module — argue the choice); Test `tests/test_units.py`

**Copy `sweep.sample_seed_for`'s shape, not `partition_units`'.** `partition_units` seeds from the digest **only**; `BaseStep.derive_seed` mixes the execution seed. § What `auto` derives from specifies an axis's `assign.seed` as **digest + the axis name + the resolved roster**.

**Produces:** `assign_seed_for(block: Mapping[str, Any], axis: str, digest: str, roster: UnitList) -> int`

- [ ] **Step 1: Write the failing tests.** Four properties, each with the control that discriminates it:

```python
def test_a_pinned_assign_seed_is_returned_literally():
    """§ What `auto` derives from: 'pinning an integer is the deliberate act,
    and the one to take for anything you intend to cite', so a pinned seed must
    survive a roster change. Same block, two different rosters, same answer."""

def test_the_derived_seed_moves_with_the_roster():
    """'the roster changes, or any axis is added or edited'. Two rosters
    differing by one unit -> different seeds. THE CONTROL: the same roster in a
    different ORDER must also differ, because `units_hash` covers order and
    § Where units come from says two runs that resolved the same units in a
    different sequence did not allocate the same trial."""

def test_the_derived_seed_moves_with_the_axis_name():
    """Two axes over one roster and one digest draw differently, or a crossed
    design assigns both axes identically."""

def test_the_derived_seed_moves_with_the_digest():
    ...
```

- [ ] **Step 2: Run them; confirm each fails.**
- [ ] **Step 3: Implement.** Mix `digest`, the axis name and `units_hash(roster)`. **Do not compute the digest on the pinned path at all** — that is the property `sample_seed_for` documents and the reason a pinned seed is stable.
- [ ] **Step 4: Mutate** — drop each of the three inputs in turn; each must fail exactly the test named for it. **If dropping the axis name fails nothing, the axis-name test's two axes are not actually drawing.**
- [ ] **Step 5: Commit.**

---

## Task 7: The draw's authority, and the shape that can express it

**Files:** Modify `src/publishable/units.py`, `src/publishable/cli.py`, `src/publishable/artifacts.py`; Test `tests/test_units.py`, `tests/test_cli.py`

**The seam, and the task most likely to produce this project's recurring defect.** `arms_of`'s docstring calls a second notion of arm membership *"the validate-clean-then-disagree gap in a new shape"*. `validate` needs membership too, so the draw cannot live in the runner.

`arm_members`' `axes` parameter is `Mapping[str, tuple[str, Sequence[str]]]` — **a column and levels. A drawn axis has no column.**

**Produces:**

```python
@dataclass(frozen=True)
class ArmPlan:
    """One axis's realized membership: level -> unit keys, roster order."""
    levels: tuple[str, ...]
    members: Mapping[str, tuple[str, ...]]
    seed: int | None       # the realized draw seed; None under `by_attribute`
    strata: tuple[str, ...]  # the realized `stratify_by`; empty under `by_attribute`
```

and `assignment_for(roster, axis, block, levels, digest, clusters) -> ArmPlan`, dispatching on `block["method"]`: `by_attribute` calls `arms_of` unchanged; `random`/`blocked` raise `NotImplementedError` **until tasks 8 and 10** — an explicit hole, not a silent fallback.

- [ ] **Step 1: Write the failing test** — `by_attribute` through the new type gives exactly what `arms_of` gives today, over `_arm_roster12`'s 7/5 split, with `seed is None` and `strata == ()`.
- [ ] **Step 2–4:** Fail, implement, pass. Change `arm_members`' parameter type, `_resolved_group_axes`' return type, and `build_allocation_document`'s parameter.
- [ ] **Step 5: The recomputation check.** `build_allocation_document` calls `arms_of` a **second** time on the same axes. Under a draw a second call must be provably identical, or the plan must be computed once and passed. **Decide, implement, and say which in the docstring.** Assert it: the plan the runner narrows with and the plan `allocation.json` records must be the same object or provably equal.
- [ ] **Step 6: Mutation** — make `assignment_for` return a fresh partition rather than the shared plan; a test must fail. If none does, nothing pins the single authority.
- [ ] **Step 7: Commit.**

---

## Task 8: `random` honouring `ratio`, unclustered

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**Interfaces — Consumes:** `assign_seed_for` (task 6), `ArmPlan`/`assignment_for` (task 7).

- [ ] **Step 1: Write the failing tests**

```python
def test_a_random_draw_honours_an_unequal_ratio():
    """12 units, ratio {control: 1, treatment: 2} -> 4 and 8. Deliberately
    unequal AND not a half: 4/8 cannot be confused with 6/6, with 12, or with
    each other. Assert the exact sizes and the exact membership under a pinned
    seed."""

def test_a_random_draw_is_a_partition():
    """Every unit in exactly one arm, every declared level non-empty — the
    property `arms_of` guarantees for a read assignment and a draw must too."""

def test_the_same_seed_draws_the_same_arms():
    """And THE CONTROL: a different pinned seed draws different arms. Without
    it, a draw that ignored the seed entirely would pass the first half."""

def test_a_ratio_that_does_not_divide_the_roster_is_reported_not_rounded_away():
    """13 units at {1: 2} — assert the realized sizes exactly, and state in the
    docstring which unit the remainder went to and why."""
```

- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutations** — ignore the ratio (equal split); ignore the seed; drop the remainder unit. Each fails its own test.
- [ ] **Step 6: Commit.**

---

## Task 9: `random` over whole clusters

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**A sibling of `_assign_whole_clusters`, not a parameterization of it** — spec decision 6. That function deals whole clusters to the **least-loaded** of `k` *equal* buckets; an unequal `ratio` needs *furthest below its own target share*. Its fold behaviour is pinned by a bit-stability oracle, and **changing it risks a fold regression for an arm feature.**

- [ ] **Step 1: Write the failing tests.** The fixture must not let clusters and arms coincide:

```python
def test_a_clustered_random_draw_keeps_every_cluster_whole():
    """§ Clustered units: 'core computed the partition, so core keeps it
    indivisible.' 12 units in 5 clusters of 4/3/2/2/1 — sizes chosen so no
    subset sums to exactly half, so a draw that split a cluster could not
    reproduce a legal-looking balance by accident."""

def test_a_clustered_draw_approaches_an_unequal_ratio_as_closely_as_clusters_allow():
    """Assert the realized sizes exactly, and state in the docstring why they
    are not the exact ratio: a cluster is the smallest thing that can move, so
    one large cluster sets a floor. `partition_units`' docstring makes the same
    argument for folds — do not claim the stronger thing."""
```

- [ ] **Step 2: Confirm the fold oracle still passes before you touch anything**, and name it in your report.
- [ ] **Step 3–4:** Fail, implement, pass.
- [ ] **Step 5: Mutations** — route the clustered draw through `_assign_whole_clusters` unchanged (the ratio test fails); split a cluster (the whole-cluster test fails). **And re-run the fold oracle**: if it moved, the sibling is not a sibling.
- [ ] **Step 6: Commit.**

---

## Task 10: `blocked`, `block_size`, and the whole-multiple rule

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`; Test `tests/test_units.py`, `tests/test_validate.py`

- [ ] **Step 1: Write the failing tests.** **The global constraints name this task's fixture trap** — an equal ratio with `auto` over a divisible roster gives `random` and `blocked` the same sizes:

```python
def test_a_blocked_draw_balances_within_every_whole_block():
    """14 units, ratio {1:1}, block_size auto = 4. 14 is NOT a multiple of 4:
    three whole blocks of 4 and a trailing 2, so a draw that balanced only
    overall would pass a size assertion and fail this one. Assert each whole
    block holds exactly 2 and 2, and assert the trailing partial block's actual
    composition rather than ignoring it."""

def test_blocked_reads_the_roster_order_as_data():
    """§ Where units come from: 'the one declaration that reads the order as
    data'. The same units in a different resolved order give a different
    assignment. THE CONTROL: `random` over the same two rosters gives the same
    assignment, because it does not read order."""

def test_auto_block_size_is_twice_the_ratio_sum():
    """{control: 1, treatment: 2} -> sum 3 -> auto 6. And with `ratio: {}` over
    two levels -> auto 4, per § Allocation."""

def test_an_explicit_block_size_must_be_a_whole_multiple_of_the_ratio_sum(write_config):
    """*Block size fills the arms*: block_size 3 with ratio summing to 2 'can't
    hold each arm's share'. The control is 4, which can."""
```

- [ ] **Step 2–4:** Fail, implement, pass. `validate` owns the whole-multiple refusal; `units` owns the draw.
- [ ] **Step 5: Mutations** — balance overall rather than per block; shuffle the roster before blocking; `auto` as the ratio sum rather than twice it.
- [ ] **Step 6:** Note in your report that **appending a unit re-blocks rather than redraws** — boundaries move relative to every earlier unit, so units that never moved rows change arms. Do not write a test asserting otherwise.
- [ ] **Step 7: Commit.**

---

## Task 11: `blocked` beside `cluster_by` is refused

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_validate.py`

Task 2 wrote the ruling; this implements it. Mint `E-DATA-ASSIGN-BLOCKED-CLUSTER`.

- [ ] **Step 1: Write the failing test, with two controls that must report** — `random` beside `cluster_by` is legal (task 9 built it); `blocked` with no `cluster_by` is legal (task 10 built it). Assert exact finding sets on all three.
- [ ] **Step 2–4:** Fail, implement, pass. The message says what the sibling refusals say: block size counts units, a cluster is indivisible, no block size honours both — and names the two honest routes (`random` for a clustered draw, `by_attribute` for a read one).
- [ ] **Step 5: Mutate** each control separately; neither may die to the other's branch.
- [ ] **Step 6: Registry row in sort order**, checking every row it moves. Commit.

---

## Task 12: `assign.stratify_by` in the draw

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`; Test `tests/test_units.py`, `tests/test_validate.py`

**Interfaces — Consumes:** `units.stratum_varies_within_cluster` (exists; do not reimplement the constancy test).

- [ ] **Step 1: Write the failing tests**

```python
def test_a_stratified_draw_balances_arms_within_every_stratum():
    """`stratify_by: [site]` over 12 units in sites A(6)/B(4)/C(2) — three
    strata of different sizes, so a draw balancing only overall would leave at
    least one stratum lopsided. Assert each stratum's per-arm counts exactly."""

def test_a_stratum_that_varies_within_a_cluster_is_refused(write_config):
    """§ Clustered units: `validate` 'rejects it instead of silently
    prioritizing one constraint'. Reuses `stratum_varies_within_cluster`."""

def test_an_unknown_stratum_attribute_is_refused(write_config):
    """*Allocation strata exist* — E-DATA-ASSIGN-STRATIFY-UNKNOWN, minted in
    task 3. The control: a declared attribute must NOT be refused."""
```

- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: `W-DATA-CLUSTER-UNDECLARED`'s exclusion list** excludes an attribute "a `sweep.groups` axis names or an `assign.from` reads… any `stratify_by`". **Under a draw there is no `assign.from`** — check the exclusion reaches `assign.stratify_by`, and add a test either way.
- [ ] **Step 6: Record, do not fix** — `assign.<axis>.stratify_by` is **not** in `CONSTANT_COLUMN_RULES`, so a stratum varying across a unit's measurement rows collapses silently, unlike `assign.<axis>.from` which H3c-1 wired in. Record it in `reference.md`, not in the gitignored `spec-defects.md`.
- [ ] **Step 7: Mutations; commit.**

---

## Task 13: Forward-only stratification

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`; Test `tests/test_units.py`, `tests/test_validate.py`

**A sequencing requirement, not a check.** Axis 2's draw consumes axis 1's **realized** membership as its stratum column. Nothing today establishes any per-axis draw order — `_resolved_group_axes` builds a dict in declaration order **by accident of construction, not by contract**.

- [ ] **Step 1: Write the failing tests**

```python
def test_an_axis_may_stratify_on_an_earlier_axis():
    """experimental-designs.md § Between-subjects factorial: 'Axes resolve in
    declaration order and `stratify_by` may name an earlier axis'. `sex` then
    `arm: {stratify_by: [sex]}` — assert arm is balanced WITHIN each sex."""

def test_stratifying_on_a_later_axis_is_refused(write_config):
    """*Stratification is forward-only*: 'an axis may only stratify on one
    already resolved'. The control is the same pair declared the other way
    round, which must be accepted."""

def test_the_draw_order_is_the_declaration_order_by_contract():
    """Pins the sequencing itself, so a later refactor of `_resolved_group_axes`
    into an unordered mapping fails here rather than silently reordering draws."""
```

- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutation** — reverse the draw order; the earlier-axis test must fail. **If it passes, axis 2 is not actually consuming axis 1's membership** and the feature is decorative.
- [ ] **Step 6: Commit.**

---

## Task 14: `allocation.json` records the draw; the refusal retires

**Files:** Modify `src/publishable/artifacts.py`, `src/publishable/validate.py`, `docs/reference.md`, `docs/experimental-designs.md`; Test `tests/test_artifacts.py`, `tests/test_cli.py`, `tests/test_validate.py`

**Only now, after everything the refusal masks is built.** H3c-1's ordering lesson: a retirement ahead of its preconditions ships a wrong number, and each of the three retirements this project has done made a latent defect live.

- [ ] **Step 1: `allocation.json` gains `seed` and `strata`.** § `allocation.json` prints them keyed by axis. **The change is *add per-axis entries for drawn axes*, not *replace the empties*** — that section says a `by_attribute` axis "is left out of both". Two tests lock the current shape literally (`doc["strata"] == {}` in `tests/test_artifacts.py`, `alloc["strata"] == {}` in `tests/test_cli.py`) and `build_allocation_document`'s four-paragraph docstring argues for the empties. All three change.
- [ ] **Step 2: The mixed case is the test that matters** — one `by_attribute` axis beside one `random` axis, asserting the drawn axis appears in `seed` and `strata` and the read one does not, in the same document.
- [ ] **Step 3: Retire `E-DATA-ASSIGN-DRAWN`.** Remove the `elif` branch and `DRAWN_ASSIGN_METHODS`. **Work from task 1's site list**, and check off each of the ten prose surfaces.
- [ ] **Step 4: Grep both directions, and prove the grep can fail.** The three retired-code greps in H3c-1 found a true hit only because the sweep was re-run without a filter — **filter the file list, never the output.** Run against a code you know is present and show the non-empty result first.
- [ ] **Step 5: Re-record the `resume` gap.** § Resuming says `allocation.json` is "read rather than re-drawn on resume". **There is still no `resume` command** — `OPERATION_COMMANDS = {"validate", "run"}` — and under `by_attribute` that was harmless because re-reading a column is idempotent. **Under a draw it stops being harmless.** Say that in `reference.md`; do not build `resume`.
- [ ] **Step 6: The `NOT BUILT` register.** Check whether retiring this code changes it — the register marks *declarations*, and this is a *method value*, so most likely it does not. **Check rather than assume**, and check the spelled count and the enumeration, not only the markers.
- [ ] **Step 7: Commit.**

---

## Sequencing

1 → 14 in order. Tasks 1–3 are the documents and two of them are **rulings**, which must land before the code that implements them. Task 4 closes the block so tasks 5–13's four new keys cannot be silently misspelled. Task 5 ships a live-gap fix that needs no drawing. Task 6 is the seed and task 7 the authority seam — **7 is the one whose failure mode is a second membership producer**, and 8–13 all consume it. Task 14 retires last, after everything the refusal masks is built.

## Where this slice will be attacked

The acceptance property, stated so task 14 can verify it: **a drawn assignment is a partition of the roster into the declared levels, reproducible from `(digest, axis, roster, seed)` alone, recorded in `allocation.json`, and identical between the plan `validate` computes and the one the runner executes.** H3c-1's bar was defeated three times — twice by a shape nobody had tried and once by the documented feature itself. Expect the same here, and expect the successful attack to come from roster content rather than config shape.
