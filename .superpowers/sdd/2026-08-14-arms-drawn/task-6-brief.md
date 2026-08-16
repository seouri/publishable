## Task 6: The `assign.seed` derivation

**Files:** Modify `src/publishable/units.py` (or a new module — argue the choice); Test `tests/test_units.py`

**Copy `sweep.sample_seed_for`'s shape, not `partition_units`'.** `partition_units` seeds from the digest **only**; `BaseStep.derive_seed` mixes the execution seed. § What `auto` derives from specifies an axis's `assign.seed` as **digest + the axis name + the resolved roster**.

**Produces:** `assign_seed_for(block: Mapping[str, Any], axis: str, digest: str, roster: UnitList) -> int`

- [ ] **Step 1: Write the failing tests.** Four properties, each with the control that discriminates it:

```python
def test_a_pinned_assign_seed_is_returned_literally():
    """§ What `auto` derives from: 'pinning an integer is the deliberate act,
    and the one to take for anything you intend to cite', so a pinned seed must
    survive a roster change. Same block, two different rosters, same answer."""

def test_the_derived_seed_moves_with_the_roster():
    """'the roster changes, or any axis is added or edited'. Two rosters
    differing by one unit -> different seeds. THE CONTROL: the same roster in a
    different ORDER must also differ, because `units_hash` covers order and
    § Where units come from says two runs that resolved the same units in a
    different sequence did not allocate the same trial."""

def test_the_derived_seed_moves_with_the_axis_name():
    """Two axes over one roster and one digest draw differently, or a crossed
    design assigns both axes identically."""

def test_the_derived_seed_moves_with_the_digest():
    ...
```

- [ ] **Step 2: Run them; confirm each fails.**
- [ ] **Step 3: Implement.** Mix `digest`, the axis name and `units_hash(roster)`. **Do not compute the digest on the pinned path at all** — that is the property `sample_seed_for` documents and the reason a pinned seed is stable.
- [ ] **Step 4: Mutate** — drop each of the three inputs in turn; each must fail exactly the test named for it. **If dropping the axis name fails nothing, the axis-name test's two axes are not actually drawing.**
- [ ] **Step 5: Commit.**

---

