## Task 12: The arm is a subset view of the one roster

**Files:** Modify `src/publishable/cli.py`, `src/publishable/units.py`; Test `tests/test_cli.py`

**The acceptance bar H2 deferred:** two conditions' rosters must **differ**, and handing them the same roster must be impossible rather than merely avoided.

**An arm is a view, never a re-resolution.** `Unit` is frozen and hashable by key *because* one roster is resolved per run and shared; re-resolving per condition would break `units_hash` and every provenance claim on it.

### First: `groups` with `allocation: within` must be refused

**A gap tasks 7–8 found that no task owned.** § Validation carries *Arms need allocation* —
*"`sweep.groups` declares arms but `allocation` is `within`, which says every unit appears in every
condition"* — and **it is unimplemented**. Verified: no emit site exists.

Once task 17 retires the two refusals, that config **validates clean and hands every condition the
whole roster** — which is exactly *"two identical measurements reported as two arms"*, the outcome
task 20 step 6 must show is structurally impossible and the reason H2 deferred `groups` to H3 at all.
`between` is not the only way to reach the bar; `within` is the way to defeat it.

Implement the row, with its identifier and a control (`between` + `groups` draws nothing). This is
**the same task as the subset view** because both answer "can a condition ever be handed the whole
roster when arms are declared" — and closing one without the other looks complete from inside itself,
the shape three whole-branch reviews have now caught.

- [ ] **Step 1: Write the failing test**

```python
def test_two_arms_get_different_rosters_and_neither_is_the_whole_roster():
    """The bar H2 set: 'a groups axis that expanded conditions while handing each
    the same roster would report two identical measurements as two arms'.
    12 units, 7 control and 5 treatment — deliberately uneven, so the two arms
    cannot be confused with each other or with the roster by size alone."""
    ...
    assert sizes == {7, 5} and 12 not in sizes
```

- [ ] **Step 2–4:** Fail, implement, pass. **`units_hash` over the full roster is unchanged** — assert it.
- [ ] **Step 5: Two mutations** — hand every condition the whole roster (the size assertion fails); re-resolve per condition (the `units_hash` assertion fails).
- [ ] **Step 6: Commit.**

---

