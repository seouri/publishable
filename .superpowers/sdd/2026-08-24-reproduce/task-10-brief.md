## Task 10

**Ruling BB's first half: `reproduce` writes the expectation and refuses nothing on apparatus grounds.**

> **RULING BB** as restated in task 9. **This task's half is the writer.** `reproduce` **probes nothing,
> compares nothing and refuses nothing** on apparatus grounds — it is not one of the four places a probe
> runs, exactly as `diff` is not, and for the same reason: no config resolved against a plugin it does not
> have.

When `provenance.apparatus` is non-`null`, write `configs/<name>/apparatus.expected.json` — the recorded
`facts` mapping **verbatim**, condition key to fact mapping — **once**, refusing to overwrite an existing
one (`E-REPRODUCE-EXPECTED-EXISTS`) rather than replacing it, and print the block § Reproducing on another
device already specifies:

```
This run measured through an apparatus. Reproducing it needs:
  llm_deployment   model_revision  gpt-5.5-2026-06-11
                   api_version     2026-05-01
```

**`provenance.apparatus` gains no key naming the expectation**, and H6a Ruling C's refusal of a definition
marker is the precedent: the reproduction's record carries what it **observed**, and a key naming what it
was compared against is a second source of truth for a comparison the checkout's own file already holds.
Disclosure item 4.

**Fixture O.** The template is **project-local** with a real installed probe distribution, and
`provenance.apparatus.facts` **has two conditions with different facts** — one condition cannot tell a
per-condition write from a flattened one. Arm 2 is the second `reproduce` into a destination already
holding the file.

**Mutations:** overwrite an existing file (O arm 2); flatten the per-condition mapping (O arm 1, which
asserts mapping for mapping).

**Must not touch:** `apparatus.py`, `run_record.py`'s `provenance` assembly, guard-pin arm G's cited
`provenance` key-list arms.

---

