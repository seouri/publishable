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

