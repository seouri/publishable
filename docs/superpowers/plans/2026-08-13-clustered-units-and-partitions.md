# H3b Clustered Units and Partitions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `data.units.cluster_by` and a `fold` level's `stratify_by` execute — whole clusters go to one side of a split, `n` reports `clusters`, and the intervals become cluster-robust — retiring `E-DATA-CLUSTER-UNSUPPORTED` and `E-REPL-FOLD-STRATIFY-UNSUPPORTED`.

**Architecture:** Cluster membership resolves once beside the roster, the way H3a returned `technical_n` beside it, and is read by the partitioner, the statistics and the checks — one authority, never an attribute of `UnitList`. `partition_units` is rewritten once, from a shuffle-and-stride into a group-shuffle-and-assign, shaped so H3c can add cells and H3d an uneven two-way split without rewriting it again.

**Tech Stack:** Python 3.12+, `uv`, pytest, ruff, mypy. No new dependencies.

## Global Constraints

Every task's requirements implicitly include this section.

- **The documents lead the code.** `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md` and `docs/reference.md` are normative. Where code cannot follow, **the document changes first**; where the code is wrong, record the gap rather than editing a document to describe code that does not exist. This project has shipped that defect at three layers in one commit.
- **`validate` collects findings and never raises.** A wrongly-typed or absent field produces a finding, never a `TypeError` — and must not silently *skip* its check.
- **Assert exact numbers, not directions.** H3a shipped **eight** checks that could not discriminate, including one asserting an interval was "wider" that passed against the wrong degrees of freedom, and a strict-`xfail` forcing function that asserted shape rather than arithmetic. **CR1's entire point is `df = clusters − 1` — assert the number.**
- **Every probe needs a control that must report.** Four of the controller's own verification probes in H3a reported nothing for *every* input — including the case that had to fail — because the harness bailed first.
- **Beware fixtures where two quantities coincide.** A prescribed `mean → median` mutation could not fail because both are `15.0` for `[10, 20]`. **Under equal-sized or singleton clusters the clustered and unclustered partitioners agree**, so every partition test uses deliberately uneven clusters and says why its numbers discriminate.
- **The unit-table reconciliation.** `resolved == completed + ineligible + failed`. H3a found three ways to break it, none raising an error. Every new path is checked against `n`'s parts, not only against its own output.
- **Mutation testing is never reasoned about.** Apply, run the named test, confirm FAIL, revert, confirm PASS. **Delete `__pycache__` between mutation and revert** — CPython validates a `.pyc` against source mtime truncated to *seconds* plus size, so a same-size same-second revert stays invisible. **Verify reverts by behaviour, never `git status`.**
- **A new code raised from `replication.py` must join `validate.REPL_DECLARATION_CODES`**, or it escapes `validate` entirely. That frozenset is what translates a raise into a finding.
- **Verify every helper and fixture exists before calling it.** `tests/test_validate.py`'s `write_config`/`codes` are real; `write_config` writes `input/index.csv` with the single column `patient_id`, so a test needing more columns writes its own table into that same `input/` directory.
- `uv run pytest`, `uv run ruff check .`, `uv run mypy` green. **Do not run `ruff format .`** — it reformats repo-wide, pre-existing, out of scope.
- Cite by section, never line number; `×` not `x`; **hyphen never an en dash** in anything becoming a filename or anchor.
- **The worked example declares no `cluster_by`.** Nothing about `cohort-pilot` may move: 240/228/12; r = 0.581 / 0.607 / 0.412; delta 0.026, ci95 [−0.007, 0.059]; kendall −0.169, [−0.213, −0.125]; `repeat_spread` std 0.014; hashes `8e21`/`1a2b`/`3d8a`/`6b1f`; README's demo `2f5c8d0`.

---

## Verified interfaces — these were read from the code, not assumed

| Site | Signature / fact |
|---|---|
| `units.partition_units` | `(roster: UnitList, k: int, digest: str) -> list[list[Unit]]` — a shuffle then `shuffled[i::k]`. **One caller**, `cli.py`'s fold-partition step |
| `units.resolve_units` | returns `(UnitList, technical_n \| None, columns: frozenset[str])` — H3a made it a three-tuple |
| `units.collapse_measurements` | `(units: list[Unit], by: str, collapse: Any) -> tuple[list[Unit], list[int]]` — groups rows by key, so it is the one place holding **pre-collapse** values |
| `replication._fold_k` | `(level: dict, unit_count: int \| None) -> int`. Raises `E-REPL-FOLD-STRATIFY-UNSUPPORTED` **before** `k` is read — see task 8's ordering trap |
| `replication.resolve_repeats` | `(config, digest, unit_count=None)`. **Two callers**: `validate` (passing its resolved count) and `cli` (passing `len(roster)`) |
| `validate.REPL_DECLARATION_CODES` | The frozenset translating a `replication.py` raise into a finding |
| `validate._check_units` | wraps `resolve_units` in `except ContractError` — the route a `units.py` raise takes to become a validate-time finding |
| `stats._t_critical` | `(df: float, confidence: float) -> float` — H3a extracted it; `df` is already a float |
| `cli` | `derived_metric_draws = 2000`, a **hard constant** — the derived-metric percentile draw runs unconditionally, ungated by `statistics.resample` |

**No fixture named in this plan exists yet.** Follow each test file's existing patterns.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/units.py` | Cluster resolution as one authority; the `partition_units` rewrite; the constancy check in `collapse_measurements` |
| `src/publishable/replication.py` | `stratify_by` honoured; `k` and `k: all` bounded by cluster count |
| `src/publishable/stats.py` | `t_over_units_clustered` (CR1); the clustered percentile draw |
| `src/publishable/runner.py` | `n` gains `clusters` — **conditionally** |
| `src/publishable/validate.py` | The cluster-attribute check, the undeclared warning, the fold/cluster checks, both retirements |
| `src/publishable/cli.py` | Threading cluster membership to the partitioner and the statistics, including the unconditional derived draw |
| `docs/reference.md` | The owed *Cluster attribute exists* row; `W-DATA-CLUSTER-UNDECLARED`; the `× measurements` rule; the `NOT BUILT` count nine → seven |

---

## Task 1: The documents first

**Files:** Modify `docs/reference.md`

Nothing in this slice may land a check describing a rule no document states. Three document changes come first, and each is a rule the code below implements rather than a description of code that exists.

- [ ] **Step 1: The owed *Cluster attribute exists* row.** § Validation has *"Weight attribute exists"* — `data.units.weight_by` names something that is not a unit attribute — and **no cluster equivalent**, though `cluster_by` names an attribute the same way. Add the row, phrased as its weight sibling is. Read that sibling first; do not invent a phrasing.

- [ ] **Step 2: `W-DATA-CLUSTER-UNDECLARED`.** § Clustered units already promises it — *"`validate` warns when an attribute looks like a cluster identifier (few distinct values, many units each) but hasn't been declared as one"* — and § Validation carries the row *"Clustering looks undeclared"*. **The identifier does not exist in any file.** Add its row to § Warnings core reports, stating the trigger the way `W-DATA-WEIGHT-UNDECLARED`'s row does.

**The trigger is structural here, and that is worth stating.** H3a's weight warning needed a *name* test (`weight`/`_prob`/`probability`) because `age`, `dose` and `latency` are shape-identical to a sampling weight. A cluster is not: "few distinct values, many units each" is a genuine structural discriminator, which is why § Weighted samples says the weight case is *"not by the same means"*. **Do not add a name test here** — say in the row what the structural trigger is.

- [ ] **Step 3: The `× measurements` rule.** § Clustered units gains the sentence that a cluster must not vary within a unit's measurement rows, mirroring the one § Weighted samples carries for weights. State the consequence, because it is worse than the weight case: a mis-collapsed cluster decides **which side of a train/test split** a unit lands on, which is the leak the section calls "the difference between a valid evaluation and a leaky one".

- [ ] **Step 4: Mechanical pass over the edited rows, then commit.**

```bash
git commit -am "docs: name the cluster checks the code is about to implement"
```

---

## Task 2: Cluster resolution, one authority

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**Interfaces:**
- Produces: `clusters_of(roster: UnitList, cluster_by: str) -> dict[str, str]` — unit key to cluster id, and `cluster_count(...)`. Everything below reads these; **nothing re-derives cluster membership**.

H3a proved this pattern twice (`units.usable_weight`, `units.is_measurement_numeric`): one function answers the question, read by `validate` and by `stats`, so a config that validates cannot crash on a value `validate` approved. Three near-misses on a fourth notion were caught in H3a — do not create one here.

**`cluster_by` names a declared attribute**, exactly as `weight_by` does and unlike `measurements.by`, which names a source column. H3a's task 6 shipped a Critical by getting that backwards; § Clustered units' own YAML and the *Cluster attribute exists* row you wrote in task 1 settle it.

- [ ] **Step 1: Write the failing test**

```python
def test_clusters_group_units_by_their_declared_attribute():
    units = [Unit(key=f"u{i}", paths=(), attributes={"site": s})
             for i, s in enumerate(["S1", "S1", "S1", "S2", "S3"])]
    roster = UnitList(units)
    assert clusters_of(roster, "site") == {
        "u0": "S1", "u1": "S1", "u2": "S1", "u3": "S2", "u4": "S3"}
    assert cluster_count(roster, "site") == 3   # 3 clusters over 5 units, deliberately uneven
```

- [ ] **Step 2: Run it, confirm it fails** on the missing name.
- [ ] **Step 3: Implement**, raising `ContractError` for a unit missing the attribute — the code the *Cluster attribute exists* row implies, taken from your task 1 row rather than invented.
- [ ] **Step 4: Run, confirm pass.**
- [ ] **Step 5: Mutation-test** — return the unit key as its own cluster; the count assertion must fail.

- [ ] **Step 6: Emit `W-DATA-CLUSTER-UNDECLARED`.** Task 1 minted the identifier and wrote its row; **no other task owns the emit site**, so without this step the slice ships a documented warning nothing raises. Task 1's implementer found this and it is a real plan gap, not a scope creep.

Implement the trigger **exactly as task 1's row states it** — read that row, do not re-derive from this sentence. It is deliberately predicate-only with no numeric threshold, because `CLAUDE.md` puts every threshold in `limits` and adding a `limits` key is code task 1 could not write. If a predicate proves unimplementable, **change the row and say so** rather than implementing something the document does not describe.

Two tests, and the second is the one that matters:

```python
def test_a_column_that_looks_like_a_cluster_warns_when_undeclared():
    ...
    assert "W-DATA-CLUSTER-UNDECLARED" in codes(path)

def test_the_worked_examples_own_attributes_do_not_warn():
    """cohort-pilot declares `[label, age, sex]` and no cluster_by. `sex` has two
    values over many units, which "few distinct values, many units each" reads as
    a cluster — so this is the control that decides whether the trigger is usable
    at all, not a nicety. Task 1 verified the row's predicates are silent here."""
    assert "W-DATA-CLUSTER-UNDECLARED" not in codes(path)
```

Mutation-test the trigger, and confirm the negative control fails under a deliberately loosened predicate.

- [ ] **Step 7: Commit.**

---

## Task 3: A cluster must not vary within a unit's measurement rows

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`, `tests/test_validate.py`

**This closes H3a's open weight gap with the same machinery — wire both callers.** § Weighted samples already states the weight rule with the check owed; building the mechanism and wiring only the cluster caller would ship a capability and an identical known bug side by side.

Reproduced before this plan was written:

```
p1's replicate rows declare site S1 and S2
collapse -> 'S1', chosen by the `first` fallback
```

**`validate` cannot host this check.** `resolve_units` collapses internally, so a validate-time check sees the post-collapse roster and the varying values are already gone — which is exactly why H3a could only state the weight rule. `collapse_measurements` groups rows by key and holds the pre-collapse values, so the check belongs there, told which columns must not vary.

- [ ] **Step 1: Write the failing tests** — one per column kind, each asserting the code:

```python
def test_a_cluster_varying_within_a_unit_is_refused():
    """A mis-collapsed cluster decides which side of a split a unit lands on."""
    units = [Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
             Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S2"})]
    with pytest.raises(ContractError) as e:
        collapse_measurements(units, by="read", collapse="first", constant=("site",))
    assert e.value.code == "E-DATA-CLUSTER-VARIES"

def test_a_cluster_constant_within_a_unit_is_accepted():
    """The control: same shape, agreeing rows, must NOT raise."""
    units = [Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
             Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S1"})]
    collapsed, _ = collapse_measurements(units, by="read", collapse="first", constant=("site",))
    assert collapsed[0].site == "S1"
```

- [ ] **Step 2: Run, confirm both fail** — the first on the missing parameter, not on a passing assertion.
- [ ] **Step 3: Implement.** `collapse_measurements` gains `constant: tuple[str, ...] = ()` and refuses a named column that varies within a group. `resolve_units` passes the names it already knows from `units_decl` — `cluster_by`'s, and `weight_by`'s. **Two codes, not one**: the cluster case and the weight case say different things about what breaks, so `E-DATA-WEIGHT-VARIES` is the weight half and closes H3a's gap.
- [ ] **Step 4: Run, confirm pass**, including the weight half end to end through `validate` (a `ContractError` from `units.py` reaches `validate` through `_check_units`'s `except ContractError` — the route `E-UNITS-COLLAPSE-RULE` already takes).
- [ ] **Step 5: Mutation-test each half separately.** One mutation killing both is not two tests.
- [ ] **Step 6: Both registry rows, both dual-listed** as `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` is — they are raised from `units.py` and surface at both `validate` and run time. Commit.

---

## Task 4: `partition_units` draws whole clusters

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**The slice's load-bearing task.** § Clustered units: *"Whole clusters go to one side of a split; a cluster is never divided between train and test … the metric is inflated before any interval is computed — so cluster-robust standard errors don't repair it."*

**What balances is unit count, not cluster count**, and the existing docstring's promise weakens. It currently claims "sizes differ by at most one". Under indivisible clusters that cannot hold, so it becomes *as even as indivisible clusters allow*. **Say the weaker thing in the docstring rather than keep claiming the stronger one.**

**The assignment order is part of the contract, not an implementation detail.** Measured over the fixture below (sizes 7/3/3/1/1 at `k = 2`):

| Order clusters are assigned in | Resulting folds |
|---|---|
| largest first | **8, 7** |
| smallest first | 11, 4 |

So the rule is: **shuffle the clusters with the digest-seeded RNG, then assign largest first, each to the currently-smallest fold.** The shuffle is what keeps the draw a function of the design digest — and what breaks ties among equal-sized clusters, which is the only place it can still matter once the sort is stable. Sorting without shuffling would make the partition deterministic given the sizes alone, which contradicts § What auto-derives from; shuffling without sorting gives the 11/4 split above. **Both halves are load-bearing and each needs its own mutation.**

- [ ] **Step 1: Write the failing test — uneven clusters, and say why they discriminate**

```python
def test_no_cluster_is_split_across_folds():
    """Cluster sizes 7/3/3/1/1 over k=2. Deliberately uneven: with equal-sized or
    singleton clusters the clustered and unclustered partitioners agree, so a test
    over those could not see this rewrite at all."""
    sizes = {"S1": 7, "S2": 3, "S3": 3, "S4": 1, "S5": 1}
    units, clusters = [], {}
    for site, n in sizes.items():
        for i in range(n):
            key = f"{site}_{i}"
            units.append(Unit(key=key, paths=(), attributes={"site": site}))
            clusters[key] = site
    folds = partition_units(UnitList(units), k=2, digest="sha256:abc", clusters=clusters)
    seen = {}
    for f, fold in enumerate(folds):
        for u in fold:
            assert seen.setdefault(clusters[u.key], f) == f, "a cluster spans two folds"
    assert sum(len(f) for f in folds) == 15          # every unit lands exactly once
    assert {len(f) for f in folds} == {8, 7}          # balanced by UNIT count
```

- [ ] **Step 2: Run, confirm it fails.**
- [ ] **Step 3: Implement.** `clusters: dict[str, str] | None = None`; when `None`, behaviour is **byte-identical to today** — pin that separately, because every existing fold test depends on it.
- [ ] **Step 4: Run the whole existing fold suite untouched.** It is the oracle for the unclustered path.
- [ ] **Step 5: Four mutations, separately.**
  - assign units rather than clusters → the split test fails;
  - balance *cluster* count instead of unit count → the `{8, 7}` assertion fails;
  - **drop the largest-first sort**, keeping the shuffle → the `{8, 7}` assertion fails for at least one seed. **Find a seed where it does and pin that seed**, because for some shuffles the greedy result coincides with the sorted one — this mutation is otherwise a check that could not fail, which is the trap this slice has met eight times;
  - **drop the shuffle**, keeping the sort → a test asserting two different digests give different assignments must fail. Write that test; without it the digest-seeding rule is claimed and not provided.
  Each with `__pycache__` cleared, reverts verified by behaviour.
- [ ] **Step 6: Commit.**

---

## Task 5: `k` and `k: all` are bounded by clusters

**Files:** Modify `src/publishable/replication.py`, `src/publishable/validate.py`, `src/publishable/cli.py`; Test `tests/test_replication.py`, `tests/test_validate.py`

§ Validation, *"Folds fit inside the clusters"*: `{kind: fold, k: 10}` with `cluster_by: animal_id` over 6 animals — **clusters are indivisible, so `k` may not exceed the cluster count**. And *"Leave-one-out is affordable"* is **already implemented and this task makes it wrong**: `k: all` stops meaning one unit per fold and starts meaning leave-one-*cluster*-out.

**`unit_count` reaches `_fold_k` by two arrival paths and both must change** — `validate`'s call and `cli`'s. H3a's task 10 shipped a bug by changing two of three sites; the regression test for the *unclustered* path is what catches changing only one here.

- [ ] **Step 1: Write the failing tests** — `k` above the cluster count refused; `k: all` yielding the cluster count; and **the control**, an unclustered run whose `k: all` still yields the unit count.
- [ ] **Step 2–4:** Fail, implement, pass. Pass a cluster count where the unit count goes today; do not add a second parameter that can disagree with the first.
- [ ] **Step 5: Mutation** — leave one arrival path unchanged; a named test must fail.
- [ ] **Step 6:** Update the *Leave-one-out is affordable* row for what `k: all` now means under clustering, and commit.

---

## Task 6: `stratify_by`, and strata that survive clustering

**Files:** Modify `src/publishable/replication.py`, `src/publishable/units.py`, `src/publishable/validate.py`; Test `tests/test_units.py`, `tests/test_validate.py`

Two rows. *"Stratification attribute exists"* — shared three ways, and **only its `fold.` half is yours**; `assign.*.` is H3c's and `holdout.` is H3d's, so scope the check to a `fold` level and say so. And *"Fold strata survive clustering"*: `{kind: fold, stratify_by: label}` with `cluster_by: animal_id` where `label` varies within an animal — **a stratum cannot be balanced across a split that cannot divide the cluster carrying both values.**

**The ordering trap the scoping found.** `_fold_k` raises `E-REPL-FOLD-STRATIFY-UNSUPPORTED` **before** `k` is read, so retiring it changes what other configs report: `{k: 1, stratify_by: x}` becomes `E-REPL-FOLD-K` and `{k: 99, …}` becomes `E-REPL-FOLD-K-TOO-LARGE`. **Pin both of those before touching the raise**, so the change in reported code is visible rather than discovered.

**`_fold_k` has no roster**, so the survives-clustering check cannot live there. It needs cluster membership and the stratum attribute together — put it where both are in hand, and say where in the report.

- [ ] **Step 1–6:** Failing tests (each row's identifier, plus the two ordering pins and a control where the stratum *is* constant within every cluster); implement; mutate each check separately; commit.

---

## Task 7: The stratified partition

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**Why this task exists.** Task 6 made `fold.stratify_by` *validated* — both its checks land — but `partition_units` takes no stratum, so **a declared stratification has no effect on the split.** § Repeat kinds calls folds "stratified" when it is declared, so this is a declaration accepted whose effect is not delivered: the risk this project names first, and the one task 12 would make live by retiring `E-REPL-FOLD-STRATIFY-UNSUPPORTED`.

**This was a gap in the plan, not in task 4 or 6.** Task 4's heading said "and honouring a stratification" and no step owned it; task 6's implementer found it and said so. It is the second gap of that exact shape in this slice, the first being `cli` calling `partition_units` without the clusters.

**Interfaces, read from the code:**
- `units.partition_units(roster, k, digest, clusters: dict[str, str] | None = None)` — task 4's rewrite: group in roster order, shuffle cluster names with the digest-seeded RNG, stable-sort by descending size, assign each whole cluster to the currently-smallest fold by unit count.
- `units.stratum_varies_within_cluster(roster, cluster_by, stratify_by)` — task 6's check, which guarantees that **when clustering is declared, every cluster carries exactly one stratum value.** That is what makes a cluster assignable to a stratum at all, and it is why this task can treat cluster and stratum as compatible rather than competing.
- `units.clusters_of` — the single authority. Do not group a second way.

**The two objectives, and how they compose.** Task 4 balances **unit count** across folds. Stratification balances **stratum proportions**. Because task 6 guarantees a cluster carries one stratum value, a cluster belongs to exactly one stratum — so the composition is: **partition within each stratum, using task 4's rule, then merge the per-stratum folds index-wise.** That keeps clusters whole, keeps each fold's stratum mix close to the roster's, and reuses the existing rule rather than inventing a second balancer.

**Unclustered is the degenerate case, not a separate path.** With no `clusters`, treat each unit as its own cluster of one — the same code, and task 4's `clusters=None` behaviour must stay **byte-identical** because every existing fold test is its oracle.

- [ ] **Step 1: Write the failing test — asymmetric strata, and say why they discriminate**

```python
def test_each_fold_gets_a_proportional_share_of_each_stratum():
    """12 units, 8 label=0 and 4 label=1, at k=2. Deliberately asymmetric: with
    a 6/6 split an unstratified partition often lands 3/3 by luck, so a balanced
    fixture cannot see this rule at all. Here each fold must get 4 and 2."""
    ...
    for fold in folds:
        counts = Counter(u.label for u in fold)
        assert counts["0"] == 4 and counts["1"] == 2
```

- [ ] **Step 2: Run it, confirm it fails.**
- [ ] **Step 3: Implement.** `partition_units(..., strata: dict[str, str] | None = None)`.
- [ ] **Step 4: Run, and run the whole existing fold suite untouched** — it is the oracle for `strata=None`.
- [ ] **Step 5: Four mutations, separately.**
  - drop the stratification (partition the whole roster at once) → the proportion test fails;
  - merge the per-stratum folds by **sorting on size** instead of index-wise → find a fixture where that unbalances the strata and pin it, **or say the mutation cannot fail and why**;
  - **split a cluster** while stratifying → task 4's no-split test must still fail, proving stratification did not reintroduce the leak;
  - stratify but ignore `clusters` → the no-split test fails.
  Each with `__pycache__` cleared, reverts verified by behaviour.
- [ ] **Step 6: State the interaction in the docstring** — that a cluster carries one stratum value *because task 6 refuses otherwise*, so this composition is sound only while that check exists. A later slice removing it would silently break this.
- [ ] **Step 7: Commit.**

---

## Task 8: `n` gains `clusters`

**Files:** Modify `src/publishable/runner.py`, `src/publishable/stats.py`, `src/publishable/cli.py`; Test `tests/test_runner.py`, `tests/test_cli.py`

§ The three-part `n`: each part is *"present only when it applies so a design that never skips reads as it always did"*. H3a built the route and this task follows it rather than inventing a second one: **a key that joins `n` travels in `summarize_step`'s `counts`; a key that sits beside `n` travels in `beside_n`.** `clusters` joins `n`, so it is `counts` work — the same slot `effective` took.

**The regression test is a run that declares no `cluster_by`** — write it first. Everything else is easy to get right while quietly breaking it, which is exactly how H3a's `effective` nearly shipped unconditional.

- [ ] **Step 1–6:** Failing tests (`clusters` present and exact; **absent** without `cluster_by`); implement across all three `n`-building sites in `runner.py`; mutate to make it unconditional and confirm the regression test fails; commit.

---

## Task 9: `t_over_units_clustered` — CR1

**Files:** Modify `src/publishable/stats.py`; Test `tests/test_stats.py`

§ Statistical reporting: *"Cluster-robust (CR1: the sandwich estimator with the standard finite-sample scaling), **df = clusters − 1**. The df is the part that bites — 10 animals give 9, not 299."*

**Assert the number.** H3a's task 9 asserted a weighted interval was "wider than unweighted" and passed against an implementation using the row count for df, because it is still wider. The same trap is here in sharper form: a clustered interval over correlated data is wider than the unclustered one *whatever* df it uses.

- [ ] **Step 1: Write the failing tests, the df one first**

```python
def test_the_clustered_interval_takes_its_df_from_the_cluster_count():
    """10 clusters of 3 units. df must be 9, not 29 — the document's own example
    is '10 animals give 9, not 299'. Asserting only that the interval is wider
    would pass against an implementation using the unit count, because a
    cluster-robust interval over correlated data is wider either way."""
    ...
    # Compare against `t_over_units` on a three-point fixture whose df is 9 by
    # construction, so the expectation does not come from the code under test.
```

Reuse `_t_critical(df, confidence)` — H3a extracted it precisely so two critical-value expressions cannot drift, and its `df` is already a `float`.

- [ ] **Step 2–4:** Fail, implement the CR1 sandwich with its finite-sample scaling, pass.
- [ ] **Step 5: Two mutations, separately** — df from the unit count; and the finite-sample scaling dropped. **If no existing test fails for the second, write one**: it is the "CR1" half of the name, and an interval that omits it is a different construction wearing the same `method`.
- [ ] **Step 6:** Registry/§ Statistical reporting consistency, and commit.

---

## Task 10: The clustered percentile draw

**Files:** Modify `src/publishable/stats.py`; Test `tests/test_stats.py`

§ Statistical reporting: the percentile forms *"resample whole clusters"*. Note `percentile_over_units` **sorts its pool**, with a comment saying the resample must depend on the multiset rather than row order — H3a's weighted version had to keep each value with its own weight through that sort, and the clustered one must keep each value with its **cluster**.

- [ ] **Step 1: Write the failing test** — a fixture where drawing clusters and drawing units give **different, asserted** numbers. With singleton clusters they coincide, which is the trap.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutation** — draw units rather than clusters; the test must fail.
- [ ] **Step 6: Commit.**

---

## Task 11: Wire the partition and both constructions, including the draw that already runs

### First, and it is the slice's whole point: `cli` calls `partition_units` without the clusters

**A gap this plan did not contain, found by tasks 4 and 5 independently.** `cli.py`'s fold step is:

```python
        partitions = partition_units(roster, fold_level.n, digest)
```

No `clusters` argument. So today a clustered run gets the right fold **count** — task 5 wired that — and the **wrong membership**: task 4's rewrite is never reached, and every fold still trains on other units of the cluster it tests on. That is precisely the leak § Clustered units calls *"the difference between a valid evaluation and a leaky one"*, and `experimental-designs.md` § Mistakes core prevents requires it to be **structurally impossible**.

Task 3 closed the input-file route and task 4 built the partitioner, but **until this line passes `clusters`, the fold route is open**. Pass it, using `units.clusters_of` — task 2's single authority — and **also the strata task 7 added**, since a declared `fold.stratify_by` is equally unwired at that call site. Both arguments or neither: wiring one and not the other ships half a guarantee that looks whole.

**Pin it end to end, not at the function.** `partition_units`' own tests already prove the partitioner; what is unproven is that a *run* reaches it. Assert over a real run that no cluster appears in two folds, with an unclustered control that must report. And beware the coincidence that caught the controller's own probe: on some fixtures the clustered and unclustered partitioners give the **same fold sizes** while differing in membership — assert membership, never sizes.

### Then: the constructions

**Files:** Modify `src/publishable/cli.py`, `src/publishable/stats.py`; Test `tests/test_cli.py`, `tests/test_stats.py`

**`derived_metric_draws = 2000` is a hard constant, so the derived-metric percentile interval draws unconditionally, ungated by `statistics.resample`.** Un-refusing `cluster_by` therefore makes an **already-running** interval wrong. That is why this slice owns the draw at all, and it is the one wiring that cannot be deferred.

H3a's task 11 is the precedent for what "wired" means: **both the value and the interval**, and the weight vector filtered and ordered exactly as the values are. The same applies to cluster membership — a misalignment weights the wrong unit's cluster and produces a plausible number, not an error.

- [ ] **Step 1–6:** Failing end-to-end tests asserting exact numbers; implement at every `summarize_step` call site (H3a found **three** in `cli.py`, all needing the same argument); mutate by dropping the argument at each site separately; commit.

---

## Task 12: Refuse what has no construction, then retire both codes

### Two refusals, not one — and the second was found by task 10

**The clustered contrast family.** § Statistical reporting extends the `_clustered` suffix to the **contrast** constructions — `paired_*` and the unpaired forms, "jointly across both sides when paired". Those do not exist, so retiring `E-DATA-CLUSTER-UNSUPPORTED` without addressing it makes every clustered `vs_baseline` delta a wrong number.

**The clustered derived-metric draw.** Task 10 found that my earlier brief conflated two functions. `percentile_over_units` — which task 10 made cluster-aware — is reached only through `statistics.resample`, still refused by `E-STATS-RESAMPLE-UNSUPPORTED`. The interval that runs **unconditionally** is `percentile_of_derived`, driven by `cli`'s hard-coded `derived_metric_draws = 2000`, and **its clustered form does not exist**. Verified: `percentile_over_units` has zero callers outside `stats.py`; `percentile_of_derived` has one.

Exposure is narrow but real: the shipped `generic` template does not override `aggregate`, so only a **user-written template that derives a metric** reaches it. **Ruled by the user: refuse the combination rather than growing the construction here.**

**Both refusals follow H3a's `E-DATA-WEIGHT-CONTRAST` precedent**, which retired a broad refusal and minted a narrow one for the combination it had just made reachable but could not yet compute. H4 owns lifting both, alongside the `_clustered` family it already owns.

**Measure each blast radius before writing the guard.** H3a's implementer found that gating on the *resolved family* (`comparisons > 0`) rather than on the declaration was both narrower and wider in the right places — a bare `sweep.baseline` produces no comparison and must stay legal. Ask the same question of the derived refusal: **what does "returns derived metrics" mean at validate time**, when `aggregate` is user code core never inspects? If it cannot be known before the run, say so and say where the refusal has to live instead.

### Then: the retirements

### The retirement details


**Files:** Modify `src/publishable/validate.py`, `src/publishable/replication.py`, `docs/reference.md`; Test `tests/test_validate.py`

§ Statistical reporting extends the `_clustered` suffix to the **contrast** constructions — `paired_*` and the unpaired forms, *"jointly across both sides when paired"*. Those do not exist, so retiring `E-DATA-CLUSTER-UNSUPPORTED` without addressing it makes every clustered `vs_baseline` delta a wrong number.

**Mint a narrow temporary refusal**, exactly as H3a did with `E-DATA-WEIGHT-CONTRAST` and H2 with `E-SWEEP-SAMPLE-BASELINE`. **Measure the blast radius first**: H3a's implementer found that gating on the *resolved family* (`comparisons > 0`) rather than on the declaration is both narrower and wider in the right places — a bare `sweep.baseline` produces no comparison and must stay legal. Reuse that shape and say what you measured.

Then the retirements. Both refusals go; § The one config file's prose count goes **nine → seven**; and `E-REPL-FOLD-STRATIFY-UNSUPPORTED`'s removal is the ordering flip task 6 pinned.

- [ ] **Step 1–6:** The refusal with its blast-radius measurement and registry rows; both retirements; **grep every tracked `*.md` for both retired codes and prove the grep can fail** against one that exists; commit.

---

## Task 13: The consistency passes and the exit criterion

**Files:** whichever of the four documents the passes find defects in.

- [ ] **Step 1: Both retirements, both directions** — absent from `src/**/*.py` **and** every tracked `*.md`. Use `--include='*.py'`; stale bytecode has produced a false positive on this exact check. State each command and prove it can fail.
- [ ] **Step 2: The `NOT BUILT` count reads seven**, and exactly `cluster_by` and the fold `stratify_by` left. A number in prose that no mechanical check catches.
- [ ] **Step 3: Registry integrity, both directions** — and remember the codeless § Validation **checks** table carries rows no identifier grep sees.
- [ ] **Step 4: H3b's rows by title**, never by number: *Clustering looks undeclared*, *Folds fit inside the clusters*, *Fold strata survive clustering*, the `fold.` half of *Stratification attribute exists*, the new *Cluster attribute exists*, and the corrected *Leave-one-out is affordable*.
- [ ] **Step 5: `partition_units`' new contract is stated where H3c and H3d will read it** — they both build on it, and H3c rewrites it next.
- [ ] **Step 6: The worked example did not move.** Verify with a **real temporary commit** — a working-tree edit is invisible to a two-dot diff, which is how this check silently passes.
- [ ] **Step 7: The four prevented mistakes, one at a time.** `experimental-designs.md` § Mistakes core prevents carries **four** cluster rows, and `CLAUDE.md` requires each to be **structurally impossible, not merely discouraged**. Check each against what this slice actually built, and say which task provides it:

| Row | Must be impossible via | Owner |
|---|---|---|
| **Ignored clustering** | the cluster-robust intervals **and** the undeclared warning | tasks 9, 9, 2 |
| **A cluster split across train and test** | the partition rewrite **and** the constancy check — the partition closes the fold route, the check closes the *input-file* route, and **both are needed**: a cluster mis-collapsed at resolution is already in the wrong place before any partition runs | tasks 4, 3 |
| **Resampling clustered rows as if independent** | **Corrected after task 11.** Task 10's `percentile_over_units_clustered` closes the `statistics.resample` path, which H4 still refuses and which has **no caller at all** today. The **live** path is `percentile_of_derived`, still unit-level — so this row closes only by **task 12's refusal** of `cluster_by` beside a derived metric, not by task 10's construction. Check the refusal, not the function | task 12 (task 10 for the gated path) |
| **A permutation that shuffles away the matching** | `null_test`, refused by `E-STATS-NULLTEST-UNSUPPORTED` — **out of scope, and still refused**. Confirm the refusal is live rather than assuming it | H4 |

The second row is the one to check hardest: it is the only one where two different tasks each close half of it, and closing one half looks complete from inside that task.

- [ ] **Step 8: The mechanical pass, then the cross-document pass** over `CLAUDE.md`'s remaining drift classes — **declared vs. derived** (`clusters` is derived; no passage may show it as a settable input), **config completeness**, and **enum comments**.
- [ ] **Step 9: Fix what the passes find; commit only if something changed.** A clean result is a real result — do not create an empty commit.

---

## Sequencing

1 → 13 in order. Task 1 states the rules everything below implements. Tasks 2–3 build the authority and the constancy check the partitioner depends on. Task 4 is the load-bearing rewrite; 5 and 6 depend on it. Tasks 7–10 are the reporting and statistics, which need cluster membership resolved. Task 11 retires only after everything it was masking is handled — the ordering H3a proved, where a retirement ahead of its preconditions ships a wrong number. Task 12 runs last, over a settled tree.
