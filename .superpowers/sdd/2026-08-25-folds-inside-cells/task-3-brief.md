## Task 3

**Corrections that bind this task: C4, C10, C25.** **Ruling LL binds this task**: `fold_basis`
answers one question and is not touched.

**Build `units.cell_fold_basis(roster, cluster_by, cells)`.**

```python
def cell_fold_basis(
    roster: UnitList,
    cluster_by: str | None,
    cells: Mapping[tuple[tuple[str, str], ...], frozenset[str]],
) -> int:
```

The minimum over **non-empty** cells of `fold_basis(sub_roster, cluster_by)`, where each sub_roster
is built from `roster` **in roster order**. **One number, not two, and not a mapping** — the return
type is `int`, exactly as `fold_basis`'. An empty `cells`, or one whose cells are all empty, returns
`fold_basis(roster, cluster_by)` — the one-cell reduction.

**Docstring must say:** that `fold_basis` is deliberately unchanged and why (its third caller asks a
different question — `limits.min_clusters`' denominator, over the whole unit table a resample draws
from); and that returning a per-cell mapping is forbidden for the reason `fold_basis`' own docstring
gives.

**Fixture (F2, the one every later task reuses):** 16 units; `control` = clusters `A`×5, `B`×3;
`treatment` = `C`×4, `D`×3, `E`×1; **clusters nest inside arms, no spanning cluster** (C1's fixture
deliberately has one and is not used here). Computed literals: cell cluster counts **2** and **3**;
`cell_fold_basis` clustered = **2**, unclustered = **8**; whole-roster `fold_basis` clustered = **5**,
unclustered = **16**. **Cells with different cluster counts, so "minimum" and "first" differ.**

**Mutations:** MU-3 (`max` for `min` → `{kind: fold, k: 3}` must be refused: max 3 clears, min 2
refuses), MU-4 (return the first cell's basis → run the fixture with the cells in **both** orders,
naming them so one sorts first and the other last; a single order rules out only one wrong answer).

**Must not touch:** `fold_basis` — signature, body, docstring or tests.

---

# Batch B — the hoist and validate's cell view

