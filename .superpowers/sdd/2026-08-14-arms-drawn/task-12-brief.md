## Task 12: `assign.stratify_by` in the draw

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`; Test `tests/test_units.py`, `tests/test_validate.py`

**Interfaces — Consumes:** `units.stratum_varies_within_cluster` (exists; do not reimplement the constancy test).

- [ ] **Step 1: Write the failing tests**

```python
def test_a_stratified_draw_balances_arms_within_every_stratum():
    """`stratify_by: [site]` over 12 units in sites A(6)/B(4)/C(2) — three
    strata of different sizes, so a draw balancing only overall would leave at
    least one stratum lopsided. Assert each stratum's per-arm counts exactly."""

def test_a_stratum_that_varies_within_a_cluster_is_refused(write_config):
    """§ Clustered units: `validate` 'rejects it instead of silently
    prioritizing one constraint'. Reuses `stratum_varies_within_cluster`."""

def test_an_unknown_stratum_attribute_is_refused(write_config):
    """*Allocation strata exist* — E-DATA-ASSIGN-STRATIFY-UNKNOWN, minted in
    task 3. The control: a declared attribute must NOT be refused."""
```

- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: `W-DATA-CLUSTER-UNDECLARED`'s exclusion list** excludes an attribute "a `sweep.groups` axis names or an `assign.from` reads… any `stratify_by`". **Under a draw there is no `assign.from`** — check the exclusion reaches `assign.stratify_by`, and add a test either way.
- [ ] **Step 6: Record, do not fix** — `assign.<axis>.stratify_by` is **not** in `CONSTANT_COLUMN_RULES`, so a stratum varying across a unit's measurement rows collapses silently, unlike `assign.<axis>.from` which H3c-1 wired in. Record it in `reference.md`, not in the gitignored `spec-defects.md`.
- [ ] **Step 7: Mutations; commit.**

---

