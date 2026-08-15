# Reporting strata (S4d) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A run reports each metric over the subgroups a config names, without adding an execution, a condition, or a place in the correction family.

**Architecture:** A pure `strata.py` maps an attribute to its levels and their unit keys. `cli.py` filters the collapsed table and the roster to one level, then calls the **same** `stats.summarize_step` the parent block already uses — a stratum is the existing number over fewer rows, not a new construction. `validate` refuses an undeclared attribute and warns on a level the roster says is thin; `run` warns again on the level's realized completed count, which is what attrition makes different.

**Tech Stack:** Python 3.11+, `uv`, pytest, ruff, mypy, numpy, scipy.

## Global Constraints

- Python >= 3.11.
- Runtime dependencies are exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`. Adding one is out of scope.
- ruff: line-length 100, select `["E","F","I","UP","B"]`. mypy: strict over `src/`.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run mypy`. (`ruff format` reformats ~33 pre-existing files — do not run it; `ruff check` is the gate.)
- `×`, not `x`, for multiplication — including inside fenced blocks and commit messages.
- `stats.py`, `sweep.py`, `contrasts.py`, `correction.py` and the new `strata.py` are **pure**: no filesystem, and no runtime import of `config`, `artifacts`, `runner`, or `cli`.
- `artifacts.py` is the only module that writes inside a run directory.
- `validate.py` **collects** findings and never raises to report one — including on a config value of the wrong type. Guard before `len()`, `in`, iteration, or set membership.
- Every `E-`/`W-` identifier must have a test that produces it; for a validate-time code that means through `validate_config`, and for a run-time one through `main(["run", ...])`.
- The four documents in `docs/` are normative and lead. Where code cannot follow them, the document changes first and the gap is recorded in `docs/superpowers/spec-defects.md`.
- Unimplemented must mean **refused**, never silently ignored.
- **Strata add no executions.** `dry-run`'s count must not move.
- **Strata never join the correction family.** `correction.Member`s are built only from comparisons; nothing in this slice may build one.
- **Do not amend a reviewed commit.** New commits only.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/strata.py` *(new)* | **Pure.** `levels_for(roster, attribute)` — level value to unit keys |
| `src/publishable/cli.py` | Build `aggregated.<step>.by.<attribute>.<level>.<metric>`; the run-time thin warning |
| `src/publishable/validate.py` | Retire `E-STATS-REPORTBY-UNSUPPORTED`; refuse an undeclared attribute; `_check_shape` guard; `W-STATS-REPORTBY-THIN` |
| `docs/reference.md` | Add the metric level to the § Reporting strata example |

**Read before starting:** `docs/superpowers/specs/2026-08-10-reporting-strata-design.md`, and `reference.md` § Reporting strata.

---

### Task 1: `reference.md`'s stratum example gains its metric level

The document leads, so this lands before any code reads it.

**Files:**
- Modify: `docs/reference.md` (the § Reporting strata `aggregated` example)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing in code. Task 5 builds the record shape this edit fixes, and Task 7 asserts it.

- [ ] **Step 1: Find the example**

Run: `grep -n "by:" docs/reference.md`

The § Reporting strata example shows `by` as a sibling of the metric `r`, with `by.sex.f` holding a metric entry directly.

- [ ] **Step 2: Understand why it is wrong before changing it**

`aggregated.<step>` is a **metric block** — a mapping of metric name to entry. The example's `by.sex.f` is an *entry*, so the metric name appears nowhere beneath `by`. That is self-consistent only when a step reports exactly one metric; with two, the second has nowhere to go. Write this reasoning down in your report — a reviewer will ask whether the document was wrong or merely abbreviated.

- [ ] **Step 3: Add the metric level**

Change:

```yaml
    by:
      sex:
        f: {value: 0.591, basis: units, n: {resolved: 120, completed: 114, failed: 6}, ci95: [...]}
        m: {value: 0.622, basis: units, n: {resolved: 120, completed: 114, failed: 6}, ci95: [...]}
```

to:

```yaml
    by:
      sex:
        f:
          r: {value: 0.591, basis: units, n: {resolved: 120, completed: 114, failed: 6}, ci95: [...]}
        m:
          r: {value: 0.622, basis: units, n: {resolved: 120, completed: 114, failed: 6}, ci95: [...]}
```

Every number is unchanged. This example belongs to the shared worked example (`step03_analyze`, metric `r`, 240 resolved / 228 completed / 12 failed), whose figures `CLAUDE.md` § The worked example pins — only the nesting moves.

- [ ] **Step 4: Run the mechanical pass**

Write a throwaway script under the session scratchpad (the repo ships no markdown tooling on purpose). **Skipping fenced code blocks**, check: every relative link and `#anchor` resolves, no two headings collide on an anchor, every table row matches its header's column count, and no line carries trailing whitespace, a tab, or invisible unicode.

The edit is *inside* a fence, so those checks will not see it — run them anyway to confirm nothing above or below broke.

- [ ] **Step 5: Run the cross-document pass**

`CLAUDE.md` § Checking consistency names the classes that actually drift. Two apply:

- **The shared worked example.** Grep README.md, `docs/design-principles.md` and `docs/reference.md` for `0.591` and `0.622`. If either appears elsewhere in a `by` block, it needs the same nesting change; if it appears in prose, confirm the prose does not describe the old shape.
- **Schema fields in prose.** Grep the four documents for `report_by` and confirm no passage describes the record shape in a way the new nesting contradicts.

- [ ] **Step 6: Commit**

```bash
git add docs/reference.md
git commit -m "Give a stratum's entry the metric level it needs"
```

---

### Task 2: `strata.levels_for`

**Files:**
- Create: `src/publishable/strata.py`
- Test: `tests/test_strata.py` *(new)*

**Interfaces:**
- Consumes: `units.UnitList` and `units.Unit` under `TYPE_CHECKING` only — `Unit` is frozen with `key: str` and `attributes: Mapping[str, Any]`.
- Produces: `levels_for(roster: "UnitList", attribute: str) -> dict[str, set[str]]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_strata.py`:

```python
from publishable.strata import levels_for
from publishable.units import Unit, UnitList


def _roster(*specs):
    return UnitList([Unit(key=k, paths=(), attributes=a) for k, a in specs])


def test_each_level_holds_the_units_that_carry_it():
    roster = _roster(
        ("u1", {"sex": "f"}), ("u2", {"sex": "m"}), ("u3", {"sex": "f"})
    )
    assert levels_for(roster, "sex") == {"f": {"u1", "u3"}, "m": {"u2"}}


def test_values_compare_as_strings():
    """A config's YAML gives `1` as an int while the same attribute read from a
    CSV is `"1"`. `contrasts.units_matching` coerces for this reason and so does
    this: two units whose attribute differs only in type are one level, not two,
    or a stratum silently splits in half."""
    roster = _roster(("u1", {"site": 1}), ("u2", {"site": "1"}), ("u3", {"site": 2}))
    assert levels_for(roster, "site") == {"1": {"u1", "u2"}, "2": {"u3"}}


def test_a_unit_missing_the_attribute_forms_no_level():
    """`.get` returns `None` for an attribute a unit does not carry. Coercing that
    to the string `"None"` would publish a subgroup named after a bug — the same
    trap `contrasts.resolve_contrasts` hit with a missing `id`. Such a unit is in
    no level, and so is absent from every stratum's `n`."""
    roster = _roster(("u1", {"sex": "f"}), ("u2", {}), ("u3", {"sex": None}))
    assert levels_for(roster, "sex") == {"f": {"u1"}}


def test_an_unknown_attribute_yields_no_levels():
    """Not an exception: `validate` refuses an undeclared attribute (Task 3), so
    this is unreachable from a validated config, and a pure function has no
    diagnostic to raise into."""
    roster = _roster(("u1", {"sex": "f"}))
    assert levels_for(roster, "nosuch") == {}


def test_an_empty_roster_yields_no_levels():
    assert levels_for(UnitList([]), "sex") == {}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_strata.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'publishable.strata'`.

- [ ] **Step 3: Implement**

Create `src/publishable/strata.py`:

```python
"""Which units each level of a reporting attribute picks out. Pure: roster in,
key sets out.

`docs/reference.md` § Reporting strata: `report_by` names unit attributes, and
core "repeats the aggregation it already performs, over the subsets of the
per-unit table each level picks out". This module is only the *which units*
half — the aggregation itself is `stats.summarize_step`, unchanged.
"""

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from publishable.units import UnitList


def levels_for(roster: "UnitList", attribute: str) -> dict[str, set[str]]:
    """Each level of `attribute`, and the keys of the units carrying it.

    Values compare as strings, the same coercion `contrasts.units_matching`
    makes and for the same reason: a config's YAML gives `1` as an int while
    the same attribute read from a table is `"1"`, and a stratum that split on
    the difference would report one subgroup as two.

    A unit whose attribute is absent or `None` joins no level. Coercing it to
    the string `"None"` would publish a subgroup named after a bug, and there
    is no honest level for "we don't know" — such a unit is simply absent from
    every stratum's `n`, which is why the levels' counts need not sum to the
    condition's.

    An attribute no unit carries yields `{}` rather than raising: `validate`
    refuses one not declared in `data.units.attributes`, so this is unreachable
    from a validated config, and a pure function has no diagnostic to raise.
    """
    out: dict[str, set[str]] = defaultdict(set)
    for unit in roster:
        value = unit.attributes.get(attribute)
        if value is not None:
            out[str(value)].add(unit.key)
    return dict(out)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_strata.py -v && uv run ruff check . && uv run mypy`
Expected: PASS.

- [ ] **Step 5: Prove the tests discriminate**

Apply each mutation, run the named test, confirm it fails, revert with `git checkout -- src/publishable/strata.py`, and confirm `git status --porcelain` is empty before the next.

| Mutation | Must fail |
|---|---|
| `out[value].add(...)` — drop the `str()` | `test_values_compare_as_strings` |
| Drop the `if value is not None` guard | `test_a_unit_missing_the_attribute_forms_no_level` |
| `out[str(value)].add(unit)` — the unit, not its key | `test_each_level_holds_the_units_that_carry_it` |

- [ ] **Step 6: Commit**

```bash
git add src/publishable/strata.py tests/test_strata.py
git commit -m "Map a reporting attribute to its levels"
```

---

### Task 3: `validate` accepts `report_by`, and refuses what it cannot honour

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: nothing new. `_check_shape`'s `_bad(key, value, kind)` helper and the `E-CONFIG-SHAPE` identifier already exist; `_check_unimplemented` holds the refusal to retire.
- Produces: `E-STATS-REPORTBY-UNKNOWN` (new). `E-STATS-REPORTBY-UNSUPPORTED` is retired.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_validate.py` (`_TWO_CONDITIONS` and the `write_config`/`codes` helpers already exist there):

```python
_UNITS_WITH_SEX = {"from": "index.csv", "key": "patient_id", "attributes": ["sex"]}


def test_a_declared_report_by_is_no_longer_refused(write_config):
    """S4d implements it, so the blanket refusal retires with the slice — the
    same way `E-STATS-CONTRASTS-UNSUPPORTED` retired with S4b."""
    found = codes(
        write_config(
            {"data.units": _UNITS_WITH_SEX, "statistics": {"report_by": ["sex"]}}
        )
    )
    assert "E-STATS-REPORTBY-UNSUPPORTED" not in found
    assert "E-STATS-REPORTBY-UNKNOWN" not in found


def test_a_report_by_attribute_must_be_declared(write_config):
    """`reference.md` § Reporting strata: "validate rejects a `report_by`
    attribute that isn't declared in `data.units.attributes`". Left unchecked,
    `strata.levels_for` returns `{}` for a typo, which is indistinguishable from
    an attribute no unit happens to carry — the record would simply hold no `by`
    block and never say why."""
    found = codes(
        write_config(
            {"data.units": _UNITS_WITH_SEX, "statistics": {"report_by": ["sexx"]}}
        )
    )
    assert "E-STATS-REPORTBY-UNKNOWN" in found


def test_a_non_list_report_by_is_refused_without_raising(write_config):
    """`validate.py` collects findings and never raises. `report_by` is a nested
    config value that new code reads, and this slice's predecessor shipped two
    crashes of exactly that kind — a scalar `statistics.contrasts` reaching
    `_check_sweep`, and an unhashable contrast `id` reaching a set."""
    for block in (5, True, "sex", {"sex": 1}):
        found = codes(
            write_config(
                {"data.units": _UNITS_WITH_SEX, "statistics": {"report_by": block}}
            )
        )
        assert "E-CONFIG-SHAPE" in found


def test_a_non_string_report_by_entry_is_refused(write_config):
    """A list is well-shaped but its *entries* may not be. An unhashable entry
    would reach a set membership test against `data.units.attributes`."""
    found = codes(
        write_config(
            {"data.units": _UNITS_WITH_SEX, "statistics": {"report_by": [["sex"]]}}
        )
    )
    assert "E-STATS-REPORTBY-UNKNOWN" in found
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_validate.py -k report_by -v`
Expected: the first FAILs because the refusal still fires; the others FAIL because neither the check nor the guard exists.

- [ ] **Step 3: Retire the refusal**

In `_check_unimplemented`, delete the `report_by` tuple from the refused list:

```python
        (
            "report_by",
            "E-STATS-REPORTBY-UNSUPPORTED",
            "no stratified reporting runs",
        ),
```

Then grep the whole tree for the identifier — `grep -rn "E-STATS-REPORTBY-UNSUPPORTED" src/ tests/ docs/` — and remove every remaining reference in `src/`, `tests/` and the four documents. Hits inside `docs/superpowers/` (plans, specs, spec-defects) are history and stay. This is the pattern S4b followed when it retired `E-STATS-CONTRASTS-UNSUPPORTED`.

- [ ] **Step 4: Add the shape guard**

In `_check_shape`, beside the existing `statistics.contrasts` nested block:

```python
        report_by = statistics.get("report_by")
        if report_by is not None and not isinstance(report_by, list):
            _bad("statistics.report_by", report_by, "list")
```

This sits inside the existing `if isinstance(statistics, dict):` block — check how `statistics.contrasts` is guarded there and follow it exactly.

- [ ] **Step 5: Refuse an undeclared or non-string attribute**

Add a `_check_report_by(doc, c)` function, called from `validate_config` beside `_check_contrasts`:

```python
def _check_report_by(doc: dict[str, Any], c: Collector) -> None:
    """Each `statistics.report_by` attribute, checked against the declared ones.

    `reference.md` § Reporting strata: "validate rejects a `report_by` attribute
    that isn't declared in `data.units.attributes`". The reason is the same one
    `E-STATS-CONTRAST-WITHIN` exists for: `strata.levels_for` reads the attribute
    with `.get`, which returns `None` for a typo exactly as it would for an
    attribute no unit carries, so the two are indistinguishable downstream — the
    record would hold no `by` block and never say why.

    A non-string entry is refused under the same code rather than reaching the
    set membership test below, where an unhashable one would raise out of a
    module whose contract is that it collects.
    """
    entries = ((doc.get("statistics") or {}).get("report_by")) or []
    if not isinstance(entries, list):
        return  # `_check_shape` already refused it, and returned early
    declared = set(((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
    for i, name in enumerate(entries):
        if not isinstance(name, str) or name not in declared:
            c.error(
                "E-STATS-REPORTBY-UNKNOWN",
                f"statistics.report_by[{i}]",
                f"names `{name!r}`, which is not in `data.units.attributes`",
            )
```

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

Expected: all pass. If a pre-existing test asserted `E-STATS-REPORTBY-UNSUPPORTED`, update it to the new behaviour and say which in your report — do not weaken it to pass.

- [ ] **Step 7: Record the new identifier**

`reference.md` states the rule and names no code, so append an entry to `docs/superpowers/spec-defects.md` in the shape `E-STATS-CONTRAST-WITHIN`'s entry uses: which sentence it implements, why the document names no identifier, and what it would be indistinguishable from otherwise. That file is gitignored — write it anyway.

- [ ] **Step 8: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Accept report_by, and refuse an attribute nothing declares"
```

---

### Task 4: `W-STATS-REPORTBY-THIN` at validate time

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `strata.levels_for` (Task 2); `_check_report_by` (Task 3), which this extends. `validate_config` already resolves the roster — find how by grepping `resolve_units` in `validate.py`; it may be `None` when the units cannot be resolved, and this check must be skipped then rather than guessing.
- Produces: `W-STATS-REPORTBY-THIN` (new).

- [ ] **Step 1: Write the failing test**

```python
def test_a_thin_report_by_level_warns_before_the_run(write_config, tmp_path):
    """`reference.md` § Reporting strata: validate "warns when a level would hold
    fewer units than `limits.min_reported_n` — before the run rather than at
    disclosure." Counting is over *resolved* units, which is all validate can
    see; the realized count after attrition is `W-STATS-STRATUM-THIN`'s job at
    run time (Task 6)."""
    data = tmp_path / "data"
    data.mkdir()
    rows = "\n".join(f"p{i},{'f' if i <= 2 else 'm'}" for i in range(1, 13))
    (data / "index.csv").write_text(f"patient_id,sex\n{rows}\n")
    found = codes(
        write_config(
            {
                "data.units": _UNITS_WITH_SEX,
                "data.input_dir": str(data),
                "limits": {"min_reported_n": 10},
                "statistics": {"report_by": ["sex"]},
            }
        )
    )
    assert "W-STATS-REPORTBY-THIN" in found
```

The `f` level holds 2 units against a floor of 10; `m` holds 10 and does not warn. **Check how `write_config` sets `data.input_dir`** before relying on the key name above — read the helper and match it. If it does not support pointing at a real roster, build the config with `generate_experiment` the way `tests/test_cli.py::run_a_project` does, and say so in your report.

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_validate.py -k thin_report_by -v`
Expected: FAIL — no such identifier is produced.

- [ ] **Step 3: Implement**

**This changes Task 3's signature.** `_check_report_by(doc, c)` becomes
`_check_report_by(doc, c, roster: "UnitList | None")`, and its call site in `validate_config` must
pass the roster that function already resolved — find how the roster reaches `_check_sweep` there
(it is passed as `unit_count=len(roster) if roster is not None else None`) and pass the roster
itself the same way. Keep `entries`, `declared` and the refusal loop from Task 3 exactly as they
are; this appends to the end of the same function.

Then warn per level:

```python
    if roster is None or not isinstance(floor, (int, float)) or isinstance(floor, bool):
        return
    for name in entries:
        if not isinstance(name, str) or name not in declared:
            continue  # already refused above
        for level, keys in sorted(levels_for(roster, name).items()):
            if len(keys) < floor:
                c.warn(
                    "W-STATS-REPORTBY-THIN",
                    f"statistics.report_by[{entries.index(name)}]",
                    f"level `{level}` of `{name}` would hold {len(keys)} of "
                    f"{len(roster)} units, below limits.min_reported_n ({floor})",
                )
```

`floor` is `(doc.get("limits") or {}).get("min_reported_n")`. The `isinstance` guard is not decoration: `limits` is user-written and `validate` must not raise on a string threshold. `bool` is excluded because `True` compares as `1` and would warn on every level of size 0 only — a guard that reads as protection and is not. Sorting the levels makes the diagnostics' order a function of the roster rather than of set iteration.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the test discriminates**

| Mutation | Must fail |
|---|---|
| `len(keys) > floor` | the thin-level test |
| Drop the `bool` exclusion and set `min_reported_n: false` in a second test | that second test — write it, since `False == 0` makes the floor 0 and every level passes, which is the case that earns the guard |

Run both, report the observed output, restore, and confirm `git status --porcelain` is empty.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Warn before the run about a stratum the roster says is thin"
```

---

### Task 5: The `by` block in the record

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `strata.levels_for` (Task 2); `stats.summarize_step(collapsed, counts, derived=None, seed=None, resample=None, draws=2000) -> dict[str, dict[str, Any]]`; `runner.attrition(results, roster, step_name, condition_index, fold_members=None) -> dict[str, int]`; `units.UnitList(units: list[Unit], train=None)`.
- Produces: `aggregated[cond][step]["by"][attribute][level]` — a metric block, the same shape `aggregated[cond][step]` itself is.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_cli.py`. `run_a_project` already writes a `cohort` column (alternating `a`/`b`) into `index.csv` and takes `unit_attributes=` to declare it:

```python
def test_a_reporting_stratum_repeats_the_metric_over_its_own_units(
    tmp_path, capsys, monkeypatch
):
    """`reference.md` § Reporting strata: core "repeats the aggregation it already
    performs, over the subsets of the per-unit table each level picks out". Each
    level's `n` and `ci95` are its own — computed over that level's units, not
    the condition's. A stratum whose numbers equal the parent's is the defect
    this test exists to catch."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    by = step_block["by"]["cohort"]
    assert set(by) == {"a", "b"}
    for level in ("a", "b"):
        entry = by[level]["pred"]
        assert entry["basis"] == "units"
        assert entry["n"]["completed"] == 20
        assert entry["ci95"] is not None
        # `repeat_spread` is the parent block's, not a stratum's: the documented
        # example carries value, basis, n and ci95 and nothing else, and `cli`
        # attaches spread outside `summarize_step`.
        assert "repeat_spread" not in entry
    # The parent block is unchanged and covers every unit.
    assert step_block["pred"]["n"]["completed"] == 40
    # Each level's interval is its own, not a copy of the parent's.
    assert by["a"]["pred"]["ci95"] != step_block["pred"]["ci95"]


def test_two_attributes_are_two_marginal_splits_not_their_cross(
    tmp_path, capsys, monkeypatch
):
    """`reference.md` § Reporting strata: "`report_by: [sex, site]` adds a `by.sex`
    block and a `by.site` block, each over the whole table; it does not produce a
    `f × site_03` cell." The cartesian product is the thing that section exists to
    avoid — five reporting attributes would be a cell explosion of subgroups
    nobody asked for."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort", "arm"],
        statistics={"report_by": ["cohort", "arm"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    by = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["by"]
    assert set(by) == {"cohort", "arm"}
    assert set(by["cohort"]) == {"a", "b"}
    # Each marginal covers the whole table, so the two levels sum to every unit.
    assert sum(by["cohort"][lv]["pred"]["n"]["completed"] for lv in by["cohort"]) == 40
    # No cell of the cross exists anywhere.
    assert "a__x" not in by["cohort"]
    assert not any(isinstance(v, dict) and "arm" in v for v in by["cohort"].values())


def test_a_run_without_report_by_has_no_by_block(tmp_path, capsys, monkeypatch):
    """Absent, not empty — the rule `vs_baseline` and `contrasts` already follow.
    An empty `by: {}` would claim a stratification was performed and found
    nothing."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(tmp_path, capsys=capsys, units=40)
    text = (doc["run_dir"] / "run.yaml").read_text()
    assert "by:" not in text


def test_strata_do_not_join_the_correction_family(tmp_path, capsys, monkeypatch):
    """`reference.md` § Reporting strata: "Strata don't join the correction
    family, because a stratum is a description rather than a comparison a reader
    acts on." If they did, adding `report_by` would enlarge the family, shrink α,
    and silently tighten every real comparison in the run."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    sweep = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]},
    }
    without = run_a_project(tmp_path / "a", capsys=capsys, units=40, sweep=sweep)
    with_strata = run_a_project(
        tmp_path / "b",
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        sweep=sweep,
        statistics={"report_by": ["cohort"]},
    )
    sizes = []
    for doc in (without, with_strata):
        run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
        entry = _first_contrast(run, "method=spearman")
        sizes.append((entry["family_size"], entry["family"]))
    assert sizes[0] == sizes[1]
```

`run_a_project` writes only a `cohort` column today. The two-attribute test needs a second: extend the roster writer to emit an `arm` column as well (alternate `x`/`y`), the same way `cohort` is written, and declare it via `unit_attributes`. Keep it unconditional — an undeclared column is never read.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_cli.py -k "stratum or marginal or by_block or correction_family" -v`
Expected: the first two FAIL with `KeyError: 'by'`; the third passes already (a regression guard); the fourth passes already (a guard against the mutation this task must not introduce).

- [ ] **Step 3: Implement**

In `command_run`'s aggregate loop, after `aggregated[cond.index][step_name] = step_summary` is assigned, build the strata for that step:

```python
                    report_by = (doc.get("statistics") or {}).get("report_by") or []
                    by_block: dict[str, dict[str, dict[str, Any]]] = {}
                    for attribute in report_by if isinstance(report_by, list) else []:
                        if not isinstance(attribute, str):
                            continue  # `validate` refused it; do not crash here
                        levels: dict[str, dict[str, Any]] = {}
                        for level, keys in sorted(levels_for(roster, attribute).items()):
                            # One key set decides BOTH the table and the counts.
                            # Taking the level's rows beside the condition's `n`
                            # is the S4b Critical's shape — a number reported
                            # against a denominator computed over other units.
                            level_collapsed = {k: v for k, v in collapsed.items() if k in keys}
                            level_roster = UnitList([u for u in roster if u.key in keys])
                            level_counts = attrition(
                                results, level_roster, step_name, cond.index,
                                fold_members=fold_members,
                            )
                            level_summary = summarize_step(
                                level_collapsed,
                                level_counts,
                                derived=derived,
                                seed=resample_seed_value,
                                resample=resample_fns,
                                draws=derived_metric_draws,
                            )
                            if level_summary:
                                levels[level] = level_summary
                        if levels:
                            by_block[attribute] = levels
                    if by_block:
                        aggregated[cond.index][step_name]["by"] = by_block
```

Read the surrounding loop before writing this: `collapsed`, `derived`, `resample_fns`, `results`, `fold_members`, `resample_seed_value` and `derived_metric_draws` are all already in scope there under those names — confirm each and adjust if one differs.

Three things this deliberately does **not** do. It builds no `correction.Member`, so a stratum cannot enter the correction family. It passes the run's own `resample_seed_value` rather than deriving a per-level seed — a level draws from its own key set, which is what makes its resample its own. And it omits `repeat_spread`, which `summarize_step` does not add.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| `level_collapsed = collapsed` — stratify over every unit | `test_a_reporting_stratum_repeats_the_metric_over_its_own_units` (each level's `ci95` becomes the parent's) |
| `level_counts = counts` — the condition's counts beside the level's rows | the same test's `n["completed"] == 20` |
| Build the cross: nest the second attribute's levels inside the first's | `test_two_attributes_are_two_marginal_splits_not_their_cross` |
| Assign `aggregated[...]["by"] = {}` unconditionally | `test_a_run_without_report_by_has_no_by_block` |

Run each, report the observed output, restore with `git checkout -- src/publishable/cli.py`, confirm `git status --porcelain` is empty.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "Report each metric over the subgroups a config names"
```

---

### Task 6: `W-STATS-STRATUM-THIN` at run time

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: the `by_block` loop from Task 5, and `aggregate_c` — the `Collector` that loop already warns into for `W-STATS-AGGREGATE-FAILED`. Confirm its name in the surrounding code.
- Produces: `W-STATS-STRATUM-THIN` (new).

- [ ] **Step 1: Write the failing test**

```python
def test_a_stratum_thinned_by_attrition_warns_at_run_time(tmp_path, capsys, monkeypatch):
    """The gap validate cannot see. `W-STATS-REPORTBY-THIN` counts *resolved*
    units from the roster; attrition happens during the run, so a level that
    looked fine can complete on a handful. `reference.md` § What study add
    redacts is explicit that a per-subgroup result over a handful of units is
    exactly what no automatic rule can judge safe — so it is disclosed where it
    is first knowable."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_ONE_COHORT_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        limits={"min_reported_n": 10},
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-STRATUM-THIN" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    by = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["by"]
    # The thin level still gets a block: that the subgroup produced almost
    # nothing IS the finding, and dropping it would hide what the warning names.
    assert by["cohort"]["a"]["pred"]["n"]["completed"] < 10
```

`_SKIP_ONE_COHORT_STEP` is a new fixture that calls `io.skip` on most of one cohort so that level completes thin while the other does not:

```python
_SKIP_ONE_COHORT_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # Cohort `a` all but disappears through `io.skip`, so its level is thin
        # only AFTER the run — the case a roster-time count cannot predict.
        kept = 0
        for unit in io.units:
            if unit.attributes["cohort"] == "a" and kept >= 3:
                io.skip(unit.key, "outside the eligibility window")
                continue
            if unit.attributes["cohort"] == "a":
                kept += 1
            io.record(unit.key, {{"pred": float(len(unit.key))}})
        return {{"n_units": len(io.units)}}
'''
```

The doubled braces are required — `run_a_project` formats these fixtures with `.format(pkg=...)`.

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_cli.py -k thinned_by_attrition -v`
Expected: FAIL — no such identifier is emitted.

- [ ] **Step 3: Implement**

Inside Task 5's level loop, after `level_summary` is computed:

```python
                            floor = (doc.get("limits") or {}).get("min_reported_n")
                            completed = level_counts.get("completed", 0)
                            if (
                                isinstance(floor, (int, float))
                                and not isinstance(floor, bool)
                                and completed < floor
                            ):
                                aggregate_c.warn(
                                    "W-STATS-STRATUM-THIN",
                                    "limits.min_reported_n",
                                    f"condition {cond.index}, step {step_name!r}: "
                                    f"level `{level}` of `{attribute}` completed "
                                    f"{completed} units, below limits.min_reported_n "
                                    f"({floor})",
                                )
```

The `isinstance`/`bool` pair is the same guard Task 4 uses and exists for the same reason.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the test discriminates**

| Mutation | Must fail |
|---|---|
| `completed = level_counts.get("resolved", 0)` | the attrition test — resolved is 20, above the floor, so nothing warns |
| Drop the `< floor` comparison and always warn | add an assertion to Task 5's first test that `W-STATS-STRATUM-THIN` is **absent** when every level is thick, then run this mutation against it |

- [ ] **Step 6: Record the new identifier**

`W-STATS-STRATUM-THIN` is in no document. Append a `docs/superpowers/spec-defects.md` entry: which `reference.md` sentence it extends, that the documented validate-time warning counts resolved units and therefore cannot see attrition, and that `W-STATS-CONTRAST-THIN` already warns at run time for the same reason.

- [ ] **Step 7: Commit**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "Warn when attrition leaves a stratum thin"
```

---

### Task 7: The acceptance test

**Files:**
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing importable. This task should need **zero** `src/` changes; if it needs one, an earlier task left a gap and that is the finding, not a step.

- [ ] **Step 1: Write the end-to-end tests**

```python
def test_a_derived_metric_is_stratified_with_its_own_resample(
    tmp_path, capsys, monkeypatch
):
    """A derived metric has no per-unit value, so its stratum interval is
    `aggregate` recomputed on that level's resampled table — the same
    construction the parent block uses, over fewer rows. A stratum reusing the
    parent's interval, or reporting none, both look plausible in the record."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {"score": sum(units.pred) / len(units)},
    )
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    parent = step_block["score"]
    level = step_block["by"]["cohort"]["a"]["score"]
    assert level["basis"] == "units"
    assert level["ci95"] is not None
    assert level["ci95"] != parent["ci95"]
    assert level["value"] != parent["value"]


def test_a_stratum_carries_no_corrected_fields(tmp_path, capsys, monkeypatch):
    """Strata are not comparisons, so nothing in a `by` block is corrected — and
    the four correction fields must be absent rather than null, the same
    distinction `correction: none` observes."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    for condition in run["results"]["conditions"]:
        for level in condition["aggregated"]["step01_summarize_units"]["by"]["cohort"].values():
            for entry in level.values():
                assert {"ci95_corrected", "correction_level", "family_size", "family"}.isdisjoint(entry)


def test_report_by_adds_no_executions(tmp_path, capsys, monkeypatch):
    """`reference.md` § Reporting strata's first property: "No executions are
    added — the run is unchanged and the split happens over a table that already
    exists." The ledger is the ground truth for what ran."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    without = run_a_project(tmp_path / "a", capsys=capsys, units=40)
    with_strata = run_a_project(
        tmp_path / "b",
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    assert without["results"] == with_strata["results"]
```

- [ ] **Step 2: Run them**

Run: `uv run pytest tests/test_cli.py -k "stratified_with_its_own or carries_no_corrected or adds_no_executions" -v`
Expected: PASS with no `src/` change. If one fails, fix the **source** gap it found and say which earlier task should have covered it.

- [ ] **Step 3: Run the whole gate**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py
git commit -m "Stratify a run end to end"
```

---

## After the last task

- [ ] Re-read the design's § Scope and confirm every In row landed and no Out row (the `aggregate` table's attributes, non-numeric columns, the string collapse rule) was touched.
- [ ] Confirm `docs/superpowers/spec-defects.md` carries entries for `E-STATS-REPORTBY-UNKNOWN` and `W-STATS-STRATUM-THIN`, and that the S4c-era entry assigning `report_by` to a later slice is marked resolved.
- [ ] Run the **whole-branch review** over `merge-base(main, HEAD)..HEAD` on the most capable model available. It has found a Critical on every slice but the last, and S4c's own fix wave corrected the review twice. Do not merge without it.
