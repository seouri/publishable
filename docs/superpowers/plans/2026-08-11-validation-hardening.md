# H1 Validation Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `publishable validate` reports every fault it can find and never dies, over a config schema that is actually closed — and every identifier it emits has a seat in the documents.

**Architecture:** A new pure module `src/publishable/envelope.py` holds a declarative leaf-type schema and a checker; it subsumes `validate.py`'s `_check_shape` rather than sitting beside it, and stops at `parameters`, where `parameter_spec` remains the sole authority. `docs/reference.md` § Validation gains a table naming the 72 `E-` codes `validate` surfaces. Tasks 1–4 and 9–12 touch `src/`; tasks 5–8 touch documents and the ledger.

**Tech Stack:** Python 3.12, `uv`, pytest, ruff, mypy. Markdown for the four documents.

## Global Constraints

- **The four documents are `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`.** They are **normative and lead the code**: a document statement describing behaviour the code lacks is a defect, and so is code breaking a documented promise.
- **`validate` collects findings and never raises.** This is the contract the whole slice serves. No task may introduce a path where `validate_config` propagates an exception.
- **`parameter_spec` is the single source of truth for `parameters.*`.** The envelope stops there. A second authority over those keys is the defaults-file problem and is forbidden.
- **No pinned worked-example figure may change**, anywhere: `cohort-pilot`, r = 0.581 / 0.607 / 0.412 with intervals [0.488, 0.661] / [0.517, 0.683] / [0.347, 0.477], delta 0.026 with paired ci95 [−0.007, 0.059], kendall −0.169 [−0.213, −0.125], 240 resolved / 228 completed / 12 failed, `repeat_spread` std 0.014, `cohens_d: null`, hash prefixes `8e21` / `1a2b` / `3d8a` / `6b1f`.
- **Every `E-`/`W-` identifier the code emits needs a test producing it.** This is why the 42 blocked checks are out of scope rather than stubbed.
- **Identifiers are grepped before being minted.** Check every new code against all four documents and all of `src/` first. A prior slice asserted three codes were unnamed and two already existed.
- **`docs/superpowers/` is gitignored.** A task whose only output lands there produces an empty `git diff` — expected, not a failure.
- `×` not `x` for multiplication. Hyphen never an en dash in anything becoming a filename or anchor. Cite another file by section, never by line number. No trailing whitespace, no tabs.
- Commands: tests `uv run pytest`, lint `uv run ruff check .`, format `uv run ruff format .`, types `uv run mypy`. The suite is at **905 passing**; ruff and mypy are clean and must stay so. (`ruff format --check` reports 38 files unformatted on `main` — pre-existing, do not reformat.)

## Out of scope, with owners

Do not implement these. Each is a check over a block currently refused wholesale by an `-UNSUPPORTED` code, so no config can reach the state it describes:

| Count | Blocked on |
|---|---|
| 25 | **H3 Units** — `allocation`, `assign`, `holdout`, `folds`, `cluster_by`, `weight_by`, `measurements`, resolvers |
| 7 | **H7 Plugins** — the four registries, entry-point resolution |
| 6 | **H2 Sweeps** — `ablate`, `groups`, `paired`, `sample`, per-cell baseline |
| 4 | **H4 Statistics** — `resample`, `null_test` |

Also out of scope: **diagnostic ordering** (settled — § Exit codes now argues for grouping by check, and the spine's charter line was amended to drop it), and the **`E-SWEEP-BASELINE-PARTIAL` question**, which belongs to H2 and rests on a citation this plan's spec shows to be fabricated.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `src/publishable/envelope.py` | **New, pure.** The declarative config-envelope schema and its checker | Created in task 1 |
| `src/publishable/validate.py` | Collects findings, never raises | `_check_shape` replaced by an `envelope` call; unknown-key closure; `compare` grammar check; 2 missing checks; 7 partials |
| `tests/test_envelope.py` | **New.** Unit tests for the schema and checker | Created in task 1 |
| `tests/test_validate.py` | End-to-end `validate_config` behaviour | Failure-mode tests, closure tests, new checks |
| `docs/reference.md` | Normative | § Validation gains the `E-` registry table; § Pre-registration gains `compare`'s grammar |
| `docs/superpowers/spec-defects.md` | The ledger (gitignored) | Fifteen entries amended to name the new registry home |

---

## Task 1: `envelope.py` — the declarative schema and its checker

**Files:**
- Create: `src/publishable/envelope.py`
- Test: `tests/test_envelope.py`

**Interfaces:**
- Consumes: nothing
- Produces: `LEAF_TYPES: dict[str, type | tuple[type, ...]]` keyed by dotted path; `check_envelope(doc: dict[str, Any]) -> list[tuple[str, str, str]]` returning `(code, field, message)` triples. `validate.py` (task 2) converts each triple into a `Collector` finding. Returning triples rather than taking a `Collector` is what keeps this module pure and unit-testable without constructing one.

**This module is pure:** no filesystem, no imports of `config`, `artifacts`, `runner`, `cli`, or `validate`. It matches `contrasts.py`, `correction.py`, `strata.py` and `hypotheses.py`.

**The schema stops at `parameters`.** `parameter_spec` is the sole authority for `parameters.*`; the envelope must not declare a single key beneath it.

- [ ] **Step 1: Read the authoritative field set before writing the table**

`docs/reference.md` § The one config file is the complete config schema. Read it, and cross-check against a materialized config:

```bash
grep -n "^## The one config file" -A 140 docs/reference.md | head -150
```

The leaves a materialized `generic` config actually carries, with their types, are:

```
schema_version str · experiment_type str · template_version str · plugin str|None · entrypoint str
metadata.name str · metadata.description str · metadata.authors list · metadata.institution str
data.input_dir str · data.output_dir str · data.input_manifest_policy str
data.units.from str · data.units.key str · data.units.attributes list
data.units.allocation str · data.units.cluster_by str|None · data.units.weight_by str|None
data.units.measurements str|None · data.units.holdout str|None
replication.repeats list · replication.order str · replication.rationale str
statistics.correction str
limits.max_executions int · limits.max_failed_fraction float · limits.max_ineligible_fraction float
limits.min_units_per_cell int · limits.min_clusters int · limits.min_reported_n int
hypotheses list
```

§ The one config file also documents optional blocks a materialized file omits — `sweep`'s modes, `statistics.contrasts` / `.resample` / `.null_test` / `.report_by`, `data.units.assign` / `.folds`. Declare types for every leaf that section documents, not only the materialized ones.

- [ ] **Step 2: Write the failing tests**

```python
def test_a_wrong_typed_scalar_leaf_is_reported() -> None:
    findings = check_envelope({"metadata": {"name": ["a", "b"]}})

    assert [(f[0], f[1]) for f in findings] == [("E-CONFIG-TYPE", "metadata.name")]


def test_a_numeric_string_is_refused_rather_than_coerced() -> None:
    """`n: "5"` is a typo YAML can express, and silent coercion is how
    `limits.max_executions: "5"` skips its budget check today."""
    findings = check_envelope({"limits": {"max_executions": "5"}})

    assert [f[1] for f in findings] == ["limits.max_executions"]


def test_a_well_typed_config_reports_nothing() -> None:
    doc = {
        "schema_version": "1.0",
        "metadata": {"name": "cohort-pilot", "authors": ["a"]},
        "data": {"input_dir": "/in", "output_dir": "/out"},
        "limits": {"max_executions": 15, "max_failed_fraction": 0.1},
    }

    assert check_envelope(doc) == []


def test_the_envelope_declares_nothing_under_parameters() -> None:
    """`parameter_spec` is the single source of truth there. A second authority
    over the same keys is the defaults-file problem."""
    assert not [path for path in LEAF_TYPES if path == "parameters" or path.startswith("parameters.")]


def test_a_parameters_leaf_of_any_type_is_left_alone() -> None:
    assert check_envelope({"parameters": {"analysis": {"method": ["not", "a", "string"]}}}) == []


def test_an_absent_leaf_is_not_a_finding() -> None:
    """An absent key is a missing-key question its own check owns, and a
    `null` is treated as absent, matching the rest of validate."""
    assert check_envelope({"metadata": {}}) == []
    assert check_envelope({"metadata": {"name": None}}) == []


def test_a_bool_is_not_accepted_where_an_int_is_declared() -> None:
    """`bool` is a subclass of `int` in Python, so a naive isinstance passes
    `max_executions: true` — which is not a budget."""
    findings = check_envelope({"limits": {"max_executions": True}})

    assert [f[1] for f in findings] == ["limits.max_executions"]
```

- [ ] **Step 3: Run them and watch them fail**

Run: `uv run pytest tests/test_envelope.py -v`
Expected: **FAIL** — `ModuleNotFoundError: No module named 'publishable.envelope'`.

- [ ] **Step 4: Write the module**

```python
# src/publishable/envelope.py
"""The config envelope's leaf types. See docs/reference.md § Validation.

Declarative rather than a hundred hand-written guards, for the same reason
`parameter_spec` is declarative: a table can be read against § The one config
file, and scattered `isinstance` calls cannot. The table stops at `parameters`,
where `parameter_spec` is the single source of truth — a second authority over
those keys is the defaults-file problem in another costume.

Pure: this module returns findings and never raises, and imports nothing from
`config`, `artifacts`, `runner`, `cli` or `validate`.
"""

from typing import Any

# `bool` is deliberately absent from every numeric entry: it is a subclass of
# `int`, so listing `int` alone would accept `max_executions: true`, which is
# not a budget. `_is_type` special-cases it.
LEAF_TYPES: dict[str, type | tuple[type, ...]] = {
    "schema_version": str,
    "experiment_type": str,
    "template_version": str,
    "plugin": str,
    "entrypoint": str,
    "metadata.name": str,
    "metadata.description": str,
    "metadata.authors": list,
    "metadata.institution": str,
    "data.input_dir": str,
    "data.output_dir": str,
    "data.input_manifest_policy": str,
    "data.units.from": (str, dict),
    "data.units.key": str,
    "data.units.attributes": list,
    "data.units.allocation": str,
    "data.units.cluster_by": str,
    "data.units.weight_by": str,
    "data.units.measurements": str,
    "data.units.holdout": (str, float, int),
    "replication.repeats": list,
    "replication.order": str,
    "replication.rationale": str,
    "statistics.correction": str,
    "limits.max_executions": int,
    "limits.max_failed_fraction": float,
    "limits.max_ineligible_fraction": float,
    "limits.min_units_per_cell": int,
    "limits.min_clusters": int,
    "limits.min_reported_n": int,
    "hypotheses": list,
}

_LABEL = {str: "a string", int: "an integer", float: "a number", list: "a list", dict: "a mapping"}


def _label(expected: type | tuple[type, ...]) -> str:
    if isinstance(expected, tuple):
        return " or ".join(_LABEL[t] for t in expected)
    return _LABEL[expected]


def _is_type(value: Any, expected: type | tuple[type, ...]) -> bool:
    allowed = expected if isinstance(expected, tuple) else (expected,)
    # A `bool` satisfies only an explicit `bool` declaration. Python makes
    # `isinstance(True, int)` true, and a budget of `true` is not a budget.
    if isinstance(value, bool):
        return bool in allowed
    # An `int` satisfies a `float` declaration: `confidence: 1` is the number
    # one, not a type error, and YAML gives no way to write `1.0` as `1`.
    if isinstance(value, int) and float in allowed:
        return True
    return isinstance(value, allowed)


def check_envelope(doc: dict[str, Any]) -> list[tuple[str, str, str]]:
    """`(code, field, message)` per wrong-typed leaf, in table order.

    An absent leaf is not a finding — a required key absent is its own check's
    report — and a `null` is treated as absent, matching `doc.get("x") or {}`
    everywhere else in `validate`.
    """
    findings: list[tuple[str, str, str]] = []
    for path, expected in LEAF_TYPES.items():
        node: Any = doc
        for part in path.split("."):
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(part)
        if node is None:
            continue
        if not _is_type(node, expected):
            findings.append(
                (
                    "E-CONFIG-TYPE",
                    path,
                    f"is a {type(node).__name__} (`{node!r}`); expected {_label(expected)}",
                )
            )
    return findings
```

- [ ] **Step 5: Run the tests and the suite**

Run: `uv run pytest tests/test_envelope.py -v`
Expected: **PASS**, all seven.

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green, 905 + 7 passing.

- [ ] **Step 6: Mutation-test — apply, run, confirm failure, revert, confirm clean**

**Run each. Do not reason about them.** After every revert, confirm `git status --porcelain` is empty.

| Mutation | Test that must fail |
|---|---|
| Change `_is_type` to `return isinstance(value, allowed)` (drop the bool special-case) | `test_a_bool_is_not_accepted_where_an_int_is_declared` |
| Make `_is_type` return `True` unconditionally | `test_a_wrong_typed_scalar_leaf_is_reported`, `test_a_numeric_string_is_refused_rather_than_coerced` |
| Add `"parameters.analysis.method": str` to `LEAF_TYPES` | `test_the_envelope_declares_nothing_under_parameters`, `test_a_parameters_leaf_of_any_type_is_left_alone` |
| Remove the `if node is None: continue` guard | `test_an_absent_leaf_is_not_a_finding` |

- [ ] **Step 7: Commit**

```bash
git add src/publishable/envelope.py tests/test_envelope.py
git commit -m "feat: declare the config envelope's leaf types"
```

---

## Task 2: Wire the envelope into `validate`, subsuming `_check_shape`

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `check_envelope(doc) -> list[tuple[str, str, str]]` and `LEAF_TYPES` from task 1
- Produces: nothing new for later tasks; `validate_config`'s behaviour widens

**Read `_check_shape` before touching it.** It checks container shapes over 8 top-level blocks (`_MAPPING_BLOCKS`, `_LIST_BLOCKS`, `_STRING_BLOCKS`) plus hand-enumerated nested containers, reports `E-CONFIG-SHAPE`, and **returns a bool** — `validate_config` returns early when it is `False`, because every later check indexes into those blocks.

**Subsume, do not replace.** `E-CONFIG-SHAPE` and every existing `_check_shape` test must survive untouched. This task adds the leaf layer beside the container layer in one walk.

**The fatal/non-fatal split is the subtle part.** A wrong-typed *container* stays fatal — later checks index into it. A wrong-typed *leaf* must **not** be fatal: a bad `metadata.name` must not suppress a `data.input_dir` finding. Getting this backwards is the defect this task is most likely to ship.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_validate.py`, using the file's own helpers — read it first for the real fixture names:

```python
def test_a_wrong_typed_leaf_is_a_diagnostic_not_a_traceback(tmp_path: Path) -> None:
    """`validate` collects findings and never raises. Before the envelope this
    ended the process in `re.match`'s TypeError with no diagnostic at all."""
    findings = _validate_with(tmp_path, {"metadata": {"name": ["a", "b"]}})

    assert "E-CONFIG-TYPE" in [f.code for f in findings]


def test_a_wrong_typed_leaf_does_not_suppress_later_findings(tmp_path: Path) -> None:
    """A leaf fault is fatal to its field, not to the pass. A container fault
    is fatal to the pass, and that difference is the point."""
    findings = _validate_with(
        tmp_path, {"metadata": {"name": ["a", "b"]}, "data": {"input_dir": "/nonexistent"}}
    )

    codes = [f.code for f in findings]
    assert "E-CONFIG-TYPE" in codes
    assert len([c for c in codes if c != "E-CONFIG-TYPE"]) > 0


def test_a_wrong_typed_container_is_still_fatal(tmp_path: Path) -> None:
    """The existing early return, unchanged: later checks index into the block."""
    findings = _validate_with(tmp_path, {"metadata": ["not", "a", "mapping"]})

    assert "E-CONFIG-SHAPE" in [f.code for f in findings]
```

`_validate_with` is a helper you write in this task if the file has no equivalent: it writes a scaffolded config with the given keys overlaid and returns `validate_config`'s findings. Reuse the file's existing scaffolding fixtures rather than building a new project harness.

- [ ] **Step 2: Run them and watch them fail**

Run: `uv run pytest tests/test_validate.py -k "wrong_typed" -v`
Expected: the first two **FAIL** — the first with a `TypeError` escaping (pytest reports it), the second because `E-CONFIG-TYPE` does not exist. The third should already **PASS**.

- [ ] **Step 3: Wire it in**

In `validate.py`, import `check_envelope` and call it inside `_check_shape`, after the container loops and before the return:

```python
    # The leaf layer, in the same walk as the container layer above: shape and
    # type are one question asked at two depths, and two walks over one document
    # is how the two rules drift apart. Leaf faults are deliberately NOT fatal —
    # `ok` is untouched here. A wrong-typed `metadata.name` must not suppress a
    # `data.input_dir` finding, while a wrong-typed *container* must, because
    # every later check indexes into it.
    for code, field, message in check_envelope(doc):
        c.error(code, field, message)
```

- [ ] **Step 4: Run the tests and the whole suite**

Run: `uv run pytest tests/test_validate.py -v`
Expected: **PASS**, including every pre-existing `_check_shape` test unmodified.

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green.

- [ ] **Step 5: Mutation-test**

| Mutation | Test that must fail |
|---|---|
| Set `ok = False` on a leaf finding (make leaves fatal) | `test_a_wrong_typed_leaf_does_not_suppress_later_findings` |
| Remove the `check_envelope` loop | `test_a_wrong_typed_leaf_is_a_diagnostic_not_a_traceback` |
| Move the loop above the container loops and return early on any finding | both of the first two |

- [ ] **Step 6: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "fix: report a wrong-typed config leaf instead of crashing on it"
```

---

## Task 3: The silent-skip class

**Files:**
- Modify: `src/publishable/validate.py` (only if a guard must change)
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: task 2's wiring
- Produces: nothing later tasks read

**This is the task the spec calls the one to write first in spirit, because it pins the failure mode a "no traceback" test would miss.** `_check_sweep`'s budget check is guarded by `isinstance(budget, int)`, so `limits.max_executions: "5"` does not crash — the check is **skipped**, and a design that exceeds its budget validates clean. An envelope that reports the type fault and still skips the check has moved the bug, not fixed it.

- [ ] **Step 1: Write the failing test**

```python
def test_a_string_budget_is_reported_and_the_budget_check_still_runs(tmp_path: Path) -> None:
    """Two findings, not one. Before the envelope this reported neither: the
    isinstance guard skipped the budget check and nothing typed the leaf."""
    findings = _validate_with(tmp_path, {"limits": {"max_executions": "5"}})

    codes = [f.code for f in findings]
    assert "E-CONFIG-TYPE" in codes


def test_a_well_typed_budget_below_the_design_still_warns(tmp_path: Path) -> None:
    """The envelope must not have displaced the check it exposed. This is the
    test that fails if a fix reports the type fault and drops the warning."""
    findings = _validate_with(tmp_path, {"limits": {"max_executions": 1}})

    assert "W-EXEC-BUDGET" in [f.code for f in findings]
```

Read `_check_sweep`'s budget arithmetic first to pick a `max_executions` genuinely below the scaffolded design's execution count — the scaffolded `generic` config runs 1 condition × 5 seed repeats, so `1` is below it. Confirm by reading the code, not by assuming.

- [ ] **Step 2: Run and see where you stand**

Run: `uv run pytest tests/test_validate.py -k budget -v`
Expected: the first **PASSES** already (task 2 supplies `E-CONFIG-TYPE`); the second states existing behaviour and should also pass. **If the second fails, the envelope displaced the check and that is this task's bug to fix.**

- [ ] **Step 3: Prove the second test bites**

Delete the `W-EXEC-BUDGET` emit in `_check_sweep`, run `test_a_well_typed_budget_below_the_design_still_warns`, confirm it **FAILS**, revert, confirm `git status --porcelain` is empty. A test that cannot fail is worse than no test.

- [ ] **Step 4: Decide whether the `isinstance` guard stays**

With the envelope reporting the type, the guard is now belt-and-braces rather than the only defence. **Keep it** — `_check_sweep` may be reached by a caller that skips the envelope — but replace its comment with one saying so, and saying that the envelope is what reports the fault. A guard whose comment implies it is the only defence invites its own deletion.

- [ ] **Step 5: Run the suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/validate.py tests/test_validate.py
git commit -m "test: pin that a wrong-typed budget is reported and its check still runs"
```

---

## Task 4: Close the schema

**Files:**
- Modify: `src/publishable/envelope.py`, `src/publishable/validate.py`
- Test: `tests/test_envelope.py`, `tests/test_validate.py`

**Interfaces:**
- Consumes: `LEAF_TYPES` and `check_envelope` from task 1
- Produces: `check_envelope` additionally reports unknown keys

§ Validation says "the schema is closed and `validate` checks every key against it". Reproduced at `HEAD`: a top-level `sweeep:` and a `metadata.athors:` both validate clean. The closure holds for `parameters.*` (via `E-PARAM-UNKNOWN`) and `sweep`'s top-level modes (via `E-SWEEP-KEY-UNKNOWN`) and nowhere else.

**`parameters` and `sweep` are excluded from this closure** — they have their own authorities. Closing over `parameters` must break `parameter_spec`'s own tests, and that is a mutation this task runs.

- [ ] **Step 1: Grep for an existing identifier before minting one**

```bash
grep -rhoE "\bE-CONFIG-[A-Z-]+\b" src/ | sort -u
grep -rn "E-CONFIG-KEY-UNKNOWN\|E-CONFIG-UNKNOWN" src/ docs/ README.md
```

`E-CONFIG-PARSE` and `E-CONFIG-SHAPE` exist. If no unknown-key code exists, mint one and say so in your report; the plan assumes `E-CONFIG-KEY-UNKNOWN`.

- [ ] **Step 2: Write the failing tests**

```python
def test_an_unknown_top_level_key_is_reported() -> None:
    findings = check_envelope({"sweeep": {"grid": {}}})

    assert [(f[0], f[1]) for f in findings] == [("E-CONFIG-KEY-UNKNOWN", "sweeep")]


def test_an_unknown_nested_key_is_reported() -> None:
    findings = check_envelope({"metadata": {"athors": ["x"]}})

    assert [f[1] for f in findings] == ["metadata.athors"]


def test_parameters_is_exempt_from_the_closure() -> None:
    """`parameter_spec` owns that namespace and reports E-PARAM-UNKNOWN with a
    difflib hint. A second authority would double-report and could disagree."""
    assert check_envelope({"parameters": {"anything": {"at": "all"}}}) == []


def test_sweeps_modes_are_exempt_from_the_closure() -> None:
    """`_check_sweep` owns the mode list and reports E-SWEEP-KEY-UNKNOWN."""
    assert check_envelope({"sweep": {"whatever": {}}}) == []
```

Then end to end in `tests/test_validate.py`:

```python
def test_a_misspelled_key_anywhere_is_reported(tmp_path: Path) -> None:
    findings = _validate_with(tmp_path, {"sweeep": {"grid": {}}, "metadata": {"athors": ["x"]}})

    fields = [f.field for f in findings if f.code == "E-CONFIG-KEY-UNKNOWN"]
    assert "sweeep" in fields
    assert "metadata.athors" in fields
```

- [ ] **Step 3: Run and watch them fail**

Run: `uv run pytest tests/test_envelope.py tests/test_validate.py -k "unknown or exempt or misspelled" -v`
Expected: the two unknown-key tests and the end-to-end **FAIL**; the two exemption tests pass trivially.

- [ ] **Step 4: Implement the closure**

Derive the known-key set from `LEAF_TYPES`' paths plus the container prefixes they imply, and walk the doc reporting any key not in it. Skip the `parameters` and `sweep` subtrees entirely — a constant naming them, with a comment saying which authority owns each. Include a `difflib.get_close_matches` hint in the message, matching what `E-PARAM-UNKNOWN` already does for `parameters`; a misspelling the user cannot see is a misspelling they will retype.

- [ ] **Step 5: Run the tests and the suite**

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green. **If any pre-existing test fails, read it before changing it** — a test asserting a config with an extra key validates clean may be encoding the gap this task closes, or may be a legitimate optional block your `LEAF_TYPES` omits. The second case means task 1's table is incomplete, not that the test is wrong.

- [ ] **Step 6: Mutation-test**

| Mutation | Test that must fail |
|---|---|
| Stop skipping the `parameters` subtree | `test_parameters_is_exempt_from_the_closure`, and at least one `E-PARAM-UNKNOWN` test in `tests/test_validate.py` — name it in your report |
| Stop skipping the `sweep` subtree | `test_sweeps_modes_are_exempt_from_the_closure` |
| Report only top-level unknown keys | `test_an_unknown_nested_key_is_reported` |

- [ ] **Step 7: Commit**

```bash
git add src/publishable/envelope.py src/publishable/validate.py tests/
git commit -m "fix: close the config schema over every block that has no other authority"
```

---

## Task 5: § Validation gains the validate-time error registry — `E-DATA-*`, `E-UNITS-*`, `E-REPL-*`

**Files:**
- Modify: `docs/reference.md` § Validation

**Interfaces:**
- Consumes: nothing from tasks 1–4
- Produces: the table skeleton tasks 6 and 7 add rows to. **Create the section heading and the table header in this task**, so the later two only append.

`validate` surfaces 72 `E-` codes and the four documents name 8. § Errors core raises cannot hold them: it scopes itself to "exactly the run-time surface, where there is a step to raise into", and states that everything a *command* reports is a diagnostic rather than an exception. So a validate-time code is a diagnostic and belongs beside the warnings table.

**Fifteen ledger entries have proposed adding these to § Errors core raises since S1** — an unlandable fix. Task 8 amends them; do not amend them here.

- [ ] **Step 1: Enumerate the codes this task owns**

```bash
grep -hoE "\bE-(DATA|UNITS|REPL)-[A-Z0-9-]*[A-Z0-9]\b" src/publishable/validate.py | sort -u
```

Expected: about 25 (`E-DATA-*` 12, `E-UNITS-*` 1, `E-REPL-*` 12). Also check `src/publishable/replication.py` and `src/publishable/units.py` — `validate` **translates** `REPL_DECLARATION_CODES` and surfaces `resolve_units` codes, so a code a user sees from `validate` may be emitted in another module.

- [ ] **Step 2: Read each emit site and write its condition from the code**

For each identifier, read the branch that emits it. **The identifier's name is a label, not a specification.** A row stating the wrong condition is worse than a missing row — a missing row is a known gap, a wrong row is a false promise. A prior slice found two of eleven rows described the wrong branch.

- [ ] **Step 3: Add the section and the table**

Add to § Validation, after § Warnings core reports:

```markdown
### Errors `validate` reports

A validate-time error is a [diagnostic](#exit-codes-and-diagnostics), not an exception —
`validate` collects every fault it can find in one pass, and modelling each as a raise would
force it to stop at the first. [§ Errors core raises](#errors-core-raises) covers the run-time
surface, where there is a step to raise into; these are the codes a *command* reports. Each
carries a stable `E-` identifier for the same reason a raise-time code does: a message gets
clearer over time, and something pinned to the wording breaks when it does.

Each row states the condition, not the wording.

| Reported when | Code |
|---|---|
| … |  `E-…` |
```

Fill the ~25 rows this task owns, grouped by prefix. Leave the table open for tasks 6 and 7.

- [ ] **Step 4: Verify**

Every `#anchor` must resolve. Run a fence-skipping checker **with a self-test proving it can fail**:

```bash
python3 - <<'PY'
import re, pathlib, sys
text = pathlib.Path('docs/reference.md').read_text()
body = re.sub(r'```.*?```', '', text, flags=re.S)
heads = {re.sub(r'[^a-z0-9 -]', '', re.sub(r'`', '', h).lower()).replace(' ', '-')
         for h in re.findall(r'^#{2,6} (.+)$', body, re.M)}
bad = sorted({a for a in re.findall(r'\]\(#([a-z0-9-]+)\)', body) if a not in heads})
print("UNRESOLVED:", bad or "none")
print("SELF-TEST:", "ok" if "zzz-fake" not in heads else "BLIND")
sys.exit(1 if bad else 0)
PY
```

Then confirm every code you added is real:

```bash
for c in $(awk '/^### Errors `validate` reports/,0' docs/reference.md | grep -ohE "\bE-[A-Z][A-Z0-9-]*[A-Z0-9]\b" | sort -u); do
  grep -rq -- "$c" src/ || echo "DOCUMENTED BUT NOT EMITTED: $c"
done
```

Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add docs/reference.md
git commit -m "docs: open the validate-time error registry with the data and replication codes"
```

---

## Task 6: The registry's `E-SWEEP-*`, `E-STATS-*` and `E-HYPOTHESIS-*` rows

**Files:**
- Modify: `docs/reference.md` § Validation → § Errors `validate` reports

**Interfaces:**
- Consumes: task 5's table skeleton
- Produces: rows only

- [ ] **Step 1: Enumerate**

```bash
grep -hoE "\bE-(SWEEP|STATS|HYPOTHESIS)-[A-Z0-9-]*[A-Z0-9]\b" src/publishable/validate.py | sort -u
```

Expected: about 31 (`E-SWEEP-*` 10, `E-STATS-*` 10, `E-HYPOTHESIS-*` 11).

- [ ] **Step 2: Read each emit site and write its condition from the code**

Same standard as task 5: the condition comes from the branch, not the name.

**One family needs care.** The `-UNSUPPORTED` codes among these refuse features that are specified but unbuilt. The project's standing policy — recorded in the ledger — is that a `-UNSUPPORTED` code **stays out of the documents** and retires with the slice that implements its feature, because a document must not name an error for a feature it specifies as working. Count how many of your set are `-UNSUPPORTED`, exclude them, and **state the count and the policy in your report** so a reviewer does not flag them as missing rows.

- [ ] **Step 3: Append the rows, grouped by prefix**

- [ ] **Step 4: Verify**

Re-run task 5's anchor checker and its documented-but-not-emitted loop. Expected: `UNRESOLVED: none`, no output from the loop.

- [ ] **Step 5: Commit**

```bash
git add docs/reference.md
git commit -m "docs: register the sweep, statistics and hypothesis validate-time errors"
```

---

## Task 7: The registry's remaining rows, and the completeness check

**Files:**
- Modify: `docs/reference.md` § Validation → § Errors `validate` reports

**Interfaces:**
- Consumes: tasks 5 and 6
- Produces: a registry that is complete for `validate`'s surface

- [ ] **Step 1: Enumerate what is left**

```bash
comm -23 \
  <(grep -hoE "\bE-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*\b" src/publishable/validate.py | sort -u) \
  <(awk '/^### Errors `validate` reports/,0' docs/reference.md | grep -ohE "\bE-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*\b" | sort -u)
```

Expected: about 14 — `E-PARAM-*` 3, `E-TEMPLATE-*` 2, `E-NAME-*` 2, `E-ENTRYPOINT-*` 2, `E-CONFIG-*` 2 (plus task 1's and task 4's new codes), `E-META-*` 1, `E-GIT-*` 1 — minus any `-UNSUPPORTED` excluded by policy and minus any already named in § Errors core raises.

- [ ] **Step 2: Include the codes this slice itself minted**

`E-CONFIG-TYPE` (task 1) and the unknown-key code (task 4) are validate-time diagnostics and belong in this table. Verify their final names from `src/` rather than from this plan.

- [ ] **Step 3: Read each emit site, write each condition, append the rows**

- [ ] **Step 4: The completeness check both directions**

```bash
# Every code validate surfaces is documented somewhere in the four documents
comm -23 \
  <(grep -hoE "\bE-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*\b" src/publishable/validate.py | sort -u) \
  <(grep -hoE "\bE-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*\b" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md | sort -u)
```

Expected: **only `-UNSUPPORTED` codes**, per the standing policy. Any other survivor is a missing row. State the exact survivor list in your report.

Also check the reverse — nothing documented that is not emitted — with task 5's loop.

Then re-run the anchor checker with its self-test.

- [ ] **Step 5: Commit**

```bash
git add docs/reference.md
git commit -m "docs: complete the validate-time error registry"
```

---

## Task 8: Amend the fifteen ledger entries proposing the unlandable fix

**Files:**
- Modify: `docs/superpowers/spec-defects.md`

**Interfaces:**
- Consumes: tasks 5–7's registry
- Produces: a ledger with no entry proposing a fix that cannot land

**This task produces no commit** — `docs/superpowers/` is gitignored. Do not `git add` it and do not create an empty commit.

Since S1, entries have proposed adding a validate-time code to § Errors core raises. That section scopes itself to the raise-time surface and cannot accept them, so those proposals were never landable.

- [ ] **Step 1: Find them**

```bash
grep -n "Errors core raises" docs/superpowers/spec-defects.md
```

For each hit, read the entry and decide whether it proposes a **validate-time** code (this task's business) or a genuinely raise-time one (leave alone).

- [ ] **Step 2: Amend each in place**

At the entry's own heading, not as a new entry lower in the file — filing rather than amending is what made this ledger stale in the first place. Use the file's established form:

```markdown
**AMENDED 2026-08-11 (H1 Validation):** the proposed resolution — adding this to § Errors core
raises — was never landable: that section scopes itself to the run-time surface, "where there is
a step to raise into", and this is a code a *command* reports. Landed instead in
`reference.md` § Errors `validate` reports, the validate-time registry H1 created. CLOSED.
```

Where an entry is only *partly* closed by the registry, say which half closes and which stands.

- [ ] **Step 3: Verify**

```bash
grep -c "AMENDED 2026-08-11 (H1 Validation)" docs/superpowers/spec-defects.md
grep -n "Errors core raises" docs/superpowers/spec-defects.md
```

Every surviving mention must be either a raise-time code or inside an `AMENDED` block. Report the count and the survivors.

---

## Task 9: `compare`'s grammar — the sentence, then the check

**Files:**
- Modify: `docs/reference.md` § Pre-registration, `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: nothing from tasks 1–8
- Produces: nothing later tasks read

`compare: {condition: X}` with no `to:` and no `sweep.baseline` fires neither the baseline check nor the contrast check. **The user settled the ruling: refuse it.** A `compare` naming one condition with nothing to compare against names no comparison.

**The document goes first.** `reference.md` § Pre-registration states no rule for this form, and core deciding a question the document has not asked is what task 14 of the checkpoint declined to do. Per the document-leads rule, write the sentence, then the check that enforces it.

- [ ] **Step 1: Write the § Pre-registration sentence**

Declarative and reason-giving. It must say that `compare` names both sides — a condition and what it is compared against — that `to: baseline` is the ordinary spelling, that a bare `{condition: X}` with no declared baseline is refused, and *why*: a hypothesis whose comparison cannot be resolved has no quantity under test, which is the same reason `metric` is required. Do not add an implicit default; the user ruled against defaulting to the baseline.

- [ ] **Step 2: Grep before minting an identifier**

```bash
grep -rhoE "\bE-HYPOTHESIS-[A-Z-]+\b" src/ | sort -u
grep -rn "E-HYPOTHESIS" docs/reference.md
```

An existing `E-HYPOTHESIS-*` code may already fit. Prefer reusing one whose condition genuinely covers this form over minting a second code for one condition.

- [ ] **Step 3: Write the failing test**

```python
def test_a_compare_naming_a_condition_with_no_baseline_is_refused(tmp_path: Path) -> None:
    """Neither check fired before: the baseline check needs `to: baseline`, and
    the contrast check needs `compare.contrast`. This form fell between them."""
    findings = _validate_with(
        tmp_path,
        {
            "hypotheses": [
                {
                    "id": "h1",
                    "kind": "confirmatory",
                    "metric": "r",
                    "step": "step02_fit_model",
                    "direction": "greater",
                    "threshold": 0.02,
                    "compare": {"condition": "spearman"},
                }
            ]
        },
    )

    assert any(f.code.startswith("E-HYPOTHESIS-") for f in findings)
```

Read `tests/test_validate.py`'s existing hypothesis tests for the real required-field set before writing this fixture — an incomplete hypothesis would fail for the wrong reason, and a test that passes for the wrong reason is the failure mode this project keeps finding.

- [ ] **Step 4: Run, implement, run**

Run the test, confirm it **FAILS** with no `E-HYPOTHESIS-*` finding. Add the check to `validate.py`'s hypothesis checks. Re-run: **PASS**.

Then confirm the well-formed cases still pass:

```bash
uv run pytest tests/test_validate.py -k hypothes -v
```

- [ ] **Step 5: Mutation-test**

| Mutation | Test that must fail |
|---|---|
| Remove the new check | the new test |
| Fire it also when `to: baseline` is present | an existing well-formed-hypothesis test — name it |
| Fire it also when `sweep.baseline` is declared | **add a test**: a bare `{condition: X}` *with* a declared baseline, which the ruling does not refuse |

The third mutation needs a test the plan does not give you. Write it: the refusal is for the form with **no** baseline, so a declared baseline must make the same `compare` acceptable.

- [ ] **Step 6: Suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add docs/reference.md src/publishable/validate.py tests/test_validate.py
git commit -m "feat: state and enforce compare's grammar for a bare condition"
```

---

## Task 10: The two buildable-now missing checks

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: nothing from tasks 1–9
- Produces: nothing later tasks read

Two rows of § Validation state checks nothing performs, and unlike the other 42 they are buildable today.

**Row 271 — "baseline leaves contrasts confounded".** `confounded` is computed only at run time (`cli.py`, `differs_on > 1`). A ≥2-axis `grid` with a fully-fixed `baseline` is a supported design today, so the warning is writable against `expand(doc)` alone. It has **no `W-` identifier yet** — grep before minting, then add it to § Warnings core reports in this task, since that table is the complete set.

**Row 276 — "contrast stratum is populated".** `W-STATS-CONTRAST-THIN` exists but fires only at run time over `n_paired`. § Validation lists it as a validate-time check against the roster — the same split `W-STATS-REPORTBY-THIN` / `W-STATS-STRATUM-THIN` already draws for `report_by`.

- [ ] **Step 1: Read both rows in § Validation and both existing run-time emit sites**

The document is normative: implement what the row states, not what seems reasonable. If the row and the run-time behaviour disagree about the condition, say so in your report — that is a document decision, not yours to make silently.

- [ ] **Step 2: Write the failing tests, one per row**

For row 271: a config with a 2-axis `grid` and a `baseline` fixing both axes, asserting the new warning appears. For row 276: a config declaring a `statistics.contrasts` entry with a `within` whose stratum the roster cannot populate, asserting `W-STATS-CONTRAST-THIN` at validate time.

Both need a roster, so reuse `tests/test_validate.py`'s existing unit-table fixtures — read the file for how it builds an `index.csv`.

- [ ] **Step 3: Run, implement, run** — each test must fail first for the stated reason.

- [ ] **Step 4: Mutation-test each**

For each new check: remove it and confirm its test fails; then invert its threshold comparison and confirm the test still fails. A threshold check that passes with the comparison inverted is testing nothing.

- [ ] **Step 5: Suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/validate.py docs/reference.md tests/test_validate.py
git commit -m "feat: add the two validate-time checks the document states and code lacked"
```

---

## Task 11: The seven partials

**Files:**
- Modify: `src/publishable/validate.py`, `src/publishable/replication.py`, `src/publishable/units.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: tasks 1–4's envelope (two of the seven are envelope consequences and may already be closed)
- Produces: nothing later tasks read

Seven checks are implemented narrower or broader than their § Validation row states. The full classification is in `docs/superpowers/H1-SCOPING.md` — read it, then verify each against the code yourself before changing anything, because that file is a measurement and not all of its claims were independently confirmed.

| Row | The divergence |
|---|---|
| 205 Types | No leaf outside `parameters` had a declared type — **tasks 1–4 should have closed this.** Confirm, and if so record it closed rather than editing anything |
| 208 Unknown keys | Closure held only for `parameters.*` and `sweep`'s modes — **task 4 should have closed this.** Confirm |
| 211 Template is installed | The row's `plugin`-field hint is absent. **H7 owns the registry** — record and route, do not implement |
| 212 Template version moved | Compares against the module constant `materialize.TEMPLATE_VERSION`, not the installed template's own reported version; `BaseTemplate` declares no `version`. The row's "`request.timeout` is new and unset" half is not reported at all |
| 225 Batch takes no fields | `E-REPL-LEVEL-FIELD` refuses only `k` on a non-fold level. The row says `n` is the only field a `batch` accepts — `{kind: batch, n: 5, stratify_by: x}` is accepted silently |
| 244 Attributes have a source | `E-UNITS-ATTR-MISSING` covers the *table* source only. The row's own example is the **glob** source, and `_from_glob` builds every `Unit` with `attributes={}` without reading the declaration — so `from: {glob: "*.dcm"}` with declared attributes validates clean and yields empty attributes |
| 284 Correction can be applied | `W-STATS-CORRECTION-INAPPLICABLE` fires whenever `correction == "fdr_bh"` and the family is non-empty; it never tests whether `null_test` is declared. Correct by accident today because `null_test` is refused — **becomes over-broad the moment H4 lands** |

- [ ] **Step 1: Triage all seven before editing**

For each, write down: is it closed by tasks 1–4, implementable now, or owned by another slice? **Rows 211 and 284 are the ones to be careful with** — 211 needs H7's registry, and 284's correct-by-accident status means narrowing it now requires reasoning about a feature that does not exist. Recording either as routed is a legitimate outcome; silently implementing half of one is not.

- [ ] **Step 2: For each you implement, write its failing test first**

Each test must fail for the stated reason before the fix. Use the exact divergence from the table above as the test's premise — e.g. for 225, `{kind: batch, n: 5, stratify_by: x}` must produce a finding.

- [ ] **Step 3: For each you route, record it**

Append a `docs/superpowers/spec-defects.md` entry naming the row, the divergence, and the owning slice from the spine's table. That directory is gitignored, so this produces no diff.

- [ ] **Step 4: Mutation-test every check you changed** — remove it, confirm its test fails, revert, confirm the tree is clean.

- [ ] **Step 5: Suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/ tests/
git commit -m "fix: narrow the validation checks that diverged from their documented rule"
```

---

## Task 12: The import-path residual, and the consistency passes

**Files:**
- Modify: whichever of the four documents the passes find defects in
- Read: all four documents, `CLAUDE.md`

**Interfaces:**
- Consumes: every task above
- Produces: the slice's exit criterion

- [ ] **Step 1: The import-path residual**

A bare `BaseException` subclass raised at a user package's module scope still escapes `validate`'s catch. A prior review judged this acceptable — catching `KeyboardInterrupt` would break Ctrl-C, and no stdlib type raises `BaseException` directly at import. **Confirm that judgement still holds** and record it as a closed decision in the ledger rather than changing the code, unless you find a reachable case.

- [ ] **Step 2: Add `envelope.py` to § Package layout**

Task 1 created a module, and `docs/reference.md` § Package layout's fenced tree is a map of core's
own source. The S5 checkpoint spent a whole task adding six built modules that had accumulated
there unlisted — do not start a seventh backlog. Insert it in the tree's existing ordering, with a
`#` comment in the style of its neighbours, beside `validate.py` since that is its only caller:

```
│   ├── envelope.py            # the config envelope's leaf types and the closed-schema walk
```

- [ ] **Step 3: The mechanical pass**

Write throwaway checks — `CLAUDE.md` is explicit that this repo keeps no checker. Skip fenced code blocks in all of them: the documents contain markdown inside markdown. Check that every relative link and `#anchor` resolves, no two headings in a file produce the same anchor, every table row matches its header's column count, and no line carries trailing whitespace, a tab, or invisible unicode. **Include a self-test proving each check can fail** — a prior slice found a supplied checker that could not fail, and reported a clean pass from it.

- [ ] **Step 4: The cross-document pass**

`CLAUDE.md` names seven drift classes; none is visible to a script. The ones this slice most plausibly disturbed:

| Class | Why this slice touches it |
|---|---|
| Config completeness | Task 1's `LEAF_TYPES` is a second enumeration of the config's fields. Every leaf it declares must exist in § The one config file, and vice versa — a leaf in one and not the other is this class exactly |
| Schema fields in prose | Tasks 5–7 added ~70 rows naming fields and conditions |
| Enum comments | An inline `# a \| b \| c` must list every value its table defines; task 9 and task 10 may have added values |
| Prevented mistakes | `experimental-designs.md` § Mistakes core prevents must stay structurally impossible in the schema. Task 4's closure and task 9's refusal both strengthen that — confirm neither weakened it |

- [ ] **Step 5: Reconcile `LEAF_TYPES` against § The one config file, both directions**

This is the check most likely to find something:

```bash
uv run python - <<'PY'
from publishable.envelope import LEAF_TYPES
import re, pathlib
sec = pathlib.Path('docs/reference.md').read_text().split('## The one config file')[1].split('\n## ')[0]
missing = [p for p in LEAF_TYPES if p.split('.')[-1] not in sec]
print("declared in LEAF_TYPES, absent from § The one config file:", missing or "none")
PY
```

A survivor is either a field the document forgot or a key the envelope invented. Both are defects; say which.

- [ ] **Step 6: Fix what the passes find, then confirm and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add -A README.md CLAUDE.md docs/
git commit -m "docs: consistency passes over the validation hardening"
```

If every check came back clean and no file changed, **do not create an empty commit** — report that plainly. A clean result is a real result.

---

## Sequencing

Task 1 → 2 → 3 → 4 (the envelope, in order — each builds on the last), then 5 → 6 → 7 → 8 (the registry, sequenced because they land in one table), then 9, 10, 11 in any order, then 12 last.

Tasks 5–8 touch only documents and the ledger; tasks 1–4 and 9–11 touch only code and tests. The two groups cannot conflict, but they are sequenced rather than parallel because a merge conflict in `reference.md` costs more than the serialization saves.

Task 8 and any step writing only to `docs/superpowers/` produce **no commit** — that directory is gitignored, and an empty `git diff` there is the expected outcome.
