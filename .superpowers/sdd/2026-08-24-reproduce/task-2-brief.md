## Task 2

**Ruling Y, and the operand reader.** Build `src/publishable/reproduce.py` with the operand
discrimination and its refusals, and nothing else. Nothing is written to disk by this task.

> **RULING Y (binding, restated here):** `reproduce` takes a path and nothing else, and it does **not**
> resolve a target device. *"Reproducing on another device"* names where the user is, not an argument, so
> `reproduce` runs **on** the other device against a record it is given. No `--into`, no host, no user, no
> key, no behaviour-changing environment variable. **Cost if wrong:** a user with a bundle cannot
> reproduce from it, which is the case `study` exists to serve — so the bundle-member form is a
> first-class arm, not a note.

The discrimination is **structural, never by basename** (design Decision 1). A bundle member is
`main.run.yaml`, so `endswith("run.yaml")` is the reserved-name proxy this repo has already paid for at a
`report_by` stratum:

```python
def classify_operand(path: Path, c: Collector) -> "Operand | None":
    """One YAML parse, then three structural questions. See the design's
    Decision 1.

    NOT by basename: a bundle member is `main.run.yaml` (measured — the
    bundle `study add` writes holds `study.yaml` and `main.run.yaml` and no
    directory), so a basename test refuses the form Ruling Y exists for.
    """
    if path.is_dir():
        # E-REPRODUCE-OPERAND, naming `<path>/run.yaml`. `resume` is the one
        # command that takes a directory, and giving `reproduce` the same
        # operand for the opposite action is the confusion this refuses.
        ...
    doc = <parse; a read or parse failure is E-IO-FAILED, `diff`'s and
           `resume`'s precedent, not a code of this slice's own>
    if not isinstance(doc, dict):
        ...  # E-REPRODUCE-OPERAND
    if "study" in doc or "members" in doc:   # read study.py for the real key
        ...  # E-REPRODUCE-BUNDLE, LISTING the member names
    if "run_id" in doc:
        return Record(read_record_file(path), path)   # correction 7
    if "provenance" in doc or "results" in doc:
        ...  # E-REPRODUCE-OPERAND — an edited record, NOT read as a config
    if "experiment_type" in doc:
        return ConfigOperand(path)
    ...  # E-REPRODUCE-OPERAND
```

**Read `src/publishable/study.py` for the bundle root's actual key set before writing the
`E-REPRODUCE-BUNDLE` branch** — do not guess it from `study.yaml`'s documented example, and report what
you read.

**Every refusal goes through a fresh credential-bearing `Collector`, never raised into `main`**
(correction 21, H9b Decision 13): `main`'s handler applies no redaction pass.

**Fixture S**, five arms — a run directory, a `study.yaml` (a bundle with **two** members, because a
one-member bundle cannot distinguish *lists members* from *names the first*), a `run.yaml` with `run_id`
deleted, a YAML list, a missing path.

**Mutations:** discriminate by basename (caught by a bundle-member arm — build a minimal one here and
hand the full Fixture F to task 3's batch); read a `run_id`-less mapping as a config (Fixture S arm 3 —
its file has `provenance` and `results`, so the two readings genuinely differ); print the member
**count** instead of the names (Fixture S arm 2 — two members, so a count and a list differ).

**Must not touch:** `cli.py`'s dispatch (task 11), `lineage.py`, any guard-pin arm, the four documents.

---

