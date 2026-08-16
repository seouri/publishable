## Task 7: The draw's authority, and the shape that can express it

**Files:** Modify `src/publishable/units.py`, `src/publishable/cli.py`, `src/publishable/artifacts.py`; Test `tests/test_units.py`, `tests/test_cli.py`

**The seam, and the task most likely to produce this project's recurring defect.** `arms_of`'s docstring calls a second notion of arm membership *"the validate-clean-then-disagree gap in a new shape"*. `validate` needs membership too, so the draw cannot live in the runner.

`arm_members`' `axes` parameter is `Mapping[str, tuple[str, Sequence[str]]]` — **a column and levels. A drawn axis has no column.**

**Produces:**

```python
@dataclass(frozen=True)
class ArmPlan:
    """One axis's realized membership: level -> unit keys, roster order."""
    levels: tuple[str, ...]
    members: Mapping[str, tuple[str, ...]]
    seed: int | None       # the realized draw seed; None under `by_attribute`
    strata: tuple[str, ...]  # the realized `stratify_by`; empty under `by_attribute`
```

and `assignment_for(roster, axis, block, levels, digest, clusters) -> ArmPlan`, dispatching on `block["method"]`: `by_attribute` calls `arms_of` unchanged; `random`/`blocked` raise `NotImplementedError` **until tasks 8 and 10** — an explicit hole, not a silent fallback.

- [ ] **Step 1: Write the failing test** — `by_attribute` through the new type gives exactly what `arms_of` gives today, over `_arm_roster12`'s 7/5 split, with `seed is None` and `strata == ()`.
- [ ] **Step 2–4:** Fail, implement, pass. Change `arm_members`' parameter type, `_resolved_group_axes`' return type, and `build_allocation_document`'s parameter.
- [ ] **Step 5: The recomputation check.** `build_allocation_document` calls `arms_of` a **second** time on the same axes. Under a draw a second call must be provably identical, or the plan must be computed once and passed. **Decide, implement, and say which in the docstring.** Assert it: the plan the runner narrows with and the plan `allocation.json` records must be the same object or provably equal.
- [ ] **Step 6: Mutation** — make `assignment_for` return a fresh partition rather than the shared plan; a test must fail. If none does, nothing pins the single authority.
- [ ] **Step 7: Commit.**

---

