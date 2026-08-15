# Batch and Nested Repeats (S3b) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A design can declare a `batch` repeat level, nest a second level inside it, and ask for the executions inside each batch to be shuffled.

**Architecture:** `resolve_repeats` stops returning a flat list of leaves and returns `list[RepeatLevel]` instead — kind, `n`, and its own members. The runner crosses those levels outer-to-inner into leaf executions with composed labels (`batch03_seed42`) and nested directories. `order: randomized` shuffles the `(condition, inner-repeat)` pairs within each batch while leaving batch order fixed. Nothing in this slice touches `io.units`, the collapse arithmetic, or attrition — those are S3c's.

**Tech Stack:** Python 3.11+, `uv`, pytest, ruff, mypy.

## Global Constraints

- Python >= 3.11.
- Runtime dependencies are exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`. Adding one is out of scope.
- ruff: line-length 100, select `["E","F","I","UP","B"]`. mypy: strict over `src/`.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy`.
- `×`, not `x`, for multiplication — including inside fenced blocks and commit messages.
- `sweep.py` and `stats.py` are **pure**: no filesystem access, and no runtime import of `config`, `artifacts`, `runner`, or `cli`. `stats.py` must not be modified at all by this slice.
- `artifacts.py` is the only module that writes inside a run directory. (`sweep.yaml`'s write from `cli.py` is a pre-existing, adjudicated exception — do not "fix" it.)
- `validate.py` **collects** findings and never raises to report one.
- Every `E-`/`W-` identifier must have a test that produces it.
- The four documents in `docs/` are normative and lead. Where code cannot follow them, the document changes first and the gap is recorded in `docs/superpowers/spec-defects.md`.
- Unimplemented must mean **refused**, never silently ignored.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/replication.py` | `RepeatLevel`, `RepeatMember`, `resolve_repeats` returning levels, per-level collision checks, the three refusals |
| `src/publishable/runner.py` | Crossing levels into leaves; nested directory paths; the within-batch shuffle |
| `src/publishable/validate.py` | The three refusals as diagnostics; loading the experiment; `W-REPL-DETERMINISTIC` and `E-ENTRYPOINT-IMPORT` |
| `src/publishable/artifacts.py` | `read_upstream` resolving the target step's directory by scope instead of hard-coding `shared/` |
| `src/publishable/cli.py` | Passing levels through; `order_seed` and the realized `execution_order` into `sweep.yaml` |
| `tests/test_replication.py` | The level model, labels, per-level collisions, refusals |
| `tests/test_runner.py` | Crossing, nested paths, the shuffle |
| `tests/test_validate.py` | Refusal diagnostics and the warning |
| `tests/test_artifacts.py` | `read_upstream` across scopes |
| `tests/test_cli.py` | The acceptance test |

---

### Task 1: The level model

Replace the flat `list[Repeat]` return with `list[RepeatLevel]`, preserving today's single-`seed`-level behaviour exactly.

**Files:**
- Modify: `src/publishable/replication.py`
- Test: `tests/test_replication.py`

**Interfaces:**
- Consumes: `_seed_for(digest: str, index: int) -> int` (already exists).
- Produces:
  - `@dataclass(frozen=True) class RepeatMember: label: str; seed: int`
  - `@dataclass(frozen=True) class RepeatLevel: kind: str; members: list[RepeatMember]` with a read-only `members`, and `n` as a property returning `len(self.members)`.
  - `resolve_repeats(config: dict[str, Any], digest: str) -> list[RepeatLevel]`
  - `MAX_LEVELS = 2`
  - The existing `Repeat` dataclass **stays** — Task 2 keeps using it for leaves.

**Why `n` is a property, not a field:** two sources of truth for a count is how they drift. `n` is read off `members`, which is the thing that actually exists.

- [ ] **Step 1: Write the failing tests**

```python
def test_no_replication_block_yields_one_anonymous_seed_level():
    levels = resolve_repeats({}, "d")
    assert len(levels) == 1
    assert levels[0].kind == "seed"
    assert levels[0].n == 1
    assert levels[0].members[0].label == ""


def test_a_single_seed_level_resolves_as_before():
    levels = resolve_repeats({"replication": {"repeats": [{"kind": "seed", "n": 3}]}}, "d")
    assert len(levels) == 1
    assert levels[0].kind == "seed"
    assert levels[0].n == 3
    assert all(m.label.startswith("seed") for m in levels[0].members)
    assert len({m.seed for m in levels[0].members}) == 3
    assert len({m.label for m in levels[0].members}) == 3


def test_a_batch_level_labels_positionally_from_one():
    levels = resolve_repeats({"replication": {"repeats": [{"kind": "batch", "n": 3}]}}, "d")
    assert [m.label for m in levels[0].members] == ["batch01", "batch02", "batch03"]


def test_two_levels_resolve_outer_to_inner():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}]}}, "d")
    assert [lv.kind for lv in levels] == ["batch", "seed"]
    assert [lv.n for lv in levels] == [3, 2]


def test_members_are_not_mutable_through_the_level():
    levels = resolve_repeats({"replication": {"repeats": [{"kind": "seed", "n": 2}]}}, "d")
    with pytest.raises((AttributeError, TypeError)):
        levels[0].members.append(RepeatMember(label="x", seed=1))
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_replication.py -v`
Expected: FAIL — `RepeatLevel` / `RepeatMember` do not exist.

- [ ] **Step 3: Implement the model**

Replace `resolve_repeats`'s body. Keep `_seed_for` and `Repeat` untouched.

```python
MAX_LEVELS = 2


@dataclass(frozen=True)
class RepeatMember:
    label: str
    seed: int


@dataclass(frozen=True)
class RepeatLevel:
    kind: str
    members: tuple[RepeatMember, ...]

    @property
    def n(self) -> int:
        return len(self.members)


def _seed_members(digest: str, kind: str, n: int) -> tuple[RepeatMember, ...]:
    """`seed` members carry their value in the label; `batch` members are positional.

    A batch varies nothing the pipeline declares, so its label says *which* block
    it is, not what was drawn for it — see reference.md § A `batch` says *when*,
    not *what*. It still carries a seed, because a step at batch scope still needs
    a stream to draw from.
    """
    seeds = [_seed_for(f"{digest}|{kind}", i) for i in range(n)]
    if kind == "batch":
        return tuple(
            RepeatMember(label=f"batch{i + 1:02d}", seed=s) for i, s in enumerate(seeds)
        )
    labels = [f"seed{s % 100:02d}" for s in seeds]
    if len(set(labels)) != n:
        labels = [f"seed{s}" for s in seeds]
    return tuple(RepeatMember(label=lb, seed=s) for lb, s in zip(labels, seeds, strict=True))
```

and the resolver:

```python
def resolve_repeats(config: dict[str, Any], digest: str) -> list[RepeatLevel]:
    levels = ((config.get("replication") or {}).get("repeats")) or []
    if not levels:
        return [RepeatLevel(kind="seed", members=(RepeatMember(label="", seed=_seed_for(digest, 0)),))]
    if len(levels) > MAX_LEVELS:
        raise ContractError(
            f"{len(levels)} repeat levels are declared; this build supports at most "
            f"{MAX_LEVELS}, and every design the documents describe is two deep",
            code="E-REPL-LEVEL-DEPTH",
        )
    resolved: list[RepeatLevel] = []
    for level in levels:
        kind = level.get("kind")
        if kind in REJECTED_KINDS:
            raise ContractError(
                f"`{kind}` is not a repeat kind — {REJECTED_KINDS[kind]}", code="E-REPL-KIND"
            )
        if kind == "fold":
            raise ContractError(
                "repeat kind `fold` is specified but not implemented in this build; it "
                "changes what `io.units` hands a step and how per-unit values combine, "
                "and will be honored in a later slice",
                code="E-REPL-FOLD-UNSUPPORTED",
            )
        if kind not in SUPPORTED_KINDS:
            raise ContractError(f"`{kind}` is not a repeat kind", code="E-REPL-KIND")
        n = int(level.get("n", 1))
        if n < 1:
            raise ContractError(
                f"`{{kind: {kind}, n: {n}}}` executes nothing; n must be at least 1",
                code="E-REPL-N",
            )
        resolved.append(RepeatLevel(kind=kind, members=_seed_members(digest, kind, n)))
    kinds = [lv.kind for lv in resolved]
    if len(set(kinds)) != len(kinds):
        raise ContractError(
            f"repeat levels {kinds} declare the same kind twice; labels compose by kind "
            "and dispersion is reported one entry per level, so two levels of one kind "
            "are ambiguous in both",
            code="E-REPL-LEVEL-DUPLICATE",
        )
    for lv in resolved:
        _check_no_collisions(lv, digest)
    return resolved
```

Set `SUPPORTED_KINDS = ("seed", "batch")` and delete `PLANNED_KINDS` (grep for it — it must have no remaining references).

- [ ] **Step 4: Rewrite `_check_no_collisions` to take a level**

The existing function takes `list[Repeat]` and checks seeds and labels across the whole flat list. **That is now wrong across levels and right within one.** Under `batch` × `seed`, `batch01_seed42` and `batch02_seed42` deliberately share a seed — a batch varies nothing, so the same seed re-run later is the point. Checking across leaves would reject the design the kind exists to express.

```python
def _check_no_collisions(level: RepeatLevel, digest: str) -> None:
    # Within one level, two members deriving the same seed are not two repeats:
    # they execute identically and would silently understate dispersion. Across
    # levels, a shared seed is correct — a `batch` varies nothing the pipeline
    # declares, so batch01_seed42 and batch02_seed42 SHOULD draw alike.
    seeds_seen: dict[int, int] = {}
    labels_seen: dict[str, int] = {}
    for index, m in enumerate(level.members):
        if m.seed in seeds_seen:
            raise ContractError(
                f"{level.kind} members {seeds_seen[m.seed]} and {index} both derive seed "
                f"{m.seed} from digest {digest!r}; two repeats cannot share a seed",
                code="E-REPL-SEED-COLLISION",
            )
        seeds_seen[m.seed] = index
        if m.label in labels_seen:
            raise ContractError(
                f"{level.kind} members {labels_seen[m.label]} and {index} both resolve to "
                f"label {m.label!r} from digest {digest!r}; two repeats cannot share a label",
                code="E-REPL-SEED-COLLISION",
            )
        labels_seen[m.label] = index
```

- [ ] **Step 5: Add the collision-scope test**

```python
def test_two_levels_may_share_a_seed_across_levels():
    """A batch varies nothing, so the same seed re-run later is the point —
    a collision check spanning levels would reject the design `batch` exists for."""
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]}}, "d")
    outer = {m.seed for m in levels[0].members}
    inner = {m.seed for m in levels[1].members}
    assert len(outer) == 2 and len(inner) == 2   # distinct WITHIN each level
```

- [ ] **Step 6: Fix the one caller so the suite runs**

`cli.py:111` is the only caller. Temporarily flatten so nothing else breaks yet:

```python
levels = resolve_repeats(doc, digest)
repeats = [Repeat(kind=levels[0].kind, label=m.label, seed=m.seed) for m in levels[0].members]
```

Add a comment saying Task 2 replaces this with real crossing. Everything downstream keeps its current shape for now.

- [ ] **Step 7: Run the full suite**

Run: `uv run pytest -v && uv run ruff check . && uv run mypy`
Expected: all pass. Pre-existing tests asserting `E-REPL-KIND-UNSUPPORTED` for `batch` must be updated to expect success; ones asserting it for `fold` become `E-REPL-FOLD-UNSUPPORTED`. Nesting tests move to `E-REPL-LEVEL-DEPTH` only if they declare three or more levels — a two-level config now succeeds.

- [ ] **Step 8: Commit**

```bash
git add src/publishable/replication.py tests/test_replication.py src/publishable/cli.py
git commit -m "Return repeat levels instead of a flat list of leaves"
```

---

### Task 2: Crossing levels into leaf executions

**Files:**
- Modify: `src/publishable/replication.py`
- Test: `tests/test_replication.py`

**Interfaces:**
- Consumes: `RepeatLevel`, `RepeatMember` from Task 1; the existing `Repeat(kind, label, seed)`.
- Produces: `cross_levels(levels: list[RepeatLevel]) -> list[Repeat]`

The leaf's `kind` is the **innermost** level's kind and its `seed` is the innermost member's seed, because the inner level is what varies between consecutive executions. The label composes outer-to-inner joined by `_`.

- [ ] **Step 1: Write the failing tests**

```python
def test_one_level_crosses_to_its_own_members():
    levels = resolve_repeats({"replication": {"repeats": [{"kind": "seed", "n": 3}]}}, "d")
    leaves = cross_levels(levels)
    assert [lf.label for lf in leaves] == [m.label for m in levels[0].members]


def test_two_levels_cross_with_the_inner_varying_fastest():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}]}}, "d")
    leaves = cross_levels(levels)
    assert len(leaves) == 6
    inner = [m.label for m in levels[1].members]
    assert [lf.label for lf in leaves] == [
        f"batch01_{inner[0]}", f"batch01_{inner[1]}",
        f"batch02_{inner[0]}", f"batch02_{inner[1]}",
        f"batch03_{inner[0]}", f"batch03_{inner[1]}",
    ]


def test_a_leaf_takes_the_innermost_seed_and_kind():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]}}, "d")
    leaves = cross_levels(levels)
    inner = levels[1].members
    assert [lf.seed for lf in leaves] == [inner[0].seed, inner[1].seed] * 2
    assert {lf.kind for lf in leaves} == {"seed"}


def test_the_anonymous_single_repeat_keeps_its_empty_label():
    leaves = cross_levels(resolve_repeats({}, "d"))
    assert [lf.label for lf in leaves] == [""]
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_replication.py -k cross -v`
Expected: FAIL — `cross_levels` is not defined.

- [ ] **Step 3: Implement**

```python
def cross_levels(levels: list[RepeatLevel]) -> list[Repeat]:
    """Cross the levels outer-to-inner into one leaf per execution.

    The inner level varies fastest, so the sequence reads like nested loops
    written in declaration order — the same rule `sweep.expand` follows for
    conditions. A leaf takes the innermost level's kind and seed because the
    inner level is what differs between consecutive executions.
    """
    leaves: list[Repeat] = []
    inner = levels[-1]
    for combo in itertools.product(*[lv.members for lv in levels]):
        label = "_".join(m.label for m in combo if m.label)
        leaves.append(Repeat(kind=inner.kind, label=label, seed=combo[-1].seed))
    return leaves
```

Add `import itertools` at the top.

- [ ] **Step 4: Run to verify they pass**

Run: `uv run pytest tests/test_replication.py -v`
Expected: PASS.

- [ ] **Step 5: Use it in the caller**

Replace Task 1's temporary flattening in `cli.py` with:

```python
levels = resolve_repeats(doc, digest)
repeats = cross_levels(levels)
```

Keep `levels` in scope — Tasks 5 and 7 need it.

- [ ] **Step 6: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/replication.py tests/test_replication.py src/publishable/cli.py
git commit -m "Cross repeat levels into one leaf per execution"
```

---

### Task 3: Nested repeat directories

**Files:**
- Modify: `src/publishable/runner.py` (`step_dir_for`)
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: leaf labels from `cross_levels` — a composed label is a single string containing `_`.
- Produces: no signature change. `step_dir_for(run_dir, execution, collapse_repeats)` keeps its shape.

**The point of this task is that it is nearly a no-op, and you must confirm that rather than assume it.** A composed label `batch01_seed42` is one path segment, so `base / execution.repeat_label` already produces `conditions/00_baseline/batch01_seed42/step/`. Verify by test, and fix only what the tests show is broken.

- [ ] **Step 1: Write the tests**

**`Execution` has six fields and the first is `step_cls`** — `step_cls`, `step_name`, `scope`, `condition_index`, `condition_label`, `repeat_label`. It cannot be constructed without a step class, so these tests need one. Check `tests/test_runner.py` for the dummy step class it already uses and reuse it; `_Step` below stands for whatever that is named.

```python
def test_a_composed_repeat_label_is_one_directory_segment(tmp_path):
    ex = Execution(step_cls=_Step, step_name="fit", scope="repeat", condition_index=0,
                   condition_label="baseline", repeat_label="batch01_seed42")
    assert step_dir_for(tmp_path, ex, collapse_repeats=False) == (
        tmp_path / "conditions" / "00_baseline" / "batch01_seed42" / "fit"
    )


def test_a_single_level_run_is_unchanged(tmp_path):
    ex = Execution(step_cls=_Step, step_name="fit", scope="repeat", condition_index=None,
                   condition_label=None, repeat_label="seed42")
    assert step_dir_for(tmp_path, ex, collapse_repeats=False) == (
        tmp_path / "seed42" / "fit"
    )


def test_a_collapsed_repeat_still_collapses_with_a_composed_label(tmp_path):
    ex = Execution(step_cls=_Step, step_name="fit", scope="repeat", condition_index=None,
                   condition_label=None, repeat_label="batch01_seed42")
    assert step_dir_for(tmp_path, ex, collapse_repeats=True) == tmp_path / "fit"
```

- [ ] **Step 2: Run them**

Run: `uv run pytest tests/test_runner.py -k directory -v`
Expected: PASS without any source change. If any fails, fix `step_dir_for` minimally and say in your report what was actually wrong — an unexpected failure here means the path rule is not what this plan assumed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_runner.py
git commit -m "Pin that a composed repeat label is one directory segment"
```

---

### Task 4: The three refusals in `validate`

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `resolve_repeats` raises `ContractError` for the three refusals. `validate` must **not** let that escape — it collects.
- Produces: diagnostics `E-REPL-FOLD-UNSUPPORTED`, `E-REPL-LEVEL-DUPLICATE`, `E-REPL-LEVEL-DEPTH`, `E-REPL-ORDER`.

`W-REPL-DETERMINISTIC` is **Task 5**, because it needs a capability `validate` does not yet have.

**Read `_check_replication` and `_check_unimplemented` before writing.** `E-REPL-ORDER-UNSUPPORTED` currently lives in `_check_unimplemented` and must be **deleted** — `as_declared` and `randomized` both ship in Task 5. Replace it with a check that any *other* `order` value is refused as `E-REPL-ORDER`.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_fold_level_is_refused_by_name(write_config):
    assert "E-REPL-FOLD-UNSUPPORTED" in codes(
        write_config({"replication": {"repeats": [{"kind": "fold", "k": 5}]}}))


def test_two_levels_of_one_kind_are_refused(write_config):
    assert "E-REPL-LEVEL-DUPLICATE" in codes(write_config({"replication": {"repeats": [
        {"kind": "seed", "n": 2}, {"kind": "seed", "n": 3}]}}))


def test_three_levels_are_refused(write_config):
    assert "E-REPL-LEVEL-DEPTH" in codes(write_config({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}, {"kind": "seed", "n": 2}]}}))


def test_two_levels_of_different_kinds_validate_clean(write_config):
    found = codes(write_config({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]}}))
    assert not [c for c in found if c.startswith("E-REPL")]


def test_randomized_order_is_accepted(write_config):
    found = codes(write_config({"replication": {
        "repeats": [{"kind": "seed", "n": 2}], "order": "randomized"}}))
    assert "E-REPL-ORDER-UNSUPPORTED" not in found
    assert "E-REPL-ORDER" not in found


def test_an_unknown_order_is_refused(write_config):
    assert "E-REPL-ORDER" in codes(write_config({"replication": {
        "repeats": [{"kind": "seed", "n": 2}], "order": "sideways"}}))
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_validate.py -k repl -v`

- [ ] **Step 3: Implement the refusals**

In `_check_replication`, call the resolver and translate its refusal into a finding rather than letting it raise:

```python
    try:
        resolve_repeats(doc, "validate")
    except ContractError as exc:
        if exc.code in REPL_DECLARATION_CODES:
            c.error(exc.code, "replication.repeats", str(exc))
        else:
            raise
```

with, at module level:

```python
# Refusals that are properties of the DECLARATION, so `validate` reports them as
# findings. Anything else `resolve_repeats` raises is a genuine fault and still
# propagates — swallowing all of them is how a real error becomes a silent pass.
REPL_DECLARATION_CODES = frozenset({
    "E-REPL-FOLD-UNSUPPORTED", "E-REPL-LEVEL-DUPLICATE", "E-REPL-LEVEL-DEPTH",
    "E-REPL-KIND", "E-REPL-N", "E-REPL-SEED-COLLISION",
})
```

The digest string `"validate"` is a placeholder: seeds do not matter here, only the declaration does. Say so in a comment, because a reader will otherwise wonder why validate invents a digest.

- [ ] **Step 4: Replace the order refusal**

Delete the `E-REPL-ORDER-UNSUPPORTED` block from `_check_unimplemented` and add to `_check_replication`:

```python
    order = (doc.get("replication") or {}).get("order")
    if order is not None and order not in ("as_declared", "randomized"):
        c.error(
            "E-REPL-ORDER",
            "replication.order",
            f"is `{order}`; the only orders are `as_declared` and `randomized`",
        )
```

Grep the whole tree for `E-REPL-ORDER-UNSUPPORTED` afterwards — src, tests, and the four documents. It must be gone.

- [ ] **Step 5: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Refuse fold, duplicate levels, and a depth past two"
```

---

### Task 5: `validate` loads the experiment, and `W-REPL-DETERMINISTIC`

**Files:**
- Modify: `src/publishable/validate.py`, `src/publishable/cli.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `_load_experiment(repo_root: Path, entrypoint: str) -> BaseExperiment` in `cli.py:47`; `BaseStep.nondeterministic` (exists on the base class, read by nothing today).
- Produces: `validate_config` gaining an optional loaded experiment; the diagnostic `W-REPL-DETERMINISTIC`; and a diagnostic for an entrypoint that cannot be imported.

**Why this task is architectural, not cosmetic.** `validate` today resolves the template from a registry (`get_template`) and **never imports the user's experiment**. `command_run` loads it separately at `cli.py:108`, *after* calling `validate_config` at line 92. `W-REPL-DETERMINISTIC` has to read `nondeterministic` off a step class, so it cannot be answered without that import.

Warning at run time instead was considered and rejected: a warning is non-fatal, so the run proceeds and spends the compute the warning is about. `reference.md` § A `batch` says *when*, not *what* says `validate` warns, and validate is the only place where warning saves anything.

**The risk to handle deliberately:** importing user code can raise. A step module with a syntax error, a missing import, or a side effect at module scope currently surfaces during `run`. After this change it surfaces during `validate` — which is better, but only if it is a *finding* rather than a traceback. `validate` collects and never raises to report.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_batch_level_warns_when_no_step_is_nondeterministic(write_config):
    assert "W-REPL-DETERMINISTIC" in codes(
        write_config({"replication": {"repeats": [{"kind": "batch", "n": 3}]}}))


def test_no_warning_when_a_step_declares_nondeterminism(write_config_nondet):
    assert "W-REPL-DETERMINISTIC" not in codes(
        write_config_nondet({"replication": {"repeats": [{"kind": "batch", "n": 3}]}}))


def test_no_warning_without_a_batch_level(write_config):
    assert "W-REPL-DETERMINISTIC" not in codes(
        write_config({"replication": {"repeats": [{"kind": "seed", "n": 3}]}}))


def test_an_unimportable_entrypoint_is_a_finding_not_a_traceback(write_config_broken):
    """validate collects; a broken step module must not escape as a traceback."""
    found = codes(write_config_broken({}))
    assert "E-ENTRYPOINT-IMPORT" in found
```

`write_config_nondet` is a fixture whose experiment has one step with `nondeterministic = True`; `write_config_broken` writes a step module that raises on import. Build both by copying the existing `write_config` fixture — **read it first and match how it constructs the experiment module** rather than inventing a second idiom.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_validate.py -k nondeterministic or entrypoint -v`

- [ ] **Step 3: Give `validate_config` the experiment**

Add a keyword-only parameter so every existing caller keeps working:

```python
def validate_config(
    config_path: Path, c: Collector, *, experiment: Any | None = None
) -> dict[str, Any] | None:
```

Inside, after the config is loaded and the entrypoint is known, load it when the caller did not supply one. Catch **only** the import itself:

```python
    if experiment is None and doc.get("entrypoint"):
        try:
            experiment = _load_experiment(repo_root, doc["entrypoint"])
        except Exception as exc:                  # noqa: BLE001 — see below
            # Importing user code can fail any way user code can fail. `validate`
            # reports rather than raises, so every failure here is one finding;
            # letting it propagate would turn a diagnosable config into a traceback.
            c.error(
                "E-ENTRYPOINT-IMPORT",
                "entrypoint",
                f"could not be imported: {type(exc).__name__}: {exc}",
            )
```

Move `_load_experiment` out of `cli.py` into a module both can import — put it wherever the existing layout suggests, and say in your report where. `cli.py` importing from `validate.py` or the reverse is a cycle waiting to happen; check before choosing.

Then have `command_run` pass the experiment it already loaded into `validate_config`, so the import happens once per run rather than twice.

- [ ] **Step 4: Add the check**

In `_check_replication`, which now receives the experiment:

```python
    kinds = {lv.get("kind") for lv in ((doc.get("replication") or {}).get("repeats") or [])}
    if "batch" in kinds and experiment is not None:
        if not any(getattr(s, "nondeterministic", False) for s in experiment.steps):
            c.warn(
                "W-REPL-DETERMINISTIC",
                "replication.repeats",
                "declares a `batch` level, but no step sets `nondeterministic = True`; "
                "under a fully deterministic pipeline a batch recomputes the same answer "
                "each time, so its dispersion is a row of zeros bought with n× the compute",
            )
```

`experiment is not None` matters: when the import failed, `E-ENTRYPOINT-IMPORT` is already reported and a second finding about determinism would be noise about a pipeline nobody could load.

- [ ] **Step 5: Record the new identifier**

`E-ENTRYPOINT-IMPORT` is new. Grep `docs/reference.md` for it first — several codes this project "added" already existed in its registry. Record it in `docs/superpowers/spec-defects.md` alongside the other new codes, noting that `validate` importing the entrypoint is a capability the documents describe implicitly (by requiring the `nondeterministic` warning) but never state.

- [ ] **Step 6: Run the full suite and commit**

Confirm `validate` on a project whose steps import cleanly is no slower in a way that matters, and that no existing test broke on the new import.

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/validate.py src/publishable/cli.py tests/test_validate.py
git commit -m "Load the experiment in validate, and warn on a deterministic batch"
```

---

### Task 6: `order: randomized`

**Files:**
- Modify: `src/publishable/replication.py`
- Test: `tests/test_replication.py`

**Interfaces:**
- Consumes: `RepeatLevel`, `cross_levels`, `_seed_for`.
- Produces:
  - `order_seed_for(digest: str) -> int`
  - `realize_order(pairs: list[tuple[int, str]], levels: list[RepeatLevel], mode: str, order_seed: int) -> list[tuple[int, str]]`

`pairs` is `(condition_index, leaf_label)` in declared order. The return is the realized execution order.

**The rule, from `reference.md` § A `batch` says *when*, not *what*:** batches execute in order and the shuffle happens *within* one. A batch is a position in time, so shuffling batches against each other destroys the thing being declared. **With no `batch` level declared the whole run is one block** — this is the case the documents do not cover and the spec pins deliberately.

Group by the batch member's label, which is the leading segment of the composed label when a batch level exists. Do not parse the string: derive the grouping from `levels`, since the label format is not a contract you want two readers of.

- [ ] **Step 1: Write the failing tests**

```python
def test_as_declared_is_the_identity():
    levels = resolve_repeats({"replication": {"repeats": [{"kind": "seed", "n": 2}]}}, "d")
    pairs = [(0, lf.label) for lf in cross_levels(levels)]
    assert realize_order(pairs, levels, "as_declared", 7) == pairs


def test_randomized_keeps_batches_in_declared_order():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1) for lf in cross_levels(levels)]
    out = realize_order(pairs, levels, "randomized", 7)
    batches = [lb.split("_")[0] for _, lb in out]
    assert batches == sorted(batches), "batches must not be shuffled against each other"
    assert len(out) == len(pairs) and sorted(out) == sorted(pairs)


def test_randomized_shuffles_within_a_batch():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 4}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1, 2) for lf in cross_levels(levels)]
    out = realize_order(pairs, levels, "randomized", 7)
    assert out != pairs, "some batch's interior must have been reordered"


def test_the_same_order_seed_reproduces_the_same_order():
    levels = resolve_repeats({"replication": {"repeats": [
        {"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1) for lf in cross_levels(levels)]
    assert realize_order(pairs, levels, "randomized", 7) == \
           realize_order(pairs, levels, "randomized", 7)
    assert realize_order(pairs, levels, "randomized", 7) != \
           realize_order(pairs, levels, "randomized", 99)


def test_with_no_batch_level_the_whole_run_is_one_block():
    """The documents describe the shuffle only in terms of batches; the spec pins
    this case: no batch boundary means nothing bounds the shuffle."""
    levels = resolve_repeats({"replication": {"repeats": [{"kind": "seed", "n": 4}]}}, "d")
    pairs = [(c, lf.label) for c in (0, 1, 2) for lf in cross_levels(levels)]
    out = realize_order(pairs, levels, "randomized", 7)
    assert sorted(out) == sorted(pairs) and out != pairs
```

The third test is the one that matters most: an implementation shuffling batches too would pass "the order differs from declared" while destroying the declaration. That is why the second test exists beside it.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_replication.py -k order -v`

- [ ] **Step 3: Implement**

```python
def order_seed_for(digest: str) -> int:
    """From the design digest, never from `parameters_hash`.

    Editing any parameter would otherwise redraw the execution order of a run
    that varied nothing about it — see reference.md § What auto-derives from.
    """
    return _seed_for(f"{digest}|order", 0)


def realize_order(
    pairs: list[tuple[int, str]],
    levels: list[RepeatLevel],
    mode: str,
    order_seed: int,
) -> list[tuple[int, str]]:
    """Shuffle within each batch; never across them.

    A batch is a position in time, so shuffling batches against each other would
    destroy the thing being declared. With no `batch` level the whole run is one
    block, because there is no boundary to shuffle inside.
    """
    if mode != "randomized":
        return list(pairs)
    batch_level = next((lv for lv in levels if lv.kind == "batch"), None)
    if batch_level is None:
        blocks: list[list[tuple[int, str]]] = [list(pairs)]
    else:
        by_batch: dict[str, list[tuple[int, str]]] = {m.label: [] for m in batch_level.members}
        for pair in pairs:
            # The batch member's label is a segment of the composed leaf label;
            # matching against the resolved members keeps the label FORMAT out
            # of this function, so changing it cannot silently regroup a run.
            member = next(m.label for m in batch_level.members
                          if m.label in pair[1].split("_"))
            by_batch[member].append(pair)
        blocks = [by_batch[m.label] for m in batch_level.members]
    rng = random.Random(order_seed)
    out: list[tuple[int, str]] = []
    for block in blocks:
        shuffled = list(block)
        rng.shuffle(shuffled)
        out.extend(shuffled)
    return out
```

Add `import random` at the top. Use `random.Random(order_seed)` — an explicit instance, never the module-level global, which core seeds for a different purpose.

- [ ] **Step 4: Run to verify they pass, then the full suite**

Run: `uv run pytest -v && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Commit**

```bash
git add src/publishable/replication.py tests/test_replication.py
git commit -m "Shuffle executions within a batch, never across batches"
```

---

### Task 7: `read_upstream` stops hard-coding `shared/`

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

**Interfaces:**
- Consumes: `self._step_scopes: dict[str, str] | None`, `self._conditions`, `condition_dir_name` — all already on `StepIO`.
- Produces: no signature change to `read_upstream(step, name)`.

**The bug:** `read_upstream` reads `self.run_dir / "shared" / step / name` unconditionally. `shared/` is where **`run`-scoped** steps write. A `condition`-scoped step writes to `conditions/<nn>_<label>/<step>/`, so a repeat-scoped step reading a condition-scoped step looks in the wrong place and fails. Nested repeats make this more reachable, not less.

**`StepIO.__init__` does not carry its own condition** — its keyword-only parameters are `step_dir`, `input_dir`, `run_dir`, `units`, `scope`, `conditions`, `repeats`, `step_scopes`. It knows every condition in the run and not which one it is in. So this task adds two: `condition_index: int | None = None` and `condition_label: str | None = None`, stored as `self._condition_index` / `self._condition_label`, defaulting to `None` so every existing construction site keeps working. `runner.py` passes them from the `Execution` it is running.

- [ ] **Step 1: Write the failing test**

```python
def test_a_repeat_step_reads_a_condition_scoped_step(tmp_path):
    """The case that fails today: `shared/` is where run-scoped steps write, and a
    condition-scoped step writes under its own condition directory."""
    cond = tmp_path / "conditions" / "00_baseline" / "fit"
    cond.mkdir(parents=True)
    (cond / "model.json").write_bytes(b'{"m": 1}')
    io = make_io(tmp_path, scope="repeat", condition_index=0, condition_label="baseline",
                 step_scopes={"fit": "condition"})
    assert io.read_upstream("fit", "model.json") == {"m": 1}


def test_a_condition_step_still_reads_a_run_scoped_step(tmp_path):
    shared = tmp_path / "shared" / "load"
    shared.mkdir(parents=True)
    (shared / "cohort.json").write_bytes(b'{"n": 3}')
    io = make_io(tmp_path, scope="condition", condition_index=0, condition_label="baseline",
                 step_scopes={"load": "run"})
    assert io.read_upstream("load", "cohort.json") == {"n": 3}


def test_reading_a_narrower_step_is_still_refused(tmp_path):
    io = make_io(tmp_path, scope="condition", condition_index=0, condition_label="baseline",
                 step_scopes={"analyze": "repeat"})
    with pytest.raises(ContractError) as exc:
        io.read_upstream("analyze", "scores.json")
    assert exc.value.code == "E-STEP-READ-DIRECTION"
```

`make_io` stands for however `tests/test_artifacts.py` already builds a `StepIO`. **Read that file and use its existing helper** — do not add a second constructor idiom.

- [ ] **Step 2: Run to verify the first fails**

Run: `uv run pytest tests/test_artifacts.py -k read_upstream -v`
Expected: the first test FAILS with a missing-file error; the other two pass.

- [ ] **Step 3: Implement**

Keep the direction check exactly as it is, and replace only the path construction:

```python
        if target == "run" or target is None:
            base = self.run_dir / "shared"
        elif target == "summary":
            base = self.run_dir / "summary"
        else:
            # A condition-scoped target lives under the caller's own condition:
            # `read_upstream` reads WIDER steps, and the only condition wider
            # than this execution's is the one it is running in.
            base = self.run_dir
            if self._condition_label is not None and self._condition_index is not None:
                base = base / "conditions" / condition_dir_name(
                    self._condition_index, self._condition_label
                )
        return self._read(base / step / name)
```

`target is None` keeps today's behaviour for a step whose scope is unknown — that is the pre-existing default and this task does not change it.

- [ ] **Step 4: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/artifacts.py tests/test_artifacts.py
git commit -m "Resolve an upstream read by the target step's scope"
```

---

### Task 8: `order` and `order_seed` in `sweep.yaml`

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `sweep_document(conditions, repeats, digest, order, execution_order, order_seed=None) -> dict` (already exists, already the documented shape); `order_seed_for`, `realize_order`, `cross_levels`, `levels`.
- Produces: no new functions.

`sweep.yaml`'s schema is already correct and matches `docs/reference.md` § `sweep.yaml` — the resolved plan. This task only feeds it real values instead of defaults. Do **not** change `sweep_document`'s shape; if you believe it is wrong, stop and report.

Per `reference.md`, `order: randomized` adds `order_seed` beside the `execution_order` the shuffle produced — the seed so the plan is derivable, the order because what happened is not a thing to re-derive. Under `as_declared` there is no shuffle, so pass `order_seed=None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_sweep_yaml_records_the_order_mode_and_seed(tmp_path):
    doc = run_a_project(tmp_path, replication={
        "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}],
        "order": "randomized"})
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    assert sweep["order"] == "randomized"
    assert isinstance(sweep["order_seed"], int)
    assert len(sweep["execution_order"]) == len(sweep["labels"]) * len(sweep["conditions"])


def test_as_declared_records_no_order_seed(tmp_path):
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 2}]})
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    assert sweep["order"] == "as_declared"
    assert sweep.get("order_seed") is None


def test_the_recorded_order_is_the_order_that_ran(tmp_path):
    """The realized order is a fact about the run, not a rule to re-derive."""
    doc = run_a_project(tmp_path, replication={
        "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}],
        "order": "randomized"})
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    recorded = [(e["condition"], e["repeat"]) for e in sweep["execution_order"]]
    ran = [(r.condition_index, r.repeat_label) for r in doc["results"] if r.repeat_label]
    assert recorded[:len(ran)] == ran[:len(recorded)] or set(recorded) >= set(ran)
```

`run_a_project` stands for however `tests/test_cli.py` already drives an end-to-end run. **Read that file and reuse its existing helper.** If none exists, the acceptance test in Task 8 builds one — write these tests against that helper and note the ordering dependency in your report.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_cli.py -k sweep_yaml -v`

- [ ] **Step 3: Implement in `command_run`**

```python
    mode = ((doc.get("replication") or {}).get("order")) or "as_declared"
    order_seed = order_seed_for(digest) if mode == "randomized" else None
    declared_pairs = [(c.index, lf.label) for c in conditions for lf in repeats]
    execution_order = realize_order(declared_pairs, levels, mode, order_seed or 0)
```

Then pass `mode`, `execution_order`, and `order_seed` into the existing `sweep_document(...)` call, and **use `execution_order` to order the plan actually executed** — a recorded order that is not the executed order is worse than none. Where the plan is built, reorder the repeat-scoped executions to match. Say in your report exactly where you applied it.

- [ ] **Step 4: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/cli.py tests/test_cli.py
git commit -m "Record the order mode, its seed, and the order that ran"
```

---

### Task 9: The acceptance test

**Files:**
- Test: `tests/test_cli.py`
- Modify: whatever the test shows is still unwired.

**Interfaces:**
- Consumes: everything above.
- Produces: no new source interfaces.

This is the task that proves the slice is real rather than a set of green unit tests over dead wiring. Every previous slice in this project ended with a piece that worked in isolation and was unreachable from `main(["run", ...])`.

**Acceptance, from the design spec:** 2 conditions × 3 batches × 2 seeds = 12 executions in `conditions/<nn>_<label>/batchNN_seedNN/<step>/`; `order: randomized` producing an order fixed across batches and shuffled within one and reproducible from the recorded `order_seed`; `W-REPL-DETERMINISTIC` firing; and a single-level `seed` run unchanged from S3a.

- [ ] **Step 1: Write the acceptance test**

```python
def test_a_nested_batch_seed_run_end_to_end(tmp_path):
    doc = run_a_project(
        tmp_path,
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman"]}},
        replication={"repeats": [{"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}],
                     "order": "randomized"},
    )
    run_dir = doc["run_dir"]
    repeat_dirs = sorted(p.name for p in (run_dir / "conditions").glob("*/*") if p.is_dir())
    assert len(repeat_dirs) == 2 * 3 * 2 // 2      # 6 repeat dirs per condition, 2 conditions
    assert all(re.fullmatch(r"batch0\d_seed\d+", n) for n in set(repeat_dirs))
    sweep = yaml.safe_load((run_dir / "sweep.yaml").read_text())
    batches = [e["repeat"].split("_")[0] for e in sweep["execution_order"]]
    assert batches == sorted(batches), "batches must run in declared order"
    assert len(sweep["execution_order"]) == 12


def test_the_recorded_order_seed_reproduces_the_order(tmp_path):
    a = run_a_project(tmp_path / "a", replication={
        "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}],
        "order": "randomized"})
    b = run_a_project(tmp_path / "b", replication={
        "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}],
        "order": "randomized"})
    sa = yaml.safe_load((a["run_dir"] / "sweep.yaml").read_text())
    sb = yaml.safe_load((b["run_dir"] / "sweep.yaml").read_text())
    assert sa["order_seed"] == sb["order_seed"]
    assert sa["execution_order"] == sb["execution_order"]


def test_a_single_level_seed_run_has_no_composed_labels(tmp_path):
    """The regression risk of introducing a level is that it appears where it should not."""
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 2}]})
    dirs = [p.name for p in doc["run_dir"].rglob("*") if p.is_dir()]
    assert not any("_seed" in d for d in dirs)
    assert not any(d.startswith("batch") for d in dirs)
```

Both runs in the second test must use the same experiment and config so their design digests match; if `run_a_project` embeds a timestamp or path into the digest, that test will fail for the wrong reason — check before assuming, and report what you found.

- [ ] **Step 2: Run and fix what is unwired**

Run: `uv run pytest tests/test_cli.py -k nested or order_seed or single_level -v`

Fix whatever these expose. Report every source change you had to make here — each one is a piece an earlier task left inert.

- [ ] **Step 3: Run the whole suite, plus a manual run**

```bash
uv run pytest && uv run ruff check . && uv run mypy
```

Then scaffold a project by hand and run it with a nested `batch` × `seed` block, and paste `sweep.yaml` and the directory tree into your report. A test can share a bug with the code it tests; a tree you read cannot.

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py src/
git commit -m "Run a nested batch × seed design end to end"
```

---

## Self-Review

**Spec coverage.** Level model → Task 1. Crossing and composed labels → Task 2. Nested directories → Task 3. Three refusals → Task 4. `W-REPL-DETERMINISTIC` → Task 5. `order: randomized`, the no-batch case, and `order_seed` derivation → Task 6. `read_upstream` → Task 7. `sweep.yaml` fields → Task 8. Acceptance → Task 9. `E-REPL-ORDER-UNSUPPORTED` retires in Task 4. No spec section is unassigned.

**Placeholders.** None: every code step carries the code, every test step carries the test. Four tasks name an existing test helper (`_Step`, `make_io`, `run_a_project`, `write_config`) rather than inventing one, and each says explicitly to read the file and match its idiom — a deliberate instruction, not a gap.

**Type consistency.** `RepeatLevel(kind, members)` with `n` as a property is used identically in Tasks 1, 2, 6, and 8. `cross_levels(levels) -> list[Repeat]` returns the existing `Repeat`, so `execute_plan`'s `repeats: list[Repeat]` parameter is unchanged — that is why Task 3 is nearly a no-op. `realize_order(pairs, levels, mode, order_seed)` is called in Task 8 exactly as defined in Task 6. `order_seed_for(digest)` returns `int`, and Task 8 passes `order_seed or 0` into `realize_order` while recording `None` in `sweep.yaml` — deliberate, since `as_declared` ignores the seed and the record should not imply a shuffle happened.

**Three assumptions verified against the codebase before writing, because plan text has been this project's weakest artifact.** `Execution` takes six fields with `step_cls` first, so Task 3's tests construct it fully. `StepIO.__init__` carries no condition of its own, so Task 7 adds two parameters rather than "checking whether" they exist. `validate` never imports the user's experiment — `command_run` loads it separately, *after* validating — which is why Task 5 exists at all instead of being three lines inside Task 4.

**The risk this plan carries.** Task 5 changes what `validate` is allowed to do. Importing user code can fail any way user code can fail, and `validate` must report rather than raise, so `E-ENTRYPOINT-IMPORT` catching broadly is deliberate. The mitigation is that a broken step module becomes a *finding* at validate time instead of a traceback at run time — an improvement, but a behaviour change worth watching in review.
