# H3a Weighted and Technical Units Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `data.units.weight_by` and `data.units.measurements` execute — a weight changes the interval it is declared for, and a technical replicate is collapsed before any step sees it — retiring `E-DATA-WEIGHT-UNSUPPORTED` and `E-DATA-MEASUREMENTS-UNSUPPORTED`.

**Architecture:** Two halves that were planned as independent. They share one thing in the landed code — `units.usable_weight` reads `units.is_measurement_numeric`, so the weight half depends on the measurements half's predicate, deliberately and one-way. And the whole-branch review found they share a *failure mode* the "share nothing" framing hid: a weight column is collapsed by `measurements` like any other attribute, so no task owned the combination. `measurements` adds one collapse function in `units.py` called by both arrival paths (the input table, and a step's `io.record(..., measurement=)`), collapsing before `n` is counted. `weight_by` adds three validate-time checks and a weighted interval construction in `stats.py` whose degrees of freedom come from Kish's effective sample size. Neither touches `partition_units`, which is this slice's claim to being first in H3.

**Tech Stack:** Python 3.12+, `uv`, pytest, ruff, mypy. No new dependencies.

## Global Constraints

Every task's requirements implicitly include this section.

- **The documents lead the code.** `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md` and `docs/reference.md` are normative. Where code cannot follow a document, **the document changes first** — and where the code is what is wrong, record the gap in `docs/superpowers/spec-defects.md` rather than editing the document to describe code that does not exist. Editing a document to describe absent code is a defect this project has shipped, at three layers in one commit.
- **`validate` collects findings and never raises.** A wrongly-typed or absent field produces a finding, never a `TypeError` — and must not silently *skip* its check either. The silent skip is worse than the crash.
- **`parameter_spec` is the sole authority for `parameters.*`.** Nothing in this slice may become a second one.
- **Every check needs a test producing its identifier**, and — specific to this slice — **every declaration needs a second test proving its effect**. An identifier test alone is what would let a validated-but-inert declaration ship.
- **Mutation testing is not optional and is never reasoned about.** Apply the mutation, run the named test, confirm it FAILS, revert, confirm the test passes again. **Delete `__pycache__` between mutation and revert**: CPython validates a `.pyc` against source mtime truncated to *seconds* plus size, so a same-size edit inside one wall-clock second is invisible, and once cached a same-size same-second revert stays invisible permanently. **Verify a revert by behaviour, never by `git status`.**
- **The `-UNSUPPORTED` family is deliberately absent from the validate-time registry.** A retired one is recorded by editing § The one config file's `NOT BUILT` list — a **count in prose** ("Eleven declarations above are not yet built") that no mechanical check catches. This slice takes it **eleven → nine**.
- **Every new identifier needs a row** in `reference.md` § Validation's `### Errors validate reports` (currently 65 `E-` rows) or § Warnings core reports (currently 18 `W-` rows).
- `units.py` must stay importable without the filesystem where it already is. `stats.py` is pure in the sense that matters — no filesystem, no `config`/`artifacts`/`cli` — but it now imports `publishable.units` for the shared `usable_weight` predicate, which is acyclic since `units` imports only `publishable.errors`. Do not restate it as "imports only errors and replication".
- `condition_dir_name` is the single source of truth for artifact paths. Do not touch it.
- `×` not `x` for multiplication, including inside fenced blocks. **Hyphen, never an en dash**, in anything becoming a filename or an anchor.
- Cite another file by section — `reference.md` § "Weighted samples" — **never by line number**.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run mypy`. **Do not run `ruff format .`** — it reformats 36 files at HEAD, pre-existing house style, out of scope.
- **No fixture named in this plan exists yet.** `write_index`, `step_io`, `step_io_undeclared` and `read_parquet` are all shorthand for setup you must write; the tests in `tests/test_artifacts.py` build a `StepIO` directly as `StepIO(step_dir=..., input_dir=..., run_dir=..., units=roster)`. Follow the surrounding file's existing pattern rather than introducing a fixture layer. **Verify every helper you call exists before calling it** — an invented API in a task brief has cost this project real rework.
- The worked example (`cohort-pilot`: 240 units, 228 complete, 12 failed; r = 0.581 / 0.607 / 0.412; delta 0.026, ci95 [−0.007, 0.059]; `repeat_spread` std 0.014; hashes `8e21`/`1a2b`/`3d8a`/`6b1f`) declares **neither** field. Nothing about it may move.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/units.py` | **Create** `collapse_measurements`; call it from `resolve_units` before the uniqueness check. `partition_units` is **untouched** |
| `src/publishable/stats.py` | **Create** `weighted_t_over_units` and `kish_effective_n`; the percentile path recomputes the weighted statistic per draw |
| `src/publishable/artifacts.py` | `io.record` gains `measurement=`; the undeclared raise; `measurements.parquet` at finalize |
| `src/publishable/validate.py` | Four new checks; two refusals removed from the five-field loop; two truthiness holes closed |
| `src/publishable/envelope.py` | `data.units.measurements`' whole-leaf `dict` replaced by typed leaves |
| `src/publishable/runner.py` | `n` gains `effective` — **conditionally** |
| `docs/reference.md` | The `NOT BUILT` list eleven → nine; new registry rows; the whole-leaf passage |

---

## Task 1: The collapse function

**Files:**
- Modify: `src/publishable/units.py`
- Test: `tests/test_units.py`

**Interfaces:**
- Consumes: `Unit` (frozen, hashable by `key`, with `.attributes`), `UnitList`
- Produces: `collapse_measurements(units, by, collapse) -> tuple[list[Unit], list[int]]` — the collapsed units in first-seen order, and the per-unit measurement counts in the same order. Task 3 calls it; task 5 calls `rule_for`/`apply_rule` instead (see task 5).
- Produces: `COLLAPSE_RULES = ("mean", "median", "sum", "first", "mode")` and `NUMERIC_COLLAPSE_RULES = ("mean", "median", "sum")`, both read by task 2.

**The vocabulary is five rules in two groups**, from `reference.md` § What isn't a repeat: *"`collapse` is `mean`, `median`, or `sum` for numeric columns and `first` or `mode` for the rest — `first` meaning the earliest row in resolution order, and `mode` breaking a tie the same way, by whichever tied value appeared first."* Two documented guarantees ride on that sentence and each needs a test: `first` means resolution order (which is the order `collapse_measurements` appends within a group), and `mode` breaks ties by first appearance.

**One further rule from the same passage:** *"Attributes constant within a key collapse to that value with no rule needed."* Put that in `apply_rule`, **after** the rule-name validation so a bogus rule still raises over a single-member group — task 5 calls `apply_rule` directly with already-grouped values and gets the same behaviour for free.

`collapse` is either one rule applied to every column, or a mapping of column name to rule. A column absent from the mapping falls back to `first`, because a column the config did not name is one the design did not ask to average.

- [ ] **Step 1: Write the failing test**

```python
def test_rows_sharing_a_key_collapse_to_one_unit():
    units = [
        Unit(key="p1", paths=(), attributes={"read_id": "r1", "depth": 10, "site": "A"}),
        Unit(key="p1", paths=(), attributes={"read_id": "r2", "depth": 20, "site": "A"}),
        Unit(key="p2", paths=(), attributes={"read_id": "r3", "depth": 30, "site": "B"}),
    ]
    collapsed, counts = collapse_measurements(units, by="read_id", collapse="mean")
    assert [u.key for u in collapsed] == ["p1", "p2"]
    assert counts == [2, 1]
    assert collapsed[0].depth == 15.0        # mean of 10 and 20
    assert collapsed[0].site == "A"          # non-numeric, constant: carried
    assert "read_id" not in collapsed[0].attributes   # the measurement axis is consumed
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `uv run pytest tests/test_units.py::test_rows_sharing_a_key_collapse_to_one_unit -v`
Expected: FAIL, `ImportError` / `NameError` on `collapse_measurements`.

- [ ] **Step 3: Implement**

```python
COLLAPSE_RULES = ("mean", "median", "sum", "first", "mode")
NUMERIC_COLLAPSE_RULES = ("mean", "median", "sum")


def rule_for(column: str, collapse: Any) -> str:
    """One rule for every column, or a per-column map falling back to `first`.

    A column the config did not name is one the design did not ask to average,
    so the fallback carries the first value rather than guessing at a statistic.
    """
    if isinstance(collapse, Mapping):
        return str(collapse.get(column, "first"))
    return str(collapse)


def apply_rule(rule: str, values: list[Any]) -> Any:
    if rule == "first":
        return values[0]
    if rule == "mode":
        return Counter(values).most_common(1)[0][0]
    if rule == "mean":
        return sum(values) / len(values)
    raise ContractError(
        f"`data.units.measurements.collapse` names {rule!r}; expected one of "
        f"{', '.join(COLLAPSE_RULES)}",
        code="E-UNITS-COLLAPSE-RULE",
    )


def collapse_measurements(
    units: list[Unit], by: str, collapse: Any
) -> tuple[list[Unit], list[int]]:
    """Collapse rows sharing a `key` into one unit, in first-seen order.

    `reference.md` § What isn't a repeat: rows sharing a key are technical
    replicates, collapsed at resolution, before any step sees them — which is
    what keeps them out of `n`. The measurement axis `by` is consumed: it
    distinguished the rows and has no value once they are one unit.

    Returns the collapsed units and their measurement counts in the same order,
    because `technical_n` is `{min, max, median}` over exactly these counts and
    recomputing them from a second walk is how the two come to disagree.
    """
    groups: dict[str, list[Unit]] = {}
    for unit in units:
        groups.setdefault(unit.key, []).append(unit)
    collapsed: list[Unit] = []
    counts: list[int] = []
    for key, members in groups.items():
        names: list[str] = []
        for member in members:
            for name in member.attributes:
                if name != by and name not in names:
                    names.append(name)
        merged = {
            name: apply_rule(
                rule_for(name, collapse),
                [m.attributes[name] for m in members if name in m.attributes],
            )
            for name in names
        }
        paths = tuple(p for m in members for p in m.paths)
        collapsed.append(Unit(key=key, paths=paths, attributes=merged))
        counts.append(len(members))
    return collapsed, counts
```

Add `from collections import Counter` and `from collections.abc import Mapping` to the imports if absent.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `uv run pytest tests/test_units.py -v`

- [ ] **Step 5: Mutation-test**

Change `return values[0]` in the `first` branch to `return values[-1]`. Run the test — it must FAIL on `collapsed[0].site`. Revert, delete `__pycache__`, confirm it passes by behaviour.

Then a second mutation that matters more: make `counts` be recomputed as `[len(groups[u.key]) for u in collapsed]` in a separate walk instead of accumulated in the loop. This must NOT change behaviour today — note in your report that it does not, and that the docstring's reason is about future drift rather than a current bug, so the claim is honest.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/units.py tests/test_units.py
git commit -m "feat: collapse rows sharing a key into one unit"
```

---

## Task 2: Row 243 — the collapse rule fits the column

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: task 1's `COLLAPSE_RULES`; `validate`'s existing roster resolution, which returns `None` when `input_dir` is unreadable or the roster cannot resolve
- Produces: `E-DATA-MEASUREMENTS-INVALID` (shape) and `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` (row 243)

**Do not remove `E-DATA-MEASUREMENTS-UNSUPPORTED` in this task** — task 6 retires it, after both paths execute. A check that fires only behind a refusal is dead code, so write the tests to call the check directly as well as through `validate_config`.

`reference.md` § Validation row 243 is: *"Collapse rule fits the column — `measurements.collapse: mean` over `site`, which is a string — use `first` or `mode`, or a per-column map."* The type comes from the **resolved roster's actual attribute values**, which `validate` already resolves against a real table. When the roster does not resolve, the check is skipped — and that skip must be *reachable in a test with the roster resolvable*, so it does not become the silent-skip class.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_mean_collapse_over_a_string_column_is_refused(write_config):
    """Row 243. `mean` over `site` has no meaning; the row names the remedies."""
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["site", "read_id"],
        "measurements": {"by": "read_id", "collapse": "mean"},
    }}})
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" in codes(path)


def test_a_per_column_map_sparing_the_string_column_is_accepted(write_config):
    """The remedy the row names must actually work, or the check is a trap."""
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["site", "depth", "read_id"],
        "measurements": {"by": "read_id", "collapse": {"depth": "mean", "site": "first"}},
    }}})
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" not in codes(path)


def test_measurements_missing_by_is_refused(write_config):
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "measurements": {"collapse": "mean"},
    }}})
    assert "E-DATA-MEASUREMENTS-INVALID" in codes(path)


def test_an_empty_measurements_block_is_a_finding_not_a_default(write_config):
    """Decision 3. The truthiness gate that lets `{}` through today is a hole:
    un-refusing a declaration must not turn its empty form into a working default."""
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id", "measurements": {},
    }}})
    assert "E-DATA-MEASUREMENTS-INVALID" in codes(path)
```

- [ ] **Step 2: Run them and confirm each fails**

Run: `uv run pytest tests/test_validate.py -k measurements -v`
Expected: all four FAIL. **Read the failure text** — a test failing because `E-DATA-MEASUREMENTS-UNSUPPORTED` fired instead is failing for the wrong reason and tells you nothing yet.

- [ ] **Step 3: Implement `_check_measurements`**

**Import `COLLAPSE_RULES` and `NUMERIC_COLLAPSE_RULES` from `units.py`** — task 1 exports both. Do not restate either set here; two lists of what `mean` may be applied to is how the check and the collapse come to disagree.

```python
def _check_measurements(units: dict[str, Any], roster: UnitList | None, c: Collector) -> None:
    """`data.units.measurements` — shape, then the collapse rule against the column.

    The type comes from the resolved roster's own attribute values rather than
    from a declaration, because `attributes` declares names and not types.
    When the roster does not resolve, the type half is skipped and the shape
    half still runs: a config can be wrong about its shape without a directory.
    """
    decl = units.get("measurements")
    if decl is None:
        return
    if not isinstance(decl, dict) or not decl:
        c.error(
            "E-DATA-MEASUREMENTS-INVALID",
            "data.units.measurements",
            "is empty or is not a mapping; it needs `by` (the attribute distinguishing "
            "one measurement of a unit from another) and `collapse` (how rows sharing a "
            "key become one). An empty declaration changes no behavior, which is the "
            "failure the refusal it replaces existed to prevent",
        )
        return
    by = decl.get("by")
    if not isinstance(by, str) or not by:
        c.error(
            "E-DATA-MEASUREMENTS-INVALID",
            "data.units.measurements.by",
            "is missing or is not an attribute name; without it nothing distinguishes "
            "a second measurement of one unit from a resumed retry of the same one, "
            "and the two collapse in opposite directions",
        )
    collapse = decl.get("collapse")
    rules = collapse.values() if isinstance(collapse, dict) else [collapse]
    for rule in rules:
        if rule not in COLLAPSE_RULES:
            c.error(
                "E-DATA-MEASUREMENTS-INVALID",
                "data.units.measurements.collapse",
                f"names {rule!r}; expected one of {', '.join(COLLAPSE_RULES)}, or a "
                "mapping of column name to one of them",
            )
            return
    if roster is None:
        return
    for name in sorted({n for u in roster for n in u.attributes} - {by}):
        rule = collapse.get(name, "first") if isinstance(collapse, dict) else collapse
        if rule not in NUMERIC_COLLAPSE_RULES:
            continue
        offenders = [
            u.attributes[name]
            for u in roster
            if name in u.attributes and not isinstance(u.attributes[name], (int, float))
        ]
        if offenders:
            c.error(
                "E-DATA-MEASUREMENTS-COLLAPSE-TYPE",
                f"data.units.measurements.collapse.{name}",
                f"is {rule!r} over {name!r}, which holds {offenders[0]!r} — a "
                f"{type(offenders[0]).__name__}. Use `first` or `mode` for it, or a "
                "per-column map giving each column the rule that fits it",
            )
```

Call it from `_check_data`'s existing roster-resolving path, where the roster is already in hand.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `uv run pytest tests/test_validate.py -k measurements -v`

- [ ] **Step 5: Mutation-test**

Change `if rule not in NUMERIC_COLLAPSE_RULES: continue` to `if rule in NUMERIC_COLLAPSE_RULES: continue`. `test_a_mean_collapse_over_a_string_column_is_refused` must FAIL. Revert, delete `__pycache__`, verify by behaviour.

Then check the skip is not silent: temporarily make the roster unresolvable in the first test and confirm the *shape* findings still fire. Revert.

- [ ] **Step 6: Add the two registry rows and commit**

Both go in `reference.md` § Validation's `### Errors validate reports` table, in alphabetical position. Row count 65 → 67. Write each row's condition from the emit site, not from this plan.

```bash
git add src/publishable/validate.py tests/test_validate.py docs/reference.md
git commit -m "feat: check the collapse rule against the column it collapses"
```

---

## Task 3: The input path collapses before uniqueness

**Files:**
- Modify: `src/publishable/units.py`
- Test: `tests/test_units.py`

**Interfaces:**
- Consumes: task 1's `collapse_measurements`
- Produces: `resolve_units(units_decl, input_dir) -> tuple[UnitList, dict[str, float] | None, frozenset[str]]` — collapsing when `measurements` is declared, and returning `technical_n` **beside** the roster rather than on it

The uniqueness check currently raises `E-UNITS-KEY-DUPLICATE` on a repeated key. Under a `measurements` declaration a repeated key is **the point**, so the collapse must happen **before** that check — and the check must still fire for a config with no `measurements`.

- [ ] **Step 1: Write the failing tests**

```python
def test_duplicate_keys_collapse_when_measurements_is_declared(tmp_path):
    write_index(tmp_path, [
        {"patient_id": "p1", "read_id": "r1", "depth": "10"},
        {"patient_id": "p1", "read_id": "r2", "depth": "20"},
        {"patient_id": "p2", "read_id": "r3", "depth": "30"},
    ])
    roster, technical_n = resolve_units({
        "from": "index.csv", "key": "patient_id",
        "attributes": ["depth", "read_id"],
        "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
    }, tmp_path)
    assert len(roster) == 2
    assert technical_n == {"min": 1, "max": 2, "median": 1.5}


def test_the_unit_list_gains_no_new_operation(tmp_path):
    """The contract is exactly three operations plus `.train`
    (`reference.md` § The unit list is three operations). `technical_n` is a
    second return value precisely so it cannot become a fourth."""
    write_index(tmp_path, [{"patient_id": "p1"}, {"patient_id": "p2"}])
    roster, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, tmp_path)
    assert not hasattr(roster, "technical_n")


def test_duplicate_keys_still_raise_without_measurements(tmp_path):
    """The collapse is what makes a repeated key legal. Without the declaration
    it is the duplicate it always was."""
    write_index(tmp_path, [
        {"patient_id": "p1", "read_id": "r1"},
        {"patient_id": "p1", "read_id": "r2"},
    ])
    with pytest.raises(ContractError) as excinfo:
        resolve_units({"from": "index.csv", "key": "patient_id"}, tmp_path)
    assert excinfo.value.code == "E-UNITS-KEY-DUPLICATE"


def test_technical_n_is_absent_when_measurements_is_undeclared(tmp_path):
    """A design that never measures twice must read exactly as it did before."""
    write_index(tmp_path, [{"patient_id": "p1"}, {"patient_id": "p2"}])
    roster, technical_n = resolve_units({"from": "index.csv", "key": "patient_id"}, tmp_path)
    assert technical_n is None
```

- [ ] **Step 2: Run and confirm each fails**

Run: `uv run pytest tests/test_units.py -k "collapse or technical" -v`

- [ ] **Step 3: Implement**

### The contract task 3 must honour, or this slice ships a config that validates and then crashes

Task 2's check and `apply_rule` use **deliberately different** notions of "numeric", and that is correct — but it puts the burden here. Measured:

```
is_measurement_numeric("10")     -> True     # validate accepts a CSV-sourced numeric column
apply_rule("mean", ["10", "10"])     -> '10'     # constant shortcut fires; returns a STRING
apply_rule("mean", ["10", "20"])     -> TypeError    # bare, no E- code
```

`validate` says the column is fine for `mean`; `apply_rule` cannot actually compute it. Task 2's implementer deliberately did **not** rewire `apply_rule` to use the permissive predicate, and was right: that converts a silent wrong value into a crash without fixing anything.

**So task 3 must coerce numeric-looking strings to numbers before `apply_rule` ever sees them**, using `is_measurement_numeric` as the gate so the two answers cannot part. Two consequences to test, not just to implement:

- A CSV-sourced roster with `collapse: mean` over a numeric column must **collapse to a number**, not raise and not return a string. This is the headline test.
- A `TypeError` escaping `resolve_units` would escape **`validate`** too — it wraps the call in `except ContractError` only — breaking the hard invariant that `validate` collects findings and never raises. If any path can still raise a non-`ContractError`, convert it, and pin it.

Task 5 calls `apply_rule` directly on recorded rows and inherits the same obligation; `io.record` coerces its values, so check whether that already settles it there rather than assuming either way.

---

**Do not put `technical_n` on `UnitList`.** `reference.md` § The unit list is three operations, and `CLAUDE.md`'s invariant, both say `io.units` supports *exactly* three operations — iterate, `len`, index — plus `.train`. `io.units` **is** a `UnitList` handed to steps, so a public `technical_n` property widens a deliberately narrow surface, and a private one with a module-level accessor is the same thing wearing a disguise.

Instead, change the signature to **`resolve_units(units_decl, input_dir) -> tuple[UnitList, dict[str, float] | None, frozenset[str]]`** — the collapse produces two things, and the caller that needs both asks for both. There are exactly two call sites: `validate.py` (inside its `except ContractError` wrapper, which discards the second element) and `cli.py`'s phase-5 roster resolution, which carries it to the record. Update both, and the tests that call it directly.

Then, in `resolve_units`, between building `units` and the uniqueness loop:

```python
    technical_n = None
    measurements = units_decl.get("measurements")
    if measurements:
        units, counts = collapse_measurements(
            units, str(measurements["by"]), measurements.get("collapse", "first")
        )
        technical_n = {
            "min": min(counts),
            "max": max(counts),
            "median": statistics.median(counts),
        }
```

and pass `technical_n` into the returned `UnitList`.

`reference.md` § What isn't a repeat requires `{min, max, median}` rather than a scalar, and states the reason: real files are uneven, and a bare `technical_n: 3` is a claim of balance nobody checked. Put that reason in the code comment — it is why the shape is not a simplification waiting to happen.

- [ ] **Step 4: Run and confirm they pass**

- [ ] **Step 5: Mutation-test**

Move the collapse to *after* the uniqueness loop. `test_duplicate_keys_collapse_when_measurements_is_declared` must FAIL with `E-UNITS-KEY-DUPLICATE` — proving the ordering is load-bearing and not incidental. Revert, delete `__pycache__`, verify by behaviour.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: collapse technical replicates at resolution, before n is counted"
```

---

## Task 4: `io.record` gains `measurement=`

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

**Interfaces:**
- Produces: `record(self, unit_key: str, values: dict[str, Any], measurement: str | None = None)`; `E-STEP-MEASUREMENT-UNDECLARED`

`reference.md` § The importable surface already documents this three-argument form — the document leads and the code lags, so this closes a gap rather than adding a feature. The `measurement=` argument is the **only** discriminator between a resumed retry (first write wins, deduplicate) and a second measurement (collapse and average); `reference.md` § What isn't a repeat says nothing in the row itself distinguishes them.

- [ ] **Step 1: Write the failing tests**

```python
def test_two_measurements_of_one_unit_are_both_kept(step_io):
    step_io.record("p1", {"score": 10}, measurement="r1")
    step_io.record("p1", {"score": 20}, measurement="r2")
    assert len(step_io.measurement_rows()) == 2


def test_two_records_without_a_measurement_are_first_write_wins(step_io):
    """The retry path, unchanged. This is the behaviour `measurement=` exists
    to be distinguishable from."""
    step_io.record("p1", {"score": 10})
    step_io.record("p1", {"score": 20})
    assert step_io.rows() == [{"unit": "p1", "score": 10}]


def test_a_measurement_without_the_declaration_raises(step_io_undeclared):
    with pytest.raises(ContractError) as excinfo:
        step_io_undeclared.record("p1", {"score": 10}, measurement="r1")
    assert excinfo.value.code == "E-STEP-MEASUREMENT-UNDECLARED"
```

- [ ] **Step 2: Run and confirm each fails**

- [ ] **Step 3: Implement**

`StepIO.__init__` is keyword-only and is constructed in **exactly one place**, `runner.py`. Add **`measurements: dict[str, Any] | None = None`** — the declaration itself, not a boolean. Task 5 needs the collapse *rule* from it, so a `measurements_declared: bool` would have to be widened one task later; and one field carrying the declaration cannot disagree with itself the way a flag and a rule can.

Then:

```python
    def record(
        self, unit_key: str, values: dict[str, Any], measurement: str | None = None
    ) -> None:
        """Append one row, keyed by unit — or by `(unit, measurement)`.

        `measurement=` is the only thing separating a resumed retry from a second
        measurement of the same unit: without it a second row for one unit is a
        retry to be deduplicated under first-write-wins, with it a measurement to
        be averaged, and nothing in the row itself says which
        (`reference.md` § What isn't a repeat).
        """
        if measurement is not None and not self._measurements:
            raise ContractError(
                "`io.record` was given `measurement=` while `data.units.measurements` "
                "is undeclared, so there is no rule to collapse the rows under. Declare "
                "it with a `by` and a `collapse`, or drop the argument — without a rule "
                "a second row for one unit is a resumed retry, not a measurement",
                code="E-STEP-MEASUREMENT-UNDECLARED",
            )
```

Measurement rows accumulate in a separate `dict[tuple[str, str], dict]` keyed by `(unit_key, measurement)`, itself first-write-wins so a resumed *measurement* is still idempotent.

- [ ] **Step 4: Run and confirm they pass**

- [ ] **Step 5: Mutation-test**

Drop the `measurement is not None` guard so the raise fires unconditionally. `test_two_records_without_a_measurement_are_first_write_wins` must FAIL. Revert, delete `__pycache__`, verify by behaviour.

- [ ] **Step 6: Add the registry row and commit**

`E-STEP-MEASUREMENT-UNDECLARED` is raise-time, so it belongs in § Errors core raises — **not** the validate-time table. Confirm which by reading both sections' own scoping sentences before writing the row.

```bash
git commit -am "feat: io.record takes a measurement, and refuses one with no rule"
```

---

## Task 5: The step path collapses, and `measurements.parquet`

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

### The central obligation: a measured unit must count as *completed*

Measured with a control, at task 4's HEAD:

```
io.record("p1", {"score": 10}, measurement="r1")   # measured only
io.record("p2", {"score": 20})                     # plain, the control
io.recorded_keys  ->  ['p2']        # p1 is absent
```

`recorded_keys` is populated only by the plain branch, and `finalize` writes `units.parquet` only `if self._rows:` — while measurement rows live in a separate store. So today a unit that is **only** measured is counted neither `completed` nor `ineligible`, which by `runner`'s subtraction makes it **`failed`**. `reference.md` § The unit table is the inference base states the accounting directly: *"`completed` is how many distinct unit keys reached `io.record` in it — measurements of one unit collapse before they are counted"*.

So the collapse is not merely about producing a nice table: **it is what makes a measured unit exist at all** to the rest of core. Collapse `_measurement_rows` into `_rows` (and `_recorded_keys`) *before* `finalize`'s existing `units.parquet` block, so collapsed units flow through the path that already works rather than a parallel one.

**Pin it with the reconciliation, not just the file**: a run whose step only measures must report `completed` equal to the number of distinct units measured, `failed` zero, and `resolved == completed + ineligible + failed`.

### Also settle: a unit with both a plain row and measurement rows

Task 4 left this reachable in either order, and it is out of that task's scope but squarely in yours:

```
io.record("p1", {"score": 1})
io.record("p1", {"score": 2}, measurement="r1")   # no raise; unit now in both stores
```

Task 4's implementer was asked to argue which is right — refuse the mixture, or define which store wins — citing a document sentence if one settles it. **Read its report before deciding**, then implement your decision and pin it. Silently letting both stores contribute to one unit row is the one outcome to avoid: it is the retry-versus-measurement ambiguity the `measurement=` argument exists to remove, reappearing one layer down.

### First: thread `measurements` from the config into `StepIO`, or none of this is reachable

Task 4 added `StepIO(measurements=...)` and scoped itself to `artifacts.py`, so **`runner.py` never passes it**. Verified: `runner.py`'s single `StepIO(...)` construction has no `measurements` argument, so in a real run `io.record(..., measurement="r1")` raises `E-STEP-MEASUREMENT-UNDECLARED` **even when the config declares `measurements`** — the declaration is honoured at the input path and refused at the step path.

Thread `data.units.measurements` through to that constructor, and pin it with a test that runs a **real step** calling `io.record(..., measurement=)` under a declaring config and gets rows rather than a raise. A `StepIO` built directly in a test cannot catch this — that is exactly how it got missed.

**Interfaces:**
- Consumes: task 1's **`rule_for`, `apply_rule` and `coerce_for_rule`** — not `collapse_measurements` itself.

**Coercion applies here too.** Task 3 established that a numeric rule must never reach `apply_rule` with unconverted values. `io.record` coerces through `coerce_scalars`, so recorded values are already `int`/`float`/`str`/`bool`/`None` rather than CSV strings — **check whether that fully settles it rather than assuming either way**, and say which in your report. A recorded `str` column under `collapse: mean` is still reachable if a step records `"10"`.

**A correction to decision 4, found by this plan's type-consistency pass.** The spec says both paths call "one collapse function". They cannot call the *same* one as task 1 writes it: `collapse_measurements` takes `list[Unit]` and returns `Unit`s, while this path holds recorded rows keyed by `(unit_key, measurement)` and must produce rows. **What is genuinely shared is the rule application** — `rule_for` (per-column rule, falling back to `first`) and `apply_rule` (the rule itself). Both live in `units.py`; `rule_for` is already public because task 2's check calls it too, so you are its **third** caller. `apply_rule` is still private with one caller outside its module — make it public if you need it, in the same commit, and update every reference.

**Also expect `is_measurement_numeric` (or whatever task 3 names it) to be there by the time you arrive** — task 2 wrote a numeric predicate, and it is being moved beside `apply_rule` so that the validate-time "this column is numeric" and the runtime's cannot disagree. Use it; do not write a second one.

Decision 4's *reason* is untouched and is what matters: one place decides what `mean` means, so the retry path and the measurement path cannot come to disagree about identical-looking rows. Making `collapse_measurements` generic over mappings to satisfy the letter of "one function" would be worse — a signature shaped by a slogan rather than by either caller. Record this correction in your report; it amends the spec, and the spec is what a later reader will check the code against.

At finalize, measurement rows collapse into unit rows under the declared rule, then flow into `units.parquet` exactly as recorded rows do. The uncollapsed rows are written to `measurements.parquet` at `(unit, measurement)` — **present only when a step passed `measurement=`**, per decision 5: the artifact holds what the *run* measured, and input rows are the input's.

- [ ] **Step 1: Write the failing tests**

```python
def test_measurement_rows_collapse_into_one_unit_row(step_io):
    step_io.record("p1", {"score": 10}, measurement="r1")
    step_io.record("p1", {"score": 20}, measurement="r2")
    step_io.finalize()
    assert read_parquet(step_io.dir / "units.parquet") == [{"unit": "p1", "score": 15.0}]


def test_measurements_parquet_holds_the_uncollapsed_rows(step_io):
    step_io.record("p1", {"score": 10}, measurement="r1")
    step_io.record("p1", {"score": 20}, measurement="r2")
    step_io.finalize()
    rows = read_parquet(step_io.dir / "measurements.parquet")
    assert rows == [
        {"unit": "p1", "measurement": "r1", "score": 10},
        {"unit": "p1", "measurement": "r2", "score": 20},
    ]


def test_no_measurements_parquet_when_no_step_measured(step_io):
    """Decision 5: the file holds what the run measured, not what the input carried."""
    step_io.record("p1", {"score": 10})
    step_io.finalize()
    assert not (step_io.dir / "measurements.parquet").exists()
```

- [ ] **Step 2: Run and confirm each fails**

- [ ] **Step 3: Implement**, calling `rule_for` and `apply_rule` rather than re-deriving what a rule means.

- [ ] **Step 4: Run and confirm they pass**

- [ ] **Step 5: Mutation-test — the one that matters most in this slice**

Change the *step path* to average with a hand-written `sum(...)/len(...)` instead of calling `apply_rule`. Confirm the tests still pass (they will — the rule agrees today), then change task 1's `apply_rule` `mean` branch to a median and confirm **only the input path's test fails** while the step path's passes. That divergence is the defect decision 4 exists to prevent; having seen it, revert both, delete `__pycache__`, verify by behaviour, and record in your report that the shared call is what keeps them from drifting.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: collapse a step's measurements under the same rule the input takes"
```

---

## Task 6: Carry `technical_n`, and retire `E-DATA-MEASUREMENTS-UNSUPPORTED`

### Precondition: `measurements.by` is never checked against the declared attributes

**Close this before retiring the refusal.** Measured at task 3's HEAD, over a table with two rows per patient:

```
measurements: {by: nonexistent, collapse: {depth: mean}}
  -> units: [('p1', 15.0), ('p2', 35.0)]
  -> technical_n: {'min': 2, 'max': 2, 'median': 2.0}
```

A typo'd `by` silently averages rows that **nothing declared to be measurements of one unit**, and reports a `technical_n` claiming the collapse was intentional. Today `E-DATA-MEASUREMENTS-UNSUPPORTED` masks it — the config never gets that far. Retiring the refusal makes a wrong-answer path reachable, which is worse than the missing-diagnostic gaps elsewhere in this task.

`validate` already refuses an unknown attribute elsewhere (`E-UNITS-ATTR-MISSING`), and `data.units.attributes` is the declared set. Refuse a `by` that names nothing in it, and pin it. Task 3's implementer disclosed this in `spec-defects.md`; it is not a task 3 defect, but it **is** this task's gate.

### Sequencing constraint

**Task 6 must not land its `technical_n` route before task 9 has made its `counts` shape decision** — or the two tasks invent two routes for the same problem. Task 9 is explicitly scoped to decide how a sibling-of-`n` travels through `runner`'s attrition counts and `stats.summarize_step`; `technical_n` is the same question asked first. Either make the shape decision here and have task 9 follow it, or agree the route with task 9's brief before implementing. Say which you did.


### First: `technical_n` must actually be reported

Task 3 computes `technical_n` and returns it beside the roster, and **nothing carries it anywhere**. `reference.md` § What isn't a repeat says it "is reported for transparency — as `{min, max, median}` rather than a single number, because real files are uneven and a bare `technical_n: 3` would be a claim of balance nobody checked."

**Retiring the refusal is exactly the wrong moment to leave that undone.** Retiring it declares the declaration honoured; a feature that collapses replicates and never reports how many it collapsed is a declaration accepted whose effect is half-delivered — the risk this slice's spec names first.

Task 3's implementer investigated the route and did **not** guess, which was right. Its findings, to start from rather than redo:
- The shape `reference.md` shows puts it beside a *metric's* `n`, whose route is `runner`'s attrition counts → `stats.summarize_step`. That plumbing is task 9's, and task 9 is in the other half of the slice.
- `provenance.units` is documented as exactly `{n, key}`, so parking it there would invent an undocumented `run.yaml` field.

**Decide and justify.** It lands here rather than in task 9 so that the `measurements` half stays self-contained and the slice keeps its documented split seam at the 6/7 boundary. If you conclude the only correct home genuinely requires task 9's plumbing, say so and report `DONE_WITH_CONCERNS` rather than inventing a field — but say which document sentence forces that, not which is more convenient.

Whatever you choose, **pin it with a test that reads it back from a real run's artifacts**, not from a return value.

### Then: the retirement

**Files:**
- Modify: `src/publishable/validate.py`, `src/publishable/envelope.py`, `src/publishable/materialize.py`, `docs/reference.md`
- Test: `tests/test_validate.py`

- [ ] **Step 1: Write the failing test**

```python
def test_a_declared_measurements_block_is_no_longer_refused(write_config):
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["depth", "read_id"],
        "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
    }}})
    assert "E-DATA-MEASUREMENTS-UNSUPPORTED" not in codes(path)
```

- [ ] **Step 2: Run and confirm it fails**

- [ ] **Step 2b: Three stale `reference.md` bits, routed here by task 3 because this task rewrites these sections.** **Amended after task 5: `finalize` is now a *second* raise surface** — a step recording a non-numeric value under a numeric rule raises `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` at collapse time, so the execution fails on a *value the step recorded* rather than on anything the step did, and the user sees a code with no lookup. The row you write must cover **both** `resolve_units` and `finalize`, or it ships incomplete. `resolve_units` raises `E-DATA-MEASUREMENTS-INVALID` and `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`, but (i) both rows sit only in § Errors `validate` reports, (ii) neither carries the dual-listing clause `E-UNITS-COLLAPSE-RULE` has, and neither has a counterpart in § Errors core raises, and (iii) `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`'s row says `is_measurement_numeric` is "the single authority this check and **a future run-time coercion** both read" — that coercion is no longer future, and a row edit that only adds the dual-listing clause would leave this one false. Fix all three.

- [ ] **Step 3: Remove `("measurements", "E-DATA-MEASUREMENTS-UNSUPPORTED")` from the five-field loop.** Close the whole-leaf `envelope.py` block: replace the bare `dict` for `data.units.measurements` with typed leaves for `.by` (`str`) and `.collapse` (`str` or `dict`), so an unknown key inside it is reached by a check. Update `materialize.py`'s inline comment to drop `NOT BUILT`.

- [ ] **Step 4: Documents.** In `reference.md` § The one config file: the `NOT BUILT` marker on `measurements:` goes, and the prose count **eleven → ten**.

**Do not edit the "latent rather than live" passage** — it is about **`holdout`**, not `measurements`, and `holdout` stays refused until H3d. I checked this rather than inferring it, because editing a passage about a neighbouring block while believing it is about yours is precisely the document-defect class this project keeps shipping.

The relevant enumeration is `reference.md`'s closed-schema paragraph, which names **four** whole-leaf blocks the claim excepts: a `hypotheses` entry, a `statistics.contrasts` entry, a `replication.repeats` entry of kind `seed` or `fold`, and the mapping form of `data.units.from`. **`measurements` is not among them** — it is typed as a bare `dict` in `envelope.py` but excluded from that list because the whole block is refused.

So there are exactly two honest outcomes, and step 3 decides which:
- **If you fully type `.by` and `.collapse` as leaves** (the plan's intent), `measurements` never becomes a whole-leaf block and **neither passage needs an edit**. Verify by pinning that a typo *inside* the block — `{by: read_id, colapse: mean}` — now reports `E-CONFIG-KEY-UNKNOWN`.
- **If you cannot fully type it**, then `measurements` becomes a fifth live whole-leaf block and you **must add it to that enumeration**, with the slice that closes it named, exactly as the other four are.

Say which outcome you landed in and show the evidence. Silently leaving it typed `dict` while retiring the refusal is the one thing that must not happen: that turns a latent gap live without recording it anywhere.

- [ ] **Step 5: Run the full suite.** Then grep every tracked `*.md` for `E-DATA-MEASUREMENTS-UNSUPPORTED`; it must appear nowhere. **Prove the grep can fail** by running it against a code that does exist.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: data.units.measurements is a declaration core honors"
```

---

## Task 7: `weight_by`'s three checks

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Produces: `E-DATA-WEIGHT-UNKNOWN` (row 291), `E-DATA-WEIGHT-INVALID` (row 292), `W-DATA-WEIGHT-UNDECLARED` (row 293)

The three rows, verbatim: *"Weight attribute exists — `data.units.weight_by` names `sampling_weight`, which is not a unit attribute."* *"Weights are usable — `sampling_weight` holds a zero or negative value for 3 units; a weight is what a unit stands for."* *"Weighting looks undeclared — `sampling_weight` varies across units and looks like an inverse sampling probability, but `weight_by` is unset (warning)."*

The third fires when `weight_by` is **unset**, so it must not depend on the declaration it is about. Choose its heuristic and **state it in the row you write** — a warning whose trigger is unstated is one a user cannot act on. Recommended: a numeric attribute named `*weight*` or `*_prob*`, all values positive, and more than one distinct value.

- [ ] **Step 1: Write the failing tests** — one per identifier, plus:

```python
def test_an_empty_weight_by_is_a_finding_not_a_default(write_config):
    """Decision 3, the second truthiness hole."""
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id", "weight_by": "",
    }}})
    assert "E-DATA-WEIGHT-UNKNOWN" in codes(path)


def test_no_weight_warning_for_a_constant_column(write_config):
    """A column that does not vary is not a sampling weight, and warning about it
    would train a reader to ignore the warning."""
    ...
    assert "W-DATA-WEIGHT-UNDECLARED" not in codes(path)
```

- [ ] **Step 2: Run and confirm each fails.**

- [ ] **Step 3: Implement `_check_weight_by`**

```python
_WEIGHT_HINTS = ("weight", "_prob", "probability")


def _check_weight_by(units: dict[str, Any], roster: UnitList | None, c: Collector) -> None:
    """`data.units.weight_by` — the attribute exists, its values are usable, and
    a column that looks like a weight is not silently going unused.

    The name check runs without a roster; the value checks need one. Skipping the
    value half when the roster does not resolve is not the silent skip H1 removed:
    the name half still reports, and a test pins that.
    """
    declared = units.get("weight_by")
    if declared is not None and not declared:
        c.error(
            "E-DATA-WEIGHT-UNKNOWN",
            "data.units.weight_by",
            "is empty; it names the unit attribute holding the weight, and an empty "
            "declaration changes no behavior",
        )
        return
    names = sorted({n for u in roster for n in u.attributes}) if roster is not None else []
    if declared:
        if roster is not None and declared not in names:
            c.error(
                "E-DATA-WEIGHT-UNKNOWN",
                "data.units.weight_by",
                f"names {declared!r}, which is not a unit attribute. Declared "
                f"attributes are {', '.join(names) or 'none'}",
            )
            return
        if roster is None:
            return
        bad = [u.key for u in roster
               if not isinstance(u.attributes.get(declared), (int, float))
               or u.attributes[declared] <= 0]
        if bad:
            c.error(
                "E-DATA-WEIGHT-INVALID",
                "data.units.weight_by",
                f"holds a zero, negative or non-numeric value for {len(bad)} unit(s) "
                f"(first: {bad[0]!r}); a weight is what a unit stands for, so it has "
                "to be a positive number",
            )
        return
    if roster is None:
        return
    for name in names:
        if not any(hint in name.lower() for hint in _WEIGHT_HINTS):
            continue
        values = [u.attributes.get(name) for u in roster]
        if not all(isinstance(v, (int, float)) and v > 0 for v in values):
            continue
        if len({float(v) for v in values}) < 2:
            continue  # a column that does not vary is not a sampling weight
        c.warn(
            "W-DATA-WEIGHT-UNDECLARED",
            f"data.units.attributes.{name}",
            f"{name!r} is numeric, positive and varies across units, so it looks like "
            "an inverse sampling probability — but `data.units.weight_by` is unset, so "
            "it is reported and never weighted with. Set `weight_by` if it is one, or "
            "rename it if it is not",
        )
        return
```

**Write the heuristic into the `W-` row you add in step 6**, in these terms: a numeric attribute whose name contains `weight`, `_prob` or `probability`, all of whose values are positive and not all equal. A warning whose trigger is unstated is one a user cannot act on.

- [ ] **Step 4: Run and confirm they pass.**

- [ ] **Step 5: Mutation-test each of the three separately.** A single mutation that kills all three is not three tests.

- [ ] **Step 6: Registry rows and commit.** Two `E-` rows (67 → 69) and one `W-` row (18 → 19).

```bash
git commit -am "feat: check that a weight exists, is usable, and is not silently absent"
```

---

## Task 8: The weighted interval

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Produces: `kish_effective_n(weights) -> float`, `weighted_t_over_units(values, weights, confidence=0.95) -> Interval | None`

Kish's effective sample size is `(Σw)² / Σw²`. `reference.md` § Weighted samples: weighting concentrates the estimate on fewer units, and an interval that ignored that would be narrower than the sample supports. The existing `t_over_units(values, confidence)` computes df as `len(values) − 1` and must keep doing so for unweighted designs.

### First: promote the usability predicate, do not re-derive it

Task 7 built `validate._usable_weight` — positive, finite, and numeric via `units.is_measurement_numeric`. That is **the predicate `validate` approves a config against**, and it is currently private to `validate.py`. If the weighted mean is built on a different notion of a usable weight, this slice re-opens the validate-clean-then-crash gap it spent tasks 2 and 3 closing: a config `validate` accepts whose weights `stats` cannot use.

**Promote it beside `is_measurement_numeric` in `units.py`** and have both `validate` and `stats` read it. Do not import a private helper across modules — there is no precedent for that here, and task 2 established the pattern when `rule_for` gained a second caller. Mutation-test the sharing: changing the predicate must fail a test in **both** `test_validate.py` and `test_stats.py`, which is what makes the single-authority claim provided rather than stated.

Remember the CSV trap that has now bitten two tasks: table-sourced values arrive as `str`, so `isinstance(v, (int, float))` is `False` for every real weight. `is_measurement_numeric` is what handles that.

- [ ] **Step 1: Write the failing tests — the widening one first**

```python
def test_a_weighted_interval_is_wider_than_the_unweighted_one():
    """The point of Kish's size. A test asserting only that `weighted_by` was
    recorded would pass against an implementation that stores the declaration and
    computes the unweighted interval — which is the bug, not the fix."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    weights = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 20.0]   # genuinely uneven
    plain = t_over_units(values)
    weighted = weighted_t_over_units(values, weights)
    assert (weighted.high - weighted.low) > (plain.high - plain.low)


def test_equal_weights_reproduce_the_unweighted_interval():
    """The boundary that proves the construction is a generalization, not a
    different statistic wearing the same name."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    weighted = weighted_t_over_units(values, [1.0] * 5)
    plain = t_over_units(values)
    assert weighted.low == pytest.approx(plain.low)
    assert weighted.high == pytest.approx(plain.high)


def test_kish_effective_n_of_equal_weights_is_the_count():
    assert kish_effective_n([2.0, 2.0, 2.0, 2.0]) == pytest.approx(4.0)
```

`Interval` is a frozen dataclass of `low`, `high`, `method` — compare the two floats, not the objects: `method` legitimately differs between the two constructions, so `==` on the dataclass would fail for the right reason and tell you the wrong thing.

- [ ] **Step 2: Run and confirm each fails.**

- [ ] **Step 3: Implement**

```python
def kish_effective_n(weights: Sequence[float]) -> float:
    """Kish's effective sample size: (Σw)² / Σw².

    Equals the count when the weights are equal, and falls as they spread — which
    is the whole reason it is here. `reference.md` § Weighted samples: weighting
    concentrates the estimate on fewer units, and an interval whose df ignored
    that would be narrower than the sample supports.
    """
    total = sum(weights)
    squares = sum(w * w for w in weights)
    if squares == 0:
        return 0.0
    return (total * total) / squares


def weighted_t_over_units(
    values: Sequence[float], weights: Sequence[float], confidence: float = 0.95
) -> Interval | None:
    """Student's t on the weighted per-unit values, df = Kish's effective n − 1.

    Returns None below two values, matching `t_over_units`: df would be zero and
    there is no dispersion to describe. Reporting a point with no interval is
    honest; inventing one is not.
    """
    if len(values) < 2:
        return None
    total = sum(weights)
    mean = sum(w * v for w, v in zip(values, weights, strict=True)) / total
    # The weights are in the variance as well as the mean. Keeping them in only
    # the mean is the mutation step 5 requires a test for: it leaves the point
    # estimate right and the interval wrong, which is the failure that survives
    # an eyeball.
    variance = sum(w * (v - mean) ** 2 for w, v in zip(values, weights, strict=True)) / total
    effective = kish_effective_n(weights)
    if effective < 2:
        return None
    sem = math.sqrt(variance) / math.sqrt(effective)
    # Same construction as `t_over_units`, with Kish's size in place of the row
    # count — including a fractional df, which `t.ppf` accepts and which is the
    # honest value: the effective size of an uneven weighting is not an integer.
    critical = float(_scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=effective - 1))
    half = critical * sem
    return Interval(low=mean - half, high=mean + half, method="weighted_t_over_units")
```

**There is no `_t_critical` helper** — `t_over_units` calls `_scipy_stats.t.ppf` inline, and the line above matches it deliberately. If you would rather extract a shared helper, that is a reasonable call, but then **change both call sites in the same commit**: two critical-value expressions is how the weighted and unweighted intervals drift apart. Say which route you took.

- [ ] **Step 4: Run and confirm they pass.**

- [ ] **Step 5: Mutation-test — two separately.** First: use `len(values) − 1` for df instead of Kish's size. `test_a_weighted_interval_is_wider_than_the_unweighted_one` must FAIL. Second: drop the weights from the variance while keeping them in the mean. A test must FAIL — if none does, **write one**, because that is the defect the equal-weights test cannot see.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: a weighted interval takes its df from Kish's effective size"
```

---

## Task 9: `n` gains `effective`, and the record carries `weighted_by`

**Files:**
- Modify: `src/publishable/runner.py`, `src/publishable/stats.py`, `src/publishable/run_record.py`
- Test: `tests/test_runner.py`, `tests/test_cli.py`

`reference.md` § The three-part n: `effective` joins `n` **whenever `weight_by` makes Kish's size the one the interval was computed at**, and each part is *present only when it applies* so a design that never weights reads as it always did. That conditionality is the requirement, not a nicety.

- [ ] **Step 1: Write the failing tests**

```python
def test_n_gains_effective_under_a_weighted_design(...):
    assert metric["n"]["effective"] == pytest.approx(expected_kish)
    assert metric["weighted_by"] == "sampling_weight"


def test_n_has_no_effective_key_without_weight_by(...):
    """The regression: an unweighted run's `n` must not grow a key."""
    assert "effective" not in metric["n"]
    assert "weighted_by" not in metric
```

- [ ] **Step 2–4:** Fail, implement, pass.

**The three sites are verified**, all in `runner.py`: the no-roster early return, the no-recording-execution early return, and the accumulating return at the end. All three must agree, and the second test above is what catches having changed only two.

The route from there to a metric is `stats.summarize_step(collapsed, counts, derived=..., seed=..., resample=..., draws=...)` — `counts` **is** the dict those three sites build. So `effective` reaches a metric by riding that argument, and `weighted_by` needs its own way through; decide which and say so, rather than widening `counts` with a key that is not a count.

- [ ] **Step 5: Mutation-test.** Make `effective` unconditional. `test_n_has_no_effective_key_without_weight_by` must FAIL.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: report the effective n a weighted interval was computed at"
```

---

## Task 10: Wire the weighted estimator, and the percentile path

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`, `tests/test_cli.py`

### First: nothing calls `weighted_t_over_units`, and task 11 makes that a wrong number

**A gap this plan did not contain, found after task 9.** `grep` confirms the only mentions of `weighted_t_over_units` outside `stats.py` are *comments*. So today a weighted run records `weighted_by` and `n.effective` beside an **unweighted** mean and interval — the exact risk this slice's spec names first: *a declaration accepted whose effect is not delivered.*

It is latent only because `E-DATA-WEIGHT-UNSUPPORTED` refuses every config that declares `weight_by`. **Task 11 retires that refusal**, which turns it live. Task 9 left an `xfail(strict=True)` end-to-end pin that will XPASS-fail the suite at that moment — a deliberate forcing function, so this cannot be forgotten.

The site is `summarize_step`'s recorded-column loop:

```python
        values = [float(v) for v in raw]
        interval = t_over_units(values)
        out[column] = {
            **(beside_n or {}),
            "value": mean_of(values),
```

**Both lines must become weighted when weights are declared** — § Weighted samples says the construction "uses the weighted **mean** and the weighted variance". Wiring only the interval leaves the point estimate unweighted, which is the same half-delivered failure one level down, and would pass any test that checks only the interval.

Two things to get right, and to test rather than assume:
- **The weights must be aligned to the units the values came from.** `raw` is built by filtering `collapsed` for units that have the column, so the weight vector must be filtered the same way, in the same order. A misalignment silently weights the wrong unit and produces a plausible number.
- **A derived metric** — one `aggregate` computed, with no per-unit value — has no per-unit vector to weight. Say what happens to it, and check what § Weighted samples and § The unit table is the inference base require rather than choosing.

Assert **exact numbers**, not directions: task 8's headline test asserted a weighted interval was "wider than unweighted" and passed against an implementation using the row count for df, because it is still wider.

### Then: the percentile path

`reference.md` § Weighted samples: *"A percentile interval draws units as usual and recomputes the weighted statistic on each draw, so the weights are in the estimate rather than in the drawing."* Weighting the *draw* would be a different estimator; this is the distinction to test, not just to implement.

- [ ] **Step 1: Write the failing test**

```python
def test_a_percentile_draw_is_unweighted_while_its_statistic_is_not():
    """The weights belong in the estimate, not in the drawing — and the difference
    is observable in the output, with no test-only hook.

    21 units: twenty at 1.0, one at 100.0 carrying almost all the weight. Drawing
    UNWEIGHTED, the heavy unit is absent from a good fraction of the draws, and a
    draw without it has a weighted mean of 1.0 — so the interval reaches down to 1.
    Drawing WEIGHTED, the heavy unit would fill nearly every slot of every draw,
    the weighted mean would be ~100 every time, and the interval would collapse to
    a point near 100. The low bound is what separates the two estimators."""
    values = [1.0] * 20 + [100.0]
    weights = [1.0] * 20 + [500.0]
    result = percentile_over_units(values, weights=weights, draws=2000, seed=7)
    assert result.low == pytest.approx(1.0, abs=0.5)   # a draw-weighted impl cannot reach here
    assert result.high > 50.0                          # ...while the statistic is still weighted
```

**Do not add a test-only hook to the production signature** to observe the draw — a hook that exists only for the test is a second API. The assertion above sees the draw through the output, which is the route to prefer. If you find it does not discriminate, test the draw helper directly instead, and say in your report which route you took and why.

Note that `percentile_over_units` currently **sorts its pool**, with a comment explaining that the resample must depend on the multiset rather than on row order. A weighted version must keep each value with its own weight — sort the `(value, weight)` pairs together, or draw indices against an unsorted pair list. Getting this wrong silently pairs values with the wrong weights, and the equal-weights test cannot see it.

- [ ] **Step 2–4:** Fail, implement, pass.

- [ ] **Step 5: Mutation-test.** Weight the draw instead of the statistic; the test must FAIL.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: a percentile draw stays unweighted while its statistic does not"
```

---

## Task 11: Refuse a weighted contrast, and retire `E-DATA-WEIGHT-UNSUPPORTED`

### First, and it gates the retirement: contrasts are still unweighted

`reference.md` § Weighted samples: *"a [contrast](#contrasts-claims-that-arent-condition-vs-baseline) between two weighted conditions uses **the same weights on both sides**, which is automatic under `allocation: within` and worth checking when it isn't."*

**No weighted contrast construction exists.** `paired_t_over_units(diffs, confidence)` takes only differences; `paired_delta_of_derived` and `paired_percentile_of_derived` likewise. Task 10 wired the *single-condition* estimators — value, interval and `n.effective` — but a `vs_baseline` delta is still computed unweighted. Retiring the refusal without addressing that turns every weighted run's delta into a wrong number, which is the same forbidden move task 10 was widened to prevent one level up.

**Ruling: mint a narrow, temporary refusal rather than building the estimator family here.** Building it is a second slice's worth of work — three constructions plus their wiring — and H4 Statistics already owns the contrast and correction family. The precedent is exact: H2 retired `E-SWEEP-BASELINE-PARTIAL` and minted `E-SWEEP-SAMPLE-BASELINE` for the combination it had just made reachable but could not yet compute.

So `data.units.weight_by` becomes legal, **except** in combination with a contrast:

| Config | Outcome |
|---|---|
| `weight_by`, no contrast | works — weighted mean, weighted interval, `n.effective`, `weighted_by` |
| `weight_by` + `sweep.baseline` | refused |
| `weight_by` + `statistics.contrasts` | refused |

Follow `E-SWEEP-SAMPLE-BASELINE`'s shape when writing it: the message says what is wrong, what to do instead, and that the combination will be honoured once the contrast estimators weight. **Measure the blast radius before writing the guard** — refuse only the combinations that actually produce a wrong delta, and pin each edge. A refusal wider than the harm strands designs that are fine, which is the failure H2 checked for explicitly.

The identifier needs a registry row, and § The one config file's `NOT BUILT` list still has to go **ten → nine** for `weight_by` itself. Say in your report whether the new code belongs in that list too — it refuses a *combination*, not a declaration, and H2 ruled that such a code carries a registry row and does **not** join the `NOT BUILT` count.

### Then: the retirement

Mirrors task 6. Remove `("weight_by", "E-DATA-WEIGHT-UNSUPPORTED")` from the five-field loop; `materialize.py`'s comment loses `NOT BUILT`; `reference.md`'s prose count goes **ten → nine**. `weight_by` is already a typed `str` leaf in `envelope.py`, so there is no whole-leaf block to close here — **verify that rather than assuming it**.

- [ ] **Step 1: Write the failing test**

```python
def test_a_declared_weight_by_is_no_longer_refused(write_config):
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["sampling_weight"],
        "weight_by": "sampling_weight",
    }}})
    assert "E-DATA-WEIGHT-UNSUPPORTED" not in codes(path)
```

- [ ] **Step 2: Run it and confirm it fails.**

- [ ] **Step 3: Remove the tuple from the five-field loop; update `materialize.py`.**

- [ ] **Step 4: `reference.md` § The one config file — drop the `NOT BUILT` marker on `weight_by:` and take the prose count ten → nine.**

- [ ] **Step 5: Full suite, then grep every tracked `*.md` for `E-DATA-WEIGHT-UNSUPPORTED` — it must appear nowhere. Prove the grep can fail against a code that does exist.**

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: data.units.weight_by is a declaration core honors"
```

---

## Task 12: The consistency passes and the exit criterion

**Files:** whichever of the four documents the passes find defects in.

- [ ] **Step 0: H3a's four § Validation rows, by title not number.** `docs/superpowers/H3-SCOPING.md` names them as rows 243, 291, 292, 293 — **those numbers are already stale**: the first is now 244 and the weight rows are at 292–294, because the table grew above them during this slice. Verify by **row title**, which is stable: *"Collapse rule fits the column"* (task 2), *"Weight attribute exists"*, *"Weights are usable"*, *"Weighting looks undeclared"* (task 7). Each must have an implemented check emitting the identifier its row implies, and a test producing it. This is `CLAUDE.md`'s own "cite by section, never by line number" rule arriving as a concrete failure — do not re-cite the numbers.

- [ ] **Step 1: Both retirements, both directions.** `E-DATA-MEASUREMENTS-UNSUPPORTED` and `E-DATA-WEIGHT-UNSUPPORTED` must be absent from `src/**/*.py` **and** from every tracked `*.md`. The second direction is the one `comm -23` cannot see — a surviving row for a retired code is the mirror of an undocumented code. **State the command and prove it can fail.** Exclude `__pycache__` with `--include='*.py'`; stale bytecode has produced a false positive on this exact check before.

- [ ] **Step 2: The `NOT BUILT` count is nine**, and exactly `measurements` and `weight_by` left the list. This is a number in prose that no mechanical check catches.

- [ ] **Step 3: Registry counts.** § Errors `validate` reports 65 → 69, § Warnings core reports 18 → 19, and every new row's condition read from its emit site rather than from this plan. Both directions: every code `src/` emits is documented or is a surviving `-UNSUPPORTED`; every documented code is still emitted.

- [ ] **Step 4: `partition_units` is untouched.** `git diff main..HEAD -- src/publishable/units.py` must show no change inside it. **This is H3a's own claim to being first in H3, and H3b and H3c both rely on it.**

- [ ] **Step 5: The worked example did not move.** `cohort-pilot` declares neither field. Verify with a **real temporary commit** — a working-tree edit is invisible to a two-dot diff, which is how this check silently passes.

- [ ] **Step 6: The mechanical pass**, then the **cross-document pass** over `CLAUDE.md`'s seven drift classes. The ones this slice most plausibly disturbed: **config completeness** (two fields changed meaning), **enum comments** (`collapse` must list what the code accepts), **schema fields in prose**, and **declared vs. derived** (`technical_n` and `effective` are derived — no passage may show either as a settable input).

- [ ] **Step 7: Fix what the passes find; commit only if something changed.** A clean result is a real result — do not create an empty commit.

---

## Sequencing

1 → 12 in order. Tasks 1–6 are `measurements`, 7–11 are `weight_by`, and **the two halves share nothing**: if the slice runs long it splits cleanly at the 6/7 boundary. Task 1 is what tasks 3 and 5 both call; task 4 must precede task 5; tasks 6 and 11 retire their refusals only after the behaviour behind them works, so that no check lands as dead code behind a refusal. Task 12 runs last, over a settled tree.
