# Fold Repeats (S3c) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `fold` repeat hands each execution one test partition, and the inference base is rebuilt from the concatenation of those partitions rather than from an average over them.

**Architecture:** Partitioning is a pure function in `units.py` over the roster and `k`, drawn from the design digest once per run and shared across conditions. A fold level's members are labeled `fold01…foldNN`, and a map from fold label to unit keys (`fold_members`) is threaded into the three functions whose rules change: `stats.collapse_repeats`, `runner.attrition`, and `runner._units_failed_anywhere`. When no fold is declared that map is `None` and every one of them behaves exactly as it does today.

**Tech Stack:** Python 3.11+, `uv`, pytest, ruff, mypy.

## Global Constraints

- Python >= 3.11.
- Runtime dependencies are exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`. Adding one is out of scope.
- ruff: line-length 100, select `["E","F","I","UP","B"]`. mypy: strict over `src/`.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy`.
- `×`, not `x`, for multiplication — including inside fenced blocks and commit messages.
- `sweep.py` and `stats.py` are **pure**: no filesystem access, and no runtime import of `config`, `artifacts`, `runner`, or `cli`.
- `artifacts.py` is the only module that writes inside a run directory.
- `validate.py` **collects** findings and never raises to report one.
- Every `E-`/`W-` identifier must have a test that produces it.
- The four documents in `docs/` are normative and lead. Where code cannot follow them, the document changes first and the gap is recorded in `docs/superpowers/spec-defects.md`.
- Unimplemented must mean **refused**, never silently ignored.
- **A run with no `fold` level must be byte-for-byte unchanged.** Every rule in this plan is conditional on a fold being declared; the regression risk is that one fires when none is.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/units.py` | `partition_units` (pure); `UnitList` construction for a fold's test/train sides |
| `src/publishable/replication.py` | `fold` accepted; `k`/`all` resolved against the unit count; `E-REPL-FOLD-STRATIFY-UNSUPPORTED` and `E-REPL-FOLD-K-TOO-LARGE`; `fold_members_for` |
| `src/publishable/stats.py` | `handed_to` (shared helper); `collapse_repeats` concatenating folds and averaging seeds within one |
| `src/publishable/runner.py` | `attrition` over the repeats a unit was handed; `_units_failed_anywhere` against the partition; handing each execution its `UnitList` |
| `src/publishable/artifacts.py` | `io.units`/`io.units.train` raising at `run` and `condition` scope under a fold |
| `src/publishable/validate.py` | Threading the unit count into `_check_replication`; the two refusals as diagnostics |
| `src/publishable/cli.py` · `sweep.py` | `partitions` into `sweep.yaml` |

---

### Task 1: Partitioning

**Files:**
- Modify: `src/publishable/units.py`
- Test: `tests/test_units.py`

**Interfaces:**
- Consumes: `Unit` (frozen, hashable by `key`), `UnitList(units: list[Unit], train: UnitList | None = None)` — both already exist.
- Produces: `partition_units(roster: UnitList, k: int, digest: str) -> list[list[Unit]]`

Partitioning lives here, not in a new module: `docs/reference.md` § Package layout assigns `units.py` "unit resolution (table/glob/resolver registry), keys, attributes, **partitioning**", and the documents lead.

**The draw comes from the design digest**, never `parameters_hash` — `reference.md` § What auto-derives from is explicit that otherwise editing any parameter would redraw every fold boundary. Use `random.Random(seed)` seeded from the digest, never the module-level global.

- [ ] **Step 1: Write the failing property tests**

```python
def _roster(n):
    return UnitList([Unit(key=f"u{i:03d}", paths={}, attributes={}) for i in range(n)])


def test_every_unit_appears_in_exactly_one_partition():
    parts = partition_units(_roster(240), 10, "d")
    seen = [u.key for p in parts for u in p]
    assert len(seen) == 240
    assert len(set(seen)) == 240


def test_partitions_cover_the_roster():
    parts = partition_units(_roster(240), 10, "d")
    assert {u.key for p in parts for u in p} == {f"u{i:03d}" for i in range(240)}


def test_partition_sizes_differ_by_at_most_one():
    parts = partition_units(_roster(241), 10, "d")
    sizes = sorted(len(p) for p in parts)
    assert sizes[-1] - sizes[0] <= 1
    assert len(parts) == 10


def test_k_equal_to_n_yields_one_unit_each():
    parts = partition_units(_roster(7), 7, "d")
    assert [len(p) for p in parts] == [1] * 7


def test_the_same_digest_reproduces_the_same_split():
    a = partition_units(_roster(50), 5, "d")
    b = partition_units(_roster(50), 5, "d")
    assert [[u.key for u in p] for p in a] == [[u.key for u in p] for p in b]


def test_a_different_digest_gives_a_different_split():
    a = partition_units(_roster(50), 5, "d")
    b = partition_units(_roster(50), 5, "other")
    assert [[u.key for u in p] for p in a] != [[u.key for u in p] for p in b]
```

Construct `Unit` however `tests/test_units.py` already does — **read the file first** and match its idiom rather than inventing one; `_roster` above stands for whatever helper it uses.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_units.py -k partition -v`
Expected: FAIL — `partition_units` is not defined.

- [ ] **Step 3: Implement**

```python
def partition_units(roster: "UnitList", k: int, digest: str) -> list[list["Unit"]]:
    """Split the roster into `k` test partitions, each unit in exactly one.

    Drawn from the design digest rather than `parameters_hash`: editing an
    unrelated parameter must not redraw every fold boundary (reference.md
    § What auto-derives from). Sizes differ by at most one, so no fold is
    systematically smaller than its neighbours.
    """
    units = list(roster)
    rng = random.Random(_seed_from(digest))
    shuffled = list(units)
    rng.shuffle(shuffled)
    return [shuffled[i::k] for i in range(k)]


def _seed_from(digest: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{digest}|folds".encode()).digest()[:4], "big")
```

`shuffled[i::k]` is the stride assignment: it gives sizes differing by at most one for free, and needs no balancing pass that could be subtly wrong.

Add `import hashlib` and `import random` at the top if absent.

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_units.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/units.py tests/test_units.py
git commit -m "Split a roster into fold partitions from the design digest"
```

---

### Task 2: `fold` accepted, and its two refusals

**Files:**
- Modify: `src/publishable/replication.py`
- Test: `tests/test_replication.py`

**Interfaces:**
- Consumes: `RepeatLevel(kind, members)`, `RepeatMember(label, seed)`, `MAX_LEVELS = 2`, `_seed_for(digest, index)`, `SUPPORTED_KINDS`, `LABEL_JOIN` — all exist.
- Produces:
  - `resolve_repeats(config: dict[str, Any], digest: str, unit_count: int | None = None) -> list[RepeatLevel]` — a **new third parameter**, defaulted so existing callers keep working.
  - Fold member labels `fold01`, `fold02`, … positional, exactly like `batch`.

`fold` takes `k` — an integer ≥ 2 or the literal `all` — plus `stratify_by`, which this build refuses. `reference.md` § Repeat kinds argues `all` rather than a hard-coded count: `k: 240` works arithmetically and silently stops meaning leave-one-out the moment the cohort gains a unit.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_fold_level_resolves_to_k_members():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 5}]), "d", unit_count=240)
    assert levels[0].kind == "fold"
    assert [m.label for m in levels[0].members] == [
        "fold01", "fold02", "fold03", "fold04", "fold05"
    ]


def test_k_all_resolves_against_the_roster():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": "all"}]), "d", unit_count=7)
    assert levels[0].n == 7


def test_k_larger_than_the_roster_is_refused():
    with pytest.raises(ContractError) as exc:
        resolve_repeats(cfg([{"kind": "fold", "k": 300}]), "d", unit_count=240)
    assert exc.value.code == "E-REPL-FOLD-K-TOO-LARGE"


def test_k_below_two_is_refused():
    with pytest.raises(ContractError) as exc:
        resolve_repeats(cfg([{"kind": "fold", "k": 1}]), "d", unit_count=240)
    assert exc.value.code == "E-REPL-FOLD-K"


def test_stratify_by_is_refused():
    with pytest.raises(ContractError) as exc:
        resolve_repeats(cfg([{"kind": "fold", "k": 5, "stratify_by": "site"}]), "d",
                        unit_count=240)
    assert exc.value.code == "E-REPL-FOLD-STRATIFY-UNSUPPORTED"


def test_fold_outside_seed_composes_labels_outer_to_inner():
    levels = resolve_repeats(
        cfg([{"kind": "fold", "k": 2}, {"kind": "seed", "n": 2}]), "d", unit_count=10)
    labels = [lf.label for lf in cross_levels(levels)]
    assert labels[0].startswith("fold01" + LABEL_JOIN)
    assert len(labels) == 4
```

`cfg(...)` stands for whatever helper `tests/test_replication.py` already uses to wrap a repeats list in a `replication` block — **read the file and reuse it.**

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_replication.py -k fold -v`
Expected: FAIL — `fold` currently raises `E-REPL-FOLD-UNSUPPORTED`.

- [ ] **Step 3: Implement**

Add `"fold"` to `SUPPORTED_KINDS`, delete the `E-REPL-FOLD-UNSUPPORTED` raise, and add a resolver for `k`:

```python
def _fold_k(level: dict[str, Any], unit_count: int | None) -> int:
    """`k` is an integer >= 2, or `all` for leave-one-out.

    `all` needs the roster, because "as many folds as there are things to leave
    out" is a fact about the cohort rather than the config — which is the whole
    reason reference.md § Repeat kinds prefers it to a hard-coded count.
    """
    if level.get("stratify_by") is not None:
        raise ContractError(
            "`fold.stratify_by` is specified but not implemented in this build; "
            "stratified partitioning is a second partitioning rule with its own "
            "cross-field checks, and will be honored in a later slice",
            code="E-REPL-FOLD-STRATIFY-UNSUPPORTED",
        )
    k = level.get("k")
    if k == "all":
        if unit_count is None:
            raise ContractError(
                "`{kind: fold, k: all}` needs the resolved roster to know how many "
                "folds to draw, and none was supplied",
                code="E-REPL-FOLD-K",
            )
        k = unit_count
    if not isinstance(k, int) or isinstance(k, bool) or k < 2:
        raise ContractError(
            f"`{{kind: fold, k: {k!r}}}` is not a fold count; `k` is an integer >= 2, "
            "or `all` for leave-one-out",
            code="E-REPL-FOLD-K",
        )
    if unit_count is not None and k > unit_count:
        raise ContractError(
            f"`{{kind: fold, k: {k}}}` over {unit_count} resolved units would leave a "
            "fold with nothing to test; a fold with no units is a declaration error, "
            "not a small fold",
            code="E-REPL-FOLD-K-TOO-LARGE",
        )
    return k
```

and in `_seed_members`, label fold members positionally:

```python
    if kind in ("batch", "fold"):
        prefix = kind
        return tuple(
            RepeatMember(label=f"{prefix}{i + 1:02d}", seed=s) for i, s in enumerate(seeds)
        )
```

In `resolve_repeats`, take `unit_count: int | None = None`, and for a `fold` level use `_fold_k(level, unit_count)` as its member count instead of `n`.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -v && uv run ruff check . && uv run mypy`
Expected: pass. Existing tests asserting `E-REPL-FOLD-UNSUPPORTED` must be updated to the new truth — a `fold` now resolves. Grep the whole tree for `E-REPL-FOLD-UNSUPPORTED` afterwards; it must be gone from `src/`, `tests/`, and the four documents.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/replication.py tests/test_replication.py
git commit -m "Resolve a fold level, and refuse stratify_by and an oversized k"
```

---

### Task 3: `fold_members`, the map everything downstream keys on

**Files:**
- Modify: `src/publishable/replication.py`
- Test: `tests/test_replication.py`

**Interfaces:**
- Consumes: `RepeatLevel`, `partition_units` from Task 1.
- Produces: `fold_members_for(levels: list[RepeatLevel], partitions: list[list["Unit"]]) -> dict[str, frozenset[str]] | None`

This is the one object the three changed rules share. It maps a **fold member label** to the **unit keys** in that fold's test partition, and is `None` when no fold level is declared — which is what makes every no-fold path identical to today's.

- [ ] **Step 1: Write the failing tests**

```python
def test_no_fold_level_yields_none():
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "d")
    assert fold_members_for(levels, []) is None


def test_a_fold_level_maps_each_label_to_its_partition():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 2}]), "d", unit_count=4)
    parts = [[_u("a"), _u("b")], [_u("c"), _u("d")]]
    assert fold_members_for(levels, parts) == {
        "fold01": frozenset({"a", "b"}),
        "fold02": frozenset({"c", "d"}),
    }


def test_the_map_covers_every_unit_exactly_once():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 3}]), "d", unit_count=9)
    parts = [[_u(f"u{i}") for i in grp] for grp in ([0, 1, 2], [3, 4, 5], [6, 7, 8])]
    members = fold_members_for(levels, parts)
    allk = [k for s in members.values() for k in s]
    assert len(allk) == 9 and len(set(allk)) == 9
```

`_u(key)` stands for whatever the file already uses to build a `Unit`; read and reuse.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_replication.py -k fold_members -v`

- [ ] **Step 3: Implement**

```python
def fold_members_for(
    levels: list[RepeatLevel], partitions: list[list["Unit"]]
) -> dict[str, frozenset[str]] | None:
    """Fold label -> the unit keys in that fold's test partition, or None.

    `None` when no `fold` level is declared, which is what keeps every
    downstream rule — the collapse, attrition, and the failure fraction —
    byte-for-byte identical to a run without folds.
    """
    fold = next((lv for lv in levels if lv.kind == "fold"), None)
    if fold is None:
        return None
    return {
        m.label: frozenset(u.key for u in part)
        for m, part in zip(fold.members, partitions, strict=True)
    }
```

`strict=True` matters: a partition list of the wrong length is a core bug, and zipping silently short would drop a fold's units into nobody's membership set.

- [ ] **Step 4: Run and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/replication.py tests/test_replication.py
git commit -m "Map each fold label to the units in its test partition"
```

---

### Task 4: `handed_to`, and the collapse

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `fold_members: dict[str, frozenset[str]] | None`; `ExecutionResult` with `.execution.repeat_label`, `.recorded`, `.rows`.
- Produces:
  - `handed_to(unit_key: str, labels: list[str], fold_members: dict[str, frozenset[str]] | None) -> list[str]`
  - `collapse_repeats(results, step_name: str, condition_index: int, fold_members=None)` — a **new fourth parameter**, defaulted.

**This is the hardest code in the slice.** `reference.md` § How a metric becomes a number: core collapses **inner-to-outer**, so `10 folds × 3 seeds` averages the seeds within each fold *before* combining folds, rather than flattening thirty numbers that are not exchangeable.

Averaging across folds would divide each unit's single observation by one and look correct. Concatenating across seeds would enter a unit three times and inflate `n` with no error surfacing. **Both failures produce plausible numbers**, which is why the tests assert the *shape* of the collapsed table — row count and observations per unit — and not only its values.

- [ ] **Step 1: Write the failing tests for `handed_to`**

```python
def test_without_folds_a_unit_is_handed_to_every_repeat():
    assert handed_to("u1", ["seed01", "seed02"], None) == ["seed01", "seed02"]


def test_with_folds_a_unit_is_handed_only_to_its_own_fold():
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    assert handed_to("u1", ["fold01", "fold02"], members) == ["fold01"]


def test_under_fold_times_seed_a_unit_is_handed_to_every_seed_of_its_fold():
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    labels = ["fold01_seed01", "fold01_seed02", "fold02_seed01", "fold02_seed02"]
    assert handed_to("u1", labels, members) == ["fold01_seed01", "fold01_seed02"]
```

- [ ] **Step 2: Run to verify they fail, then implement**

Run: `uv run pytest tests/test_stats.py -k handed_to -v`

```python
def handed_to(
    unit_key: str, labels: list[str], fold_members: dict[str, frozenset[str]] | None
) -> list[str]:
    """The repeat labels this unit was actually given.

    Without a fold, every repeat — the S2 rule. With one, only the labels whose
    fold component holds this unit: `reference.md` § The per-unit tables is
    explicit that intersecting over *every* repeat "would report `completed: 0`
    for any design containing a fold, because no unit is ever in more than one
    of them."
    """
    if fold_members is None:
        return list(labels)
    mine = {f for f, keys in fold_members.items() if unit_key in keys}
    return [lb for lb in labels if set(lb.split(LABEL_JOIN)) & mine]
```

Import `LABEL_JOIN` from `replication`. **This is cycle-free and verified:** `replication.py` imports only `hashlib`, `itertools`, `random`, `dataclasses`, and `typing` — no project module at all — so nothing can come back around to `stats`. It also keeps `stats.py` pure, since `replication` is not `config`, `artifacts`, `runner`, or `cli`.

- [ ] **Step 3: Write the failing collapse tests**

```python
def test_seeds_average_and_the_table_has_one_row_per_unit():
    results = [
        _repeat_result("analyze", "seed01", 0, {"u1": {"score": 1.0}, "u2": {"score": 3.0}}),
        _repeat_result("analyze", "seed02", 0, {"u1": {"score": 3.0}, "u2": {"score": 5.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, None)
    assert set(table) == {"u1", "u2"}
    assert table["u1"]["score"] == 2.0
    assert table["u2"]["score"] == 4.0


def test_folds_concatenate_rather_than_average():
    """Each unit is tested once per fold sweep, so the collapsed table is the
    union of the partitions — not an average that would divide by one."""
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {"score": 1.0}}),
        _repeat_result("analyze", "fold02", 0, {"u2": {"score": 5.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, members)
    assert set(table) == {"u1", "u2"}        # both units present — the S2 rule dropped both
    assert table["u1"]["score"] == 1.0
    assert table["u2"]["score"] == 5.0


def test_fold_times_seed_averages_seeds_within_a_fold_then_concatenates():
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {"score": 1.0}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {"score": 3.0}}),
        _repeat_result("analyze", "fold02_seed01", 0, {"u2": {"score": 4.0}}),
        _repeat_result("analyze", "fold02_seed02", 0, {"u2": {"score": 6.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, members)
    assert set(table) == {"u1", "u2"}
    assert table["u1"]["score"] == 2.0       # averaged WITHIN fold01, not concatenated
    assert table["u2"]["score"] == 5.0


def test_a_unit_missing_from_one_seed_of_its_fold_is_dropped():
    """The intersection still applies — within the repeats the unit was handed."""
    members = {"fold01": frozenset({"u1", "u2"})}
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {"score": 1.0},
                                                        "u2": {"score": 2.0}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {"score": 3.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, members)
    assert set(table) == {"u1"}
```

`_repeat_result(step, repeat_label, condition_index, rows_by_unit)` stands for whatever `tests/test_stats.py` already uses to build an `ExecutionResult`. **Read the file and reuse it**; if no such helper exists, write one and say so in your report, since Tasks 5 and 6 will reuse it.

- [ ] **Step 4: Implement the collapse**

Replace the "recorded in *every* repeat-scoped execution" intersection with one scoped to the repeats the unit was handed, and average only within a fold:

```python
    labels = [r.execution.repeat_label or "" for r in recording]
    by_label = {r.execution.repeat_label or "": r for r in recording}
    candidates = set().union(*(r.recorded for r in recording)) if recording else set()

    gathered: dict[str, dict[str, list[float]]] = {}
    for key in candidates:
        mine = handed_to(key, labels, fold_members)
        if not mine or any(key not in by_label[lb].recorded for lb in mine):
            continue          # the intersection, scoped to what this unit was handed
        for lb in mine:
            for row in by_label[lb].rows:
                if row["unit"] != key:
                    continue
                for column, value in row.items():
                    ...       # same numeric filtering the current body already does
```

Keep the existing non-numeric filtering exactly as it is — a string or a `bool` is dropped from that column rather than averaged. The mean is then taken over `mine`, which under `fold` alone is a single label (so the value passes through unchanged, which is the concatenation) and under `fold × seed` is that fold's seeds (so they average).

**Read the current body before rewriting it.** The change is which executions a unit's values come from, not how the values themselves are handled.

- [ ] **Step 5: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py tests/test_stats.py
git commit -m "Concatenate across folds, average seeds within one"
```

---

### Task 5: `attrition` over the repeats a unit was handed

**Files:**
- Modify: `src/publishable/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `handed_to` from Task 4.
- Produces: `attrition(results, roster, step_name: str, condition_index: int, fold_members=None) -> dict[str, int]` — a **new fifth parameter**, defaulted.

`reference.md` § The per-unit tables gives the rule as three rows, and the qualifier is load-bearing:

| Repeat structure | A unit is handed to | It counts as completed when |
|---|---|---|
| `seed` or `batch` levels only | Every repeat | It completed in all of them |
| A `fold` level | Exactly one fold per sweep | It completed in that fold |
| `fold` × `seed` | Every seed of its own fold | It completed in all of that fold's seeds |

**`resolved` counts what the execution was handed, not the cohort.** Under `{k: 10}` over 240 units, a fold recording all 24 of its partition is `{resolved: 24, completed: 24, failed: 0}` — not 216 failures against a cohort it never saw.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_fold_reports_its_partition_as_resolved_not_the_cohort():
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {}, "u2": {}}),
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    counts = attrition(results, _roster4(), "analyze", 0, members)
    assert counts == {"resolved": 4, "completed": 4, "ineligible": 0, "failed": 0}


def test_the_third_row_a_unit_missing_from_one_seed_of_its_fold():
    """The case a rewrite that groups by fold but forgets to intersect WITHIN the
    group gets wrong, while the fold-alone case still passes."""
    members = {"fold01": frozenset({"u1", "u2"})}
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {}, "u2": {}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {}}),
    ]
    counts = attrition(results, _roster2(), "analyze", 0, members)
    assert counts["completed"] == 1
    assert counts["failed"] == 1


def test_without_folds_the_intersection_is_unchanged():
    results = [
        _repeat_result("analyze", "seed01", 0, {"u1": {}, "u2": {}}),
        _repeat_result("analyze", "seed02", 0, {"u1": {}}),
    ]
    counts = attrition(results, _roster2(), "analyze", 0, None)
    assert counts["completed"] == 1
    assert counts["failed"] == 1


def test_the_identity_reconciles_under_a_fold():
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {}}),
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    c = attrition(results, _roster4(), "analyze", 0, members)
    assert c["resolved"] == c["completed"] + c["ineligible"] + c["failed"]
```

`_roster2()`/`_roster4()` stand for whatever `tests/test_runner.py` already uses; read and reuse.

- [ ] **Step 2: Run to verify they fail, then implement**

Run: `uv run pytest tests/test_runner.py -k fold -v`

Replace the unconditional intersection with one scoped per unit, and count `resolved` as the union of what the executions were handed:

```python
    labels = [r.execution.repeat_label or "" for r in recording]
    by_label = {r.execution.repeat_label or "": r for r in recording}
    if fold_members is None:
        handed = keys                      # every unit, to every repeat — the S2 rule
    else:
        handed = {k for s in fold_members.values() for k in s} & keys
    completed, ineligible = set(), set()
    for key in handed:
        mine = handed_to(key, labels, fold_members)
        if not mine:
            continue
        if all(key in by_label[lb].recorded for lb in mine):
            completed.add(key)
        elif all(key in by_label[lb].skipped for lb in mine):
            ineligible.add(key)
    return {
        "resolved": len(handed),
        "completed": len(completed),
        "ineligible": len(ineligible),
        "failed": len(handed) - len(completed) - len(ineligible),
    }
```

**Update the docstring.** It currently states the intersection is across "every repeat-scoped execution", which after this task is the opposite of the truth — and this project has already shipped one stale docstring asserting a rule the code had stopped following.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/runner.py tests/test_runner.py
git commit -m "Count attrition over the repeats a unit was handed"
```

---

### Task 6: The failure fraction, which currently aborts every fold run

**Files:**
- Modify: `src/publishable/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `fold_members`.
- Produces: `_units_failed_anywhere(results, roster, fold_members=None) -> set[str]`; `execute_plan(..., fold_members=None)`.

**This is the slice's severest defect and it exists today.** `_units_failed_anywhere` computes `failed |= keys - (r.recorded | r.skipped)` where `keys` is the **entire roster**. Under `{k: 10}` over 240 units each execution is handed 24, so the other 216 are neither recorded nor skipped and count as failed — on the *first* execution. The generated config ships `max_failed_fraction: 0.2`, so the run crosses the threshold immediately, stops, and reports `failed`. **Every fold run would abort before its second execution.**

The union is right and stays: `reference.md` § The per-unit tables is explicit that the run-level fraction is a union across every recording execution, deliberately unlike `attrition`'s intersection. What changes is the **membership set it subtracts from** — the units an execution was handed, not every unit in the run.

- [ ] **Step 1: Write the failing test**

```python
def test_a_healthy_fold_run_does_not_trip_the_failure_fraction():
    """Before this fix, every unit outside a fold's partition counted as failed on
    that fold's execution, so a clean 10-fold run aborted on execution one."""
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {}, "u2": {}}),
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    assert _units_failed_anywhere(results, _roster4(), members) == set()


def test_a_genuinely_failing_fold_still_counts():
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {}}),      # u2 never settled
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    assert _units_failed_anywhere(results, _roster4(), members) == {"u2"}


def test_without_folds_the_union_is_unchanged():
    results = [
        _repeat_result("analyze", "seed01", 0, {"u1": {}}),
        _repeat_result("analyze", "seed02", 0, {"u1": {}, "u2": {}}),
    ]
    assert _units_failed_anywhere(results, _roster2(), None) == {"u2"}
```

- [ ] **Step 2: Run to verify the first fails**

Run: `uv run pytest tests/test_runner.py -k failure_fraction or failed_anywhere -v`
Expected: the first test FAILS, returning all four keys. That failure *is* the bug this task fixes — confirm you see it before changing anything, and say so in your report.

- [ ] **Step 3: Implement**

```python
    for r in results:
        if r.execution.scope != "repeat" or r.execution.step_name not in recording_steps:
            continue
        handed = _handed_keys(r.execution.repeat_label or "", keys, fold_members)
        failed |= handed - (r.recorded | r.skipped)
```

with:

```python
def _handed_keys(
    repeat_label: str, keys: set[str], fold_members: dict[str, frozenset[str]] | None
) -> set[str]:
    """The units an execution with this repeat label was actually given.

    Subtracting from the whole roster instead is what made every fold run abort:
    the k−1 partitions this execution never saw are neither recorded nor skipped,
    and would each count as a failure.
    """
    if fold_members is None:
        return keys
    parts = set(repeat_label.split(LABEL_JOIN))
    mine = [ks for f, ks in fold_members.items() if f in parts]
    return (set().union(*mine) & keys) if mine else keys
```

**It takes the label, not an `ExecutionResult`, on purpose:** Task 7 needs the same rule while planning executions, where no result exists yet. A version keyed on `ExecutionResult` would force Task 7 to fabricate one.

Then thread `fold_members` through `execute_plan` to this call.

- [ ] **Step 4: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/runner.py tests/test_runner.py
git commit -m "Measure the failure fraction against the partition, not the roster"
```

---

### Task 7: `io.units` is the partition, and raises where a fold has none

**Files:**
- Modify: `src/publishable/runner.py`, `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`, `tests/test_runner.py`

**Interfaces:**
- Consumes: `UnitList(units, train=None)`; `partition_units`; `fold_members`.
- Produces: no new public names. `StepIO` gains no parameter — the runner hands it a `UnitList` that is already the partition, or `None`.

**The rule, from `reference.md` § A `fold` repeat puts the units out of reach of the wider scopes:** when any `fold` repeat is declared, `io.units` **and** `io.units.train` raise at `"run"` and `"condition"` scope. A `condition`-scoped step fitting a model there would fit on the units later folds test on, and every fold's metric would come back in-sample. This is an effect check — core owns `io` and declines to hand over a list that could only be the wrong one.

`io.units.train` is **the same kind of sequence** as `io.units`: iteration, `len`, integer indexing. There is no `io.units.train.train` — `reference.md` § The unit list is three operations says a partition of a partition is not something the declarations describe.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_repeat_step_sees_only_its_folds_test_partition(tmp_path):
    io = make_io(tmp_path, scope="repeat",
                 units=UnitList([_u("u1")], train=UnitList([_u("u2"), _u("u3")])))
    assert [u.key for u in io.units] == ["u1"]
    assert [u.key for u in io.units.train] == ["u2", "u3"]


def test_units_raises_at_condition_scope_under_a_fold(tmp_path):
    io = make_io(tmp_path, scope="condition", units=None)
    with pytest.raises(ContractError) as exc:
        io.units
    assert exc.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_train_raises_at_run_scope_under_a_fold(tmp_path):
    io = make_io(tmp_path, scope="run", units=None)
    with pytest.raises(ContractError) as exc:
        io.units.train
    assert exc.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_there_is_no_train_of_a_train(tmp_path):
    io = make_io(tmp_path, scope="repeat",
                 units=UnitList([_u("u1")], train=UnitList([_u("u2")])))
    with pytest.raises(ContractError):
        io.units.train.train
```

`make_io` and `_u` stand for the helpers `tests/test_artifacts.py` already uses — read and reuse.

- [ ] **Step 2: Run to verify they fail, then implement**

In `runner.execute_plan`, when `fold_members` is not `None`, build each repeat-scoped execution's `UnitList` from its fold's partition with the complement as `train`, and pass `units=None` for `run`- and `condition`-scoped executions:

```python
        if fold_members is None or units is None:
            step_units = units
        elif execution.scope != "repeat":
            step_units = None      # no fold exists yet at these scopes
        else:
            handed = _handed_keys(
                execution.repeat_label or "", {u.key for u in units}, fold_members
            )
            step_units = UnitList(
                [u for u in units if u.key in handed],
                train=UnitList([u for u in units if u.key not in handed]),
            )
```

`_handed_keys` is Task 6's helper, which takes the **repeat label** rather than an `ExecutionResult` precisely so it can be reused here, where the execution has not run yet and no result exists.

The existing `io.units` raise already carries `E-STEP-UNITS-UNAVAILABLE`; its message says "needs a `data.units` declaration", which is wrong for this case. **Give the fold case its own message** naming the fold and pointing at repeat scope, while keeping the same code — it is the same fault (no such list exists here), and a second code for one fault is churn.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/runner.py src/publishable/artifacts.py tests/
git commit -m "Hand each fold execution its own test partition"
```

---

### Task 8: `validate` knows the roster size, and refuses in findings

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `resolve_repeats(config, digest, unit_count=None)`; `resolve_units(units_decl, path)`; `REPL_DECLARATION_CODES`.
- Produces: `E-REPL-FOLD-STRATIFY-UNSUPPORTED`, `E-REPL-FOLD-K-TOO-LARGE`, `E-REPL-FOLD-K` as **findings**.

`validate` resolves the roster in `_check_units` but does not share it with `_check_replication`, which calls `resolve_repeats(doc, "validate")` with no count. Without the count, `k: all` and the oversized-`k` check cannot be answered at validate time — and `reference.md` § Where units come from is explicit that resolution runs at validate precisely so unit checks are real rather than deferred.

Resolve the roster **once** and pass its length to `_check_replication`. Do not resolve twice.

- [ ] **Step 1: Write the failing tests**

```python
def test_stratify_by_is_a_finding_not_a_traceback(write_config):
    assert "E-REPL-FOLD-STRATIFY-UNSUPPORTED" in codes(write_config(
        {"replication": {"repeats": [{"kind": "fold", "k": 3, "stratify_by": "site"}]}}))


def test_an_oversized_k_is_refused_against_the_real_roster(write_config):
    assert "E-REPL-FOLD-K-TOO-LARGE" in codes(write_config(
        {"replication": {"repeats": [{"kind": "fold", "k": 9999}]}}))


def test_a_valid_fold_validates_clean(write_config):
    found = codes(write_config({"replication": {"repeats": [{"kind": "fold", "k": 2}]}}))
    assert not [c for c in found if c.startswith("E-REPL")]
```

- [ ] **Step 2: Run to verify they fail, then implement**

Add the three codes to `REPL_DECLARATION_CODES` so they are collected rather than raised, and thread the count:

```python
    count = len(roster) if roster is not None else None
    try:
        resolve_repeats(doc, "validate", unit_count=count)
    except ContractError as exc:
        ...
```

If the roster failed to resolve, `count` is `None` and `k: all` reports `E-REPL-FOLD-K` — which is honest: the fold count genuinely cannot be known, and the roster's own finding is already reported beside it.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Check a fold declaration against the resolved roster"
```

---

### Task 9: `partitions` in `sweep.yaml`, CLI wiring, and the acceptance test

**Files:**
- Modify: `src/publishable/sweep.py`, `src/publishable/cli.py`
- Test: `tests/test_sweep.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `sweep_document(..., partitions=None)` — a new trailing optional parameter.

`reference.md` § `sweep.yaml` — the resolved plan says a `fold` level adds `partitions`: the unit keys in each fold's train and test side. `sweep.py` stays **pure** — it composes the payload; `cli.py` writes the file, as it already does.

This task also proves the slice is reachable from `main(["run", ...])`. Every earlier task is testable in isolation, and this project has twice shipped a subsystem that was green in unit tests and unreachable from the CLI. **Report every `src/` change you need here — each one is a piece an earlier task left inert.**

- [ ] **Step 1: Write the failing `sweep_document` test**

```python
def test_a_fold_level_records_its_partitions():
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 2}]), "d", unit_count=4)
    parts = [[_u("a"), _u("b")], [_u("c"), _u("d")]]
    doc = sweep_document(expand({}), levels, cross_levels(levels), "sha256:x",
                         "as_declared", [], None, partitions=parts)
    assert doc["partitions"] == [
        {"fold": "fold01", "test": ["a", "b"], "train": ["c", "d"]},
        {"fold": "fold02", "test": ["c", "d"], "train": ["a", "b"]},
    ]


def test_no_fold_level_records_no_partitions_key():
    """Absent, not empty — an empty list would read as `no folds were drawn`."""
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 2}]), "d")
    doc = sweep_document(expand({}), levels, cross_levels(levels), "sha256:x",
                         "as_declared", [], None)
    assert "partitions" not in doc
```

- [ ] **Step 2: Implement, then write the acceptance test**

```python
def test_a_five_fold_run_end_to_end(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys,
                        replication={"repeats": [{"kind": "fold", "k": 5}]})
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    assert [p["fold"] for p in sweep["partitions"]] == [
        "fold01", "fold02", "fold03", "fold04", "fold05"]
    tested = [k for p in sweep["partitions"] for k in p["test"]]
    assert len(tested) == len(set(tested))          # each unit tested exactly once
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "completed"             # the abort this slice fixes
```

`run_a_project` is the end-to-end driver already in `tests/test_cli.py`; reuse it, do not add a second.

- [ ] **Step 3: Verify by hand, then commit**

Run the whole suite, then scaffold a project by hand, run it with `{kind: fold, k: 5}` over a real roster, and paste `sweep.yaml`, the directory tree, and `run.yaml`'s `n` block into your report. A test can share a bug with the code it tests; a tree you read cannot. Confirm the condition's `n` returns to the full roster by concatenation.

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/sweep.py src/publishable/cli.py tests/
git commit -m "Run a five-fold design end to end"
```

---

## Self-Review

**Spec coverage.** Partitioning → Task 1. `fold` accepted, `k`/`all`, both refusals → Task 2. The shared `fold_members` map → Task 3. The collapse → Task 4. `attrition` → Task 5. The failure-fraction abort → Task 6. `io.units`/`.train` and the scope raise → Task 7. `validate` → Task 8. `partitions`, wiring, acceptance → Task 9. `E-REPL-FOLD-UNSUPPORTED` retires in Task 2. No spec section is unassigned.

**Placeholders.** Every code step carries code and every test step carries tests. Six tasks name an existing helper (`_roster`, `_u`, `cfg`, `_repeat_result`, `make_io`, `run_a_project`) and each says to read the file and match its idiom — a deliberate instruction, since inventing a second idiom is the defect.

**Type consistency.** `fold_members: dict[str, frozenset[str]] | None` is the same type in Tasks 3–7. `handed_to(unit_key, labels, fold_members) -> list[str]` is defined in Task 4 and used in Task 5 with the same signature. `partition_units(roster, k, digest) -> list[list[Unit]]` from Task 1 feeds `fold_members_for(levels, partitions)` in Task 3 and `sweep_document(..., partitions=...)` in Task 9, all taking the same `list[list[Unit]]`. Every new parameter is added **last and defaulted**, so no existing call site breaks.

**Three assumptions verified against the codebase before writing.** `UnitList.__init__` already accepts `train` and nothing currently passes it, so Task 7 wires an existing slot rather than adding one. `resolve_repeats` has exactly two call sites (`cli.py:157`, `validate.py:481`), which is why the new `unit_count` parameter is cheap. `validate` resolves the roster in `_check_units` but never shares it with `_check_replication` — that gap is Task 8, and it is the reason `k: all` cannot be checked today.

**The risk this plan carries.** Task 4 is the hardest code in the slice, and both of its failure modes produce plausible numbers: averaging across folds divides a single observation by one, and concatenating across seeds inflates `n` silently. Its tests therefore assert the table's shape — which units are present, and how many observations each contributes — rather than only its values. If that task's review is thin, the whole-branch review should re-derive the collapse by hand against a fixture.
