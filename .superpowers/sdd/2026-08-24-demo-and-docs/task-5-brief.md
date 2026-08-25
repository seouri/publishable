## Task 5

**Binding corrections: 17, 18.**

**The `experiments` region body as a table, and `generate experiment`'s row merge** — the other
§ Generators `NOT BUILT` half. `Name | Template | Run`, one row per `configs/*/config.yaml`, sorted by
name, `Run` holding the `uv run publishable run configs/<name>/config.yaml` invocation. Empty state is
the documented `_(none yet — add one with `publishable generate experiment`)_` row.

**`## Experiments` is inside the region** as of task 3, so this body carries the heading. Read the
region span from `docs.py`; do not re-implement a scan.

**Mutation:** add a second experiment and confirm the region gains exactly one row and that **every
byte outside it is unchanged**, asserted as a whole-file comparison rather than as a substring.

---

