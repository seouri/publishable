### Task 1: `Comparison` and contrast resolution

**Files:**
- Create: `src/publishable/contrasts.py`
- Test: `tests/test_contrasts.py`

**Interfaces:**
- Consumes: `sweep.Condition` — frozen, with `index: int`, `label: str | None`, `values` (read-only mapping), `is_baseline: bool`.
- Produces:
  - `@dataclass(frozen=True) class Comparison: id: str; of: int; against: int; within: dict[str, str] | None`
  - `resolve_contrasts(config: dict[str, Any], conditions: list["Condition"]) -> list[Comparison]`

`of` and `against` are **condition indices**, resolved from the labels the config names. `docs/reference.md` § Contrasts: `of`/`against` name conditions by label — the selector property S3a's label grammar exists to provide, so a person can write one down without seeing the directory.

**Two sources, one list.** Every non-baseline condition yields a `vs_baseline` comparison against the baseline; each `statistics.contrasts` entry yields one more. A run with no baseline and no declared entries yields `[]`.

- [ ] **Step 1: Write the failing tests**

```python
def _cond(i, label, baseline=False):
    return Condition(index=i, label=label, values={}, is_baseline=baseline)


def test_no_baseline_and_no_declared_contrasts_yields_nothing():
    conds = [_cond(0, "method=pearson"), _cond(1, "method=spearman")]
    assert resolve_contrasts({}, conds) == []


def test_each_non_baseline_condition_compares_against_the_baseline():
    conds = [_cond(0, "baseline", baseline=True),
             _cond(1, "method=spearman"), _cond(2, "method=kendall")]
    got = resolve_contrasts({}, conds)
    assert [(c.of, c.against) for c in got] == [(1, 0), (2, 0)]
    assert [c.id for c in got] == ["method=spearman", "method=kendall"]


def test_a_declared_contrast_resolves_labels_to_indices():
    conds = [_cond(0, "shift=normal"), _cond(1, "shift=abnormal")]
    cfg = {"statistics": {"contrasts": [
        {"id": "sensitivity", "of": "shift=abnormal", "against": "shift=normal"}]}}
    got = resolve_contrasts(cfg, conds)
    assert [(c.id, c.of, c.against, c.within) for c in got] == [("sensitivity", 1, 0, None)]


def test_a_declared_contrast_carries_its_within_stratum():
    conds = [_cond(0, "shift=normal"), _cond(1, "shift=abnormal")]
    cfg = {"statistics": {"contrasts": [
        {"id": "sens_f", "of": "shift=abnormal", "against": "shift=normal",
         "within": {"sex": "f"}}]}}
    assert resolve_contrasts(cfg, conds)[0].within == {"sex": "f"}


def test_declared_contrasts_come_after_the_baseline_ones():
    """Order is the record's order, and vs_baseline is the documented default."""
    conds = [_cond(0, "baseline", baseline=True), _cond(1, "method=spearman")]
    cfg = {"statistics": {"contrasts": [
        {"id": "extra", "of": "method=spearman", "against": "baseline"}]}}
    assert [c.id for c in resolve_contrasts(cfg, conds)] == ["method=spearman", "extra"]
```

Build `Condition` however `tests/test_sweep.py` already does — **read it first** and reuse that idiom; `_cond` above stands for whatever it uses.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_contrasts.py -v`
Expected: FAIL — the module does not exist.

- [ ] **Step 3: Implement**

```python
"""Which comparisons a config asks for. Pure: config and conditions in, list out.

`docs/reference.md` § Contrasts: `of` and `against` name conditions **by label**,
which is the selector property the condition-label grammar exists to provide — a
label has to be something a person can write down without seeing the directory.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from publishable.sweep import Condition


@dataclass(frozen=True)
class Comparison:
    id: str
    of: int
    against: int
    within: dict[str, str] | None = None


def resolve_contrasts(
    config: dict[str, Any], conditions: list["Condition"]
) -> list[Comparison]:
    """Every non-baseline condition against the baseline, then declared entries.

    A run with no baseline and no `statistics.contrasts` compares nothing, and
    the record carries no `vs_baseline` block at all — an empty one would claim
    a comparison was made and found nothing.
    """
    by_label = {c.label: c.index for c in conditions if c.label is not None}
    out: list[Comparison] = []
    baseline = next((c for c in conditions if c.is_baseline), None)
    if baseline is not None:
        for c in conditions:
            if c.index != baseline.index and c.label is not None:
                out.append(Comparison(id=c.label, of=c.index, against=baseline.index))
    for entry in ((config.get("statistics") or {}).get("contrasts") or []):
        out.append(
            Comparison(
                id=str(entry.get("id")),
                of=by_label[entry["of"]],
                against=by_label[entry["against"]],
                within=entry.get("within"),
            )
        )
    return out
```

`by_label[...]` raising a `KeyError` on an unresolvable label is acceptable **only because Task 2 refuses that at validate time**; note it in a comment so the next reader knows the guard exists elsewhere.

- [ ] **Step 4: Run to verify they pass, then commit**

```bash
uv run pytest tests/test_contrasts.py -v && uv run ruff check . && uv run mypy
git add src/publishable/contrasts.py tests/test_contrasts.py
git commit -m "Resolve which comparisons a config asks for"
```

---

