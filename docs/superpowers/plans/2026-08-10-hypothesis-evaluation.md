# Hypothesis evaluation (S5b) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A run evaluates each declared hypothesis against its results and records the verdict, including which number it compared and who computed that number.

**Architecture:** A pure `hypotheses.py` resolves each declared hypothesis to an observed block from one of three places — a `vs_baseline` delta, a declared contrast, or a summary `Estimate` — compares it against the declared threshold on the declared basis, and records the verdict. Its correction family is the sweep family's arithmetic with one parameter changed, so `correction.py` is generalized by family size rather than duplicated.

**Tech Stack:** Python 3.11+, `uv`, pytest, ruff, mypy, numpy, scipy.

## Global Constraints

- Python >= 3.11.
- Runtime dependencies are exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`. Adding one is out of scope.
- ruff: line-length 100, select `["E","F","I","UP","B"]`. mypy: strict over `src/`.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run mypy`. (`ruff format` reformats ~33 pre-existing files — do not run it; `ruff check` is the gate.)
- `×`, not `x`, for multiplication — including inside fenced blocks and commit messages.
- `hypotheses.py`, `correction.py`, `coercion.py`, `estimate.py`, `stats.py`, `strata.py`, `contrasts.py`, `sweep.py` are **pure**: no filesystem, and no runtime import of `config`, `artifacts`, `runner`, or `cli`.
- `artifacts.py` is the only module that writes inside a run directory.
- `validate.py` **collects** findings and never raises to report one — including on a config value of the wrong type. Guard before `len()`, `in`, iteration, or set membership.
- Every `E-`/`W-` identifier must have a test that produces it; for a validate-time code that means through `validate_config`, and for a run-time one through `main(["run", ...])`.
- **Grep the four documents before minting any identifier.** S5a's plan asserted the documents named none of its three codes; `reference.md` § Errors core raises named two. Only what is genuinely unnamed gets a `docs/superpowers/spec-defects.md` entry.
- The four documents in `docs/` are normative and lead. Where code cannot follow them, the document changes first and the gap is recorded in `spec-defects.md`.
- Unimplemented must mean **refused**, never silently ignored.
- **Do not amend a reviewed commit.** New commits only.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/hypotheses.py` *(new)* | **Pure.** Resolve a hypothesis to its observation; the verdict; the family |
| `src/publishable/correction.py` | Generalized by family size, so both families share one level arithmetic |
| `src/publishable/coercion.py` | The carried `Estimate.ci95` length and ordering rules |
| `src/publishable/validate.py` | Six documented rules, the `_check_shape` guard, and retiring the refusal |
| `src/publishable/cli.py` | `results.hypotheses` with `declared_in` |

**Read before starting:** `docs/superpowers/specs/2026-08-10-hypothesis-evaluation-design.md`, and `reference.md` § Pre-registration, § What a hypothesis is tested against, § A hypothesis may name a summary metric.

**Facts established while writing this plan, so no task re-derives them:**

- `correction.Member` has fields `where`, `condition_index`, `step`, `metric`, `delta`, `ci95`, `pool`, `diffs`, and a `__post_init__` requiring exactly one of `pool`/`diffs` whenever `ci95` is not `None`.
- `cli.py` builds `Member.where` as **`cond:{comp.of}`** — the condition *index*, not its label — and **`contrast:{comp.id}`**. A hypothesis naming `compare: {condition: "method=spearman"}` therefore resolves label → index before it can find its member.
- `correction.corrected_fields(members, method)` dedupes on `(where, step, metric)`, computes `family_shape`, then loops `rank_family` assigning `_level_for(method, family_size, rank)` and `_corrected_bounds(member, level)`. Only the family size differs for hypotheses.
- **A corrected bound must be rebuilt from the same evidence**, which lives in `Member.pool`/`Member.diffs`. So `hypotheses.py` needs the `Member` list `cli` already holds — a hypothesis cannot re-derive a bound from the record alone, because the record carries no draws.
- `E-HYPOTHESIS-UNSUPPORTED` is raised in `validate.py` under `if doc.get("hypotheses"):`.

---

### Task 1: Generalize `correction.py` by family size

**Files:**
- Modify: `src/publishable/correction.py`
- Test: `tests/test_correction.py`

**Interfaces:**
- Consumes: `Member`, `family_members`, `family_shape`, `rank_family`, `_level_for`, `_corrected_bounds` — all already in the module.
- Produces: `corrected_for(members: Sequence[Member], method: str, family_size: int, shape: dict[str, int]) -> dict[tuple[str, str, str], dict[str, Any]]`. `corrected_fields(members, method)` keeps its signature and becomes a thin caller.

- [ ] **Step 1: Write the failing tests**

```python
def test_corrected_for_takes_the_family_size_it_is_given():
    """The hypothesis family "counts the confirmatory hypotheses whose
    observations core computed, where a sweep's family counts comparisons ×
    metrics" — it "multiplies nothing". Only the size differs, so only the size
    is a parameter."""
    strong, weak = _two_member_family()
    got = corrected_for([strong, weak], "bonferroni", 7, {"hypotheses": 7})
    for entry in got.values():
        assert entry["correction_level"] == pytest.approx(0.05 / 7)
        assert entry["family_size"] == 7
        assert entry["family"] == {"hypotheses": 7}


def test_corrected_fields_still_computes_the_sweep_shape():
    """The existing caller keeps its behaviour: it passes the product, and its
    breakout still names comparisons and metrics."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "bonferroni")
    for entry in got.values():
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}
        assert entry["correction_level"] == pytest.approx(0.05 / 2)


def test_holm_ranks_within_whatever_family_size_it_is_handed():
    """Holm's level is α/(m−i+1), so a larger m makes rank 1 tighter. Passing a
    size the members did not imply is exactly what the hypothesis family does."""
    strong, weak = _two_member_family()
    got = corrected_for([strong, weak], "holm", 5, {"hypotheses": 5})
    levels = sorted(e["correction_level"] for e in got.values())
    assert levels == [pytest.approx(0.05 / 5), pytest.approx(0.05 / 4)]
```

`_two_member_family()` already exists in that file from S4c — reuse it rather than writing a new fixture.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_correction.py -k corrected_for -v`
Expected: FAIL with `ImportError: cannot import name 'corrected_for'`. Add it to the file's existing `from publishable.correction import (...)` block, keeping it alphabetical or ruff `I001` fails.

- [ ] **Step 3: Implement**

Rename the body of `corrected_fields` into the general form and leave a thin caller:

```python
def corrected_for(
    members: Sequence[Member],
    method: str,
    family_size: int,
    shape: dict[str, int],
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """The corrected fields for one family, at a size the caller decides.

    Two families use this, and `reference.md` says they differ in exactly one
    respect: a sweep's family "counts comparisons × metrics", while a hypothesis
    family "multiplies nothing: it counts the confirmatory hypotheses whose
    observations core computed". Everything else — the ranking statistic, Holm's
    α/(m−i+1), Bonferroni's α/m, the interval rebuilt at a smaller α — is the
    same arithmetic, so it lives here once. Two spellings of one construction
    drifting apart is a defect this codebase has already shipped.
    """
    family = _family(members)
    if method == "none" or not family:
        return {}
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for rank, member in enumerate(rank_family(family), start=1):
        level = _level_for(method, family_size, rank)
        bounds = None if level is None else _corrected_bounds(member, level)
        out[(member.where, member.step, member.metric)] = {
            "ci95_corrected": None if bounds is None else [bounds[0], bounds[1]],
            "correction": method,
            "correction_level": level,
            "family_size": family_size,
            "family": dict(shape),
            "thin": level is not None and bounds is None,
        }
    return out


def corrected_fields(
    members: Sequence[Member], method: str
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """The sweep family: `corrected_for` at `family_shape`'s product.

    Kept as its own entry point rather than folded into the caller, because the
    product *is* this family's definition and `cli` should not have to restate
    it at the call site.
    """
    family = _family(members)
    if not family:
        return {}
    family_size, shape = family_shape(family)
    return corrected_for(members, method, family_size, shape)
```

Both need the same deduplicated family, so extract it rather than writing the comprehension twice — a duplicated logic block is a review finding in its own right, and here the two copies would have to stay in step:

```python
def _family(members: Sequence[Member]) -> list[Member]:
    """The correctable members, one per `(where, step, metric)`.

    Deduplicated because a key reaching this twice would take two ranks and
    inflate the family it is being corrected against.
    """
    return list({(m.where, m.step, m.metric): m for m in family_members(members)}.values())
```

Move `corrected_fields`' original docstring paragraphs about `none` and `thin` onto `corrected_for`, since that is where those behaviours now live.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`
Expected: all pass, unchanged. This is a refactor: every existing correction assertion must hold without edits. If one moves, stop and report it rather than adjusting the expectation.

- [ ] **Step 5: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| `corrected_for` ignores `family_size` and calls `family_shape` itself | `test_corrected_for_takes_the_family_size_it_is_given` |
| `corrected_fields` passes `len(family)` instead of the product | `test_corrected_fields_still_computes_the_sweep_shape` |

Apply each, run the named test, confirm it fails, revert with `git checkout -- src/publishable/correction.py`, confirm `git status --porcelain` is empty.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/correction.py tests/test_correction.py
git commit -m "Let a family declare its own size"
```

---

### Task 2: The carried `Estimate.ci95` rules

**Files:**
- Modify: `src/publishable/coercion.py`
- Test: `tests/test_coercion.py`
- Modify: `docs/superpowers/spec-defects.md` *(gitignored; write it anyway)*

**Interfaces:**
- Consumes: `Estimate`; `_coerce_estimate` in `coercion.py`, which already refuses a non-`summary` scope and a `ci95` without a `method`.
- Produces: one new identifier for a malformed `ci95`. **Grep first** — `grep -rn "E-STEP-ESTIMATE" src/ docs/` — and reuse an existing code if one covers it; mint `E-STEP-ESTIMATE-CI95` only if none does.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_ci95_that_is_not_two_elements_is_refused():
    """S5b indexes this list to read a bound. A one-element interval would raise
    an IndexError mid-run, after every execution has been spent."""
    for bad in ([0.4], [0.1, 0.2, 0.3], []):
        est = Estimate(value=0.5, ci95=bad, method="one-sided BCa")
        with pytest.raises(ContractError) as excinfo:
            coerce_scalars({"d": est}, "step04_agreement", scope="summary")
        assert excinfo.value.code == "E-STEP-ESTIMATE-CI95"


def test_a_reversed_ci95_is_refused():
    """`evaluate_on: ci95_lower` reads element 0. Reversed, it reads the upper
    bound and returns a verdict that looks authoritative and tested the wrong
    number — mechanically detectable, and not a judgement about the statistics."""
    est = Estimate(value=0.5, ci95=[0.6, 0.4], method="one-sided BCa")
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"d": est}, "step04_agreement", scope="summary")
    assert excinfo.value.code == "E-STEP-ESTIMATE-CI95"


def test_an_equal_pair_is_allowed():
    """A zero-width interval is legitimate — S4b established it for a point-mass
    bootstrap — so the check is `>`, not `>=`."""
    est = Estimate(value=0.5, ci95=[0.5, 0.5], method="point mass")
    got = coerce_scalars({"d": est}, "step04_agreement", scope="summary")["d"]
    assert got.ci95 == [0.5, 0.5]
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_coercion.py -k ci95 -v`
Expected: the first two FAIL — no such identifier is raised.

- [ ] **Step 3: Implement**

In `_coerce_estimate`, after the existing `method` check and **after** the fields are coerced (so the comparison is between plain floats, not NumPy scalars):

```python
    if coerced_ci95 is not None:
        if len(coerced_ci95) != 2:
            raise ContractError(
                f"{where} gave {key!r} a ci95 of {len(coerced_ci95)} elements; an interval is "
                "exactly two, lower then upper, because a hypothesis evaluating on "
                "`ci95_lower` or `ci95_upper` reads one of them by position",
                code="E-STEP-ESTIMATE-CI95",
            )
        if coerced_ci95[0] > coerced_ci95[1]:
            raise ContractError(
                f"{where} gave {key!r} a ci95 whose lower bound {coerced_ci95[0]} exceeds its "
                f"upper bound {coerced_ci95[1]}; reversed, `evaluate_on: ci95_lower` would read "
                "the upper bound and report a verdict against the wrong number",
                code="E-STEP-ESTIMATE-CI95",
            )
```

Read the existing function first: it builds the coerced list inline inside the `Estimate(...)` construction. Restructure so the coerced list is a local you can check before constructing, and say in your report how you did it.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| Drop the length check | `test_a_ci95_that_is_not_two_elements_is_refused` |
| Drop the ordering check | `test_a_reversed_ci95_is_refused` |
| Use `>=` instead of `>` for the ordering check | `test_an_equal_pair_is_allowed` |

- [ ] **Step 6: Record the identifier**

Append a `docs/superpowers/spec-defects.md` entry naming what the document does and does not say: `reference.md` § `Estimate` states three rules and none of them concerns `ci95`'s shape, so this is a fourth rule core enforces without the document naming it. Say why S5b is where it became necessary — nothing indexed the list until `evaluate_on` did. If your Step 2 grep found the documents *do* name a code for this, say so and skip the entry.

- [ ] **Step 7: Commit**

```bash
git add src/publishable/coercion.py tests/test_coercion.py
git commit -m "Refuse an interval a bound test cannot read"
```

---

### Task 3: Resolve a hypothesis to its observation

**Files:**
- Create: `src/publishable/hypotheses.py`
- Test: `tests/test_hypotheses.py` *(new)*

**Interfaces:**
- Consumes: nothing at runtime. `Condition` and `Member` under `TYPE_CHECKING` only.
- Produces:
  - `@dataclass(frozen=True) class Observation: where: str | None; step: str; metric: str; block: dict[str, Any] | None; rests_on: str`
  - `resolve(hyp: dict[str, Any], *, label_to_index: dict[str, int], vs_baseline, contrasts, summary) -> Observation`

`where` is `None` for a summary-metric hypothesis (there is no member to correct); otherwise it is `cond:{index}` or `contrast:{id}`, matching how `cli` names a `Member`. `rests_on` is `"computed"` for the two comparison arms and `"reported"` for the summary arm. `block` is the record entry found, or `None` when nothing matched.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_hypotheses.py`:

```python
import pytest

from publishable.hypotheses import Observation, resolve

_VS_BASELINE = {1: {"step03_analyze": {"r": {"delta": 0.026, "ci95": [-0.007, 0.059]}}}}
_CONTRASTS = [
    {"id": "sensitivity", "of": "01_a", "against": "00_b",
     "step03_screen": {"auroc": {"delta": 0.04, "ci95": [0.01, 0.07]}}}
]
_SUMMARY = {
    "step04_agreement": {
        "s_within": {"value": 0.9931, "reported": True, "ci95": [0.9931, 1.0],
                     "n": None, "method": "one-sided BCa"}
    }
}


def _resolve(hyp):
    return resolve(
        hyp,
        label_to_index={"method=spearman": 1},
        vs_baseline=_VS_BASELINE,
        contrasts=_CONTRASTS,
        summary=_SUMMARY,
    )


def test_a_condition_hypothesis_reads_that_conditions_vs_baseline_block():
    """`compare` says where; `metric` says what. The label resolves to a
    condition index because that is how `cli` addresses a Member."""
    got = _resolve({
        "id": "h1", "metric": "step03_analyze.r",
        "compare": {"condition": "method=spearman", "to": "baseline"},
    })
    assert got == Observation(
        where="cond:1", step="step03_analyze", metric="r",
        block={"delta": 0.026, "ci95": [-0.007, 0.059]}, rests_on="computed",
    )


def test_a_contrast_hypothesis_reads_that_contrast_entry():
    got = _resolve({
        "id": "s", "metric": "step03_screen.auroc", "compare": {"contrast": "sensitivity"},
    })
    assert got.where == "contrast:sensitivity"
    assert got.block == {"delta": 0.04, "ci95": [0.01, 0.07]}
    assert got.rests_on == "computed"


def test_a_summary_hypothesis_takes_no_compare_and_rests_on_reported():
    """`reference.md`: a summary metric "is one value per run rather than a
    contrast between conditions", so it takes no `compare` — and core did not
    derive it, which is the whole of what `verdict_rests_on` records."""
    got = _resolve({"id": "h2", "metric": "step04_agreement.s_within"})
    assert got.where is None
    assert got.rests_on == "reported"
    assert got.block["value"] == 0.9931


def test_an_unresolvable_metric_yields_no_block_rather_than_raising():
    """A hypothesis may name a metric no run produced — its step failed, or every
    unit was ineligible. The verdict records that rather than a boolean, and a
    pure resolver has no diagnostic to raise into."""
    got = _resolve({
        "id": "h1", "metric": "step03_analyze.nosuch",
        "compare": {"condition": "method=spearman", "to": "baseline"},
    })
    assert got.block is None
    assert got.where == "cond:1"


def test_an_unknown_condition_label_yields_no_block():
    got = _resolve({
        "id": "h1", "metric": "step03_analyze.r",
        "compare": {"condition": "nosuch", "to": "baseline"},
    })
    assert got.block is None
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_hypotheses.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'publishable.hypotheses'`.

- [ ] **Step 3: Implement**

Create `src/publishable/hypotheses.py`:

```python
"""Which number a declared hypothesis is about, and what the verdict says.

Pure: results and config in, verdict entries out.

`docs/reference.md` § Pre-registration: the config "is written before the run
and hashed at run start. That's the mechanical property pre-registration asks
for, so core lets you use it: declare what you *expect*, not only what you'll
compute."
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class Observation:
    """Where a hypothesis's number came from, and the record entry holding it.

    `where` addresses the `correction.Member` that built the entry — `cond:<index>`
    or `contrast:<id>`, the same strings `cli` uses — so a bound test can rebuild
    the interval at the hypothesis family's own level. It is `None` for a summary
    metric, which core did not compute and therefore cannot re-derive.

    `block` is `None` when nothing matched: a hypothesis may name a metric no run
    produced. That is recorded, not raised — `reference.md` gives no diagnostic
    for it, and a verdict of `false` would be indistinguishable from a claim that
    was tested and failed.
    """

    where: str | None
    step: str
    metric: str
    block: dict[str, Any] | None
    rests_on: str


def resolve(
    hyp: dict[str, Any],
    *,
    label_to_index: dict[str, int],
    vs_baseline: dict[int, dict[str, dict[str, Any]]] | None,
    contrasts: list[dict[str, Any]] | None,
    summary: dict[str, dict[str, Any]] | None,
) -> Observation:
    """The one number this hypothesis is about, from one of three places.

    `reference.md` § What a hypothesis is tested against: "`metric` is required in
    every form, because `compare` says *where* and never *what*." A contrast
    reports one value per step metric exactly as a condition does, so `compare`
    alone would leave the quantity under test unnamed.
    """
    step, _, metric = str(hyp.get("metric", "")).partition(".")
    compare = hyp.get("compare")
    if not isinstance(compare, dict):
        block = (summary or {}).get(step, {}).get(metric)
        return Observation(
            where=None, step=step, metric=metric,
            block=block if isinstance(block, dict) else None, rests_on="reported",
        )
    if "contrast" in compare:
        cid = str(compare["contrast"])
        for entry in contrasts or []:
            if entry.get("id") == cid:
                found = entry.get(step, {}).get(metric) if isinstance(entry.get(step), dict) else None
                return Observation(
                    where=f"contrast:{cid}", step=step, metric=metric,
                    block=found if isinstance(found, dict) else None, rests_on="computed",
                )
        return Observation(
            where=f"contrast:{cid}", step=step, metric=metric, block=None, rests_on="computed"
        )
    index = label_to_index.get(str(compare.get("condition")))
    if index is None:
        return Observation(
            where=None, step=step, metric=metric, block=None, rests_on="computed"
        )
    found = (vs_baseline or {}).get(index, {}).get(step, {}).get(metric)
    return Observation(
        where=f"cond:{index}", step=step, metric=metric,
        block=found if isinstance(found, dict) else None, rests_on="computed",
    )
```

Delete the empty `if TYPE_CHECKING: pass` block if nothing needs it — ruff will flag the unused import otherwise.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_hypotheses.py -v && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| Return `rests_on="computed"` for the summary arm | `test_a_summary_hypothesis_takes_no_compare_and_rests_on_reported` |
| Use the condition *label* in `where` instead of the index | `test_a_condition_hypothesis_reads_that_conditions_vs_baseline_block` |
| Raise instead of returning `block=None` on an unknown metric | `test_an_unresolvable_metric_yields_no_block_rather_than_raising` |

- [ ] **Step 6: Commit**

```bash
git add src/publishable/hypotheses.py tests/test_hypotheses.py
git commit -m "Find the number a hypothesis is about"
```

---

### Task 4: The verdict

**Files:**
- Modify: `src/publishable/hypotheses.py`
- Test: `tests/test_hypotheses.py`

**Interfaces:**
- Consumes: `Observation` from Task 3.
- Produces: `verdict_for(hyp: dict[str, Any], obs: Observation, bounds: tuple[float, float] | None) -> dict[str, Any]` returning the keys `observed`, `verdict_evaluated_on`, `supported`, `verdict_rests_on`. `bounds` is the corrected interval when this hypothesis is in the family and a correction applies, and `None` otherwise — Task 5 computes it; here it is a parameter.

- [ ] **Step 1: Write the failing tests**

```python
from publishable.hypotheses import verdict_for  # add to the existing import


_H1 = {
    "id": "h1", "kind": "confirmatory", "metric": "step03_analyze.r",
    "compare": {"condition": "method=spearman", "to": "baseline"},
    "direction": "greater", "threshold": 0.02,
}


def _obs_h1():
    return Observation(
        where="cond:1", step="step03_analyze", metric="r",
        block={"delta": 0.026, "ci95": [-0.007, 0.059]}, rests_on="computed",
    )


def test_the_worked_examples_h1_is_supported_on_the_observed_value():
    """`reference.md` § Pre-registration: "The observed delta of 0.026 clears the
    declared threshold of 0.02, so `h1` is supported on `observed`"."""
    got = verdict_for({**_H1, "evaluate_on": "observed"}, _obs_h1(), None)
    assert got["supported"] is True
    assert got["verdict_evaluated_on"] == "observed"
    assert got["verdict_rests_on"] == "computed"


def test_the_same_hypothesis_is_unsupported_on_the_lower_bound():
    """The other half of the same paragraph: "the same delta's interval over 228
    units, [−0.007, 0.059], does not exclude zero, so the same hypothesis written
    `evaluate_on: ci95_lower` would come back `supported: false`. Neither verdict
    is wrong; they answer different questions."

    An implementation ignoring `evaluate_on` passes the test above and fails this
    one, which is why the pair is the sharpest test in the slice."""
    got = verdict_for({**_H1, "evaluate_on": "ci95_lower"}, _obs_h1(), None)
    assert got["supported"] is False
    assert got["verdict_evaluated_on"] == "ci95_lower"


def test_direction_less_inverts_the_comparison():
    """An equivalence claim reads the upper bound: `reference.md` — "a mean
    absolute difference of 0.01 with an interval of [0.001, 0.30] passes
    `direction: less, threshold: 0.05` on the observed value and fails on the
    upper bound — and the second verdict is the correct one"."""
    obs = Observation(
        where="cond:1", step="s", metric="m",
        block={"delta": 0.01, "ci95": [0.001, 0.30]}, rests_on="computed",
    )
    hyp = {"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
           "direction": "less", "threshold": 0.05}
    assert verdict_for({**hyp, "evaluate_on": "observed"}, obs, None)["supported"] is True
    assert verdict_for({**hyp, "evaluate_on": "ci95_upper"}, obs, None)["supported"] is False


def test_a_corrected_bound_is_what_a_bound_test_reads_when_one_is_supplied():
    """`reference.md`: a bound test "reads the corrected bound at the level *this*
    family implies". The raw interval would say supported; the corrected one does
    not, and the corrected one is the answer."""
    obs = Observation(
        where="cond:1", step="s", metric="m",
        block={"delta": 0.10, "ci95": [0.01, 0.19]}, rests_on="computed",
    )
    hyp = {"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
           "direction": "greater", "threshold": 0.0, "evaluate_on": "ci95_lower"}
    assert verdict_for(hyp, obs, None)["supported"] is True
    assert verdict_for(hyp, obs, (-0.02, 0.22))["supported"] is False


def test_a_summary_hypothesis_reads_its_value_and_rests_on_reported():
    obs = Observation(
        where=None, step="step04_agreement", metric="s_within",
        block={"value": 0.9931, "reported": True, "ci95": [0.9931, 1.0],
               "n": None, "method": "one-sided BCa"},
        rests_on="reported",
    )
    hyp = {"id": "h2", "metric": "step04_agreement.s_within",
           "direction": "greater", "threshold": 0.99, "evaluate_on": "observed"}
    got = verdict_for(hyp, obs, None)
    assert got["supported"] is True
    assert got["verdict_rests_on"] == "reported"
    assert got["observed"]["method"] == "one-sided BCa"


def test_an_unresolvable_observation_is_supported_null_not_false():
    """A `false` would be indistinguishable from a claim that was tested and
    failed. `reference.md` covers no such case, so this is recorded in
    spec-defects rather than derived from it."""
    obs = Observation(where="cond:1", step="s", metric="m", block=None, rests_on="computed")
    got = verdict_for({"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
                       "direction": "greater", "threshold": 0.0,
                       "evaluate_on": "observed"}, obs, None)
    assert got["supported"] is None
    assert got["observed"] is None


def test_a_bound_test_on_a_metric_with_no_interval_is_supported_null():
    """Asking for a bound a metric does not have is unanswerable, not false."""
    obs = Observation(where="cond:1", step="s", metric="m",
                      block={"delta": 0.5, "ci95": None}, rests_on="computed")
    got = verdict_for({"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
                       "direction": "greater", "threshold": 0.0,
                       "evaluate_on": "ci95_lower"}, obs, None)
    assert got["supported"] is None
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_hypotheses.py -k verdict -v`
Expected: FAIL with `ImportError: cannot import name 'verdict_for'`.

- [ ] **Step 3: Implement**

Append to `hypotheses.py`:

```python
_POINT_KEYS = ("delta", "value")


def _observed_block(obs: "Observation", bounds: tuple[float, float] | None) -> dict[str, Any] | None:
    """What the record shows as `observed`, in the shape its source implies.

    `reference.md` shows two: `{delta, ci95, ci95_corrected}` for a comparison and
    `{value, ci95, method}` for a summary metric. Both are the entry's own fields,
    not a reshaping of them, so a reader can find the same numbers in the block
    the hypothesis names.
    """
    if obs.block is None:
        return None
    out = {k: obs.block[k] for k in ("delta", "value", "ci95", "method") if k in obs.block}
    if bounds is not None:
        out["ci95_corrected"] = [bounds[0], bounds[1]]
    return out


def _tested_number(
    obs: "Observation", evaluate_on: str, bounds: tuple[float, float] | None
) -> float | None:
    """The one number the verdict compares, or `None` when there isn't one.

    A bound test reads the corrected interval when this hypothesis is in a
    corrected family, and the raw one otherwise — `reference.md`: "Correction
    reaches a verdict only through a bound", and counted-iff-corrected decides
    whether there is a corrected bound at all.
    """
    if obs.block is None:
        return None
    if evaluate_on == "observed":
        for key in _POINT_KEYS:
            if key in obs.block and obs.block[key] is not None:
                return float(obs.block[key])
        return None
    interval = bounds if bounds is not None else obs.block.get("ci95")
    if not interval:
        return None
    return float(interval[0] if evaluate_on == "ci95_lower" else interval[1])


def verdict_for(
    hyp: dict[str, Any], obs: "Observation", bounds: tuple[float, float] | None
) -> dict[str, Any]:
    """The verdict fields for one hypothesis.

    `verdict_evaluated_on` is spelled out rather than echoing the config's
    `evaluate_on` because `reference.md` says "a record field one letter from a
    config field is a typo waiting to be read as agreement" — a reader must see
    which question was asked without reconstructing it.

    `supported` is `None`, never `False`, when there is no number to compare: a
    `False` would be indistinguishable from a claim that was tested and failed.
    """
    evaluate_on = str(hyp.get("evaluate_on") or "observed")
    number = _tested_number(obs, evaluate_on, bounds)
    threshold = hyp.get("threshold")
    supported: bool | None = None
    if number is not None and isinstance(threshold, (int, float)) and not isinstance(threshold, bool):
        supported = number > threshold if hyp.get("direction") == "greater" else number < threshold
    return {
        "observed": _observed_block(obs, bounds),
        "verdict_evaluated_on": evaluate_on,
        "supported": supported,
        "verdict_rests_on": obs.rests_on,
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_hypotheses.py -v && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| Ignore `evaluate_on`; always use the point estimate | `test_the_same_hypothesis_is_unsupported_on_the_lower_bound` |
| Treat `direction` as always `greater` | `test_direction_less_inverts_the_comparison` |
| Prefer `obs.block["ci95"]` over `bounds` when both exist | `test_a_corrected_bound_is_what_a_bound_test_reads_when_one_is_supplied` |
| Return `False` instead of `None` for an unresolvable observation | `test_an_unresolvable_observation_is_supported_null_not_false` |
| Read `ci95[1]` for `ci95_lower` | the `h1` pair |

- [ ] **Step 6: Commit**

```bash
git add src/publishable/hypotheses.py tests/test_hypotheses.py
git commit -m "Compare the number a hypothesis declared against the number it got"
```

---

### Task 5: The hypothesis family

**Files:**
- Modify: `src/publishable/hypotheses.py`
- Test: `tests/test_hypotheses.py`

**Interfaces:**
- Consumes: `Observation`, `verdict_for`; `correction.corrected_for` from Task 1; `correction.Member`.
- Produces: `evaluate(hyps, *, label_to_index, vs_baseline, contrasts, summary, members, method, parameters_hash) -> list[dict[str, Any]]`, the full verdict entries including `id`, `kind`, `declared_in`, and — for counted hypotheses only — `family_size` and `family`.

- [ ] **Step 1: Write the failing tests**

```python
from publishable.correction import Member
from publishable.hypotheses import evaluate  # add to the existing import


def _member(where, step, metric, delta, ci95):
    return Member(where=where, condition_index=1, step=step, metric=metric,
                  delta=delta, ci95=ci95, pool=None,
                  diffs=tuple(delta + 0.01 * ((i % 5) - 2) for i in range(60)))


def test_only_confirmatory_computed_hypotheses_are_counted():
    """`reference.md`: "Core's hypothesis family is the confirmatory hypotheses
    whose observations it computed, which keeps `family_size` predictable from
    the config." An exploratory one is evaluated and recorded, and counted by
    nothing."""
    hyps = [
        {"id": "a", "kind": "confirmatory", "metric": "s.m",
         "compare": {"contrast": "x"}, "direction": "greater", "threshold": 0.0,
         "evaluate_on": "ci95_lower"},
        {"id": "b", "kind": "exploratory", "metric": "s.m",
         "compare": {"contrast": "x"}, "direction": "greater", "threshold": 0.0,
         "evaluate_on": "ci95_lower"},
    ]
    got = evaluate(
        hyps, label_to_index={}, vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m": {"delta": 0.1, "ci95": [0.01, 0.19]}}}],
        summary={}, members=[_member("contrast:x", "s", "m", 0.1, (0.01, 0.19))],
        method="holm", parameters_hash="sha256:1a2b",
    )
    by_id = {e["id"]: e for e in got}
    assert by_id["a"]["family_size"] == 1
    assert by_id["a"]["family"] == {"hypotheses": 1}
    assert "family_size" not in by_id["b"]
    assert by_id["b"]["supported"] is not None   # still evaluated, just uncounted


def test_a_reported_estimate_hypothesis_is_evaluated_but_never_counted():
    """`reference.md`: its observation "is a reported `Estimate`, so core has
    nothing to correct — and therefore does not count it"."""
    got = evaluate(
        [{"id": "h2", "kind": "confirmatory", "metric": "step04.s",
          "direction": "greater", "threshold": 0.99, "evaluate_on": "observed"}],
        label_to_index={}, vs_baseline=None, contrasts=None,
        summary={"step04": {"s": {"value": 0.9931, "reported": True,
                                  "ci95": [0.9931, 1.0], "n": None, "method": "BCa"}}},
        members=[], method="holm", parameters_hash="sha256:1a2b",
    )
    assert got[0]["verdict_rests_on"] == "reported"
    assert got[0]["supported"] is True
    assert "family_size" not in got[0]


def test_every_verdict_carries_the_hash_that_declared_it():
    """`reference.md`: a hypothesis "carries the `parameters_hash` of the config
    that declared it. Add a hypothesis after seeing results and rerun, and the
    hash won't match the earlier run"."""
    got = evaluate(
        [{"id": "a", "kind": "confirmatory", "metric": "s.m", "compare": {"contrast": "x"},
          "direction": "greater", "threshold": 0.0, "evaluate_on": "observed"}],
        label_to_index={}, vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m": {"delta": 0.1, "ci95": [0.01, 0.19]}}}],
        summary={}, members=[], method="none", parameters_hash="sha256:1a2b",
    )
    assert got[0]["declared_in"] == "parameters_hash sha256:1a2b"


def test_the_hypothesis_family_is_its_own_size_not_the_sweeps():
    """Two confirmatory computed hypotheses over a sweep whose own family is
    larger. The level must come from 2, not from the sweep's count — the two
    families are corrected separately, which is the whole reason `family_size`
    is on the verdict at all."""
    hyps = [
        {"id": f"h{i}", "kind": "confirmatory", "metric": f"s.m{i}",
         "compare": {"contrast": "x"}, "direction": "greater", "threshold": 0.0,
         "evaluate_on": "ci95_lower"}
        for i in (1, 2)
    ]
    got = evaluate(
        hyps, label_to_index={}, vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m1": {"delta": 0.10, "ci95": [0.01, 0.19]},
                                     "m2": {"delta": 0.20, "ci95": [0.11, 0.29]}}}],
        summary={},
        members=[_member("contrast:x", "s", "m1", 0.10, (0.01, 0.19)),
                 _member("contrast:x", "s", "m2", 0.20, (0.11, 0.29))],
        method="bonferroni", parameters_hash="sha256:1a2b",
    )
    assert {e["family_size"] for e in got} == {2}
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_hypotheses.py -k "counted or family or declared_in" -v`
Expected: FAIL with `ImportError: cannot import name 'evaluate'`.

- [ ] **Step 3: Implement**

Append to `hypotheses.py`, importing `corrected_for` and `Member` from `publishable.correction` (both pure, so no cycle):

```python
def _is_counted(hyp: dict[str, Any], obs: "Observation") -> bool:
    """`reference.md`: the family "counts the confirmatory hypotheses whose
    observations core computed".

    Two exclusions, and neither is a special case: an exploratory hypothesis is
    not a confirmatory one, and a reported `Estimate` is not core's number to
    correct. Counted-iff-corrected is the same rule the sweep family follows.
    """
    return hyp.get("kind") == "confirmatory" and obs.rests_on == "computed" and obs.block is not None


def evaluate(
    hyps: Sequence[dict[str, Any]],
    *,
    label_to_index: dict[str, int],
    vs_baseline: dict[int, dict[str, dict[str, Any]]] | None,
    contrasts: list[dict[str, Any]] | None,
    summary: dict[str, dict[str, Any]] | None,
    members: Sequence["Member"],
    method: str,
    parameters_hash: str,
) -> list[dict[str, Any]]:
    """Every declared hypothesis, resolved, corrected where it counts, judged.

    The corrected bound is rebuilt from the same evidence as the raw one, at this
    family's level — which is why `members` is a parameter: the record carries no
    draws, so a bound cannot be re-derived from it.
    """
    resolved = [
        (hyp, resolve(hyp, label_to_index=label_to_index, vs_baseline=vs_baseline,
                      contrasts=contrasts, summary=summary))
        for hyp in hyps
    ]
    counted = [(h, o) for h, o in resolved if _is_counted(h, o)]
    by_key = {(m.where, m.step, m.metric): m for m in members}
    family_members_ = [
        by_key[(o.where, o.step, o.metric)]
        for _, o in counted
        if (o.where, o.step, o.metric) in by_key
    ]
    size = len(counted)
    fields = corrected_for(family_members_, method, size, {"hypotheses": size}) if size else {}
    out: list[dict[str, Any]] = []
    for hyp, obs in resolved:
        entry: dict[str, Any] = {
            "id": hyp.get("id"),
            "kind": hyp.get("kind"),
            "declared_in": f"parameters_hash {parameters_hash}",
        }
        corrected = fields.get((obs.where, obs.step, obs.metric)) if _is_counted(hyp, obs) else None
        bounds = None
        if corrected and corrected.get("ci95_corrected"):
            low, high = corrected["ci95_corrected"]
            bounds = (low, high)
        entry.update(verdict_for(hyp, obs, bounds))
        if _is_counted(hyp, obs):
            entry["family_size"] = size
            entry["family"] = {"hypotheses": size}
        out.append(entry)
    return out
```

Add `from collections.abc import Sequence` and move `Member` out of `TYPE_CHECKING` only if you reference it at runtime — you do not; keep it under `TYPE_CHECKING` and import `corrected_for` normally.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| Count exploratory hypotheses in `size` | `test_only_confirmatory_computed_hypotheses_are_counted` |
| Count a reported-`Estimate` hypothesis | `test_a_reported_estimate_hypothesis_is_evaluated_but_never_counted` |
| Attach `family_size` to every entry, counted or not | both of the above |
| Pass `len(members)` as the family size | `test_the_hypothesis_family_is_its_own_size_not_the_sweeps` |

- [ ] **Step 6: Commit**

```bash
git add src/publishable/hypotheses.py tests/test_hypotheses.py
git commit -m "Correct a hypothesis in its own family"
```

---

### Task 6: `validate`'s shape guard, form and metric rules

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `_check_shape`'s `_bad(key, value, kind)` helper and `E-CONFIG-SHAPE`; the loaded experiment, which `validate_config` already has for `W-REPL-DETERMINISTIC` and which carries each step's `scope`.
- Produces: two new identifiers for the metric and form rules. **Grep first**: `grep -rn "E-HYPOTHESIS" src/ tests/ docs/`.

**`E-HYPOTHESIS-UNSUPPORTED` stays in place for this task.** It fires alongside the new findings; the tests assert the new codes are *present*, not that they are alone. Task 8 retires it, in the same commit that makes `cli` evaluate.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_non_list_hypotheses_block_is_refused_without_raising(write_config):
    """`validate.py` collects and never raises. S4c shipped two crashes from a
    nested config value reaching a reader, and `hypotheses` is a new one."""
    for block in (5, True, "h1", {"id": "h1"}):
        assert "E-CONFIG-SHAPE" in codes(write_config({"hypotheses": block}))


def test_a_hypothesis_with_compare_and_no_metric_is_refused(write_config):
    """`reference.md`: "a contrast reports a value per step metric, so the
    quantity under test is unnamed"."""
    found = codes(write_config({
        "sweep": _TWO_CONDITIONS,
        "statistics": {"contrasts": [{"id": "x", "of": "method=spearman",
                                      "against": "baseline"}]},
        "hypotheses": [{"id": "h", "kind": "confirmatory", "compare": {"contrast": "x"},
                        "direction": "greater", "threshold": 0.0}],
    }))
    assert "E-HYPOTHESIS-METRIC" in found


_TWO_SCOPE_EXPERIMENT = """\
from publishable import BaseExperiment, BaseStep


class Step01Measure(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {}


class Step02Combine(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {}


class CohortPilotExperiment(BaseExperiment):
    steps = [Step01Measure, Step02Combine]
"""


@pytest.fixture
def write_config_two_scopes(git_repo: Path, write_config):
    """`write_config`, but the entrypoint declares a repeat step and a summary
    step — so `validate` can tell which scope a hypothesis's metric belongs to.
    Modelled on `write_config_nondet`, which is the same pattern for a different
    step property."""

    def _write(overrides: dict | None = None) -> Path:
        path = write_config(overrides)
        write_experiment_module(git_repo, _TWO_SCOPE_EXPERIMENT)
        return path

    return _write


def test_a_summary_metric_hypothesis_may_not_declare_compare(write_config_two_scopes):
    """`reference.md`: "a summary metric is one value per run, not a contrast
    between conditions — and a condition-step metric without `compare` is the
    same mistake inverted"."""
    found = codes(write_config_two_scopes({
        "sweep": _TWO_CONDITIONS,
        "hypotheses": [{"id": "h", "kind": "confirmatory",
                        "metric": "step02_combine.agreement",
                        "compare": {"condition": "method=spearman", "to": "baseline"},
                        "direction": "greater", "threshold": 0.9}],
    }))
    assert "E-HYPOTHESIS-FORM" in found


def test_a_condition_metric_hypothesis_must_declare_compare(write_config_two_scopes):
    """The same mistake inverted: a metric of a repeat-scoped step names a
    quantity that only exists per condition, so a hypothesis about it has to say
    which conditions it compares."""
    found = codes(write_config_two_scopes({
        "sweep": _TWO_CONDITIONS,
        "hypotheses": [{"id": "h", "kind": "confirmatory",
                        "metric": "step01_measure.r",
                        "direction": "greater", "threshold": 0.5}],
    }))
    assert "E-HYPOTHESIS-FORM" in found
```

Two things to confirm rather than assume, and report both: the exact step-name-to-module-attribute convention this repo uses (the fixture above guesses `step01_measure` and `step02_combine` from the class names — check how `BaseExperiment.steps` maps to the `step.metric` strings a config writes), and whether `write_experiment_module` is importable in that test file already. Adjust the fixture to what you find, keeping the assertions identical.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_validate.py -k hypothes -v`
Expected: FAIL — no such identifiers exist.

- [ ] **Step 3: Add the shape guard**

In `_check_shape`, beside the existing `statistics.contrasts` block:

```python
    hypotheses = doc.get("hypotheses")
    if hypotheses is not None and not isinstance(hypotheses, list):
        _bad("hypotheses", hypotheses, "list")
```

- [ ] **Step 4: Add the form and metric rules**

Write a `_check_hypotheses(doc, c, experiment)` called from `validate_config`, following `_check_contrasts`' shape: skip a non-list block (already refused upstream, and the guard is kept because the function is reachable directly from tests), refuse a non-mapping entry, then apply the two rules. A step's scope comes from the experiment's step list; a metric naming a step the experiment does not declare is its own case — decide whether that is one of these two rules or a third, and say which in your report.

- [ ] **Step 5: Run the full suite, then prove the tests discriminate**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

| Mutation | Must fail |
|---|---|
| Drop the `_check_shape` entry | `test_a_non_list_hypotheses_block_is_refused_without_raising` |
| Refuse only the summary-with-`compare` direction | the condition-without-`compare` test |

- [ ] **Step 6: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Check a hypothesis names one quantity in one form"
```

---

### Task 7: `validate`'s remaining rules

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `_check_hypotheses` from Task 6; `sweep.expand`; the declared `statistics.contrasts` ids.
- Produces: identifiers for the baseline, contrast and bound-exists rules, plus one warning for the inference-base rule. Grep before minting each.

Three rules and one warning, each already stated in `reference.md` § Validation:

| Rule | Fires when |
|---|---|
| Hypothesis needs baseline | `compare.to` is `baseline` and `sweep.baseline` is not declared |
| Hypothesis names a real contrast | `compare.contrast` names an id `statistics.contrasts` does not declare |
| Hypothesis bound exists | `evaluate_on` names a bound, and no metric this run computes could carry an interval — `data.units` undeclared **and** the template defines no `aggregate` |
| Hypothesis has an inference base | every metric will be `basis: repeats`: reportable but not testable (**warning**) |

- [ ] **Step 1: Write the failing tests**

Write one test per rule through `validate_config`, each asserting its identifier. For the bound-exists rule, the fixture needs a config where `data.units` is undeclared and the template contributes no `aggregate` — check what `generic` actually defines before assuming, since if it defines one the rule is unreachable that way and the fixture must differ. Report what you found.

For the warning, the discriminating case is a config that would otherwise be fine: every metric `basis: repeats`, a hypothesis naming one, and **no** bound requested — so the warning fires where the bound-exists *error* does not.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_validate.py -k "baseline or real_contrast or bound or inference" -v`

- [ ] **Step 3: Implement**

Extend `_check_hypotheses`. The baseline and contrast rules read `sweep.baseline` and the declared contrast ids; the bound rule reads `data.units` and the template. Keep each check independent — a hypothesis with two faults should report both, the way `_check_contrasts` reports a bad `of` and a bad `within` separately.

- [ ] **Step 4: Run the full suite, then prove each test discriminates**

For each of the four, apply the mutation that removes its check, confirm only its own test fails, restore, and confirm `git status --porcelain` is empty.

- [ ] **Step 5: Record any newly minted identifier**

One `docs/superpowers/spec-defects.md` entry covering whichever of this task's and Task 6's codes the four documents do not name — with the `reference.md` § Validation row each implements quoted, and a note that the row states the rule and names no code.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Check a hypothesis against the run it will be tested by"
```

---

### Task 8: Wire it, and retire the refusal

**Files:**
- Modify: `src/publishable/cli.py`, `src/publishable/validate.py`, `src/publishable/run_record.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `hypotheses.evaluate` from Task 5; the `members` list `cli` builds for the sweep family; `parameters_hash`, already computed in `command_run`.
- Produces: `results.hypotheses` in `run.yaml` — a list, or the key absent when nothing was declared.

**This task retires `E-HYPOTHESIS-UNSUPPORTED`**, in the same commit that makes `cli` evaluate, so nothing is accepted before it is honoured. Grep the tree afterwards: the identifier must be gone from `src/`, `tests/` and the four documents; hits under `docs/superpowers/` are history and stay.

- [ ] **Step 1: Write the failing test**

```python
def test_a_declared_hypothesis_gets_a_verdict(tmp_path, capsys, monkeypatch):
    """The slice end to end. A run with no `hypotheses` is unchanged; one with a
    hypothesis carries a verdict naming what it compared and who computed it."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman"]}},
        hypotheses=[{"id": "h1", "kind": "confirmatory",
                     "statement": "spearman exceeds pearson",
                     "metric": "step01_summarize_units.pred",
                     "compare": {"condition": "method=spearman", "to": "baseline"},
                     "direction": "greater", "threshold": 0.5,
                     "evaluate_on": "observed"}],
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    verdict = run["results"]["hypotheses"][0]
    assert verdict["id"] == "h1"
    assert verdict["supported"] is True          # the delta is exactly 1.0
    assert verdict["verdict_evaluated_on"] == "observed"
    assert verdict["verdict_rests_on"] == "computed"
    assert verdict["declared_in"].startswith("parameters_hash ")
    assert verdict["family_size"] == 1


def test_a_run_with_no_hypotheses_has_no_hypotheses_block(tmp_path, capsys, monkeypatch):
    """Absent, not empty — the rule `vs_baseline` and `contrasts` already follow."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(tmp_path, capsys=capsys, units=40)
    text = (doc["run_dir"] / "run.yaml").read_text()
    assert "hypotheses:" not in text
```

`run_a_project` passes `**overrides` as top-level config keys, so `hypotheses=[...]` reaches the config without a helper change — confirm that before relying on it.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_cli.py -k hypothes -v`
Expected: the first FAILs — the run is refused by `E-HYPOTHESIS-UNSUPPORTED` at exit 2.

- [ ] **Step 3: Retire the refusal**

Delete the `if doc.get("hypotheses"):` block raising `E-HYPOTHESIS-UNSUPPORTED` from `validate.py`, then grep as described above.

- [ ] **Step 4: Wire the evaluation**

In `command_run`, after `vs_baseline`, `contrasts_out` and the summary results all exist, call `hypotheses.evaluate` with the `members` list already built for the sweep family, `label_to_index` from `conditions`, the run's `parameters_hash`, and the declared `statistics.correction` (defaulting to `holm`). Pass the result to `assemble_run_yaml` as a new keyword, and have `run_record` place it at `results.hypotheses` — omitting the key entirely when the list is empty, matching how `vs_baseline` and `contrasts` are omitted.

Read how `contrasts` is threaded from `command_run` through `assemble_run_yaml` into `results` and follow it exactly; that is the closest sibling.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

Expected: all pass. Any test asserting `E-HYPOTHESIS-UNSUPPORTED` must be updated to the new behaviour, not deleted — report each one you touch.

- [ ] **Step 6: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| Pass `[]` for `members`, so no bound can be corrected | a bound-evaluating end-to-end test — write one, since the two above use `observed` |
| Write `results.hypotheses: []` when nothing is declared | `test_a_run_with_no_hypotheses_has_no_hypotheses_block` |

- [ ] **Step 7: Commit**

```bash
git add src/publishable/cli.py src/publishable/validate.py src/publishable/run_record.py tests/test_cli.py
git commit -m "Evaluate every declared hypothesis, and stop refusing them"
```

---

### Task 9: Exploratory and reported hypotheses end to end

**Files:**
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above. This task should need **zero** `src/` changes; if a test cannot pass without one, an earlier task left a gap — report it as a finding naming the source defect.

- [ ] **Step 1: Write the tests**

Three, each driving `main(["run", ...])`:

1. **An exploratory hypothesis is evaluated and uncounted.** One confirmatory and one exploratory hypothesis over the same metric: both carry `supported` and `verdict_evaluated_on`; only the confirmatory one carries `family_size`, and it is 1 rather than 2.
2. **A hypothesis naming a summary `Estimate` rests on `reported` and is uncounted.** Needs a `summary`-scoped step returning an `Estimate` — `tests/test_cli.py` gained fixtures for exactly this in S5a; reuse them rather than writing new ones. Assert `verdict_rests_on == "reported"`, a `supported` boolean, and no `family_size`.
3. **The sweep family is unmoved by declaring hypotheses.** Two runs differing only in the `hypotheses` block; a `vs_baseline` entry's `family_size` and `family` are identical. The two families are corrected separately, and this is the test that says so.

Write all three bodies in full, following the fixtures already in the file.

- [ ] **Step 2: Run them**

Run: `uv run pytest tests/test_cli.py -k "exploratory or reported_hypothesis or sweep_family_unmoved" -v`
Expected: PASS with no `src/` change.

- [ ] **Step 3: Run the whole gate**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py
git commit -m "Evaluate what the family does not count"
```

---

### Task 10: The acceptance test

**Files:**
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above. **Zero `src/` changes.**

- [ ] **Step 1: Write the pair the document pins**

One run, one metric, two hypotheses differing only in `evaluate_on` — mirroring `reference.md` § Pre-registration, where the observed delta clears its threshold while the interval's lower bound does not. Use `_METHOD_VARYING_STEP`, whose per-unit difference is exactly 1.0 with a *t* interval of width 0.1815155 at 40 units, so a threshold between the lower bound and the point estimate separates the two verdicts.

Assert, for each: `supported`, `verdict_evaluated_on`, `verdict_rests_on`, `declared_in`, and the `observed` block's keys. Compute the threshold from the fixture's own arithmetic and say in a comment why it sits where it does — a threshold chosen to make the test pass, without a stated reason, is the failure mode this project has hit repeatedly.

- [ ] **Step 2: Assert the full record shape once**

One assertion comparing a whole verdict entry against a literal dict, so a field silently disappearing is caught. `reference.md`: "A record that reported only `supported: true` would be the version worth distrusting."

- [ ] **Step 3: Run them, then the whole gate**

Run: `uv run pytest tests/test_cli.py -k acceptance -v`, then `uv run pytest -q && uv run ruff check . && uv run mypy`

If either test needs a `src/` change, fix the source gap it found and name the earlier task that should have covered it.

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py
git commit -m "Render the worked example's verdict both ways"
```

---

## After the last task

- [ ] Confirm `E-HYPOTHESIS-UNSUPPORTED` is gone from `src/`, `tests/` and the four documents.
- [ ] Re-read the design's § Scope and confirm every In row landed and nothing from the right-hand column crept in.
- [ ] Confirm `docs/superpowers/spec-defects.md` carries entries for every identifier this slice minted that the four documents do not name, and for the two things the documents do not settle (`supported: null` for an unresolvable observation; `Estimate.ci95`'s shape rules).
- [ ] Run the **whole-branch review** over `merge-base(main, HEAD)..HEAD` on the most capable model available. It has found a Critical on every slice but the last three. Do not merge without it.
- [ ] **S5 closes with this slice, and the spine's checkpoint follows** — every `spec-defects.md` entry gets reconciled against the four documents. That is its own piece of work, not part of this branch.
