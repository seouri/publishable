## Task 10

**Pointer: Decision 9 binds this task.**

Read `sweep.yaml` rather than re-deriving it, and cross-check before anything runs.

- A reader returning the recorded `conditions` list and `execution_order`. **Grep for an existing
  `sweep.yaml` reader first** — `freeze` has one — and report the grep; reuse it if it fits, and say
  what you found either way.
- Absent, unparseable, or holding no `conditions` list → `E-RESUME-PLAN-MISSING`.
- Cross-check the recorded conditions against the re-expanded ones over the **full four-tuple**
  `index`/`label`/`values`/`is_baseline`, **in recorded order** → `E-RESUME-PLAN-MISMATCH`. The
  four-tuple is `freeze`'s measured shape, not a choice: `values` determines the cfg an execution runs
  under, and a two-field check misses it moving under `ablate` or a declared `baseline`.
- Order the rebuilt plan by `execution_order`. Under a `batch` level this is load-bearing rather than
  tidy: batches are positions in time, and a resume free to pick its own order could open batch 4 while
  batch 3 still had executions outstanding.

**Must not touch:** `sweep.py`'s `sweep_document`; `freeze.py`'s own reader if you reuse it; any
`*.md`.

**Mutations:** cross-check on `index` and `label` only (caught by a fixture editing a recorded
`values` and nothing else — two branches checked: the two-field reading passes, the four-tuple reading
refuses); re-realize the order under `order: randomized` (caught by a fixture whose recorded
`execution_order` is edited to an order the seed does not reproduce).

---

