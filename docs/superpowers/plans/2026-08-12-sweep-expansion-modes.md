# H2 Sweep Expansion Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `expand()` becomes a product over axis-shaped modes; `paired`, `sample` and `ablate` execute; and a baseline expands over the axes it does not fix — the design `reference.md` tells a user to prefer and this build refuses.

**Architecture:** `src/publishable/sweep.py` stays pure and gains a two-phase `expand()`: build an axis list from every axis-shaped mode present, take the product, then apply the non-multiplying modes (`ablate`, and the baseline's expansion over unfixed axes). `label_for` loses its `grid` parameter — it has exactly one caller, inside `expand()`. `validate.py` gains four checks and retires three `-UNSUPPORTED` codes.

**Tech Stack:** Python 3.12, `uv`, pytest, ruff, mypy. Markdown for the four documents.

## Global Constraints

- **The four documents are `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`.** They are **normative and lead the code**. `docs/reference.md` § Expansion modes is this slice's specification; read it before writing any mode.
- **`sweep.py` is pure and stays pure:** a config dict in, an ordered condition list out. No filesystem, no `Config`, no git, no imports of `config`/`artifacts`/`runner`/`cli`/`validate`. Its only import today is `publishable.errors`.
- **`groups` stays refused.** `E-SWEEP-GROUPS-UNSUPPORTED` must still fire at the end of this slice. A group level is a set of units, and the assignment that makes it one belongs to H3 Units; a `groups` axis that expanded conditions while handing each the same roster would report two identical measurements as two arms.
- **No pinned worked-example figure may change**, anywhere: `cohort-pilot`, r = 0.581 / 0.607 / 0.412 with intervals [0.488, 0.661] / [0.517, 0.683] / [0.347, 0.477], delta 0.026 with ci95 [−0.007, 0.059], kendall −0.169 [−0.213, −0.125], 240 resolved / 228 completed / 12 failed, `repeat_spread` std 0.014, `cohens_d: null`, hashes `8e21` / `1a2b` / `3d8a` / `6b1f`, run IDs `run_2026-08-06T14-02-11Z_8e21ab3` and `run_2026-08-07T09-14-03Z_8e21ab3`. `cohort-pilot`'s baseline fixes `analysis.method`, the only axis it sweeps, so it stays a one-baseline design — **verify that rather than assuming it**.
- **Any sentence describing how modes compose is checked against the product loop, not against the mode being added.** H1's dominant defect — nine occurrences — was a claim true only under an unstated condition, and every one lived in prose summarising rows rather than in the rows themselves.
- **Every `E-`/`W-` identifier the code emits needs a test producing it**, and a retired identifier needs its registry row removed. `docs/reference.md` § Validation's error table holds 60 rows and § Warnings core reports holds 18; both are complete sets, so a mint without a row or a retirement without a removal breaks that.
- **Identifiers are grepped before being minted.** Check all four documents and all of `src/` first.
- **`docs/superpowers/` is gitignored.** A task whose only output lands there produces an empty `git diff` — expected, not a failure.
- **Do not amend a reviewed commit.** Stack a new one; amending orphans the object the review was performed against.
- `×` not `x` for multiplication. Hyphen never an en dash in anything becoming a filename or anchor. Cite another file by section, never by line number. No trailing whitespace, no tabs.
- Commands: tests `uv run pytest`, lint `uv run ruff check .`, types `uv run mypy`. The suite is at **955 passing**; ruff and mypy are clean and must stay so. **Do not run `ruff format`** — 38 files are unformatted on `main`, pre-existing.

## The composition matrix

Every task below implements part of this. It is `reference.md` § Expansion modes, restated once so no task re-derives it:

| Rule | Lands in |
|---|---|
| The condition set is the **product** of every axis-shaped mode present — `grid`, `paired`, `sample`, `groups` | Task 1 |
| `ablate` does **not** multiply: `n` conditions, each one change from the baseline, **reading** the baseline rather than re-emitting it | Task 7 |
| `ablate` **requires** `sweep.baseline` | Task 8 |
| `ablate ×` any **parameter** mode is **rejected** | Task 8 |
| `ablate × groups` is **permitted**, `(1 + n)` per level | **H3** — untestable while `groups` is refused |
| `sweep.baseline` may not fix a group level while `ablate` is declared | **H3** |
| A baseline fixing **every** axis → one condition `00`; fixing **some** → **one per cell of the unfixed axes** | Task 10 |
| Baseline conditions are references, not comparisons: six conditions under two per-arm baselines are **four** comparisons | Task 12 |

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `src/publishable/sweep.py` | **Pure.** Config in, ordered conditions out | Two-phase `expand()`; `label_for` drops `grid`; `paired`/`sample`/`ablate` axes; per-cell baselines |
| `src/publishable/validate.py` | Collects findings, never raises | Three `-UNSUPPORTED` retirements; four new checks; `E-SWEEP-BASELINE-PARTIAL` retirement |
| `tests/test_sweep.py` | `expand`, labels, modes | The oracle for task 1; new cases per mode |
| `tests/test_validate.py` | End-to-end `validate_config` | The four new checks |
| `docs/reference.md` | Normative | Registry rows retired; `W-SWEEP-BASELINE-CONFOUNDED`'s row re-read |

---

## Task 1: `expand()` as a product over axes

**Files:**
- Modify: `src/publishable/sweep.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: nothing
- Produces: `_axes(sweep: dict) -> list[list[dict[str, Any]]]` returning one entry per axis-shaped mode, each a list of `{path: value}` cells. `expand()` keeps its signature `(config: dict) -> list[Condition]`. Later tasks add axes to `_axes`, not to `expand`.

**This is a pure refactor. No new mode, no behaviour change.** The existing `tests/test_sweep.py` is the oracle: it must pass **untouched**. If you find yourself editing an existing test to make it pass, stop — that is the signal you changed behaviour you were meant to preserve, and it belongs in your report instead.

- [ ] **Step 1: Read the current `expand()` and write down what it does**

```bash
sed -n '137,168p' src/publishable/sweep.py
```

It prepends a baseline row when `sweep.baseline` is truthy, then runs `itertools.product` over `grid`'s values, then builds `Condition`s with `enumerate`. Note the comment on `itertools.product`: it varies the **last** argument fastest, which is the declared-order nesting the specification asks for. That property must survive.

- [ ] **Step 2: Write the characterisation test**

Add to `tests/test_sweep.py` — this pins the property the refactor must not break, and it should pass before and after:

```python
def test_grid_axes_vary_the_last_declared_axis_fastest() -> None:
    """`itertools.product` varies its last argument fastest, which is the
    declared-order nesting § Expansion modes asks for. The refactor moves this
    loop, so pin the order it produces before moving it."""
    conditions = expand(
        {"sweep": {"grid": {"a.x": [1, 2], "b.y": ["p", "q"]}}}
    )

    assert [dict(c.values) for c in conditions] == [
        {"a.x": 1, "b.y": "p"},
        {"a.x": 1, "b.y": "q"},
        {"a.x": 2, "b.y": "p"},
        {"a.x": 2, "b.y": "q"},
    ]
```

- [ ] **Step 3: Run it and the whole sweep suite**

Run: `uv run pytest tests/test_sweep.py -v`
Expected: **PASS**, including the new test. This is the baseline you must not move.

- [ ] **Step 4: Restructure**

Replace `expand`'s body with two phases. `_axes` builds the axis list; `expand` takes the product and applies the baseline:

```python
def _axes(sweep: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """One entry per axis-shaped mode present, each a list of `{path: value}` cells.

    The product of these is the condition set. `grid` contributes one axis per
    key; later modes contribute one axis each, whose cells may set several paths
    at once. Keeping every mode in this one list is what makes the composition
    rule — "the product of every axis-shaped mode present" — a property of the
    structure rather than a sentence someone has to remember.
    """
    axes: list[list[dict[str, Any]]] = []
    for path, values in (sweep.get("grid") or {}).items():
        axes.append([{path: value} for value in values])
    return axes


def expand(config: dict[str, Any]) -> list[Condition]:
    """Ordered conditions: a declared baseline as 00, then the product of every axis.

    With no `sweep` block, one condition whose label is None — which is what
    keeps the `conditions/` level out of the artifact tree.
    """
    sweep = config.get("sweep") or {}
    if not sweep:
        return [Condition(index=0, label=None, values={}, is_baseline=False)]

    rows: list[tuple[dict[str, Any], bool]] = []
    baseline = sweep.get("baseline")
    if baseline:
        rows.append((dict(baseline), True))

    axes = _axes(sweep)
    if axes:
        # `itertools.product` varies its LAST argument fastest, which is the
        # declared-order nesting the specification asks for. Preserved from the
        # grid-only implementation this replaces.
        for combo in itertools.product(*axes):
            values: dict[str, Any] = {}
            for cell in combo:
                values.update(cell)
            rows.append((values, False))

    swept = _swept_paths(sweep)
    return [
        Condition(index=i, label=label_for(values, swept, is_baseline),
                  values=values, is_baseline=is_baseline)
        for i, (values, is_baseline) in enumerate(rows)
    ]
```

- [ ] **Step 5: Change `label_for` and add `_swept_paths`**

`label_for` has exactly one caller — `expand` itself — so this signature change is contained. Verify that before editing:

```bash
grep -rn "label_for(" src/ tests/ | grep -v "def label_for" | grep -v __pycache__
```

```python
def _swept_paths(sweep: dict[str, Any]) -> list[str]:
    """Every path any axis-shaped mode sweeps, in declared order.

    `label_for` shortens these to unique suffixes, so it needs the whole set:
    a key is only unambiguous against every other swept path, not against one
    mode's. Later modes extend this and nothing else about labelling changes.
    """
    return list((sweep.get("grid") or {}))


def label_for(values: dict[str, Any], swept: list[str], is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    keys = _keys_for(swept)
    return AXIS_SEPARATOR.join(
        f"{keys.get(path, path.rsplit('.', 1)[-1])}={render_value(value)}"
        for path, value in values.items()
    )
```

- [ ] **Step 6: Run the whole suite**

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green, **955 + 1** passing, and **no existing test edited**.

```bash
git diff --stat tests/
```
Expected: only additions to `tests/test_sweep.py`.

- [ ] **Step 7: Mutation-test**

Apply each, run the named test, confirm it FAILS, revert, confirm `git status --porcelain` is empty. **Run them; do not reason about them.**

| Mutation | Test that must fail |
|---|---|
| `for combo in itertools.product(*reversed(axes))` | `test_grid_axes_vary_the_last_declared_axis_fastest` |
| `_axes` returns one axis of all values flattened, rather than one per key | the same test, plus existing grid tests |
| `_swept_paths` returns `[]` | an existing label test — name it in your report |

- [ ] **Step 8: Commit**

```bash
git add src/publishable/sweep.py tests/test_sweep.py
git commit -m "refactor: expand conditions as a product over axes"
```

---

## Task 2: `paired` joins the product

**Files:**
- Modify: `src/publishable/sweep.py`, `src/publishable/validate.py`
- Test: `tests/test_sweep.py`, `tests/test_validate.py`

**Interfaces:**
- Consumes: `_axes` and `_swept_paths` from task 1
- Produces: nothing new; `paired` becomes one axis whose cells are whole dicts

§ Expansion modes: *"When parameters must move together rather than combinatorially, a list of dicts is treated as a single axis."* Its example is `grid × paired = 2 × 2 = 4 conditions`, **not** 2×2×2.

- [ ] **Step 1: Write the failing test**

```python
def test_paired_is_one_axis_not_a_product_of_its_keys() -> None:
    """§ Expansion modes' own example: grid × paired = 2 × 2 = 4, not 2 × 2 × 2.
    A paired entry sets several paths at once and counts once."""
    conditions = expand(
        {
            "sweep": {
                "grid": {"analysis.method": ["pearson", "spearman"]},
                "paired": [
                    {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                    {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                ],
            }
        }
    )

    assert len(conditions) == 4
    assert dict(conditions[0].values) == {
        "analysis.method": "pearson",
        "analysis.min_samples": 30,
        "analysis.confidence": 0.95,
    }
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_sweep.py::test_paired_is_one_axis_not_a_product_of_its_keys -v`
Expected: **FAIL** — 2 conditions, because `_axes` ignores `paired`.

- [ ] **Step 3: Add the axis**

In `_axes`, after the grid loop:

```python
    paired = sweep.get("paired") or []
    if paired:
        # One axis, not one per key: a paired entry is a single setting that
        # happens to set several paths. Treating its keys as separate axes is
        # exactly the combinatorial reading § Expansion modes rejects.
        axes.append([dict(entry) for entry in paired])
```

And extend `_swept_paths` to include every path any paired entry names, in first-seen order.

- [ ] **Step 4: Retire the refusal**

Remove the `("paired", "E-SWEEP-PAIRED-UNSUPPORTED", …)` tuple from `validate.py`'s refusal loop, and remove `E-SWEEP-PAIRED-UNSUPPORTED`'s row from `docs/reference.md` § Validation's error table if it has one. Grep first:

```bash
grep -rn "E-SWEEP-PAIRED-UNSUPPORTED" src/ tests/ docs/ README.md
```

Standing policy keeps `-UNSUPPORTED` codes out of the four documents, so there is likely **no** row to remove — confirm, and say which in your report. There **is** a `NOT BUILT` marker in § The one config file's example if `paired` appears there; remove that too.

- [ ] **Step 5: Test that the refusal is gone**

Add to `tests/test_validate.py` a config declaring `paired` and assert `E-SWEEP-PAIRED-UNSUPPORTED` is **not** among the findings — and that the config validates cleanly otherwise.

- [ ] **Step 6: Run, mutate, commit**

Run the suite. Mutations: make `_axes` append `paired` as one axis per key (the new test must fail); make it append nothing (the same).

```bash
git add src/publishable/sweep.py src/publishable/validate.py tests/ docs/reference.md
git commit -m "feat: expand paired as a single coupled axis"
```

---

## Task 3: `sample` draws its conditions

**Files:**
- Modify: `src/publishable/sweep.py`, `src/publishable/validate.py`
- Test: `tests/test_sweep.py`, `tests/test_validate.py`

**Interfaces:**
- Consumes: `_axes` from task 1
- Produces: `sample` as one axis of realized draws

§ Expansion modes specifies `n`, `method` (`sobol | latin_hypercube | random`), `seed: auto`, and `ranges` with `uniform | int_uniform | log_uniform`. **Sampling is deterministic given its seed**, and `sweep.yaml` records both the seed and the fully realized condition list so a reader never re-derives the design and `reproduce` regenerates it.

- [ ] **Step 1: The seed derivation, already resolved — plus one consequence you must surface**

§ Expansion modes says the seed is "derived from the design digest; recorded in `sweep.yaml`". That digest is `hashes.design_digest(config)`, a **pure** function of the config dict — `hashes.py` imports only `hashlib`, `json`, `pathlib` and `typing`, and `design_digest` touches no file. So `sweep.py` may import it without breaking its own purity: `expand` remains a function of the declaration alone, which is the property its docstring promises. Do **not** add a `digest` parameter to `expand` — it has callers in `validate.py` (×7), `cli.py` (×3), `artifacts.py` (×2), `runner.py` and 23 tests, and the signature churn buys nothing.

Follow `replication.py`'s established derivation shape rather than inventing one:

```python
def _seed_for(digest: str, index: int) -> int:
    payload = f"{digest}|seed|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")
```

Use a distinct payload tag — `|sample|` rather than `|seed|` — so a sample draw and a repeat seed derived from one digest never collide.

**The consequence to surface, not to fix.** `design_digest` hashes **only** `data.units` and `sweep.groups`, deliberately: its docstring says *"so a parameter edit redraws nothing."* It ignores `sweep.sample` entirely. So two consequences follow, and both are what the document specifies:

- Editing `ranges`, `n` or `method` does **not** change the seed. The draws still change, because they are functions of those values — but the seed does not.
- A project declaring neither `data.units` nor `sweep.groups` has a digest over `{"units": null, "groups": null}` — a **constant**. Every such experiment draws the same sample.

Implement what the document says. **Then state in your report whether the second consequence is intended**, with the evidence either way. It may be correct — a sample is reproducible and nothing says draws must differ across unrelated experiments — or it may be a spec gap worth a `docs/superpowers/spec-defects.md` entry. Do not decide it silently in either direction.

- [ ] **Step 2: Write the determinism test first**

The property that matters most is that two expansions of one config agree:

```python
def test_sample_draws_are_deterministic_given_the_config() -> None:
    """§ Expansion modes: "Sampling is deterministic given its seed", and the
    seed is derived from the design digest — so one config always expands to
    the same conditions, which is what makes `reproduce` regenerate them."""
    config = {
        "sweep": {
            "sample": {
                "n": 8,
                "method": "random",
                "seed": "auto",
                "ranges": {"analysis.confidence": {"uniform": [0.80, 0.99]}},
            }
        }
    }

    first = [dict(c.values) for c in expand(config)]
    second = [dict(c.values) for c in expand(config)]

    assert first == second
    assert len(first) == 8
    assert all(0.80 <= row["analysis.confidence"] <= 0.99 for row in first)
```

- [ ] **Step 3: Run it, implement, run it**

**Implement all three methods — this is not a scope decision, it is already resolved.** `scipy>=1.11` is a declared dependency in `pyproject.toml` and `scipy.stats.qmc` provides both samplers directly: `qmc.Sobol(d=..., seed=...)` and `qmc.LatinHypercube(d=..., seed=...)`, each returning draws in the unit hypercube that you scale into the declared ranges. `random` needs only `numpy`'s generator, which the project already uses for repeat seeding. Refusing a documented method would mint an identifier and a registry row for a feature the dependency hands you.

The three `ranges` forms — `uniform`, `int_uniform`, `log_uniform` — are the scaling step, and each needs its own test: `uniform` linear in the interval, `int_uniform` integral and inclusive of both endpoints, `log_uniform` uniform in the log of the interval. Write a test asserting `sobol`'s draws differ from `random`'s on the same seed, so the method parameter is not silently ignored — a sampler whose method argument does nothing is exactly the silent-skip class H1 spent a task pinning.

- [ ] **Step 4: Record the draws in `sweep.yaml`**

`sweep_document` already writes the resolved plan. Add the seed and confirm the realized conditions are already carried — read the function and § "`sweep.yaml` — the resolved plan" before adding anything, since the conditions may already be recorded and a second copy would be the drift this project keeps finding.

- [ ] **Step 5: Retire `E-SWEEP-SAMPLE-UNSUPPORTED`**, add the "sample ranges" check § Validation states (H1's scoping row 220 — read it for the exact condition), test both, commit.

```bash
git commit -m "feat: expand sample as deterministic draws over declared ranges"
```

---

## Task 4: `ablate` emits one change at a time

**Files:**
- Modify: `src/publishable/sweep.py`, `src/publishable/validate.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: task 1's `expand`
- Produces: `ablate` applied **after** the product, not as an axis

§ Expansion modes: *"`ablate` is the one mode that does not multiply, because it isn't an axis. It emits `n` conditions, each one change away from the baseline, and it **reads** the baseline rather than re-emitting it — so a declared baseline is condition `00` exactly once, never both as `00_baseline` and as an ablate row."*

- [ ] **Step 1: Write the failing test from the document's own example**

```python
def test_ablate_emits_one_baseline_and_one_condition_per_removal() -> None:
    """§ Expansion modes: 1 + n conditions, not 2^n, and the baseline appears
    exactly once — read, not re-emitted."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {
                    "features.demographics": True,
                    "features.labs": True,
                    "features.notes": True,
                },
                "ablate": {
                    "from": "baseline",
                    "remove": ["features.demographics", "features.labs", "features.notes"],
                },
            }
        }
    )

    assert len(conditions) == 4
    assert conditions[0].is_baseline
    assert [c.is_baseline for c in conditions[1:]] == [False, False, False]
    assert dict(conditions[1].values)["features.demographics"] is False
    assert dict(conditions[1].values)["features.labs"] is True
```

`remove` sets a boolean parameter to `false` or a nullable one to `null` — read § Expansion modes for `override`, the non-boolean form, and cover it too.

- [ ] **Step 2: Run, implement, run.** `ablate` is applied after the product in `expand`, reading `sweep.baseline` rather than emitting a row of its own.

- [ ] **Step 3: Retire `E-SWEEP-ABLATE-UNSUPPORTED`**, test the retirement, commit.

---

## Task 5: `ablate`'s three composition checks

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: task 4's `ablate`
- Produces: three checks; identifiers grepped before minting

Three of H1's six blocked checks are `ablate`'s. Read each row in § Validation for its exact stated condition — **the document leads, so implement what the row says, not what seems reasonable**:

| Row | The check |
|---|---|
| 216 | Ablation targets — every `remove`/`override` path must be one the baseline fixes |
| 217 | Ablation needs a baseline — `ablate` without `sweep.baseline` is refused |
| 218 | Ablation doesn't compose with a parameter axis — `ablate ×` `grid`/`paired`/`sample` is rejected |

Row 219 (ablation baseline isn't a group level) and row 257 (axis names are distinct) **need `groups` and stay blocked** — do not implement them; confirm they are still blocked at the end.

- [ ] **Step 1: For each, grep for an existing identifier before minting one.** Prefer reusing one whose condition genuinely covers the case.
- [ ] **Step 2: Write each failing test first**, with the exact config shape the row describes.
- [ ] **Step 3: For each identifier minted, add its row** to § Validation's error table — `| Reported when | Code |`, alphabetical within family, condition written from the emit site, every gate the branch sits behind disclosed.
- [ ] **Step 4: Mutation-test each**: remove the check (its test must fail); then make it fire when the composition **is** legal (a test asserting the legal case stays clean must fail). A check that passes when inverted is testing nothing.
- [ ] **Step 5: Commit.**

---

## Task 6: The baseline expands over unfixed axes

**Files:**
- Modify: `src/publishable/sweep.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: tasks 1–4
- Produces: one baseline condition per cell of the unfixed axes

**This is the slice's central change**, and the one this build refuses with `E-SWEEP-BASELINE-PARTIAL`. § Expansion modes' two-row table:

| `sweep.baseline` | Baseline conditions | Each `vs_baseline` targets |
|---|---|---|
| A value on every axis | One, condition `00` | That single condition |
| A value on some axes | **One per cell of the unfixed axes** | Its own cell's baseline |

*"The rule underneath both is that the baseline expands over whichever axes it doesn't fix — group axes and parameter axes alike."*

- [ ] **Step 1: Write the failing test**

```python
def test_a_baseline_fixing_some_axes_expands_over_the_rest() -> None:
    """§ Expansion modes' second row: a baseline that fixes `analysis.method`
    and leaves `sex` free gives one baseline per level of `sex`, and each
    comparison targets its own cell's baseline rather than a single global one."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "data.sex": ["f", "m"],
                },
            }
        }
    )

    baselines = [c for c in conditions if c.is_baseline]
    assert len(baselines) == 2
    assert {dict(c.values)["data.sex"] for c in baselines} == {"f", "m"}
    assert all(dict(c.values)["analysis.method"] == "pearson" for c in baselines)
```

- [ ] **Step 2: Run, implement, run.** The baseline's row set becomes the product of its fixed values with the cells of the axes it does not fix.

- [ ] **Step 3: Labels gain their cell.** § Expansion modes shows `00_cohort=derivation__baseline`. One baseline stays `baseline`; per-cell baselines are `<cell>__baseline`. **`condition_dir_name` does not change** — it is the single source of truth `runner.step_dir_for` and `artifacts.StepIO.read_condition` both nest through.

- [ ] **Step 4: Verify the artifact path oracle.** Existing tests over `condition_dir_name` and condition directories must pass **untouched**:

```bash
uv run pytest tests/test_artifacts.py tests/test_runner.py -q
git diff --stat tests/test_artifacts.py tests/test_runner.py
```
Expected: green, and no diff.

- [ ] **Step 5: Mutation-test.** Make the baseline expand over axes it **does** fix (the test must fail); make it never expand (the same); make a per-cell baseline's label omit its cell (a label test must fail — write one if none exists).

- [ ] **Step 6: Commit.**

---

## Task 7: Retire `E-SWEEP-BASELINE-PARTIAL` and re-read the warning it stranded

**Files:**
- Modify: `src/publishable/validate.py`, `docs/reference.md`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: task 6's per-cell expansion
- Produces: the refusal gone; `W-SWEEP-BASELINE-CONFOUNDED`'s row true again

`E-SWEEP-BASELINE-PARTIAL`'s own message says the design is *"specified but not implemented in this build"* and *"Per-cell baselines will be honored in a later slice"*. This is that slice.

- [ ] **Step 1: Remove the refusal and its message.** Read `_check_unimplemented` first — the surrounding comment explains the `unfixed` computation, and a stale comment left behind is the defect this project keeps paying for.
- [ ] **Step 2: Test that the previously-refused config now validates and expands.** Use the exact shape the old message described: a baseline leaving a grid axis free.
- [ ] **Step 3: Re-read `W-SWEEP-BASELINE-CONFOUNDED`'s row.** H1's review ruled *"do not touch row 271"* explicitly because H2 would make its remedy expressible. Its remedy — leave one axis unfixed — was a config `E-SWEEP-BASELINE-PARTIAL` refused; now it is not. Read the row and the warning's emit site, confirm the remedy is now reachable, and remove whatever clause said it was not. **Do not weaken the warning itself** — it still fires when a fully-fixed baseline confounds contrasts.
- [ ] **Step 4: Remove `E-SWEEP-BASELINE-PARTIAL`'s registry row** from § Validation's error table, taking it from 60 rows to 59, and confirm no other document text references it:

```bash
grep -rn "E-SWEEP-BASELINE-PARTIAL" src/ tests/ docs/ README.md
```

- [ ] **Step 5: Commit.**

---

## Task 8: The comparison count under multiple baselines

**Files:**
- Modify: `src/publishable/cli.py` or `src/publishable/contrasts.py` — whichever resolves comparisons
- Test: `tests/test_contrasts.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: task 6's per-cell baselines
- Produces: `vs_baseline` targeting each condition's **own cell's** baseline, and a correction family that counts comparisons rather than conditions

§ Expansion modes: *"Baseline conditions are references rather than comparisons, so they never count as one: six conditions under two per-arm baselines are **four** comparisons in the correction family, not five."*

**This is the rule with reach outside the slice.** It changes `family_size`, which changes every corrected interval in a multi-baseline run. H4 owns the correction family, but H2 makes multi-baseline runs possible, so H2 must not leave this for H4 to discover.

- [ ] **Step 1: Read how comparisons are resolved today.** `resolve_contrasts` builds the family; `_differing_axes` decides `confounded`. Read both, and § Expansion modes' second row: *"Each `vs_baseline` targets its own cell's baseline: `sex=f__arm=treatment` compares against `sex=f__arm=control`."*
- [ ] **Step 2: Write the failing test with the document's own arithmetic** — six conditions under two per-cell baselines, asserting **four** comparisons and a `family_size` of four, not five or six.
- [ ] **Step 3: Implement, run.**
- [ ] **Step 4: Mutation-test.** Count baselines as comparisons (the test must fail); target every condition at the first baseline (a per-cell targeting test must fail).
- [ ] **Step 5: Commit.**

---

## Task 9: Consistency passes and the slice's exit criterion

**Files:**
- Modify: whichever of the four documents the passes find defects in
- Read: all four documents, `CLAUDE.md`

**Interfaces:**
- Consumes: every task above
- Produces: the slice's exit criterion

- [ ] **Step 1: Confirm `groups` is still refused.** The slice's most consequential constraint. A config declaring `groups` must still report `E-SWEEP-GROUPS-UNSUPPORTED`, and rows 219 and 257 must still be unimplemented. **If any task made a groups axis expand, that is a blocking defect**, not a minor.

- [ ] **Step 2: Confirm the worked example did not move.**

```bash
git diff main..HEAD -- README.md docs/ | grep "^-" | \
  grep -E "0\.581|0\.607|0\.412|0\.026|−0\.007|0\.059|−0\.169|0\.014|228|240|8e21|1a2b|3d8a|6b1f|2f5c8d0"
```
Expected: **no output**. Then confirm `cohort-pilot` still expands to exactly 3 conditions with one baseline, by running its expansion directly.

- [ ] **Step 3: Registry integrity.** Three `-UNSUPPORTED` codes retired and one refusal removed, so counts moved. Verify both directions: every code `src/` emits is documented or is a surviving `-UNSUPPORTED`; every documented code is still emitted.

```bash
comm -23 <(grep -rhoE "\b[EW]-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*\b" src/ | grep -v __pycache__ | sort -u) \
         <(grep -hoE "\b[EW]-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*\b" README.md docs/*.md | sort -u)
```
Expected: only surviving `-UNSUPPORTED` codes and `E-GIT-NO-REPO`. **State the method, not just the conclusion** — this project's absence claims have been wrong six times, always when established by a grep that could not fail. Include a self-test proving each check can fail.

- [ ] **Step 4: The mechanical pass.** Throwaway checks, not committed tooling: anchors and links resolve, no duplicate anchors, table rows match their headers, no trailing whitespace or tabs or invisible unicode, `×` not `x`. Skip fenced code blocks. Three anchors are known false positives of simplified sluggers — `secrets--credentials`, `naming-conventions--repeat-defaults`, the `executions.jsonl` heading — do not "fix" them.

- [ ] **Step 5: The cross-document pass.** `CLAUDE.md`'s seven drift classes. The ones this slice most plausibly disturbed: **prevented mistakes** (`experimental-designs.md` § Mistakes core prevents must stay structurally impossible — three modes just became possible, so confirm none of them re-opened a prevented mistake), **enum comments** (`method: sobol | latin_hypercube | random` must list what the code accepts), and **schema fields in prose**.

- [ ] **Step 6: Fix what the passes find; commit only if something changed.** A clean result is a real result — do not create an empty commit.

---

## Sequencing

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9, in order. Task 1 restructures what every later task extends; 6 needs 4's `ablate` to test the composition; 7 needs 6; 8 needs 6's per-cell baselines. Task 9 last, over a settled tree.

Tasks 2–5 are each small enough to land in one commit; task 6 is the largest and the only one that moves artifact paths.
