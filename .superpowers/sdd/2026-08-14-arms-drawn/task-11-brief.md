## Task 11: `blocked` beside `cluster_by` is refused

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_validate.py`

Task 2 wrote the ruling; this implements it. Mint `E-DATA-ASSIGN-BLOCKED-CLUSTER`.

- [ ] **Step 1: Write the failing test, with two controls that must report** — `random` beside `cluster_by` is legal (task 9 built it); `blocked` with no `cluster_by` is legal (task 10 built it). Assert exact finding sets on all three.
- [ ] **Step 2–4:** Fail, implement, pass. The message says what the sibling refusals say: block size counts units, a cluster is indivisible, no block size honours both — and names the two honest routes (`random` for a clustered draw, `by_attribute` for a read one).
- [ ] **Step 5: Mutate** each control separately; neither may die to the other's branch.
- [ ] **Step 6: Registry row in sort order**, checking every row it moves. Commit.

---

